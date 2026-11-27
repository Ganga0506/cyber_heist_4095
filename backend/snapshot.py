"""Create or restore a consistent SQLite snapshot at a new path."""

import argparse
import os
import sqlite3
from contextlib import closing
from pathlib import Path


def copy_database(source: Path, destination: Path):
    source = source.resolve(strict=True)
    destination = destination.absolute()
    with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as source_db:
        os.close(os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
        try:
            with closing(sqlite3.connect(destination)) as snapshot:
                source_db.backup(snapshot)
                if snapshot.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                    raise ValueError("Snapshot integrity check failed")
                if snapshot.execute("PRAGMA foreign_key_check").fetchone():
                    raise ValueError("Snapshot foreign key check failed")
        except (Exception, KeyboardInterrupt):
            destination.unlink()
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    copy_database(args.source, args.destination)
