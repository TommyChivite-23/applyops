# Walkthrough transcript

The subtitles of `applyops-walkthrough.mp4` (the video has no audio), by chapter, with timestamps.
Every command shown was really executed; its real output was captured and replayed with human-style typing.

## 1. Introduction

**[0:01]** ApplyOps is a command line tool that checks a job application before it goes out. It scores how well a job posting fits your skills, blocks cover letter sentences you cannot prove, and records the application in a tracker without creating duplicates. Everything in this video uses a fictional candidate, Alex Rivera, and a fictional employer.

**[0:24]** Here is the idea in ten seconds. First we point a shell variable at the sample candidate folder. Then we check a cover letter that makes four claims. The first passes. The other three are blocked, each with its own reason, and the command exits with an error so a script or a continuous integration pipeline can stop.

## 2. Installation

**[0:53]** ApplyOps needs Python 3.11 or newer on Windows. Open PowerShell in the project folder and create a virtual environment, which is a private folder of packages for this project.

**[1:07]** Activate it. The prompt now starts with dot venv. Then install ApplyOps in editable mode, with the optional Google Sheets libraries and the developer tools. The install output is shortened here.

**[1:30]** Check that the command is installed. There are four commands: claims, fit, tracker, and new.

## 3. Configuration

**[1:40]** A candidate is a folder with three small files. The applyops.yaml file says where the other two are and which tracker to use. Here it is a plain CSV file, so nothing needs setting up.

**[1:55]** The skills file lists each skill with the other words a job posting might use for it. The fit score uses these aliases.

**[2:05]** The claims ledger is the important file. Each entry says what Alex may claim. Match lists the words a sentence must contain. Status is done, in progress, or planned. Evidence is a link that proves it. Notice that the Kubernetes entry is only planned and has no evidence, so no letter may claim it.

**[2:28]** For the Google Sheets tracker you would add a spreadsheet identifier and credentials as environment variables, never stored in the repository. That integration is tested against a fake, and has not yet been run against a live spreadsheet.

## 4. Running a job

**[2:44]** A job posting is saved as a text file, with Title and Company lines and a list of requirements.

**[2:52]** The fit command compares each requirement with the skills file. Five of the six requirements are covered, so the fit is eight out of ten. The one gap is Terraform, which is not in Alex's skills.

## 5. Generating documents

**[3:08]** ApplyOps does not write the resume or the cover letter yet. Document generation and PDF layout checks are planned for version 0.2. Today you supply the letter, and ApplyOps checks it. Here is the sample letter Alex wrote.

## 6. Validation

**[3:24]** Now we check this letter. All three claims match a ledger entry with evidence and a matching status, so they pass. The summary says three claims, zero failed, and the exit code is zero. PDF page count and layout checks are not implemented yet.

## 7. Failure handling

**[3:46]** Now the failure cases. This letter claims a Kubernetes platform that the ledger lists as planned. It says built for an assistant that is still in progress. And it mentions a mailbox migration that is not in the ledger at all. Each failure has its own verdict and a plain reason, and the exit code is one.

**[4:18]** A third letter describes a real project, but adds an invented number, two million dollars saved, and a language that is not in the ledger. The number is blocked because it does not appear in the ledger entry.

## 8. Tracker workflow

**[4:38]** The new command runs everything together: the fit score, then the claims gate, then the tracker. If a claim fails, it stops before anything is written. We can confirm that no tracker file exists.

**[5:03]** With the supported letter, a dry run shows the row that would be added, including a follow up date seven days later.

**[5:17]** Without dry run, the row is written to the CSV tracker. Running the same command again is safe: the duplicate is skipped. The file now has a header and one row.

## 9. Developer overview

**[5:56]** For developers, the code is split into small modules. The claims module and the posting module know nothing about the tracker, and the tracker knows nothing about claims, so each part is tested on its own.

**[6:16]** The project has one hundred tests and ninety eight percent coverage. They use only fictional data and a fake of the Sheets service, so they need no network and no accounts.

**[6:32]** Lint and format checks run next, along with a pre publish audit that looks for secrets, private addresses, and personal data.

**[6:46]** The same checks run on GitHub Actions for every push and pull request, plus a gate that proves the overclaiming letters are blocked.

## 10. Conclusion

**[6:57]** To recap. ApplyOps keeps a cover letter honest by checking it against a ledger of provable facts. It scores fit, blocks unsupported claims and invented numbers, and logs applications without duplicates. It is pattern matching, not a lie detector, and its limits are documented. Developers can extend it with new claim patterns, new tracker destinations, or the planned document generator.
