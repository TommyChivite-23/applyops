from pathlib import Path

import pytest

from applyops.claims import (
    Verdict,
    check_file,
    check_text,
    claim_tense,
    load_ledger,
    split_sentences,
)

SAMPLE = Path(__file__).parent.parent / "examples" / "sample_candidate"


@pytest.fixture
def ledger():
    return load_ledger(SAMPLE / "claims.yaml")


def verdicts(text, ledger):
    return [(f.verdict, f.claim_id) for f in check_text(text, ledger)]


def test_sample_ok_letter_passes():
    findings = check_file(SAMPLE / "cover_letter_ok.md", SAMPLE / "claims.yaml")
    assert len(findings) == 3
    assert all(f.ok for f in findings)


def test_sample_overclaim_letter_fails_three_ways():
    findings = check_file(SAMPLE / "cover_letter_overclaim.md", SAMPLE / "claims.yaml")
    got = [(f.verdict, f.claim_id) for f in findings]
    assert got == [
        (Verdict.OK, "fleet-tool"),
        (Verdict.NO_EVIDENCE, "kubernetes-platform"),
        (Verdict.OVERCLAIM, "rag-assistant"),
        (Verdict.UNSUPPORTED, None),
    ]


def test_planned_entry_with_evidence_still_blocks_promise(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text(
        "claims:\n- id: k8s\n  match: [kubernetes]\n  status: planned\n  evidence: http://x\n"
    )
    [f] = check_text("I'm building a Kubernetes platform.", load_ledger(p))
    assert f.verdict is Verdict.OVERCLAIM
    assert "ledger says planned" in f.reason


def test_in_progress_supports_ongoing_but_not_completed(ledger):
    assert verdicts("I'm building an assistant over runbooks.", ledger) == [
        (Verdict.OK, "rag-assistant")
    ]
    assert verdicts("I have built an assistant over runbooks.", ledger) == [
        (Verdict.OVERCLAIM, "rag-assistant")
    ]


def test_done_supports_ongoing_wording(ledger):
    assert verdicts("I am working on the fleet device tool's next release.", ledger) == [
        (Verdict.OK, "fleet-tool")
    ]


def test_spanish_claims_are_checked(ledger):
    text = (
        "Construí una herramienta de gestión de fleet devices. "
        "Estoy construyendo una plataforma Kubernetes."
    )
    assert verdicts(text, ledger) == [
        (Verdict.OK, "fleet-tool"),
        (Verdict.NO_EVIDENCE, "kubernetes-platform"),
    ]


def test_non_claims_are_ignored(ledger):
    assert check_text("I am excited to apply. Your team builds great tools.", ledger) == []


def test_match_needs_every_term(ledger):
    # "fleet" alone is not enough; the entry also needs "device(s)".
    assert verdicts("I built a fleet of scripts.", ledger) == [(Verdict.UNSUPPORTED, None)]


def test_match_respects_word_start(ledger):
    assert verdicts("I built a deviceless fleetwood thing.", ledger) == [
        (Verdict.UNSUPPORTED, None)
    ]


@pytest.mark.parametrize(
    "sentence,tense",
    [
        ("I’m currently learning Go.", "ongoing"),
        ("I've shipped three releases.", "done"),
        ("We built it together.", None),
        ("Lideré un equipo de tres.", "done"),
    ],
)
def test_claim_tense(sentence, tense):
    assert claim_tense(sentence) == tense


def test_split_sentences_handles_paragraphs():
    assert split_sentences("One. Two!\n\nThree\nstill three.") == [
        "One.",
        "Two!",
        "Three still three.",
    ]


@pytest.mark.parametrize(
    "body,message",
    [
        ("claims:\n- text: x\n", "needs 'id' and 'match'"),
        ("claims:\n- {id: a, match: [x]}\n- {id: a, match: [y]}\n", "duplicate"),
        ("claims:\n- {id: a, match: [x], status: maybe}\n", "unknown status"),
        ("claims:\n- {id: a, match: []}\n", "at least one"),
    ],
)
def test_ledger_validation(tmp_path, body, message):
    p = tmp_path / "c.yaml"
    p.write_text(body)
    with pytest.raises(ValueError, match=message):
        load_ledger(p)


def test_single_string_match_and_empty_ledger(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("claims:\n- {id: a, match: terraform, evidence: http://x}\n")
    assert load_ledger(p)[0].match == ("terraform",)
    empty = tmp_path / "e.yaml"
    empty.write_text("")
    assert load_ledger(empty) == []
