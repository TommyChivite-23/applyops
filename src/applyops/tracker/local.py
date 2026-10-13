"""Local sinks: CSV for offline use, in-memory for tests and dry runs."""

from __future__ import annotations

import csv
from pathlib import Path

from applyops.models import TrackerRow
from applyops.tracker.base import DEFAULT_COLUMNS, TrackerSink


class CsvSink(TrackerSink):
    def __init__(self, path: Path, columns: dict[str, str] | None = None):
        self.path = Path(path)
        self.columns = columns or DEFAULT_COLUMNS

    def _rows(self) -> list[dict[str, str]]:
        if not self.path.exists():
            return []
        with self.path.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def existing_keys(self) -> set[tuple[str, str, str]]:
        c = self.columns
        return {
            (
                r.get(c["company"], "").strip().lower(),
                r.get(c["role"], "").strip().lower(),
                r.get(c["date_applied"], "").strip(),
            )
            for r in self._rows()
        }

    def _append(self, row: TrackerRow) -> str:
        new_file = not self.path.exists()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(self.columns.values()))
            if new_file:
                writer.writeheader()
            record = row.to_record()
            writer.writerow({header: record[field] for field, header in self.columns.items()})
        return f"{self.path} row {len(self._rows()) + 1}"


class MemorySink(TrackerSink):
    def __init__(self) -> None:
        self.rows: list[TrackerRow] = []

    def existing_keys(self) -> set[tuple[str, str, str]]:
        return {r.key for r in self.rows}

    def _append(self, row: TrackerRow) -> str:
        self.rows.append(row)
        return f"memory row {len(self.rows)}"
