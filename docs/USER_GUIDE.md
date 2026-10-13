# User guide

Everyday use of ApplyOps. Install first: [INSTALLATION.md](INSTALLATION.md). Overview: [README](../README.md).

## The idea in one minute

You keep three small text files about yourself, in one folder (the **candidate folder**):

| File | What it holds |
|---|---|
| `skills.yaml` | Your skills, each with the words a posting might use for it (aliases) |
| `claims.yaml` | The **ledger**: what you may claim, with evidence |
| `applyops.yaml` | Where those files are and which tracker to use |

For each job you save the posting as a text file and (optionally) write a cover letter. ApplyOps then scores
the fit, checks the letter against the ledger, and records the application.

The folder `examples/sample_candidate` is a complete fictional example. Copy it to start your own, and keep your
real one **outside** this repository.

## Posting format

A saved text file with header lines and a Requirements list:

```text
Title: Automation Engineer
Company: Acme Logistics
Location: Remote (EU)
Salary: EUR 50,000 - 60,000
URL: https://example.com/jobs/acme-automation-engineer

Requirements
- 3+ years of Python
- Docker and CI/CD pipelines
- Experience with Terraform

Nice to have
- Kubernetes
```

* `Title:` and `Company:` are required; `Location:`, `Salary:`, `URL:` are optional.
* Requirements are the bullets under a heading such as *Requirements*, *Qualifications*, *What you'll need* or
  *Must have* (or *Requisitos*). Bullets under other headings (like *Nice to have*) are not scored.
* If there is no such heading, **every** bullet is treated as a requirement.

## 1. Score the fit

```powershell
applyops fit examples/sample_candidate/posting_acme.txt --skills examples/sample_candidate/skills.yaml
```

```
Acme Logistics - Automation Engineer: fit 8/10
  gap: Experience with Terraform
```

A requirement counts as covered when any alias of any skill appears in it as a whole word. Score = covered
divided by total, scaled to 10. **Gaps** are the requirements nothing covered. To improve accuracy, add the
words postings use to the `aliases` in `skills.yaml`.

## 2. Check a cover letter

```powershell
applyops claims check examples/sample_candidate/cover_letter_overclaim.md --ledger examples/sample_candidate/claims.yaml
```

Each line is `[PASS]` or `[FAIL]`, the verdict, the matching ledger entry, and the sentence. Failed lines
add a `reason:`. The process exits with code `1` if anything failed, so you can use it in scripts.

| Verdict | Meaning | How to fix |
|---|---|---|
| `ok` | Backed by an entry with evidence | nothing |
| `unsupported` | No ledger entry matches the sentence | Remove the sentence, or add a ledger entry **only if it is true** |
| `no_evidence` | The entry exists but has no `evidence` link | Add a real link, or remove the sentence |
| `overclaim` | The wording says more than the entry's status (for example "I built" but the entry is `in_progress`) | Reword to match the status, or finish the work and set `done` |
| `unverified_figure` | The sentence quotes a number the entry does not contain | Remove the number, or add it to the entry's `text`/`facts` if it is true |

## 3. Write ledger entries

```yaml
claims:
  - id: fleet-tool
    text: Built a fleet device management tool in Python and Flask with tests and CI
    match: [fleet, "device|devices"]
    status: done
    evidence: https://github.com/example-alex/fleet-tool
    facts: ["300"]
```

* `match`: every term must appear in a sentence for this entry to apply; inside a term, `a|b` means "a or b".
  Match whole words only (`fleet` does not match `fleetwood`).
* `status`: `done`, `in_progress` or `planned`. A `planned` entry supports **nothing**; it exists so you do
  not accidentally promise it.
* `evidence`: a link that proves it. An entry without evidence cannot back any sentence.
* `facts`: numbers you may quote for this entry (numbers already inside `text` are allowed automatically).
  Quote only figures you can defend.

**Rule of thumb:** write the ledger from facts you can prove, then write the letter. Never edit the ledger to
make a sentence pass; edit the sentence.

## 4. Run the whole application: `applyops new`

```powershell
applyops new examples/sample_candidate/posting_acme.txt `
  --candidate examples/sample_candidate `
  --letter examples/sample_candidate/cover_letter_ok.md --dry-run
```

Order of work: fit score, then the claims gate, then the tracker row. If a claim fails you see
`Stopped: fix the failed claims before anything is published.` and **no tracker row is written**.

| Option | Effect |
|---|---|
| `--candidate DIR` | Folder with `applyops.yaml` (default: current folder) |
| `--letter FILE` | Letter to check; its file name is recorded in the tracker |
| `--applied` | Record status `Applied` instead of `Saved` |
| `--dry-run` | Print the row that would be added; write nothing |

The follow-up date is set to seven days after today.

## 5. Add a row by hand

```powershell
applyops tracker push --candidate examples/sample_candidate --company Initech --role SRE --date 2026-10-01 --fit 6
```

Running the same command twice prints `Skipped: ... is already tracked`.

## Tracker destinations

* **CSV (default):** `tracker.kind: csv`, `path: out/tracker.csv`. Nothing needs setting up.
* **Google Sheets:** see [INSTALLATION.md](INSTALLATION.md#google-sheets-tracker-optional). The sheet's header
  row must contain the column names ApplyOps writes (defaults: `Date Applied`, `Company`, `Role`, `Status`,
  `Location`, `Fit (1-10)`, `Priority`, `Salary`, `Source`, `Posting URL`, `Resume`, `Cover Letter`,
  `Follow-up`, `Notes`). Rename them with a `columns:` block if yours differ.

## What ApplyOps will not do (yet)

It does not write or tailor your letter, make PDFs, fetch a posting from a URL, or upload files. See the
[roadmap](ROADMAP.md).

Next: [Troubleshooting](TROUBLESHOOTING.md)
