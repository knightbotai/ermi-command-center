from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .embeddings import get_embedder
from .entities import extract_entities
from .storage import Store

TAG_KEYWORDS = {
    "architecture": {"architecture", "infrastructure", "system", "pipeline"},
    "cognition": {"memory", "cognition", "recursive", "identity"},
    "code": {"code", "python", "api", "database", "cli"},
    "strategy": {"roadmap", "plan", "phase", "goal"},
    "philosophy": {"meaning", "belief", "human", "thought"},
}


def init_archive(root: Path) -> None:
    (root / "raw").mkdir(parents=True, exist_ok=True)
    (root / "vault" / "conversations").mkdir(parents=True, exist_ok=True)
    with Store(root / "ermi.sqlite3"):
        pass


def ingest_export(source: Path, root: Path) -> dict[str, int]:
    init_archive(root)
    raw_path = copy_raw_source(source, root / "raw")
    imported_at = datetime.now(timezone.utc).isoformat()
    source_hash = sha256(source)

    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Expected a ChatGPT conversations.json list.")

    embedder = get_embedder()
    conversations = []
    with Store(root / "ermi.sqlite3") as store:
        source_id = store.upsert_source(str(raw_path), imported_at, source_hash)
        for raw in data:
            conversation = normalize_conversation(raw, source_id, root, embedder)
            write_markdown(conversation, root)
            store.replace_conversation(conversation)
            conversations.append(conversation)

    return {
        "sources": 1,
        "conversations": len(conversations),
        "messages": sum(len(item["messages"]) for item in conversations),
        "chunks": sum(len(item["chunks"]) for item in conversations),
        "entities": sum(len(item["entities"]) for item in conversations),
    }


def copy_raw_source(source: Path, raw_dir: Path) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    digest = sha256(source)[:12]
    target = raw_dir / f"{source.stem}-{digest}{source.suffix}"
    if not target.exists():
        shutil.copy2(source, target)
    return target


def normalize_conversation(raw: dict[str, Any], source_id: int, root: Path, embedder: Any) -> dict[str, Any]:
    cid = str(raw.get("id") or stable_id(raw.get("title", "conversation")))
    title = clean_title(str(raw.get("title") or "Untitled Conversation"))
    messages = reconstruct_messages(raw)
    full_text = "\n\n".join(f"{item['author']}: {item['content']}" for item in messages)
    tags = classify(full_text + " " + title)
    chunks = build_chunks(cid, title, messages, tags, embedder)
    created_at = first_present([raw.get("create_time"), *(m.get("created_at") for m in messages)])
    updated_at = first_present([raw.get("update_time")]) or (messages[-1].get("created_at") if messages else None)
    year = year_from_timestamp(created_at)
    markdown_path = root / "vault" / "conversations" / year / f"{safe_slug(title)}-{cid[:8]}.md"
    entities = [
        {"name": name, "kind": kind, "score": score}
        for name, kind, score in extract_entities(full_text + "\n" + title)
    ]
    return {
        "id": cid,
        "title": title,
        "created_at": timestamp_to_iso(created_at),
        "updated_at": timestamp_to_iso(updated_at),
        "source_id": source_id,
        "markdown_path": str(markdown_path),
        "tags": tags,
        "messages": messages,
        "chunks": chunks,
        "entities": entities,
    }


def reconstruct_messages(raw: dict[str, Any]) -> list[dict[str, Any]]:
    mapping = raw.get("mapping")
    if not isinstance(mapping, dict):
        return []
    true_path = reconstruct_true_path(raw, mapping)
    if true_path:
        return true_path
    messages = []
    for node_id, node in mapping.items():
        message = node.get("message") if isinstance(node, dict) else None
        if not message:
            continue
        content = message_text(message.get("content", {}))
        if not content.strip():
            continue
        author = message.get("author", {}).get("role") or "unknown"
        messages.append(
            {
                "id": str(message.get("id") or node_id),
                "parent_id": node.get("parent"),
                "author": str(author),
                "created_at": timestamp_to_iso(message.get("create_time")),
                "content": content.strip(),
                "metadata": {
                    "status": message.get("status"),
                    "recipient": message.get("recipient"),
                    "end_turn": message.get("end_turn"),
                },
            }
        )
    messages.sort(key=lambda item: (item.get("created_at") or "", item["id"]))
    return messages


def reconstruct_true_path(raw: dict[str, Any], mapping: dict[str, Any]) -> list[dict[str, Any]]:
    current_node_id = raw.get("current_node")
    if not current_node_id:
        return []
    messages = []
    visited = set()
    while current_node_id and current_node_id not in visited:
        visited.add(current_node_id)
        node = mapping.get(current_node_id)
        if not isinstance(node, dict):
            break
        message = node.get("message")
        if message:
            content = message_text(message.get("content", {}))
            if content.strip():
                author = message.get("author", {}).get("role") or "unknown"
                messages.append(
                    {
                        "id": str(message.get("id") or current_node_id),
                        "parent_id": node.get("parent"),
                        "author": str(author),
                        "created_at": timestamp_to_iso(message.get("create_time")),
                        "content": content.strip(),
                        "metadata": {
                            "status": message.get("status"),
                            "recipient": message.get("recipient"),
                            "end_turn": message.get("end_turn"),
                            "node_id": current_node_id,
                            "path": "current_node",
                        },
                    }
                )
        current_node_id = node.get("parent")
    messages.reverse()
    return messages


def message_text(content: dict[str, Any]) -> str:
    parts = content.get("parts") if isinstance(content, dict) else None
    if isinstance(parts, list):
        rendered = []
        for part in parts:
            if isinstance(part, str):
                rendered.append(part)
            elif isinstance(part, dict):
                rendered.append(json.dumps(part, ensure_ascii=False, sort_keys=True))
        return "\n".join(rendered)
    text = content.get("text") if isinstance(content, dict) else None
    return text if isinstance(text, str) else ""


def build_chunks(
    conversation_id: str,
    title: str,
    messages: list[dict[str, Any]],
    tags: list[str],
    embedder: Any,
    max_chars: int = 3500,
) -> list[dict[str, Any]]:
    chunks = []
    buffer: list[str] = []
    for message in messages:
        rendered = f"{message['author']}: {message['content']}"
        if buffer and sum(len(item) for item in buffer) + len(rendered) > max_chars:
            chunks.append(make_chunk(conversation_id, title, len(chunks), buffer, tags, embedder))
            buffer = []
        buffer.append(rendered)
    if buffer:
        chunks.append(make_chunk(conversation_id, title, len(chunks), buffer, tags, embedder))
    return chunks


def make_chunk(
    conversation_id: str,
    title: str,
    ordinal: int,
    lines: list[str],
    tags: list[str],
    embedder: Any,
) -> dict[str, Any]:
    text = "\n\n".join(lines)
    return {
        "id": f"{conversation_id}:chunk:{ordinal + 1:04d}",
        "title": f"{title} / Chunk {ordinal + 1}",
        "text": text,
        "tags": tags,
        "embedding": embedder.embed(text),
    }


def write_markdown(conversation: dict[str, Any], root: Path) -> None:
    path = Path(conversation["markdown_path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = {
        "id": conversation["id"],
        "title": conversation["title"],
        "created": conversation["created_at"],
        "updated": conversation["updated_at"],
        "tags": conversation["tags"],
        "participants": sorted({message["author"] for message in conversation["messages"]}),
        "embedding_status": "complete" if conversation["chunks"] else "pending",
    }
    body = ["---", yamlish(frontmatter), "---", ""]
    for message in conversation["messages"]:
        body.append(f"## {message['author']} - {message.get('created_at') or 'unknown time'}")
        body.append("")
        body.append(message["content"])
        body.append("")
    path.write_text("\n".join(body), encoding="utf-8")


def yamlish(data: dict[str, Any]) -> str:
    lines = []
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f"  - {item}" for item in value)
        elif value is None:
            lines.append(f"{key}: null")
        else:
            escaped = str(value).replace('"', '\\"')
            lines.append(f'{key}: "{escaped}"')
    return "\n".join(lines)


def classify(text: str) -> list[str]:
    lowered = text.lower()
    tags = []
    for tag, keywords in TAG_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            tags.append(tag)
    return tags or ["conversation"]


def first_present(values: list[Any]) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def timestamp_to_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return None


def year_from_timestamp(value: Any) -> str:
    iso = timestamp_to_iso(value)
    if iso and len(iso) >= 4 and iso[:4].isdigit():
        return iso[:4]
    return "undated"


def clean_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip()[:120] or "Untitled Conversation"


def safe_slug(title: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", title.lower()).strip("-")
    return slug[:80] or "untitled"


def stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
