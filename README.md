# AutoGen: An Agent Game Studio Builds an Odyssey Platformer

A team of [AutoGen](https://github.com/ag2ai/ag2) agents designs, codes, tests and reviews a 2D platformer inspired by Super Mario Odyssey. The hero throws a living cap to capture enemies and use their powers, collects Power Moons, and flies an airship between kingdoms. Everything is drawn with pygame shapes, so the game uses no Nintendo assets.

The build the reviewer approved is committed as [coding/odyssey.py](coding/odyssey.py): *Odyssey of the Living Cap*, three kingdoms and 15 moons in about 840 lines.

## Just play it

```bash
pip install pygame
python coding/odyssey.py
```

| Key | Action |
|-----|--------|
| Arrows or A/D | Run |
| Space, Up or W | Jump (hold to charge while captured as Springtoad or Rockbeetle) |
| X or J | Throw Brim the cap to capture an enemy or bounce on it mid-air. Press again to release. |
| Enter | Board the Lanternwing airship once you have enough moons |
| Esc | Quit |

Captured enemies give different powers. The Springtoad does a charged super jump. The Rockbeetle is spike-proof and smashes cracked blocks. The Puffkite glides and rides wind vents.

## What it covers

- A **group chat** (`GroupChat` + `GroupChatManager`) with four agents, each with its own role
- A **custom speaker selector**: a plain Python function hands the turn from agent to agent instead of an LLM choosing
- **Tool use**: the engineer calls `save_game`, `edit_game`, `read_game` and `smoke_test` as tools (`register_for_llm`), and a tester agent with no LLM runs them (`register_for_execution`)
- A **headless smoke test**: the game must play itself with scripted inputs under SDL's dummy video driver, so the agents can check it with no window
- A **review loop**: the reviewer approves the build or sends concrete fixes back to the engineer

## The team

| Agent | LLM | Job |
|-------|-----|-----|
| `producer` | no | Posts the pitch (that's you) |
| `game_designer` | Claude | Writes a short design doc |
| `game_engineer` | Claude | Writes `odyssey.py` and calls the tools |
| `game_tester` | no | Runs the engineer's tool calls on this machine |
| `game_reviewer` | Claude | Approves the build or lists fixes |

```
producer → designer → engineer ⇄ tester
                         ↑  ↓
                       reviewer → APPROVED → done
```

## Files

| File | What it does |
|------|--------------|
| [build_game.py](build_game.py) | Builds the agents and the group chat, then runs it |
| [game_tools.py](game_tools.py) | The `save_game`, `edit_game`, `read_game` and `smoke_test` tools |
| [claude_client.py](claude_client.py) | ag2's Anthropic client, minus the `temperature` param that current Claude models reject |

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your Anthropic API key

python build_game.py                                  # the team builds a new game
python coding/odyssey.py                              # play it
python build_game.py --idea "add a snow kingdom"      # pitch an extra idea
python build_game.py --max-round 60                   # give the team more turns
```

Set `CLAUDE_MODEL` in `.env` to use a model other than `claude-opus-5-5`, and `CLAUDE_EFFORT` (`low` to `max`, default `medium`) to change how hard Claude thinks.

A build takes about 20–30 minutes. Most of that is the engineer's first call: Opus 5.5 thinks hard and then writes the whole file, about 75K output tokens in the approved run. After that, fixes are small `edit_game` calls. Each run starts from scratch and overwrites `coding/odyssey.py`. `ClaudeClient` prints the output tokens and stop reason of every reply, so you can see where the time goes.

> ⚠️ The smoke test runs the generated game on your machine with no sandbox. Read `coding/odyssey.py` if you're unsure.
