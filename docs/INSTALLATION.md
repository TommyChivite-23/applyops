# Installation (Windows)

Return to the [README](../README.md). After installing, follow the [user guide](USER_GUIDE.md).

## Prerequisites

* **Windows 10 or 11** with PowerShell (Windows Terminal recommended).
* **Python 3.11 or newer.** Check with `py --version` or `python --version`. Install from
  <https://www.python.org/downloads/> (tick **Add python.exe to PATH**) or run
  `winget install Python.Python.3.12`.
* **Git**, only to clone the repository: `git --version`. Install from <https://git-scm.com/download/win>.

## Install ApplyOps

```powershell
git clone https://github.com/TommyChivite-23/applyops.git
cd applyops
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[sheets,dev]"
applyops --version
```

Expected: `applyops 0.1.0`.

What each step does:

| Step | Purpose |
|---|---|
| `py -3.12 -m venv .venv` | Creates a private folder of Python packages for this project, so it cannot conflict with others |
| `Activate.ps1` | Makes `python`, `pip` and `applyops` use that folder (the prompt shows `(.venv)`) |
| `pip install -e ".[sheets,dev]"` | Installs ApplyOps in *editable* mode (code changes take effect at once) with the optional Google Sheets libraries and the developer tools |
| `applyops --version` | Confirms the command is installed |

The core tool needs only PyYAML. If you do not use Google Sheets or run the tests, `pip install -e .` is enough.

If you do not want to activate the environment, run it directly: `.\.venv\Scripts\applyops --version`.

## Check the installation

```powershell
applyops claims check examples/sample_candidate/cover_letter_ok.md --ledger examples/sample_candidate/claims.yaml
```

You should see three `[PASS]` lines and `3 claims, 0 failed.`

To run the full test suite, see [TESTING.md](TESTING.md).

## Your own candidate folder

1. Create a folder **outside** this repository, for example `C:\Users\<you>\ApplyOpsData\me`.
2. Copy the three files from `examples/sample_candidate`: `applyops.yaml`, `skills.yaml`, `claims.yaml`.
3. Replace the fictional content with your own. Only put in the ledger what you can prove.
4. Pass the folder with `--candidate`, for example
   `applyops new C:\path\to\posting.txt --candidate C:\Users\<you>\ApplyOpsData\me --letter C:\path\to\letter.md`.

## Google Sheets tracker (optional)

> **Not yet verified against a live spreadsheet.** The code is tested against an in-memory fake of the
> Sheets API. Treat the first real run as a trial on a **copy** of your tracker.

1. In the Google Cloud console, create a project and enable the **Google Sheets API**.
2. Create a **service account** and download its JSON key. Save it **outside** the repository.
3. Open your spreadsheet, click **Share**, and share it with the service account's email (Editor).
4. Make sure the sheet's first row has the header names ApplyOps writes (see the
   [user guide](USER_GUIDE.md#tracker-destinations)), or map your own with a `columns:` block.
5. In `applyops.yaml`:

   ```yaml
   tracker:
     kind: sheets
     sheet: Applications
   ```

6. Provide the secrets as environment variables for the current PowerShell window:

   ```powershell
   $env:APPLYOPS_SPREADSHEET_ID = "your-spreadsheet-id"
   $env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\outside\repo\service-account.json"
   ```

   The spreadsheet ID is the long string in the sheet's URL between `/d/` and `/edit`.
7. Test with `--dry-run` first, then without it.

Never put the JSON key or the real spreadsheet ID in a file inside this repository.

## Uninstall

Delete the `.venv` folder. Nothing else is installed globally.

Problems? See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
