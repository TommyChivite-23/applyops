import io
import shutil
from pathlib import Path

import pytest

from applyops.cli import main
from applyops.config import load_config, make_sink
from applyops.posting import load_posting, load_skills, parse_posting, score_fit
from applyops.tracker import CsvSink

SAMPLE = Path(__file__).parent.parent / "examples" / "sample_candidate"


@pytest.fixture
def candidate(tmp_path):
    dest = tmp_path / "cand"
    shutil.copytree(SAMPLE, dest, ignore=shutil.ignore_patterns("out"))
    return dest


def run(*argv):
    out = io.StringIO()
    code = main(list(argv), out=out)
    return code, out.getvalue()


def test_parse_sample_posting():
    p = load_posting(SAMPLE / "posting_acme.txt")
    assert (p.company, p.title, p.location) == (
        "Acme Logistics",
        "Automation Engineer",
        "Remote (EU)",
    )
    assert len(p.requirements) == 6  # "Nice to have" bullets are excluded
    assert "Kubernetes" not in p.requirements


def test_posting_without_requirements_heading_uses_all_bullets():
    p = parse_posting("Title: X\nCompany: Y\n- Python\n* SQL\n1. Docker\n")
    assert p.requirements == ["Python", "SQL", "Docker"]


def test_posting_needs_title_and_company():
    with pytest.raises(ValueError):
        parse_posting("- Python\n")


def test_fit_score_and_gaps():
    fit = score_fit(load_posting(SAMPLE / "posting_acme.txt"), load_skills(SAMPLE / "skills.yaml"))
    assert fit.gaps == ["Experience with Terraform"]
    assert fit.score == 8  # 5 of 6


def test_fit_with_no_requirements():
    assert score_fit(parse_posting("Title: X\nCompany: Y\n"), {}).score == 0


def test_cli_claims_check_exit_codes():
    ok, out = run(
        "claims",
        "check",
        str(SAMPLE / "cover_letter_ok.md"),
        "--ledger",
        str(SAMPLE / "claims.yaml"),
    )
    assert ok == 0 and "3 claims, 0 failed" in out
    bad, out = run(
        "claims",
        "check",
        str(SAMPLE / "cover_letter_overclaim.md"),
        "--ledger",
        str(SAMPLE / "claims.yaml"),
    )
    assert bad == 1 and "3 failed" in out and "reason: no ledger entry matches" in out


def test_cli_fit():
    code, out = run(
        "fit", str(SAMPLE / "posting_acme.txt"), "--skills", str(SAMPLE / "skills.yaml")
    )
    assert code == 0 and "fit 8/10" in out and "gap: Experience with Terraform" in out


def test_cli_new_writes_tracker_row(candidate):
    code, out = run(
        "new",
        str(candidate / "posting_acme.txt"),
        "--candidate",
        str(candidate),
        "--letter",
        str(candidate / "cover_letter_ok.md"),
        "--applied",
    )
    assert code == 0, out
    text = (candidate / "out" / "tracker.csv").read_text()
    assert "Acme Logistics,Automation Engineer,Applied,Remote (EU),8" in text
    # Running again does not duplicate the row.
    code, out = run(
        "new", str(candidate / "posting_acme.txt"), "--candidate", str(candidate), "--applied"
    )
    assert code == 0 and "Skipped" in out
    assert text == (candidate / "out" / "tracker.csv").read_text()


def test_cli_new_stops_on_failed_claims(candidate):
    code, out = run(
        "new",
        str(candidate / "posting_acme.txt"),
        "--candidate",
        str(candidate),
        "--letter",
        str(candidate / "cover_letter_overclaim.md"),
    )
    assert code == 1 and "Stopped" in out
    assert not (candidate / "out" / "tracker.csv").exists()


def test_cli_new_dry_run(candidate):
    code, out = run(
        "new", str(candidate / "posting_acme.txt"), "--candidate", str(candidate), "--dry-run"
    )
    assert code == 0 and "Dry run" in out
    assert not (candidate / "out").exists()


def test_cli_tracker_push(candidate):
    args = [
        "tracker",
        "push",
        "--candidate",
        str(candidate),
        "--company",
        "Initech",
        "--role",
        "SRE",
        "--date",
        "2026-10-01",
        "--fit",
        "6",
    ]
    code, out = run(*args)
    assert code == 0 and "added Initech / SRE" in out
    code, out = run(*args)
    assert "Skipped" in out


def test_config_env_overrides_and_sheets_requires_id(candidate, monkeypatch):
    (candidate / "applyops.yaml").write_text("tracker:\n  kind: sheets\n")
    monkeypatch.delenv("APPLYOPS_SPREADSHEET_ID", raising=False)
    with pytest.raises(ValueError, match="spreadsheet_id"):
        make_sink(load_config(candidate))
    monkeypatch.setenv("APPLYOPS_SPREADSHEET_ID", "abc")
    assert load_config(candidate).tracker.spreadsheet_id == "abc"


def test_config_defaults_and_unknown_kind(tmp_path):
    cfg = load_config(tmp_path)
    assert isinstance(make_sink(cfg), CsvSink)
    (tmp_path / "applyops.yaml").write_text("tracker:\n  kind: notion\n")
    with pytest.raises(ValueError, match="unknown tracker kind"):
        make_sink(load_config(tmp_path))
