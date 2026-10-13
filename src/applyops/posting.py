"""Read a saved job posting and score it against a skills file."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from applyops.models import FitResult, Posting

_HEADER = re.compile(r"^(title|company|location|salary|url)\s*:\s*(.+)$", re.IGNORECASE)
_BULLET = re.compile(r"^\s*(?:[-*•▪]|\d+[.)])\s+(.+)$")
_REQ_HEADING = re.compile(
    r"^\s*#*\s*(requirements|qualifications|what you(?:'ll)? (?:need|bring)|must have|requisitos)",
    re.IGNORECASE,
)


def _is_heading(line: str) -> bool:
    """A short line that is not a bullet and not a sentence, e.g. "Nice to have"."""
    stripped = line.strip().lstrip("#").strip()
    if not stripped or _BULLET.match(line):
        return False
    return len(stripped.split()) <= 6 and not stripped.endswith((".", ","))


def parse_posting(text: str) -> Posting:
    """Parse a posting saved as text.

    Optional header lines (Title:, Company:, Location:, Salary:, URL:) fill the
    metadata. Requirements are the bullets under a Requirements-style heading, or
    every bullet when there is no such heading.
    """
    meta: dict[str, str] = {}
    in_reqs, saw_req_heading = False, False
    req_bullets, all_bullets = [], []
    for line in text.splitlines():
        if m := _HEADER.match(line.strip()):
            meta[m.group(1).lower()] = m.group(2).strip()
            continue
        if _REQ_HEADING.match(line):
            in_reqs = saw_req_heading = True
            continue
        if _is_heading(line):
            in_reqs = False
            continue
        if m := _BULLET.match(line):
            item = m.group(1).strip()
            all_bullets.append(item)
            if in_reqs:
                req_bullets.append(item)
    if "title" not in meta or "company" not in meta:
        raise ValueError("posting needs 'Title:' and 'Company:' lines")
    return Posting(
        title=meta["title"],
        company=meta["company"],
        location=meta.get("location", ""),
        salary=meta.get("salary", ""),
        url=meta.get("url", ""),
        requirements=req_bullets if saw_req_heading else all_bullets,
        text=text,
    )


def load_posting(path: Path | str) -> Posting:
    return parse_posting(Path(path).read_text(encoding="utf-8"))


def load_skills(path: Path | str) -> dict[str, list[str]]:
    """skills.yaml: `skills: [{name: Python, aliases: [python, flask]}, ...]`."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    out = {}
    for s in data.get("skills", []):
        out[s["name"]] = [a.lower() for a in [s["name"], *s.get("aliases", [])]]
    return out


def score_fit(posting: Posting, skills: dict[str, list[str]]) -> FitResult:
    if not posting.requirements:
        return FitResult(score=0, matched=[], gaps=[])
    matched, gaps = [], []
    for req in posting.requirements:
        lowered = req.lower()
        hit = any(
            re.search(rf"(?<![\w]){re.escape(alias)}(?![\w])", lowered)
            for aliases in skills.values()
            for alias in aliases
        )
        (matched if hit else gaps).append(req)
    score = round(10 * len(matched) / len(posting.requirements))
    return FitResult(score=score, matched=matched, gaps=gaps)
