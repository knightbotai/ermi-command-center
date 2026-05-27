from __future__ import annotations

import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .embeddings import get_embedder
from .entities import extract_entities
from .ingest import init_archive, safe_slug, sha256, timestamp_to_iso, yamlish
from .storage import Store

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$", re.MULTILINE)


def import_chatlasso(source: Path, root: Path) -> dict[str, int]:
    init_archive(root)
    files = discover_markdown(source)
    embedder = get_embedder()
    imported_at = datetime.now(timezone.utc).isoformat()
    conversations = []

    with Store(root / "ermi.sqlite3") as store:
        for file_path in files:
            raw_path = copy_chatlasso_source(file_path, root / "raw" / "chatlasso")
            source_id = store.upsert_source(str(raw_path), imported_at, sha256(file_path))
            conversation = normalize_chatlasso_file(file_path, source_id, root, embedder)
            write_chatlasso_markdown(conversation)
            store.replace_conversation(conversation)
            conversations.append(conversation)

    return {
        "sources": len(files),
        "conversations": len(conversations),
        "messages": sum(len(item["messages"]) for item in conversations),
        "chunks": sum(len(item["chunks"]) for item in conversations),
        "entities": sum(len(item["entities"]) for item in conversations),
    }


def import_chatlasso_payload(title: str, content: str, root: Path) -> dict[str, int]:
    init_archive(root)
    safe_title = clean_title(title or first_heading(split_frontmatter(content)[1]) or "ChatLasso SSI")
    payload_dir = root / "raw" / "chatlasso_payloads"
    payload_dir.mkdir(parents=True, exist_ok=True)
    digest = sha256_text(content)[:12]
    source = payload_dir / f"{safe_slug(safe_title)}-{digest}.md"
    if not source.exists():
        source.write_text(content, encoding="utf-8")
    return import_chatlasso(source, root)


def discover_markdown(source: Path) -> list[Path]:
    if source.is_file():
        return [source] if source.suffix.lower() in {".md", ".markdown"} else []
    if source.is_dir():
        return sorted(
            path
            for path in source.rglob("*")
            if path.is_file() and path.suffix.lower() in {".md", ".markdown"}
        )
    raise FileNotFoundError(source)


def copy_chatlasso_source(source: Path, raw_dir: Path) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    digest = sha256(source)[:12]
    target = raw_dir / f"{source.stem}-{digest}{source.suffix}"
    if not target.exists():
        shutil.copy2(source, target)
    return target


def sha256_text(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_chatlasso_file(source: Path, source_id: int, root: Path, embedder: Any) -> dict[str, Any]:
    text = source.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    metadata = parse_frontmatter(frontmatter)
    title = clean_title(metadata.get("title") or first_heading(body) or source.stem)
    cid = f"chatlasso_{sha256(source)[:16]}"
    created_at = metadata.get("date_extracted") or timestamp_to_iso(source.stat().st_mtime)
    year = year_from_iso(created_at)
    tags = sorted({"chatlasso", "ssi", "synthesis", *metadata_tags(metadata)})
    chunks = build_chatlasso_chunks(cid, title, body, tags, embedder)
    domain_nodes = parse_list_value(metadata.get("domain_nodes", ""))
    entity_candidates = extract_entities(text)
    entities = [{"name": name, "kind": kind, "score": score} for name, kind, score in entity_candidates]
    entities.extend({"name": item, "kind": "concept", "score": 5.0} for item in domain_nodes)
    markdown_path = root / "vault" / "chatlasso" / year / f"{safe_slug(title)}-{cid[-8:]}.md"

    return {
        "id": cid,
        "title": title,
        "created_at": created_at,
        "updated_at": created_at,
        "source_id": source_id,
        "markdown_path": str(markdown_path),
        "tags": tags,
        "messages": [
            {
                "id": f"{cid}:payload",
                "parent_id": None,
                "author": "chatlasso",
                "created_at": created_at,
                "content": text.strip(),
                "metadata": {"source_kind": "chatlasso_ssi", "source_file": str(source)},
            }
        ],
        "chunks": chunks,
        "entities": dedupe_entities(entities),
        "chatlasso_metadata": metadata,
        "source_text": text,
    }


def split_frontmatter(text: str) -> tuple[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return "", text
    return match.group(1), text[match.end() :]


def parse_frontmatter(frontmatter: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata


def parse_list_value(value: str) -> list[str]:
    value = value.strip()
    if not value.startswith("[") or not value.endswith("]"):
        return []
    inner = value[1:-1]
    return [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]


def metadata_tags(metadata: dict[str, str]) -> set[str]:
    tags = set()
    for key in ("type", "mode", "archetype", "status"):
        value = metadata.get(key)
        if value:
            tags.add(safe_slug(value))
    return tags


def first_heading(body: str) -> str | None:
    match = HEADING_RE.search(body)
    return match.group(2).strip() if match else None


def build_chatlasso_chunks(
    conversation_id: str,
    title: str,
    body: str,
    tags: list[str],
    embedder: Any,
) -> list[dict[str, Any]]:
    sections = split_sections(body)
    if not sections:
        sections = [(title, body)]
    chunks = []
    for index, (section_title, section_text) in enumerate(sections):
        text = section_text.strip()
        if not text:
            continue
        chunk_tags = sorted({*tags, safe_slug(section_title)})
        chunks.append(
            {
                "id": f"{conversation_id}:ssi:{index + 1:04d}",
                "title": f"{title} / {section_title}",
                "text": text,
                "tags": chunk_tags,
                "embedding": embedder.embed(text),
            }
        )
    return chunks


def split_sections(body: str) -> list[tuple[str, str]]:
    matches = list(HEADING_RE.finditer(body))
    if not matches:
        return []
    sections = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections.append((match.group(2).strip(), body[start:end].strip()))
    return sections


def write_chatlasso_markdown(conversation: dict[str, Any]) -> None:
    path = Path(conversation["markdown_path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = {
        "id": conversation["id"],
        "title": conversation["title"],
        "created": conversation["created_at"],
        "updated": conversation["updated_at"],
        "source": "ChatLasso",
        "tags": conversation["tags"],
        "embedding_status": "complete" if conversation["chunks"] else "pending",
    }
    body = [
        "---",
        yamlish(frontmatter),
        "---",
        "",
        conversation["source_text"].strip(),
        "",
    ]
    path.write_text("\n".join(body), encoding="utf-8")


def dedupe_entities(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for entity in entities:
        key = (entity["name"], entity["kind"])
        current = merged.get(key)
        if not current or entity["score"] > current["score"]:
            merged[key] = entity
    return list(merged.values())


def clean_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip()[:120] or "Untitled ChatLasso SSI"


def year_from_iso(value: str | None) -> str:
    if value and len(value) >= 4 and value[:4].isdigit():
        return value[:4]
    return "undated"
