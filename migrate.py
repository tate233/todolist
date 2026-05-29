#!/usr/bin/env python3
"""CLI to migrate legacy JSON/.md notes into SQLite.

Usage:
    python migrate.py            # migrate the default ~/.smart_notes store
    python migrate.py --no-backup
"""
import argparse
import logging

from config import config
from storage.migrator import migrate


def main():
    parser = argparse.ArgumentParser(description="Migrate JSON/.md notes to SQLite")
    parser.add_argument("--no-backup", action="store_true", help="skip backing up the data dir")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    report = migrate(
        json_path=config.database_file,
        notes_dir=config.notes_dir,
        sqlite_path=config.sqlite_file,
        data_dir=config.data_dir,
        do_backup=not args.no_backup,
    )
    print("迁移完成:", report)
    if report.failed:
        print("失败的笔记 id:", ", ".join(report.failed))


if __name__ == "__main__":
    main()
