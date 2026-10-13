# Security and privacy

What to keep out of the repository, how credentials are handled, and what the claims check can and cannot
guarantee. Return to the [README](../README.md).

## What must never be committed

| Never commit | Why | How it is prevented |
|---|---|---|
| Your real resume, contact details, real `claims.yaml`/`skills.yaml` | Personal data | Keep real candidate data in a folder **outside** the repo. `.gitignore` also excludes `private/` |
| Real tracker rows, exported `.xlsx`/`.csv` | Employer names, dates and pay of real applications | `.gitignore` excludes `out/`, `*.xlsx`; the audit rejects forbidden file types |
| Google service-account JSON, OAuth tokens | Full access to your Sheets | `.gitignore` excludes `credentials*.json`; the audit looks for key-like strings |
| Real spreadsheet or Drive IDs | They identify your documents | Use `APPLYOPS_SPREADSHEET_ID` (environment) not the config file |
| Private job descriptions, recruiter emails | Third-party and confidential content | Keep postings outside the repo; samples here are invented |

## Credentials

* The only secrets ApplyOps can use are for the optional Google Sheets tracker, supplied by environment variables
  (`APPLYOPS_SPREADSHEET_ID`, `GOOGLE_APPLICATION_CREDENTIALS`) or by `applyops.yaml` in your **private** candidate
  folder. See `.env.example` for placeholders only.
* Use a **service account** with access to **one** spreadsheet (share the sheet with its email). Do not use
  your personal account's broad credentials.
* Values are written to Sheets with `valueInputOption=RAW`, so a cell can never become a formula.
* The Sheets scope is `https://www.googleapis.com/auth/spreadsheets` (read and write spreadsheets).
  That is broader than needed for one sheet; a narrower scope is a future hardening item.

## The pre-publish audit

```powershell
python scripts/audit_public_repo.py --denylist C:\path\outside\the\repo\denylist.txt
```

It scans every file git would commit for: private keys and cloud keys, secrets assigned to string literals,
long high-entropy strings, private-network IP addresses, email addresses outside reserved example domains,
US phone numbers outside the fictional `555-01xx` block, Windows user-profile paths, and forbidden file types
(databases, logs, certificates, Office documents, `.env`).

The **denylist** is a plain text file, one case-insensitive term per line, kept **outside** the repository: real
names, employers, hostnames, a Drive folder name. It is the one place the real identifiers are written, which
is why it must never be committed. CI runs the audit **without** a denylist (it has none), so the denylist
check is something you run on your own machine before pushing.

Limits of the audit: it recognises patterns, not meaning. It does not read images, PDFs or video, so review
screenshots and recordings by eye. It will not know about a secret in a format it has no rule for.

## What the claims check cannot do

The claims ledger is a **guardrail against overstating, not a lie detector.** It compares a letter to a file you
wrote. If the ledger is wrong, the check will faithfully approve a false letter.

Measured behaviour on the sample ledger (every row is a test in `tests/`):

| Sentence | Result | Note |
|---|---|---|
| `I built a fleet device management tool.` | **ok** | backed by an entry with evidence |
| `Built a Kubernetes platform that serves 5,000 users.` | blocked | resume-style sentences are checked |
| `I hold an AWS Solutions Architect certification.` | blocked | certifications must be in the ledger |
| `I have 8 years of experience with Terraform.` | blocked | years of experience must be in the ledger |
| `I am fluent in German.` | blocked | languages must be in the ledger |
| `I built a fleet device management tool that saved $2M.` | blocked | numbers must appear in the entry's `text` or `facts` |
| `I built a fleet tool and a Kubernetes platform.` | blocked | **every** ledger entry a sentence mentions must pass |
| `I built a fleet device tool and a payments platform.` | **passes** | an item the ledger never mentions is invisible when bundled with a supported one; as its own sentence it is blocked |
| `Our team built a fleet device tool.` | **not checked** | plural subjects are treated as teamwork, not a personal claim |
| `My Kubernetes platform serves users.` | **not checked** | possessive sentence with no claim verb or attribute word |
| `I was the lead developer of a fleet device tool.` | **not checked** | role statements without a claim verb |
| `I have experience with fleet device tools.` | **not checked** | "experience" without a number |
| `Responsible for the fleet device tool.` | **not checked** | no first-person marker or listed verb |

What this means in practice:

1. **Write the ledger first, from facts you can prove.** The ledger is your source of truth.
2. **Read your final letter yourself.** The tool catches common overclaims; it does not replace reading.
3. **Keep one claim per sentence.** It makes failures precise and avoids the bundled-claim gap.
4. **Do not edit the ledger to make a sentence pass.** Edit the sentence.
5. **Do not describe ApplyOps as verifying that applications are truthful.** It enforces consistency with a ledger.

The `test_known_limitation_*` tests deliberately fail the day the checker gets stricter, so these docs cannot
silently drift from the behaviour.

## Reporting a vulnerability

Open a private security advisory on the GitHub repository, or contact the maintainer through the profile on
the repository page. Please do not post credentials or personal data in a public issue.

Related: [Installation](INSTALLATION.md) | [Development](DEVELOPMENT.md)
