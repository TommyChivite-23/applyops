# Testing

How to run the checks and how to read the results. Return to the [README](../README.md).

## Run everything

From the project folder with the virtual environment active:

```powershell
python scripts/audit_public_repo.py      # 1. no secrets or personal data
ruff check .                             # 2. lint
ruff format --check .                    # 3. formatting
pytest --cov=applyops --cov-report=term-missing   # 4. tests and coverage
```

Expected today: `Audit passed`, `All checks passed!`, `... files already formatted`, and `100 passed` with about 98% line coverage. Every command must succeed; CI runs the same four on every push and pull request.

If pytest fails on Windows with `PermissionError` on a `pytest-of-<you>` folder in your Temp directory, give it
a different scratch folder:

```powershell
pytest --basetemp=$env:USERPROFILE\pytest_tmp -p no:cacheprovider
```

## The four checks

| Check | Question it answers | Fails when |
|---|---|---|
| `audit_public_repo.py` | Is anything here that should never be public? | A key-like string, private IP, real-looking email or phone, user path, forbidden file type, or denylist term |
| `ruff check` | Is the code free of common mistakes (unused imports, bad patterns)? | A lint rule is broken |
| `ruff format --check` | Is the style consistent? | A file is not formatted |
| `pytest` | Does the behaviour still match what is promised? | Any assertion fails |

## What the tests cover

| File | Tests | Covers |
|---|---|---|
| `tests/test_claims.py` | 19 | The original ledger behaviour: tense detection, English and Spanish, status rules, ledger validation, sentence splitting |
| `tests/test_claims_hardening.py` | 25 | Resume-style sentences, invented numbers, `facts`, certifications, years, fluency, compound sentences, and the **named known limitations** |
| `tests/test_posting_and_cli.py` | 13 | Posting parsing, fit score and gaps, every CLI command and exit code, `new` stopping on a failed claim, dry run, duplicate prevention, configuration |
| `tests/test_samples_and_audit.py` | 10 | The sample letters behave as documented, `new` writes nothing when a number is invented, the audit catches each rule, and **the repository itself passes the audit** |
| `tests/test_error_handling.py` | 12 | Missing files, invalid ledger or YAML, a posting without a title, Sheets config without an ID, unknown tracker kind, and failing integrations (rate limit, missing columns, missing Google libraries) all end in a clear message, exit code 2 and **nothing written** |
| `tests/test_tracker.py` | 21 | CSV and in-memory sinks, Google Sheets sink against a fake API: header mapping, duplicates in different date formats, missing columns, retry and backoff, no retry on 403, column letters |

Not covered: a live Google Sheets call (the fake covers the logic, not Google's real behaviour), `build_service`
(needs the Google libraries and credentials), and the planned features that do not exist yet. Coverage output
shows the uncovered lines: `config.py` Sheets construction and `sheets.py` real-client code.

## Understanding a failure

```
FAILED tests/test_claims_hardening.py::test_known_limitation_not_detected
```

Names starting `test_known_limitation_` are **intentional alarms**. They pass today because the checker misses a
phrasing; if one fails, the checker got stricter. That is good news: update `docs/SECURITY.md` and move the case
into a normal test.

For any failure, run just that test with more detail:

```powershell
pytest tests/test_claims.py::test_spanish_claims_are_checked -x -vv
```

## Test data

Everything is fictional: Alex Rivera, Acme Logistics, `example.com` links. Tests use `tmp_path` folders and an
in-memory fake of the Sheets API, so they need **no network, no Google account and no personal files**.

## Continuous integration

`.github/workflows/ci.yml` has two jobs:

1. **test** (Python 3.11 and 3.13): install, `ruff check`, `ruff format --check`, the audit, then `pytest` with coverage.
2. **claims-gate**: runs the real CLI on the sample letters and requires that the supported letter passes and
   the overclaiming and invented-number letters are **blocked**. It proves the guardrail works in both directions.

Related: [Development](DEVELOPMENT.md) | [Security](SECURITY.md)
