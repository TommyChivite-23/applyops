"""Bad input, invalid configuration and failing integrations end in a clear message and exit code 2,
never a traceback."""

import io
import shutil
from pathlib import Path

import pytest

from applyops import cli
from applyops.cli import main
from applyops.tracker import RateLimitError, SchemaError, TrackerSink

SAMPLE = Path(__file__).parent.parent / "examples" / "sample_candidate"


@pytest.fixture
def candidate(tmp_path):
    dest = tmp_path / "cand"
    shutil.copytree(SAMPLE, dest, ignore=shutil.ignore_patterns("out"))
    return dest


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    code = main(list(argv), out=out, err=err)
    return code, out.getvalue(), err.getvalue()


def test_missing_letter_file(candidate):
    code, _, err = run(
        "claims", "check", str(candidate / "nope.md"), "--ledger", str(candidate / "claims.yaml")
    )
    assert code == 2 and "file not found" in err and "nope.md" in err


def test_missing_ledger_file(candidate):
    code, _, err = run(
        "claims", "check", str(candidate / "cover_letter_ok.md"), "--ledger", "missing.yaml"
    )
    assert code == 2 and "missing.yaml" in err


def test_invalid_ledger_is_reported(candidate):
    (candidate / "claims.yaml").write_text("claims:\n- {id: a, match: [x], status: maybe}\n")
    code, _, err = run(
        "claims",
        "check",
        str(candidate / "cover_letter_ok.md"),
        "--ledger",
        str(candidate / "claims.yaml"),
    )
    assert code == 2 and "unknown status" in err


def test_malformed_yaml_is_reported(candidate):
    (candidate / "skills.yaml").write_text("skills: [unclosed\n")
    code, _, err = run(
        "fit", str(candidate / "posting_acme.txt"), "--skills", str(candidate / "skills.yaml")
    )
    assert code == 2 and err.startswith("Error:")


def test_posting_without_title_and_company(tmp_path):
    bad = tmp_path / "bad.txt"
    bad.write_text("- Python\n")
    code, _, err = run("fit", str(bad), "--skills", str(SAMPLE / "skills.yaml"))
    assert code == 2 and "Title:" in err and "Company:" in err


def test_sheets_config_without_spreadsheet_id(candidate, monkeypatch):
    monkeypatch.delenv("APPLYOPS_SPREADSHEET_ID", raising=False)
    (candidate / "applyops.yaml").write_text("tracker:\n  kind: sheets\n")
    code, _, err = run("new", str(candidate / "posting_acme.txt"), "--candidate", str(candidate))
    assert code == 2 and "spreadsheet_id" in err


def test_unknown_tracker_kind(candidate):
    (candidate / "applyops.yaml").write_text("tracker:\n  kind: notion\n")
    code, _, err = run("new", str(candidate / "posting_acme.txt"), "--candidate", str(candidate))
    assert code == 2 and "unknown tracker kind" in err


class FailingSink(TrackerSink):
    def __init__(self, error):
        self.error = error

    def existing_keys(self):
        raise self.error

    def _append(self, row):  # pragma: no cover - never reached
        raise AssertionError


@pytest.mark.parametrize(
    "error",
    [
        RateLimitError("Sheets still failing after 4 attempts (HTTP 429)"),
        SchemaError("missing columns: Company"),
    ],
)
def test_failing_integration_is_reported_and_nothing_is_written(candidate, monkeypatch, error):
    monkeypatch.setattr(cli, "make_sink", lambda cfg: FailingSink(error))
    code, out, _ = run(
        "new", str(candidate / "posting_acme.txt"), "--candidate", str(candidate), "--applied"
    )
    assert code == 2 and "Tracker error:" in out and str(error) in out
    assert not (candidate / "out").exists()


def test_failing_integration_during_manual_push(candidate, monkeypatch):
    monkeypatch.setattr(cli, "make_sink", lambda cfg: FailingSink(RateLimitError("HTTP 429")))
    code, out, _ = run(
        "tracker", "push", "--candidate", str(candidate), "--company", "Initech", "--role", "SRE"
    )
    assert code == 2 and "Tracker error: HTTP 429" in out


def test_google_libraries_missing_message(candidate, monkeypatch):
    from applyops.tracker import TrackerError

    def boom(cfg):
        raise TrackerError("Google Sheets support needs: pip install 'applyops[sheets]'")

    monkeypatch.setattr(cli, "make_sink", boom)
    code, _, err = run("new", str(candidate / "posting_acme.txt"), "--candidate", str(candidate))
    assert code == 2 and "applyops[sheets]" in err


def test_letter_without_any_claim_passes_with_a_clear_message(tmp_path):
    letter = tmp_path / "plain.md"
    letter.write_text("Dear team, I am excited to apply. Thank you for your time.\n")
    code, out, _ = run("claims", "check", str(letter), "--ledger", str(SAMPLE / "claims.yaml"))
    assert code == 0 and "No first-person claims found." in out
