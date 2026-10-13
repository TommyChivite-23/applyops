"""Command-line entry point.

applyops claims check LETTER --ledger claims.yaml
applyops fit POSTING --skills skills.yaml
applyops tracker push --candidate DIR --company C --role R [--status Applied ...]
applyops new POSTING --candidate DIR [--letter LETTER] [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

import yaml

from applyops import __version__
from applyops.claims import check_file, check_text, load_ledger
from applyops.config import load_config, make_sink
from applyops.models import TrackerRow
from applyops.posting import load_posting, load_skills, score_fit
from applyops.tracker import DuplicateRowError, TrackerError

FOLLOW_UP_DAYS = 7


def _print_findings(findings, out) -> bool:
    if not findings:
        print("No first-person claims found.", file=out)
        return True
    for f in findings:
        mark = "PASS" if f.ok else "FAIL"
        tag = f.claim_id or "-"
        print(f"[{mark}] {f.verdict.value:<17} {tag:<20} {f.sentence}", file=out)
        if not f.ok:
            print(f"       reason: {f.reason}", file=out)
    failed = sum(not f.ok for f in findings)
    print(f"\n{len(findings)} claims, {failed} failed.", file=out)
    return failed == 0


def cmd_claims_check(args, out) -> int:
    findings = check_file(args.letter, args.ledger)
    return 0 if _print_findings(findings, out) else 1


def cmd_fit(args, out) -> int:
    posting = load_posting(args.posting)
    fit = score_fit(posting, load_skills(args.skills))
    print(f"{posting.company} - {posting.title}: fit {fit.score}/10", file=out)
    for gap in fit.gaps:
        print(f"  gap: {gap}", file=out)
    return 0


def _push(sink, row, out) -> int:
    try:
        result = sink.push(row)
    except DuplicateRowError as exc:
        print(f"Skipped: {exc}", file=out)
        return 0
    except TrackerError as exc:
        print(f"Tracker error: {exc}", file=out)
        return 2
    print(f"Tracker: added {row.company} / {row.role} at {result.location}", file=out)
    return 0


def cmd_tracker_push(args, out) -> int:
    cfg = load_config(args.candidate)
    applied = date.fromisoformat(args.date) if args.date else date.today()
    row = TrackerRow(
        date_applied=applied,
        company=args.company,
        role=args.role,
        status=args.status,
        location=args.location,
        fit_score=args.fit,
        source=args.source,
        posting_url=args.url,
        follow_up=applied + timedelta(days=FOLLOW_UP_DAYS),
        notes=args.notes,
    )
    return _push(make_sink(cfg), row, out)


def cmd_new(args, out) -> int:
    cfg = load_config(args.candidate)
    posting = load_posting(args.posting)
    fit = score_fit(posting, load_skills(cfg.skills_path))
    print(f"{posting.company} - {posting.title}: fit {fit.score}/10", file=out)
    for gap in fit.gaps:
        print(f"  gap: {gap}", file=out)

    if args.letter:
        print("\nClaims check:", file=out)
        letter = Path(args.letter).read_text(encoding="utf-8")
        if not _print_findings(check_text(letter, load_ledger(cfg.claims_path)), out):
            print("Stopped: fix the failed claims before anything is published.", file=out)
            return 1

    today = date.today()
    row = TrackerRow(
        date_applied=today,
        company=posting.company,
        role=posting.title,
        status="Applied" if args.applied else "Saved",
        location=posting.location,
        fit_score=fit.score,
        salary=posting.salary,
        posting_url=posting.url,
        cover_letter_file=Path(args.letter).name if args.letter else "",
        follow_up=today + timedelta(days=FOLLOW_UP_DAYS),
        notes="Gaps: " + "; ".join(fit.gaps) if fit.gaps else "",
    )
    if args.dry_run:
        print(f"\nDry run: would add {row.to_record()}", file=out)
        return 0
    return _push(make_sink(cfg), row, out)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="applyops",
        description="Check a job application: fit score, claims ledger and tracker row.",
    )
    p.add_argument("--version", action="version", version=f"applyops {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    claims = sub.add_parser("claims", help="claims ledger commands").add_subparsers(
        dest="claims_command", required=True
    )
    check = claims.add_parser("check", help="fail if a letter makes an unsupported claim")
    check.add_argument("letter")
    check.add_argument("--ledger", required=True)
    check.set_defaults(func=cmd_claims_check)

    fit = sub.add_parser("fit", help="score a posting against a skills file")
    fit.add_argument("posting")
    fit.add_argument("--skills", required=True)
    fit.set_defaults(func=cmd_fit)

    tracker = sub.add_parser("tracker", help="tracker commands").add_subparsers(
        dest="tracker_command", required=True
    )
    push = tracker.add_parser("push", help="append one application row")
    push.add_argument("--candidate", default=".")
    push.add_argument("--company", required=True)
    push.add_argument("--role", required=True)
    push.add_argument("--status", default="Applied")
    push.add_argument("--date", help="YYYY-MM-DD, default today")
    push.add_argument("--location", default="")
    push.add_argument("--fit", type=int)
    push.add_argument("--source", default="")
    push.add_argument("--url", default="")
    push.add_argument("--notes", default="")
    push.set_defaults(func=cmd_tracker_push)

    new = sub.add_parser("new", help="score a posting, check the letter, add the tracker row")
    new.add_argument("posting")
    new.add_argument("--candidate", default=".")
    new.add_argument("--letter")
    new.add_argument("--applied", action="store_true", help="mark Applied instead of Saved")
    new.add_argument("--dry-run", action="store_true")
    new.set_defaults(func=cmd_new)
    return p


def main(argv: list[str] | None = None, out=sys.stdout, err=None) -> int:
    """Run a command. Exit codes: 0 ok, 1 a claim failed, 2 bad input, config or tracker error."""
    err = err or sys.stderr
    args = build_parser().parse_args(argv)
    try:
        return args.func(args, out)
    except FileNotFoundError as exc:
        print(f"Error: file not found: {exc.filename}", file=err)
    except (
        OSError,
        ValueError,
        TrackerError,
        yaml.YAMLError,
    ) as exc:  # LedgerError is a ValueError
        print(f"Error: {exc}", file=err)
    return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
