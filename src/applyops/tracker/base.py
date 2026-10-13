"""Tracker sink interface and errors.

Every sink appends rows and refuses duplicates, so re-running a command is safe.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from applyops.models import TrackerRow

# Default mapping from TrackerRow fields to spreadsheet headers.
# Override per tracker with a `columns:` block in the config file.
DEFAULT_COLUMNS: dict[str, str] = {
    "date_applied": "Date Applied",
    "company": "Company",
    "role": "Role",
    "status": "Status",
    "location": "Location",
    "fit_score": "Fit (1-10)",
    "priority": "Priority",
    "salary": "Salary",
    "source": "Source",
    "posting_url": "Posting URL",
    "resume_file": "Resume",
    "cover_letter_file": "Cover Letter",
    "follow_up": "Follow-up",
    "notes": "Notes",
}


class TrackerError(Exception):
    """Base class for tracker failures."""


class DuplicateRowError(TrackerError):
    def __init__(self, row: TrackerRow):
        super().__init__(f"{row.company} / {row.role} on {row.date_applied} is already tracked")
        self.row = row


class SchemaError(TrackerError):
    """The destination is missing headers the column mapping needs."""


class RateLimitError(TrackerError):
    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


@dataclass(frozen=True)
class PushResult:
    row: TrackerRow
    location: str  # human-readable: "row 17", a file path, etc.


class TrackerSink(ABC):
    @abstractmethod
    def existing_keys(self) -> set[tuple[str, str, str]]:
        """Keys of rows already present."""

    @abstractmethod
    def _append(self, row: TrackerRow) -> str:
        """Write one row; return where it landed."""

    def push(self, row: TrackerRow) -> PushResult:
        if row.key in self.existing_keys():
            raise DuplicateRowError(row)
        return PushResult(row=row, location=self._append(row))
