from __future__ import annotations

import re
from collections import Counter

ACRONYM_RE = re.compile(r"\b[A-Z][A-Z0-9]{2,}\b")
TITLE_RE = re.compile(r"\b(?:[A-Z][a-z0-9]+(?:\s+|$)){2,4}")
STOP_PHRASES = {
    "Chat GPT",
    "Open AI",
    "Thank You",
    "Good Morning",
    "Externalized Recursive",
}


def extract_entities(text: str, *, limit: int = 30) -> list[tuple[str, str, float]]:
    counter: Counter[str] = Counter()
    for match in ACRONYM_RE.findall(text):
        counter[match.strip()] += 3
    for match in TITLE_RE.findall(text):
        name = " ".join(match.split())
        if len(name) > 3 and name not in STOP_PHRASES:
            counter[name] += 1

    entities: list[tuple[str, str, float]] = []
    for name, score in counter.most_common(limit):
        kind = "concept"
        if name.isupper():
            kind = "system"
        elif any(word in name.lower() for word in ("api", "database", "sqlite", "python")):
            kind = "tool"
        entities.append((name, kind, float(score)))
    return entities

