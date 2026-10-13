# Roadmap

Only v0.1 exists. Everything below it is **planned**, not implemented. Return to the [README](../README.md).

## v0.1 (this release)

- Claims ledger check, English and Spanish, with CI gate on sample letters
- Hardened checks: resume-style sentences, certifications/years/fluency, invented numbers (`facts`), and
  "every mentioned ledger entry must pass" for compound sentences
- Posting parser and fit score with gaps
- Tracker sync: Google Sheets (header-mapped, idempotent, retries; tested against a fake) and CSV
- `applyops new` pipeline: fit, claims, tracker row; stops before writing on any failed claim
- Public-repo audit script, CI, 100 tests

## v0.2: documents (planned)

- Fill resume and cover-letter `.docx` templates from an approved-bullets library
- Layout fixes as library functions: tight bullet indents, clickable GitHub links, page split for the education section
- PDF checks: exact page count, named section starts on page 2, links present
- Generated letters pass through the same claims check

## v0.3: posting intake and publishing (planned)

- `applyops new URL`: fetch and archive the posting text (Greenhouse, Lever, Workable)
- Upload resume and letter to Drive folders with a naming rule
- Evidence link check: each ledger URL must resolve
- Verify the Google Sheets tracker against a live spreadsheet

## Claims-check improvements (planned)

- Flag a claim bundled with an item the ledger never mentions (the known compound-sentence gap)
- Detect plural and role statements ("Our team built...", "I was the lead developer of...")
- Narrow the Sheets API scope

## Later

- Anonymized funnel dashboard (applied, replied, interview by role type)
- Requirement matching with embeddings in addition to aliases, measured against a labelled set of postings
