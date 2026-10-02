"""ag2 model client for current Claude models.

ag2 0.x's built-in AnthropicClient always sends `temperature` (default 1.0).
Current Claude models such as Opus 5.5 reject sampling parameters, so this
subclass drops it, and forwards an `"effort"` config key (low / medium / high /
xhigh / max) as `output_config.effort`, which ag2 would otherwise drop.
Everything else is ag2's own Anthropic client.

With `"stream": True` this client also:
- mutes ag2's echo of every streamed chunk (ag2 prints the whole message
  again afterwards, so each message would show up twice)
- warns when a reply hits max_tokens. ag2 hides that, and a cut-off tool
  call reaches the tool as empty arguments.

Use it by putting `"model_client_cls": "ClaudeClient"` in the llm_config and
calling `agent.register_model_client(ClaudeClient)` on each agent that uses it.
"""

from autogen.io import IOStream
from autogen.oai.anthropic import AnthropicClient


class _MutedStream:
    def print(self, *objects, **kwargs):
        pass

    def send(self, message):
        pass

    def input(self, prompt="", *, password=False):
        return ""


class ClaudeClient(AnthropicClient):
    def __init__(self, config, **kwargs):
        super().__init__(**config)
        self.last_stop_reason = None
        self.last_output_tokens = 0
        create_stream = self._client.messages.create

        def tapped_create(**kwargs):
            return self._tap(create_stream(**kwargs))

        self._client.messages.create = tapped_create

    def _tap(self, stream):
        for event in stream:
            if event.type == "message_delta":
                self.last_stop_reason = event.delta.stop_reason
                self.last_output_tokens = event.usage.output_tokens
            yield event

    def load_config(self, params):
        anthropic_params = super().load_config(params)
        anthropic_params.pop("temperature", None)
        # ag2 doesn't forward effort, the only thinking control on Opus 5.5
        if params.get("effort"):
            anthropic_params["output_config"] = {"effort": params["effort"]}
        return anthropic_params

    def create(self, params):
        if not params.get("stream"):
            return super().create(params)
        with IOStream.set_default(_MutedStream()):
            response = super().create(params)
        print(f"[ClaudeClient] {self.last_output_tokens} output tokens, stop reason: {self.last_stop_reason}")
        if self.last_stop_reason == "max_tokens":
            print("[ClaudeClient] WARNING: the reply hit max_tokens and was cut off")
        return response
