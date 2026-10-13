# Development

How to set up, change and extend ApplyOps. Return to the [README](../README.md).

## Set up

Follow [INSTALLATION.md](INSTALLATION.md) (the `.[sheets,dev]` install includes pytest, coverage and ruff). Then:

```powershell
python scripts/audit_public_repo.py && ruff check . && ruff format --check . && pytest
```

Run those four before every commit. In Windows PowerShell 5.1 `&&` is not available; run them one per line.

## Layout

```
src/applyops/   claims.py  posting.py  config.py  models.py  cli.py  tracker/
tests/          pytest suite and fakes.py (in-memory fake of the Sheets API)
examples/       sample_candidate: fictional ledger, skills, postings and letters
scripts/        audit_public_repo.py
docs/           these guides
```

Module responsibilities are in [ARCHITECTURE.md](ARCHITECTURE.md).

## Workflow

1. Create a branch: `git switch -c feat/short-description`.
2. Make the change **with a test that fails first**, then make it pass.
3. Run the four checks.
4. Commit with a conventional message (`feat:`, `fix:`, `docs:`, `test:`, `ci:`, `chore:`), the subject under
   about 70 characters, and a body explaining *why* when it is not obvious.
5. Open a pull request. CI must be green before merging.

## Common changes

### Recognise another claim phrasing

Edit the patterns near the top of `src/applyops/claims.py`: `_COMPLETED` / `_VERBS_EN` (past-tense claim verbs),
`_ONGOING` (in-progress wording), `_ATTRIBUTE` (certifications, degrees, years, fluency).

1. Add the sentence to `tests/test_claims_hardening.py` and watch it fail.
2. Change the pattern.
3. Run the whole suite: **a new pattern must not turn the sample `cover_letter_ok.md` into a failure**
   (`test_sample_letters_unchanged_by_the_new_rules` guards this).
4. If you tighten something listed under `test_known_limitation_*`, those tests will fail on purpose: move the case
   into a regular test and update [SECURITY.md](SECURITY.md#what-the-claims-check-cannot-do).

### Add a tracker destination

1. Create `src/applyops/tracker/<name>.py` with a class that subclasses `TrackerSink` and implements
   `existing_keys()` (return a set of `(company, role, date)` keys already present) and `_append(row)` (write
   it and return a human-readable location). `push()` already handles duplicates for you.
2. Export it from `tracker/__init__.py`.
3. Add a `kind:` branch in `config.make_sink`.
4. Test it the way `tests/test_tracker.py` does: against a local fake, never the real service.

### Add a CLI command

Add a `cmd_<name>(args, out)` function in `cli.py`, register its parser in `build_parser`, and return an exit
code (`0` success, `1` a checked failure, `2` an external failure). Take the output stream as `out` so tests can
capture it.

## Style

* Python 3.11+, type hints, `from __future__ import annotations`.
* `ruff` rules `E F W I B UP SIM`, line length 100. Formatting is automatic: `ruff format .`.
* Keep `claims.py` and `posting.py` free of I/O to the tracker; keep the CLI thin.
* Fictional data only in tests, examples and docs.

## Release checklist

1. All four checks pass locally and in CI.
2. `__version__` in `src/applyops/__init__.py` and `version` in `pyproject.toml` match.
3. README status table and [ROADMAP.md](ROADMAP.md) are accurate.
4. Run the audit **with your private denylist**, and look at every screenshot and video frame by eye.
5. Tag: `git tag v0.1.0` and push the tag.
