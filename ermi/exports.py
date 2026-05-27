from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ingest import classify, reconstruct_messages, safe_slug, timestamp_to_iso, yamlish

CODE_BLOCK_RE = re.compile(r"```([A-Za-z0-9_+.-]*)\n(.*?)```", re.DOTALL)
WRITING_KEYWORDS = {"story", "character", "poem", "chapter", "creative", "novel"}
PROJECT_KEYWORDS = {"protocol", "project", "sop", "plan", "summary", "meeting", "strategy"}


def load_chatgpt_export(source: Path) -> list[dict[str, Any]]:
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Expected a ChatGPT conversations.json list.")
    return data


def list_chat_titles(source: Path) -> list[str]:
    return [str(chat.get("title") or "Untitled Chat") for chat in load_chatgpt_export(source)]


def export_chat_csv(source: Path, target: Path) -> dict[str, int]:
    chats = load_chatgpt_export(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = 0
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Chat Title", "Role", "Created At", "Message"])
        for chat in chats:
            title = str(chat.get("title") or "Untitled")
            for message in reconstruct_messages(chat):
                writer.writerow([title, message["author"], message.get("created_at") or "", message["content"]])
                rows += 1
    return {"chats": len(chats), "messages": rows}


def mine_code_blocks(source: Path, target: Path) -> dict[str, int]:
    chats = load_chatgpt_export(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    blocks = 0
    with target.open("w", encoding="utf-8") as handle:
        for chat in chats:
            title = str(chat.get("title") or "Untitled")
            for message in reconstruct_messages(chat):
                if message["author"] != "assistant":
                    continue
                for language, code in CODE_BLOCK_RE.findall(message["content"]):
                    blocks += 1
                    handle.write(f"// Source Chat: {title}\n")
                    handle.write(f"// Language: {language.strip() or 'text'}\n")
                    handle.write(code.strip())
                    handle.write("\n" + ("-" * 40) + "\n\n")
    return {"chats": len(chats), "code_blocks": blocks}


def activity_summary(source: Path, limit: int = 5) -> list[dict[str, object]]:
    counts: Counter[str] = Counter()
    for chat in load_chatgpt_export(source):
        for message in reconstruct_messages(chat):
            created = message.get("created_at")
            if created:
                counts[str(created)[:10]] += 1
    return [{"date": date, "message_count": count} for date, count in counts.most_common(limit)]


def export_obsidian_second_brain(source: Path, target_dir: Path) -> dict[str, int]:
    chats = load_chatgpt_export(source)
    written = 0
    for category in ("Code", "Creative_Writing", "Projects_and_Protocols", "General"):
        (target_dir / category).mkdir(parents=True, exist_ok=True)
    for chat in chats:
        title = str(chat.get("title") or "Untitled Chat")
        messages = reconstruct_messages(chat)
        if not messages:
            continue
        full_text = "\n".join(message["content"] for message in messages)
        category = categorize_chat(title, full_text)
        created_at = first_message_time(messages) or timestamp_to_iso(chat.get("create_time"))
        tags = sorted({"chatgpt_export", category.lower(), *classify(f"{title}\n{full_text}")})
        target = target_dir / category / f"{safe_slug(title)}-{str(chat.get('id') or safe_slug(title))[:8]}.md"
        target.write_text(render_obsidian_chat(title, messages, tags, category, created_at), encoding="utf-8")
        written += 1
    return {"chats": len(chats), "files": written}


def categorize_chat(title: str, full_text: str) -> str:
    title_lower = title.lower()
    if CODE_BLOCK_RE.search(full_text):
        return "Code"
    if any(word in title_lower for word in WRITING_KEYWORDS):
        return "Creative_Writing"
    if any(word in title_lower for word in PROJECT_KEYWORDS):
        return "Projects_and_Protocols"
    return "General"


def first_message_time(messages: list[dict[str, Any]]) -> str | None:
    for message in messages:
        if message.get("created_at"):
            return str(message["created_at"])
    return None


def render_obsidian_chat(
    title: str,
    messages: list[dict[str, Any]],
    tags: list[str],
    category: str,
    created_at: str | None,
) -> str:
    frontmatter = {
        "title": title,
        "created": created_at,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "source": "ChatGPT",
        "category": category,
        "tags": tags,
        "cssclasses": ["chat-log"],
    }
    lines = ["---", yamlish(frontmatter), "---", "", f"# {title}", ""]
    for message in messages:
        role = "You" if message["author"] == "user" else "ChatGPT"
        lines.append(f"## {role} - {message.get('created_at') or 'unknown time'}")
        lines.append("")
        if message["author"] == "assistant":
            lines.extend(f"> {line}" if line else ">" for line in message["content"].splitlines())
        else:
            lines.append(message["content"])
        lines.append("")
    return "\n".join(lines)
