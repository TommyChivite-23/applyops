# Troubleshooting

Return to the [README](../README.md). Setup steps: [INSTALLATION.md](INSTALLATION.md).

## Installation and running

| Symptom | Cause | Fix |
|---|---|---|
| `Activate.ps1 cannot be loaded because running scripts is disabled` | PowerShell's execution policy | Run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or skip activation and run `.\.venv\Scripts\applyops` |
| `applyops : The term 'applyops' is not recognized` | The environment is not active, or the install failed | Run `.\.venv\Scripts\Activate.ps1` (prompt shows `(.venv)`), then `pip install -e ".[sheets,dev]"` |
| `py : The term 'py' is not recognized` | Python launcher not installed | Install Python from python.org with the launcher, or use `python -m venv .venv` |
| `requires a different Python: 3.10 not in '>=3.11'` | Python is too old | Install 3.11 or newer and create the environment with it: `py -3.12 -m venv .venv` |
| `ModuleNotFoundError: No module named 'yaml'` | Installed outside the environment | Activate `.venv`, then `pip install -e .` |
| A command you pasted ran as several lines and failed | Multi-line paste in PowerShell | Use one line, or end each line with a backtick `` ` `` as in the examples |
| `Error: Google Sheets support needs: pip install 'applyops[sheets]'` | Google libraries not installed | `pip install -e ".[sheets]"` |

## Input files

| Symptom | Cause | Fix |
|---|---|---|
| `ValueError: posting needs 'Title:' and 'Company:' lines` | The posting has no header lines | Add `Title: ...` and `Company: ...` at the top ([format](USER_GUIDE.md#posting-format)) |
| `fit 0/10` with no gaps listed | No requirement bullets were found | Use `-`, `*` or numbered bullets and a *Requirements* heading |
| A requirement you cover shows as a gap | None of your aliases appear in the requirement | Add the posting's wording to `aliases` in `skills.yaml` (matching is whole-word, case-insensitive) |
| `LedgerError: claim #N needs 'id' and 'match'` | Ledger entry missing a field | Give every entry an `id` and a `match` list |
| `LedgerError: duplicate claim id` / `unknown status` / `'facts' must be a list` | Ledger formatting | Fix the entry; statuses are `done`, `in_progress`, `planned`; `facts` is a YAML list |
| `FileNotFoundError` on `claims.yaml` or `skills.yaml` | Wrong `--candidate` folder or the file is not where `applyops.yaml` says | Check the path and the `claims:`/`skills:` lines in `applyops.yaml` |
| Non-English letters show strange characters | File not saved as UTF-8 | Save as UTF-8 (ApplyOps reads UTF-8) |

## Claims check results

| Symptom | Meaning | Fix |
|---|---|---|
| `unsupported` on a true statement | No ledger entry's `match` terms all appear in the sentence | Add a ledger entry for it, or loosen its `match` terms (use `a|b` for synonyms) |
| `overclaim: letter says completed, ledger says in progress` | "I built" needs `done` | Reword to "I'm building", or set `done` once it is finished |
| `no_evidence` | The matching entry has no `evidence` | Add a real link |
| `unverified_figure ... 2m` | The sentence quotes a number the entry lacks | Remove it, or add it to the entry's `facts` if it is true |
| A sentence you expected to fail passes | The checker only judges recognised claim wording | Read [what the check cannot do](SECURITY.md#what-the-claims-check-cannot-do) |
| `No first-person claims found.` | No sentence looked like a claim | Check the file path; the tool does not check ordinary sentences |

## Tracker

| Symptom | Cause | Fix |
|---|---|---|
| `Skipped: ... is already tracked` | Same company, role and date already exists | Expected; change `--date` or the role if it is genuinely a new application |
| `Tracker error: ... sheet '...' is missing columns: ...` (exit 2) | The sheet's header row lacks a column | Add the header, or map names with a `columns:` block |
| `tracker.kind is sheets but no spreadsheet_id is set` | No ID provided | Set `APPLYOPS_SPREADSHEET_ID` or `spreadsheet_id` in `applyops.yaml` |
| `Sheets request failed: ... HTTP 403` | The service account cannot access the sheet | Share the sheet with the service account's email (Editor) |
| `Sheets still failing after 4 attempts (HTTP 429)` | Google rate limit | Wait a minute and retry |
| CSV row shows dates as `2026-10-13` | ISO format by design | Format the column in your spreadsheet program |

## Tests and tools

| Symptom | Fix |
|---|---|
| `PermissionError` on `pytest-of-<user>` in Temp | `pytest --basetemp=$env:USERPROFILE\pytest_tmp -p no:cacheprovider` |
| `ruff format --check` says a file would be reformatted | Run `ruff format .` then re-run the checks |
| Audit reports a denylist hit on your own name | Your denylist term is too broad; use a more specific term (the audit matches substrings) |
| Audit says `unknown-type` for a file | Add the extension to `TEXT_SUFFIXES` in `scripts/audit_public_repo.py` if it is safe text, or remove the file |

Still stuck? Open an issue with the exact command, the full output, and your Python version (`python --version`).
Remove any personal data from what you paste.
