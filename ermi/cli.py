from __future__ import annotations

import argparse
from pathlib import Path

from .chatlasso import import_chatlasso
from .exports import activity_summary, export_chat_csv, export_obsidian_second_brain, list_chat_titles, mine_code_blocks
from .flags import list_flags
from .graph import export_graph
from .ingest import ingest_export, init_archive
from .ops import backup_archive, restore_archive
from .review import list_import_reviews, set_import_review_status
from .search import search
from .storage import LATEST_SCHEMA_VERSION, Store
from .timeline import concept_timeline
from .watch import add_watcher, load_watchers, scan_chatlasso_watchers, watch_chatlasso


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ermi", description="Externalized Recursive Memory Infrastructure")
    parser.add_argument("--root", type=Path, default=Path("archive"), help="Archive root directory.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Create the archive directories and SQLite schema.")

    ingest_parser = subparsers.add_parser("ingest", help="Ingest ChatGPT conversations.json.")
    ingest_parser.add_argument("source", type=Path)

    titles_parser = subparsers.add_parser("chatgpt-titles", help="List titles in a ChatGPT conversations.json export.")
    titles_parser.add_argument("source", type=Path)

    csv_parser = subparsers.add_parser("export-chatgpt-csv", help="Export true-path ChatGPT messages to CSV.")
    csv_parser.add_argument("source", type=Path)
    csv_parser.add_argument("--target", type=Path)

    code_parser = subparsers.add_parser("mine-chatgpt-code", help="Extract assistant code blocks from true-path ChatGPT messages.")
    code_parser.add_argument("source", type=Path)
    code_parser.add_argument("--target", type=Path)

    activity_parser = subparsers.add_parser("chatgpt-activity", help="Show most active days in a ChatGPT export.")
    activity_parser.add_argument("source", type=Path)
    activity_parser.add_argument("--limit", type=int, default=5)

    obsidian_parser = subparsers.add_parser("export-chatgpt-obsidian", help="Export categorized Obsidian-ready Markdown from ChatGPT.")
    obsidian_parser.add_argument("source", type=Path)
    obsidian_parser.add_argument("--target", type=Path, default=Path("archive") / "exports" / "chatgpt_obsidian")

    chatlasso_parser = subparsers.add_parser("import-chatlasso", help="Import ChatLasso SSI Markdown files.")
    chatlasso_parser.add_argument("source", type=Path)

    watch_parser = subparsers.add_parser("watch-chatlasso", help="Watch ChatLasso SSI folders and import changes.")
    watch_parser.add_argument("source", type=Path, nargs="?")
    watch_parser.add_argument("--interval", type=int, default=15)
    watch_parser.add_argument("--once", action="store_true")

    subparsers.add_parser("migrate", help="Run SQLite schema migrations.")

    search_parser = subparsers.add_parser("search", help="Hybrid search over indexed chunks.")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=5)
    search_parser.add_argument("--mode")
    search_parser.add_argument("--status")
    search_parser.add_argument("--archetype")
    search_parser.add_argument("--project")
    search_parser.add_argument("--identity")
    search_parser.add_argument("--regression", action="store_true")

    entity_parser = subparsers.add_parser("entities", help="List extracted entities.")
    entity_parser.add_argument("--limit", type=int, default=50)

    subparsers.add_parser("flags", help="List regression and import-review flags.")
    subparsers.add_parser("timeline", help="List concept evolution events.")
    subparsers.add_parser("graph", help="Export graph.json.")
    subparsers.add_parser("review", help="List import review queue.")
    accept_parser = subparsers.add_parser("accept-import", help="Accept an import review item.")
    accept_parser.add_argument("conversation_id")
    reject_parser = subparsers.add_parser("reject-import", help="Reject an import review item.")
    reject_parser.add_argument("conversation_id")
    backup_parser = subparsers.add_parser("backup", help="Create an archive backup.")
    backup_parser.add_argument("--target", type=Path)
    restore_parser = subparsers.add_parser("restore", help="Restore archive content from a backup folder.")
    restore_parser.add_argument("source", type=Path)

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
    if args.command == "chatgpt-titles":
        for title in list_chat_titles(args.source.resolve()):
            print(title)
        return 0
    if args.command == "export-chatgpt-csv":
        target = args.target or (root / "exports" / "chat_history.csv")
        stats = export_chat_csv(args.source.resolve(), target.resolve())
        print(f"CSV exported to {target.resolve()}")
        for key, value in stats.items():
            print(f"{key}: {value}")
        return 0
    if args.command == "mine-chatgpt-code":
        target = args.target or (root / "exports" / "all_extracted_code.txt")
        stats = mine_code_blocks(args.source.resolve(), target.resolve())
        print(f"Code exported to {target.resolve()}")
        for key, value in stats.items():
            print(f"{key}: {value}")
        return 0
    if args.command == "chatgpt-activity":
        for item in activity_summary(args.source.resolve(), args.limit):
            print(f"{item['date']}: {item['message_count']}")
        return 0
    if args.command == "export-chatgpt-obsidian":
        stats = export_obsidian_second_brain(args.source.resolve(), args.target.resolve())
        print(f"Obsidian export written to {args.target.resolve()}")
        for key, value in stats.items():
            print(f"{key}: {value}")
        return 0
    if args.command == "import-chatlasso":
        stats = import_chatlasso(args.source.resolve(), root)
        print("ChatLasso import complete")
        for key, value in stats.items():
            print(f"{key}: {value}")
        return 0
    if args.command == "watch-chatlasso":
        if args.source:
            watchers = add_watcher(root, args.source.resolve())
            print("Watching ChatLasso sources:")
            for item in watchers:
                print(f"  {item}")
        if args.once:
            stats = scan_chatlasso_watchers(root)
            print("Watch scan complete")
            for key, value in stats.items():
                print(f"{key}: {value}")
            return 0
        print(f"Watching ChatLasso folders every {args.interval}s. Press Ctrl+C to stop.")
        try:
            watch_chatlasso(root, args.interval)
        except KeyboardInterrupt:
            print("Stopped watcher.")
        return 0
    if args.command == "migrate":
        with Store(root / "ermi.sqlite3") as store:
            print(f"Schema version: {store.schema_version()} / {LATEST_SCHEMA_VERSION}")
        return 0
    if args.command == "search":
        filters = {
            "mode": args.mode,
            "status": args.status,
            "archetype": args.archetype,
            "project": args.project,
            "identity": args.identity,
            "regression": True if args.regression else None,
        }
        for item in search(root, args.query, args.limit, filters):
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
    if args.command == "flags":
        for item in list_flags(root):
            print(f"{item['title']} | {item['reason'] if 'reason' in item else item['loss_report'] or 'flagged'}")
        return 0
    if args.command == "timeline":
        for item in concept_timeline(root):
            print(f"{item['event_at']} | {item['concept'] or item['title']} | {item['mode'] or 'unknown'}")
        return 0
    if args.command == "review":
        for item in list_import_reviews(root):
            print(f"{item['status']} | {item['conversation_id']} | {item['title']} | {item['reason']}")
        return 0
    if args.command == "accept-import":
        print(set_import_review_status(root, args.conversation_id, "accepted"))
        return 0
    if args.command == "reject-import":
        print(set_import_review_status(root, args.conversation_id, "rejected"))
        return 0
    if args.command == "backup":
        print(f"Backup created at {backup_archive(root, args.target)}")
        return 0
    if args.command == "restore":
        print(f"Restored archive at {restore_archive(root, args.source.resolve())}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
