"""Shared timestamped progress printing, used by every engine (native, pyrit,
promptfoo) so the terminal output reads as one live timeline of the run — see
AGENTS.md: progress needs to "look good running live in front of someone."
A timestamp on each line also makes a hang or slow LLM call visible as it
happens, instead of only showing up later as a bare traceback.
"""

from datetime import datetime


def progress(message: str, *, end: str = "\n", flush: bool = False) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", end=end, flush=flush)
