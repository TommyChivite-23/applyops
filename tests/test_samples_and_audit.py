# audit:ignore-file  (contains deliberately fake secret-looking samples for the audit's own tests)
"""The sample letters behave as documented, and the pre-publish audit catches what it promises."""

import io
import sys
from pathlib import Path

import pytest

from applyops.cli import main

ROOT = Path(__file__).parent.parent
SAMPLE = ROOT / "examples" / "sample_candidate"
sys.path.insert(0, str(ROOT / "scripts"))

import audit_public_repo as audit  # noqa: E402


def run(*argv):
    out = io.StringIO()
    return main(list(argv), out=out), out.getvalue()


def check(letter):
    return run("claims", "check", str(SAMPLE / letter), "--ledger", str(SAMPLE / "claims.yaml"))


def test_sample_letter_with_invented_numbers_is_blocked():
    code, out = check("cover_letter_invented_numbers.md")
    assert code == 1
    assert "unverified_figure" in out and "2m" in out
    assert "I am fluent in German" in out and "2 claims, 2 failed" in out


def test_new_stops_before_tracker_when_a_number_is_invented(tmp_path):
    cand = tmp_path / "c"
    cand.mkdir()
    for f in SAMPLE.iterdir():
        if f.is_file():
            (cand / f.name).write_bytes(f.read_bytes())
    code, out = run(
        "new",
        str(cand / "posting_acme.txt"),
        "--candidate",
        str(cand),
        "--letter",
        str(cand / "cover_letter_invented_numbers.md"),
    )
    assert code == 1 and "Stopped" in out
    assert not (cand / "out").exists()


# -- audit script ------------------------------------------------------------------------


def rules(text, deny=None):
    return {f.rule for f in audit.scan_text("x.py", text, deny)}


@pytest.mark.parametrize(
    "text,rule",
    [
        ('api_key = "AbCdEf123456GhIjKl7890"', "secret-literal"),
        ("host = 192.168.4.20", "private-ip"),
        ("contact: jane.doe@realcompany.org", "email"),
        ("call 415-867-5309 today", "phone"),
        (r"path = C:\Users\realperson\Desktop", "user-path"),
    ],
)
def test_audit_flags_sensitive_looking_text(text, rule):
    assert rule in rules(text)


def test_audit_allows_fictional_values():
    clean = "email alex@example.com or +1 555-0123; docs at https://example.com"
    assert rules(clean) == set()


def test_audit_denylist_is_case_insensitive():
    assert rules("Worked at ACME Hospital", ["acme hospital"]) == {"denylist"}


def test_the_repository_itself_passes_the_audit():
    assert audit.audit(ROOT) == []
