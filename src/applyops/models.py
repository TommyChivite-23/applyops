"""Core data types shared across ApplyOps."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date


@dataclass(frozen=True)
class TrackerRow:
    """One application in the tracker.

    Field names are the canonical keys. A sink maps them to its own column headers,
    so the spreadsheet layout can change without touching this type.
    """

    date_applied: date
    company: str
    role: str
    status: str = "Saved"
    location: str = ""
    fit_score: int | None = None
    priority: str = ""
    salary: str = ""
    source: str = ""
    posting_url: str = ""
    resume_file: str = ""
    cover_letter_file: str = ""
    follow_up: date | None = None
    notes: str = ""

    @property
    def key(self) -> tuple[str, str, str]:
        """Identity used to avoid duplicate rows: same company, role and date."""
        return (
            self.company.strip().lower(),
            self.role.strip().lower(),
            self.date_applied.isoformat(),
        )

    def to_record(self) -> dict[str, str]:
        """Flatten to strings, the form every sink writes."""
        out: dict[str, str] = {}
        for name, value in asdict(self).items():
            if value is None:
                out[name] = ""
            elif isinstance(value, date):
                out[name] = value.isoformat()
            else:
                out[name] = str(value)
        return out


@dataclass(frozen=True)
class Posting:
    title: str
    company: str
    location: str = ""
    salary: str = ""
    url: str = ""
    requirements: list[str] = field(default_factory=list)
    text: str = ""


@dataclass(frozen=True)
class FitResult:
    score: int
    matched: list[str]
    gaps: list[str]
