"""A team of AutoGen agents builds a Super Mario Odyssey-style platformer.

Four agents share one group chat:
  game_designer  writes the design doc
  game_engineer  writes the pygame code and calls the file and smoke-test tools
  game_tester    runs those tools on this machine (no LLM)
  game_reviewer  plays the code in its head and approves it or asks for fixes

    python build_game.py                     # build the game, then play it
    python build_game.py --max-round 60      # give the team more turns
    python build_game.py --idea "add a snow kingdom with ice physics"
"""

import argparse
import os
import re

from autogen import ConversableAgent, GroupChat, GroupChatManager
from dotenv import load_dotenv

from claude_client import ClaudeClient
from game_tools import GAME_FILE, SMOKE_TEST_PASS_LINE, edit_game, read_game, save_game, smoke_test

APPROVED = "VERDICT: APPROVED"
CHANGES = "VERDICT: CHANGES NEEDED"

PITCH = """\
Build a 2D side-scrolling platformer inspired by Super Mario Odyssey, in Python with pygame.
The hero wears a living cap. They can throw it at enemies to capture them and take control
of them, and they collect Power Moons to fuel their airship and fly to the next kingdom.
Make it fun to play for five minutes."""

DESIGNER_PROMPT = """\
You are a game designer. Turn the pitch into a short, buildable design doc for a single-file
pygame game. Cover: controls, the hero's moves (run, jump, cap throw, cap bounce), the
capture mechanic with at least two enemy types that each give the hero a different ability
when captured, Power Moons and coins, at least two kingdoms with distinct colours and layouts,
the airship that travels between kingdoms, the HUD, and the title / win / game-over screens.
All art is drawn with pygame shapes. No image or sound files, and no copied Nintendo assets
or names other than the "Odyssey" theme itself. Keep it under 400 words. Do not write code."""

ENGINEER_PROMPT = f"""\
You are a senior Python game engineer. Implement the design doc as one file, odyssey.py,
using only the standard library and pygame.

Rules:
- Write the first version with save_game, which takes the whole file. Make every later fix
  with edit_game, which swaps one exact snippet, so you never resend the whole game.
  Use read_game to check the current code before an edit if you are unsure of it.
- Keep the file under about 900 lines. Prefer a tight, working game over a sprawling one.
- Draw everything with pygame shapes and fonts. Load no external files.
- Run at 60 FPS in an 960x540 window with a scrolling camera.
- `python odyssey.py --smoke-test` must run without a real display: skip the title screen,
  play about 1800 frames with scripted inputs that run, jump, throw the cap, capture an enemy,
  collect a moon and travel to the second kingdom, without waiting on the clock. You may place
  the hero next to each challenge, but the capture, the moon pickup and the travel must happen
  through the normal update and collision code, never by setting game state directly. Then print a
  line starting with "{SMOKE_TEST_PASS_LINE}" followed by a few stats and exit with code 0.
  Any exception must reach the console, so do not swallow errors.

Plan briefly, then write the code. Workflow: call save_game with the full code, then call
smoke_test. If either one reports a problem, fix it with edit_game and run smoke_test again.
When the smoke test passes, reply with a short summary of what you built and the controls,
and do not call any tool in that message."""

REVIEWER_PROMPT = f"""\
You are a lead game reviewer. The latest odyssey.py the engineer saved is at the end of this
message. Read it together with the latest smoke test result in the chat. Check that the game matches the design doc and look for real bugs: crashes,
softlocks, unreachable moons, a capture that cannot be undone, broken kingdom travel, or a
smoke test that skips the real game logic.

Start your reply with exactly one of these lines:
{APPROVED}
{CHANGES}
Approve when the smoke test passed and you found no real bugs, and add a one-line verdict.
Otherwise, list at most five concrete fixes for the engineer, most important first.
Do not ask for polish or new features. Do not write the code yourself."""


def build_llm_config():
    load_dotenv()  # searches parent folders, so the workspace-root .env works too
    return {
        "config_list": [
            {
                "api_type": "anthropic",
                "model_client_cls": "ClaudeClient",
                "model": os.getenv("CLAUDE_MODEL", "claude-opus-5-5"),
                "api_key": os.environ["ANTHROPIC_API_KEY"],
                # Opus 5.5 always thinks before it writes, and the whole game
                # file comes on top of that. The Anthropic SDK only allows a
                # max_tokens this large on streamed requests.
                "max_tokens": 128000,
                "stream": True,
                # Thinking depth (low / medium / high / xhigh / max)
                "effort": os.getenv("CLAUDE_EFFORT", "medium"),
            }
        ]
    }


def build_agents(llm_config):
    def llm_agent(name, system_message):
        return ConversableAgent(
            name=name,
            system_message=system_message,
            llm_config=llm_config,
            human_input_mode="NEVER",
        )

    designer = llm_agent("game_designer", DESIGNER_PROMPT)
    engineer = llm_agent("game_engineer", ENGINEER_PROMPT)
    reviewer = llm_agent("game_reviewer", REVIEWER_PROMPT)

    # The tester has no LLM. It only runs the tools the engineer asks for.
    tester = ConversableAgent(
        name="game_tester",
        llm_config=False,
        human_input_mode="NEVER",
    )

    for tool, description in [
        (save_game, "Save the complete odyssey.py and check that it compiles."),
        (edit_game, "Replace one exact snippet of odyssey.py and check that it still compiles."),
        (read_game, "Show a range of odyssey.py lines with line numbers."),
        (smoke_test, "Run odyssey.py --smoke-test headless and report pass or fail."),
    ]:
        engineer.register_for_llm(name=tool.__name__, description=description)(tool)
        tester.register_for_execution(name=tool.__name__)(tool)

    # Register the client last. register_for_llm rebuilds the engineer's
    # client list, which would drop a ClaudeClient registered before it.
    for agent in (designer, engineer, reviewer):
        agent.register_model_client(ClaudeClient)

    return designer, engineer, tester, reviewer


def is_approved(message):
    # Markdown bold or a leading space should not hide the verdict line
    return re.match(rf"\W*{APPROVED}", message.get("content") or "") is not None


def show_latest_game(reviewer):
    # Other agents' tool-call arguments don't reach the reviewer's history,
    # so hand it the saved file directly.
    code = GAME_FILE.read_text() if GAME_FILE.exists() else "(no file saved yet)"
    reviewer.update_system_message(f"{REVIEWER_PROMPT}\n\nodyssey.py:\n```python\n{code}\n```")


def build_speaker_selector(producer, designer, engineer, tester, reviewer):
    """Fixed hand-offs instead of letting an LLM pick who talks next."""

    def select_next_speaker(last_speaker, groupchat):
        message = groupchat.messages[-1]
        if last_speaker is producer:
            return designer
        if last_speaker is designer or last_speaker is tester:
            return engineer
        if last_speaker is engineer:
            # A tool request goes to the tester, a finished summary goes to review
            if message.get("tool_calls"):
                return tester
            show_latest_game(reviewer)
            return reviewer
        if last_speaker is reviewer:
            return None if is_approved(message) else engineer
        return None

    return select_next_speaker


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--max-round", type=int, default=40, help="most messages the team may send")
    parser.add_argument("--idea", help="an extra idea to add to the pitch")
    args = parser.parse_args()

    designer, engineer, tester, reviewer = build_agents(build_llm_config())

    # The producer is you. It only posts the pitch.
    producer = ConversableAgent(name="producer", llm_config=False, human_input_mode="NEVER")
    agents = [producer, designer, engineer, tester, reviewer]

    groupchat = GroupChat(
        agents=agents,
        messages=[],
        max_round=args.max_round,
        speaker_selection_method=build_speaker_selector(*agents),
    )
    manager = GroupChatManager(groupchat=groupchat, llm_config=False)

    pitch = PITCH if not args.idea else f"{PITCH}\nExtra idea from the producer: {args.idea}"
    producer.initiate_chat(manager, message=pitch)

    last = groupchat.messages[-1]
    if last.get("name") == reviewer.name and is_approved(last):
        print(f"\nThe reviewer approved the game. Play it:\n  python {GAME_FILE.relative_to(GAME_FILE.parent.parent)}")
    elif GAME_FILE.exists():
        print(f"\nThe team ran out of turns before approval. The latest build is at {GAME_FILE}")
    else:
        print("\nThe team ran out of turns before saving any code.")


if __name__ == "__main__":
    main()
