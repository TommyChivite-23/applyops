"""In-memory stand-in for the Google Sheets values API."""

from __future__ import annotations


class FakeHttpError(Exception):
    def __init__(self, status: int):
        super().__init__(f"HTTP {status}")
        self.resp = type("Resp", (), {"status": status})()


class _Request:
    def __init__(self, fn, fail_with: list[int]):
        self._fn = fn
        self._fail_with = fail_with

    def execute(self):
        if self._fail_with:
            raise FakeHttpError(self._fail_with.pop(0))
        return self._fn()


class FakeValues:
    def __init__(self, sheet: FakeSheet):
        self.sheet = sheet

    def get(self, spreadsheetId, range):
        self.sheet.calls.append(("get", range))
        return _Request(lambda: {"values": [list(r) for r in self.sheet.rows]}, self.sheet.failures)

    def append(self, spreadsheetId, range, valueInputOption, insertDataOption, body):
        self.sheet.calls.append(("append", range, valueInputOption))

        def run():
            self.sheet.rows.extend(body["values"])
            n = len(self.sheet.rows)
            return {"updates": {"updatedRange": f"'Applications'!A{n}:N{n}"}}

        return _Request(run, self.sheet.failures)


class FakeSheet:
    """Mimics service.spreadsheets().values() with a header row and data rows."""

    def __init__(self, rows: list[list[str]], failures: list[int] | None = None):
        self.rows = rows
        self.failures = failures or []
        self.calls: list[tuple] = []

    def spreadsheets(self):
        return self

    def values(self):
        return FakeValues(self)
