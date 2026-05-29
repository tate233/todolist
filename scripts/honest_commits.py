"""Create small, honest project-note commits.

This script appends timestamped entries to a journal file and commits only that
file. It is meant for personal practice or milestone logging without pretending
that unrelated changes are bug fixes.
"""

from __future__ import annotations

import argparse
import subprocess
from datetime import datetime
from pathlib import Path


DEFAULT_JOURNAL = "COMMIT_JOURNAL.md"


def run_git(args: list[str], *, dry_run: bool) -> None:
    command = ["git", *args]
    if dry_run:
        print(" ".join(command))
        return
    subprocess.run(command, check=True)


def append_note(journal: Path, note: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not journal.exists():
        journal.write_text("# Commit Journal\n\n", encoding="utf-8")

    with journal.open("a", encoding="utf-8") as file:
        file.write(f"- {timestamp} - {note}\n")


def build_message(index: int, total: int) -> str:
    if total == 1:
        return "chore: record project maintenance note"
    return f"chore: record project maintenance note {index}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create honest journal commits.")
    parser.add_argument("-c", "--count", type=int, default=1, help="number of commits to create")
    parser.add_argument(
        "-n",
        "--note",
        default="Personal project activity note.",
        help="journal note text to append",
    )
    parser.add_argument(
        "-j",
        "--journal",
        default=DEFAULT_JOURNAL,
        help="journal file to update",
    )
    parser.add_argument("--dry-run", action="store_true", help="print git commands without committing")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.count < 1:
        raise SystemExit("--count must be at least 1")

    journal = Path(args.journal)
    for index in range(1, args.count + 1):
        note = args.note if args.count == 1 else f"{args.note} ({index}/{args.count})"
        if args.dry_run:
            print(f"append to {journal}: {note}")
        else:
            append_note(journal, note)

        run_git(["add", "--", str(journal)], dry_run=args.dry_run)
        run_git(["commit", "-m", build_message(index, args.count)], dry_run=args.dry_run)


if __name__ == "__main__":
    main()
