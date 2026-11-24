"""Example helper script for a skill.

Put deterministic, repeatable steps in scripts like this one so the agent runs
them instead of rewriting the code each time. Print clear, specific messages:
the agent reads this output and acts on it.

Usage:
    python scripts/example.py INPUT_FILE
"""
import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", type=Path, help="file to process")
    args = parser.parse_args()

    if not args.input.exists():
        # Say what went wrong and how to fix it.
        print(f"ERROR: {args.input} not found. Pass the path to an existing file.", file=sys.stderr)
        return 1

    print(f"OK: {args.input} ({args.input.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
