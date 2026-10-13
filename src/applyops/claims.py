"""Claims ledger: every first-person claim in a cover letter must be backed by evidence.

The ledger (claims.yaml) lists what the candidate may say:

    claims:
      - id: fleet-tool
        text: Built a fleet device management tool with tests and CI
        match: [fleet, "device|devices"]
        status: done            # done | in_progress | planned
        evidence: https://github.com/example/fleet-tool
        facts: ["300"]          # optional: numbers a letter may quote for this entry

A sentence is a claim when it says "I built / I'm building / I led ..." (English or
Spanish), starts like a resume bullet ("Built a ..."), or states a first-person
attribute such as a certification, a degree, years of experience or fluency. It passes
only when:

1. a ledger entry matches every `match` term,
2. the entry has an evidence link,
3. its status supports the wording: "I built" and attribute statements need `done`,
   "I'm building" needs `in_progress` or `done`, and a `planned` entry supports nothing,
4. every number the sentence quotes ("90%", "$2M", "5,000") also appears in the entry's
   `text` or `facts`, so a true claim cannot carry an invented metric.

This is keyword and pattern matching. It cannot know whether a sentence is *true*, and it
only judges sentences it recognises as claims (see docs/SECURITY.md and the
"known limitations" tests). The ledger is the source of truth; this module only enforces
that a letter stays inside it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import yaml

DONE, IN_PROGRESS, PLANNED = "done", "in_progress", "planned"
STATUSES = {DONE, IN_PROGRESS, PLANNED}

_VERBS_EN = (
    r"built|developed|created|designed|implemented|shipped|automated|deployed|led|reduced|"
    r"cut|launched|migrated|integrated|wrote|managed|maintained|improved|increased|saved|"
    r"delivered|scaled|optimi[sz]ed|owned|rebuilt|replaced|introduced|trained|mentored|founded"
)
_ONGOING = re.compile(
    r"\b(?:I(?:'m|’m| am)\s+(?:currently\s+|now\s+)?"
    r"(?:building|developing|creating|learning|preparing|practi[cs]ing|studying|"
    r"working (?:on|through))"
    r"|estoy\s+(?:construyendo|desarrollando|creando|aprendiendo|preparando|practicando|estudiando))\b",
    re.IGNORECASE,
)
_COMPLETED = re.compile(
    rf"\b(?:I(?:\s+(?:also|recently|previously))?(?:\s+have|(?:'|’)ve)?\s+(?:{_VERBS_EN})"
    r"|(?:constru[ií]|desarroll[ée]|cre[ée]|dise[ñn][ée]|implement[ée]|automatic[ée]|lider[ée]|"
    r"reduje|migr[ée]|integr[ée]))\b",
    re.IGNORECASE,
)
# Resume style: the sentence itself opens with the verb ("Built a Kubernetes platform ...").
_BULLET_STYLE = re.compile(rf"^\s*(?:[-*•]\s*)?(?:{_VERBS_EN})\b", re.IGNORECASE)
# First-person attributes that are claims even without an action verb.
_FIRST_PERSON = re.compile(r"\b(?:I|[Mm]y)\b")
_ATTRIBUTE = re.compile(
    r"\b(?:certified|certification|certificate|licen[sc]ed|fluent|native speaker|proficient|"
    r"bilingual|degree|master['’]?s|bachelor['’]?s|\d+\+?\s*(?:years?|yrs?))\b",
    re.IGNORECASE,
)
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+|\n\s*\n|\n(?=\s*[-*•]\s)")

_NUMBER = re.compile(r"(?<![\w.])[$€£]?\d[\d,]*(?:\.\d+)?\s?(?:%|[kKmMbB]\b|\+)?")
_YEAR = re.compile(r"(?:19|20)\d\d")
_YEAR_CONTEXT = re.compile(
    r"(?:\bin|since|from|until|through|to|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
    r"[a-z]*\.?\s*$"
)


class Verdict(StrEnum):
    OK = "ok"
    UNSUPPORTED = "unsupported"  # no ledger entry matches
    NO_EVIDENCE = "no_evidence"  # entry exists but has no evidence link
    OVERCLAIM = "overclaim"  # wording claims more than the entry's status allows
    UNVERIFIED_FIGURE = "unverified_figure"  # a quoted number is not in the entry


@dataclass(frozen=True)
class Claim:
    id: str
    text: str
    match: tuple[str, ...]
    status: str
    evidence: str = ""
    facts: tuple[str, ...] = ()

    def matches(self, sentence: str) -> bool:
        lowered = sentence.lower()
        return all(
            any(
                re.search(rf"\b{re.escape(alt.strip().lower())}\b", lowered)
                for alt in term.split("|")
            )
            for term in self.match
        )

    @property
    def allowed_figures(self) -> set[str]:
        return figures(self.text) | {f for fact in self.facts for f in figures(fact)}


@dataclass(frozen=True)
class Finding:
    sentence: str
    tense: str  # "done", "ongoing" or "stated"
    verdict: Verdict
    claim_id: str | None
    reason: str

    @property
    def ok(self) -> bool:
        return self.verdict is Verdict.OK


class LedgerError(ValueError):
    pass


def load_ledger(path: Path | str) -> list[Claim]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    entries = data.get("claims", [])
    claims, seen = [], set()
    for i, raw in enumerate(entries, 1):
        try:
            cid, match, status = raw["id"], raw["match"], raw.get("status", DONE)
        except (KeyError, TypeError) as exc:
            raise LedgerError(f"claim #{i} needs 'id' and 'match'") from exc
        if cid in seen:
            raise LedgerError(f"duplicate claim id '{cid}'")
        if status not in STATUSES:
            raise LedgerError(f"claim '{cid}' has unknown status '{status}'")
        if isinstance(match, str):
            match = [match]
        if not match:
            raise LedgerError(f"claim '{cid}' needs at least one match term")
        facts = raw.get("facts") or []
        if not isinstance(facts, list):
            raise LedgerError(f"claim '{cid}': 'facts' must be a list")
        seen.add(cid)
        claims.append(
            Claim(
                id=cid,
                text=raw.get("text", ""),
                match=tuple(match),
                status=status,
                evidence=(raw.get("evidence") or "").strip(),
                facts=tuple(str(f) for f in facts),
            )
        )
    return claims


def split_sentences(text: str) -> list[str]:
    parts = (s.strip() for s in _SENTENCE_END.split(text))
    return [" ".join(p.split()) for p in parts if p]


def figures(text: str) -> set[str]:
    """Numbers, percentages and amounts quoted in `text`, normalised ("5,000" -> "5000").

    A bare four-digit year after "in", "since", a month name and similar is not a metric.
    """
    found = set()
    for m in _NUMBER.finditer(text):
        raw = m.group(0).strip()
        before = text[max(0, m.start() - 12) : m.start()].lower()
        if _YEAR.fullmatch(raw) and _YEAR_CONTEXT.search(before):
            continue
        found.add(re.sub(r"[\s,$€£]", "", raw).lower())
    return found


def claim_tense(sentence: str) -> str | None:
    if _ONGOING.search(sentence):
        return "ongoing"
    if _COMPLETED.search(sentence) or _BULLET_STYLE.match(sentence):
        return "done"
    if _FIRST_PERSON.search(sentence) and _ATTRIBUTE.search(sentence):
        return "stated"
    return None


_WORDING = {"done": "completed", "ongoing": "in progress", "stated": "stated as a fact"}


def _judge_entry(sentence: str, tense: str, entry: Claim) -> Finding:
    if not entry.evidence:
        return Finding(sentence, tense, Verdict.NO_EVIDENCE, entry.id, "entry has no evidence link")
    allowed = {DONE, IN_PROGRESS} if tense == "ongoing" else {DONE}
    if entry.status not in allowed:
        return Finding(
            sentence,
            tense,
            Verdict.OVERCLAIM,
            entry.id,
            f"letter says {_WORDING[tense]}, ledger says {entry.status.replace('_', ' ')}",
        )
    extra = sorted(figures(sentence) - entry.allowed_figures)
    if extra:
        return Finding(
            sentence,
            tense,
            Verdict.UNVERIFIED_FIGURE,
            entry.id,
            f"not in the ledger entry: {', '.join(extra)} (add to its text or facts if true)",
        )
    return Finding(sentence, tense, Verdict.OK, entry.id, f"backed by {entry.evidence}")


def _judge(sentence: str, tense: str, ledger: list[Claim]) -> Finding:
    candidates = [c for c in ledger if c.matches(sentence)]
    if not candidates:
        return Finding(sentence, tense, Verdict.UNSUPPORTED, None, "no ledger entry matches")
    # Most specific entry first, then one that is done. A sentence that mentions several ledger
    # entries must satisfy ALL of them: a true claim cannot carry an unproven one ("I built X
    # and a Kubernetes platform"), so the first entry that fails decides the verdict.
    candidates.sort(key=lambda c: (len(c.match), c.status == DONE), reverse=True)
    findings = [_judge_entry(sentence, tense, c) for c in candidates]
    return next((f for f in findings if not f.ok), findings[0])


def check_text(text: str, ledger: list[Claim]) -> list[Finding]:
    findings = []
    for sentence in split_sentences(text):
        tense = claim_tense(sentence)
        if tense:
            findings.append(_judge(sentence, tense, ledger))
    return findings


def check_file(letter: Path | str, ledger_path: Path | str) -> list[Finding]:
    return check_text(Path(letter).read_text(encoding="utf-8"), load_ledger(ledger_path))
