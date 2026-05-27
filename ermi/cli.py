from __future__ import annotations

import argparse
from pathlib import Path

from .graph import export_graph
from .ingest import ingest_export, init_archive
from .search import search
from .storage import Store


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ermi", description="Externalized Recursive Memory Infrastructure")
    parser.add_argument("--root", type=Path, default=Path("archive"), help="Archive root directory.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Create the archive directories and SQLite schema.")

    ingest_parser = subparsers.add_parser("ingest", help="Ingest ChatGPT conversations.json.")
    ingest_parser.add_argument("source", type=Path)

    search_parser = subparsers.add_parser("search", help="Semantic search over indexed chunks.")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=5)

    entity_parser = subparsers.add_parser("entities", help="List extracted entities.")
    entity_parser.add_argument("--limit", type=int, default=50)

    subparsers.add_parser("graph", help="Export graph.json.")

    args = parser.parse_args(argv)
    root = args.root.resolve()

    if args.command == "init":
        init_archive(root)
        print(f"Initialized ERMI archive at {root}")
        return 0
    if args.command == "ingest":
        stats = ingest_export(args.source.resolve(), root)
        print("Ingest complete")
        for key, value in stats.items():
            print(f"{key}: {value}")
        return 0
    if args.command == "search":
        for item in search(root, args.query, args.limit):
            print(f"{item['score']:.3f} | {item['title']}")
            print(f"      {item['markdown_path']}")
            print(f"      {item['preview']}")
        return 0
    if args.command == "entities":
        with Store(root / "ermi.sqlite3") as store:
            rows = store.conn.execute(
                "SELECT name, kind, score FROM entities ORDER BY score DESC, name LIMIT ?",
                (args.limit,),
            ).fetchall()
        for row in rows:
            print(f"{row['score']:.1f} | {row['kind']} | {row['name']}")
        return 0
    if args.command == "graph":
        target = export_graph(root)
        print(f"Exported graph to {target}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

