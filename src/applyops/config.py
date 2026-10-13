"""Candidate config: where the candidate's files live and which tracker to use.

applyops.yaml, in the candidate folder:

    candidate: Alex Rivera
    claims: claims.yaml
    skills: skills.yaml
    tracker:
      kind: sheets            # sheets | csv
      spreadsheet_id: ...     # or env APPLYOPS_SPREADSHEET_ID
      sheet: Applications
      credentials_file: ...   # or env GOOGLE_APPLICATION_CREDENTIALS
      columns: {fit_score: "Fit"}   # optional overrides of header names
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from applyops.tracker import DEFAULT_COLUMNS, CsvSink, GoogleSheetsSink, TrackerSink, build_service


@dataclass
class TrackerConfig:
    kind: str = "csv"
    path: str = "tracker.csv"
    spreadsheet_id: str = ""
    sheet: str = "Applications"
    credentials_file: str = ""
    columns: dict[str, str] = field(default_factory=dict)


@dataclass
class Config:
    root: Path
    candidate: str = ""
    claims: str = "claims.yaml"
    skills: str = "skills.yaml"
    tracker: TrackerConfig = field(default_factory=TrackerConfig)

    @property
    def claims_path(self) -> Path:
        return self.root / self.claims

    @property
    def skills_path(self) -> Path:
        return self.root / self.skills


def load_config(folder: Path | str) -> Config:
    root = Path(folder)
    path = root / "applyops.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    data = data or {}
    tracker = TrackerConfig(**(data.get("tracker") or {}))
    tracker.spreadsheet_id = os.environ.get("APPLYOPS_SPREADSHEET_ID", tracker.spreadsheet_id)
    tracker.credentials_file = os.environ.get(
        "GOOGLE_APPLICATION_CREDENTIALS", tracker.credentials_file
    )
    return Config(
        root=root,
        candidate=data.get("candidate", ""),
        claims=data.get("claims", "claims.yaml"),
        skills=data.get("skills", "skills.yaml"),
        tracker=tracker,
    )


def make_sink(cfg: Config) -> TrackerSink:
    t = cfg.tracker
    columns = {**DEFAULT_COLUMNS, **t.columns}
    if t.kind == "csv":
        return CsvSink(cfg.root / t.path, columns=columns)
    if t.kind == "sheets":
        if not t.spreadsheet_id:
            raise ValueError("tracker.kind is sheets but no spreadsheet_id is set")
        service = build_service(t.credentials_file or None)
        return GoogleSheetsSink(service, t.spreadsheet_id, sheet=t.sheet, columns=columns)
    raise ValueError(f"unknown tracker kind '{t.kind}'")
