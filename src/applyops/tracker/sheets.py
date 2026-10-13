"""Google Sheets tracker sink.

Columns are matched by header name, not position, so the sheet can have extra
columns (formulas, colour coding, notes) and a different order. Values are written
with valueInputOption=RAW, so text such as "+57 ..." or "7/10" is never reinterpreted
as a formula, number or date.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from applyops.models import TrackerRow
from applyops.tracker.base import (
    DEFAULT_COLUMNS,
    RateLimitError,
    SchemaError,
    TrackerError,
    TrackerSink,
)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
RETRYABLE_STATUS = {429, 500, 503}
_DATE_FORMATS = ("%Y-%m-%d", "%d-%b-%Y", "%d-%b-%y", "%d/%m/%Y", "%m/%d/%Y", "%d %b %Y")


def _col_letter(index: int) -> str:
    """0-based column index to A1 letters (0 -> A, 26 -> AA)."""
    letters = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def _normalize_date(value: str) -> str:
    value = value.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return value.lower()


class GoogleSheetsSink(TrackerSink):
    def __init__(
        self,
        service: Any,
        spreadsheet_id: str,
        sheet: str = "Applications",
        columns: dict[str, str] | None = None,
        header_row: int = 1,
        max_attempts: int = 4,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._values = service.spreadsheets().values()
        self.spreadsheet_id = spreadsheet_id
        self.sheet = sheet
        self.columns = columns or DEFAULT_COLUMNS
        self.header_row = header_row
        self.max_attempts = max_attempts
        self._sleep = sleep
        self._headers: list[str] | None = None

    # -- reading -----------------------------------------------------------------

    def _range(self, a1: str) -> str:
        return f"'{self.sheet}'!{a1}"

    def _read_all(self) -> list[list[str]]:
        resp = self._call(
            self._values.get(
                spreadsheetId=self.spreadsheet_id,
                range=self._range(f"A{self.header_row}:ZZ"),
            )
        )
        return resp.get("values", [])

    def headers(self) -> list[str]:
        if self._headers is None:
            rows = self._read_all()
            if not rows:
                raise SchemaError(f"sheet '{self.sheet}' has no header row")
            self._headers = [h.strip() for h in rows[0]]
        return self._headers

    def _index(self) -> dict[str, int]:
        headers = self.headers()
        lookup = {h.lower(): i for i, h in enumerate(headers) if h}
        missing = [h for h in self.columns.values() if h.lower() not in lookup]
        if missing:
            raise SchemaError(f"sheet '{self.sheet}' is missing columns: {', '.join(missing)}")
        return {field: lookup[header.lower()] for field, header in self.columns.items()}

    def existing_keys(self) -> set[tuple[str, str, str]]:
        index = self._index()
        keys = set()
        for row in self._read_all()[1:]:

            def cell(field: str, row: list[str] = row) -> str:
                i = index[field]
                return row[i] if i < len(row) else ""

            if not cell("company").strip():
                continue
            keys.add(
                (
                    cell("company").strip().lower(),
                    cell("role").strip().lower(),
                    _normalize_date(cell("date_applied")),
                )
            )
        return keys

    # -- writing -----------------------------------------------------------------

    def _append(self, row: TrackerRow) -> str:
        index = self._index()
        width = max(index.values()) + 1
        values = [""] * width
        for field, value in row.to_record().items():
            if field in index:
                values[index[field]] = value
        resp = self._call(
            self._values.append(
                spreadsheetId=self.spreadsheet_id,
                range=self._range(f"A{self.header_row}:{_col_letter(width - 1)}"),
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": [values]},
            )
        )
        return resp.get("updates", {}).get("updatedRange", self.sheet)

    # -- transport ---------------------------------------------------------------

    def _call(self, request: Any) -> dict:
        """Execute a request, retrying throttling and transient server errors."""
        delay = 1.0
        for attempt in range(1, self.max_attempts + 1):
            try:
                return request.execute()
            except Exception as exc:  # googleapiclient.errors.HttpError, without importing it
                status = getattr(getattr(exc, "resp", None), "status", None)
                if status not in RETRYABLE_STATUS:
                    raise TrackerError(f"Sheets request failed: {exc}") from exc
                if attempt == self.max_attempts:
                    raise RateLimitError(
                        f"Sheets still failing after {attempt} attempts (HTTP {status})"
                    ) from exc
                self._sleep(delay)
                delay *= 2
        raise AssertionError("unreachable")


def build_service(credentials_file: str | None = None) -> Any:
    """Create a Sheets API client.

    With a service-account JSON file, share the tracker with that account's email.
    Without one, Application Default Credentials are used.
    """
    try:
        import google.auth
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise TrackerError("Google Sheets support needs: pip install 'applyops[sheets]'") from exc

    if credentials_file:
        creds = service_account.Credentials.from_service_account_file(
            credentials_file, scopes=SCOPES
        )
    else:
        creds, _ = google.auth.default(scopes=SCOPES)
    return build("sheets", "v4", credentials=creds, cache_discovery=False)
