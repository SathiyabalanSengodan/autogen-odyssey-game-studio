"""Tools the game engineer calls and the game tester runs.

The engineer never runs code itself. It calls these tools, and the tester
agent executes them on this machine and reports the result back to the chat.
"""

import os
import py_compile
import subprocess
import sys
from pathlib import Path
from typing import Annotated

WORK_DIR = Path(__file__).parent / "coding"
GAME_FILE = WORK_DIR / "odyssey.py"
SMOKE_TEST_TIMEOUT = 90
SMOKE_TEST_PASS_LINE = "SMOKE TEST OK"


MIN_GAME_LINES = 100


def _compile_error():
    try:
        py_compile.compile(str(GAME_FILE), doraise=True)
    except py_compile.PyCompileError as error:
        return error.msg
    return None


def save_game(
    code: Annotated[str, "The complete source of odyssey.py"] = "",
) -> str:
    """Write the whole game to coding/odyssey.py and check that it compiles."""
    # A reply cut off by max_tokens reaches the tool with no arguments at all
    if not code.strip():
        return "FAILED: no code arrived. Your reply was probably cut off. Send a shorter file."
    lines = len(code.splitlines())
    if lines < MIN_GAME_LINES:
        return (
            f"REFUSED: {lines} lines is not a whole game, and saving it would wipe odyssey.py. "
            "To change part of the file, use edit_game."
        )
    WORK_DIR.mkdir(exist_ok=True)
    GAME_FILE.write_text(code)
    error = _compile_error()
    if error:
        return f"Saved {lines} lines, but it does not compile:\n{error}"
    return f"Saved {lines} lines to {GAME_FILE.name}. It compiles."


def edit_game(
    old: Annotated[str, "Exact text from the current odyssey.py. It must appear exactly once."],
    new: Annotated[str, "The text to put in its place"],
) -> str:
    """Replace one snippet of coding/odyssey.py and check that it still compiles."""
    if not GAME_FILE.exists():
        return "FAILED: odyssey.py does not exist yet. Call save_game first."
    source = GAME_FILE.read_text()
    count = source.count(old)
    if count != 1:
        return f"FAILED: the old text appears {count} times. It must appear exactly once. Use read_game to check."
    GAME_FILE.write_text(source.replace(old, new))
    error = _compile_error()
    if error:
        GAME_FILE.write_text(source)  # keep the last version that compiled
        return f"FAILED: the edit does not compile, so it was undone:\n{error}"
    return f"Edited {GAME_FILE.name}. It compiles."


def read_game(
    start_line: Annotated[int, "First line to show, counting from 1"] = 1,
    end_line: Annotated[int, "Last line to show"] = 200,
) -> str:
    """Show part of coding/odyssey.py with line numbers."""
    if not GAME_FILE.exists():
        return "odyssey.py does not exist yet."
    lines = GAME_FILE.read_text().splitlines()
    shown = lines[max(start_line, 1) - 1 : end_line]
    numbered = "\n".join(f"{n:4} {line}" for n, line in enumerate(shown, start=max(start_line, 1)))
    return f"odyssey.py has {len(lines)} lines.\n{numbered}"


def smoke_test() -> str:
    """Run `python odyssey.py --smoke-test` headless and report whether it passed."""
    if not GAME_FILE.exists():
        return "FAILED: odyssey.py does not exist yet. Call save_game first."

    # Dummy SDL drivers let pygame run with no window and no sound card
    env = {**os.environ, "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"}
    try:
        result = subprocess.run(
            [sys.executable, GAME_FILE.name, "--smoke-test"],
            cwd=WORK_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=SMOKE_TEST_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return f"FAILED: still running after {SMOKE_TEST_TIMEOUT}s. The smoke test must exit on its own."

    output = (result.stdout + result.stderr)[-3000:]  # keep the tail, where errors are
    passed = result.returncode == 0 and SMOKE_TEST_PASS_LINE in result.stdout
    verdict = "PASSED" if passed else f"FAILED (exit code {result.returncode})"
    return f"{verdict}\n--- output ---\n{output}"
