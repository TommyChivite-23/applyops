from datetime import date

import pytest

from applyops.models import TrackerRow
from applyops.tracker import (
    DEFAULT_COLUMNS,
    CsvSink,
    DuplicateRowError,
    GoogleSheetsSink,
    MemorySink,
    RateLimitError,
    SchemaError,
    TrackerError,
)
from applyops.tracker.sheets import _col_letter, _normalize_date
from tests.fakes import FakeSheet

HEADERS = ["#", *DEFAULT_COLUMNS.values(), "Interview Date"]


def row(**kw):
    base = dict(
        date_applied=date(2026, 10, 13), company="Acme Logistics", role="Automation Engineer"
    )
    return TrackerRow(**{**base, **kw})


def sink(rows, failures=None, sleeps=None):
    fake = FakeSheet(rows, failures)
    s = GoogleSheetsSink(
        fake, "sheet-id", sleep=(sleeps.append if sleeps is not None else lambda _: None)
    )
    return s, fake


def test_sheets_appends_by_header_name_not_position():
    s, fake = sink([HEADERS])
    result = s.push(row(fit_score=7, notes="+57 is text, not a formula"))
    written = fake.rows[-1]
    assert written[HEADERS.index("Company")] == "Acme Logistics"
    assert written[HEADERS.index("Fit (1-10)")] == "7"
    assert written[HEADERS.index("Date Applied")] == "2026-10-13"
    assert written[0] == ""  # unmapped column left alone
    assert result.location.endswith("A2:N2")
    assert ("append", "'Applications'!A1:O", "RAW") in fake.calls


def test_sheets_refuses_duplicate_even_with_other_date_format():
    existing = [""] * len(HEADERS)
    existing[HEADERS.index("Company")] = "ACME Logistics"
    existing[HEADERS.index("Role")] = "Automation Engineer "
    existing[HEADERS.index("Date Applied")] = "13-Oct-2026"
    s, fake = sink([HEADERS, existing])
    with pytest.raises(DuplicateRowError):
        s.push(row())
    assert len(fake.rows) == 2


def test_sheets_skips_blank_rows_and_short_rows():
    s, _ = sink([HEADERS, [], ["1"], [""] * 3])
    assert s.existing_keys() == set()


def test_sheets_missing_columns_is_schema_error():
    s, fake = sink([["Company", "Role"]])
    with pytest.raises(SchemaError, match="Date Applied"):
        s.push(row())
    assert len(fake.rows) == 1


def test_sheets_empty_sheet_is_schema_error():
    s, _ = sink([])
    with pytest.raises(SchemaError, match="no header"):
        s.headers()


def test_sheets_custom_column_names():
    headers = ["Fecha", "Empresa", "Puesto", "Estado"]
    columns = {"date_applied": "Fecha", "company": "Empresa", "role": "Puesto", "status": "Estado"}
    fake = FakeSheet([headers])
    s = GoogleSheetsSink(fake, "id", columns=columns)
    s.push(row(status="Applied"))
    assert fake.rows[-1] == ["2026-10-13", "Acme Logistics", "Automation Engineer", "Applied"]


def test_sheets_retries_throttling_with_backoff():
    sleeps = []
    s, fake = sink([HEADERS], failures=[429, 503], sleeps=sleeps)
    s.push(row())
    assert sleeps == [1.0, 2.0]
    assert len(fake.rows) == 2


def test_sheets_gives_up_after_max_attempts():
    s, _ = sink([HEADERS], failures=[429, 429, 429, 429])
    with pytest.raises(RateLimitError, match="4 attempts"):
        s.headers()


def test_sheets_does_not_retry_client_errors():
    sleeps = []
    s, _ = sink([HEADERS], failures=[403], sleeps=sleeps)
    with pytest.raises(TrackerError, match="HTTP 403"):
        s.headers()
    assert sleeps == []


@pytest.mark.parametrize("i,expected", [(0, "A"), (25, "Z"), (26, "AA"), (38, "AM"), (701, "ZZ")])
def test_col_letter(i, expected):
    assert _col_letter(i) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("2026-10-05", "2026-10-05"),
        ("05-Oct-2026", "2026-10-05"),
        ("05/10/2026", "2026-10-05"),
        ("TBD", "tbd"),
    ],
)
def test_normalize_date(raw, expected):
    assert _normalize_date(raw) == expected


def test_csv_sink_writes_header_once_and_blocks_duplicates(tmp_path):
    path = tmp_path / "t.csv"
    s = CsvSink(path)
    s.push(row())
    s.push(row(role="Integration Engineer"))
    with pytest.raises(DuplicateRowError):
        s.push(row())
    lines = path.read_text().splitlines()
    assert lines[0].startswith("Date Applied,Company,Role")
    assert len(lines) == 3


def test_memory_sink():
    s = MemorySink()
    s.push(row())
    assert s.push(row(company="Other")).location == "memory row 2"


def test_row_key_and_record():
    r = row(fit_score=None, follow_up=date(2026, 10, 20))
    assert r.key == ("acme logistics", "automation engineer", "2026-10-13")
    rec = r.to_record()
    assert rec["fit_score"] == "" and rec["follow_up"] == "2026-10-20"
