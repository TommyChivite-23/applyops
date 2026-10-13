"""Checks added after probing the original validator with realistic letter sentences.

Each test is a sentence that slipped through (or must still be handled) and why.
All data is fictional.
"""

from pathlib import Path

import pytest

from applyops.claims import Verdict, check_file, check_text, claim_tense, figures, load_ledger

SAMPLE = Path(__file__).parent.parent / "examples" / "sample_candidate"

LEDGER_YAML = """
claims:
  - id: fleet-tool
    text: Built a fleet device management tool used on 300 devices
    match: [fleet, "device|devices"]
    status: done
    evidence: https://github.com/example-alex/fleet-tool
    facts: ["99.5%"]
  - id: aws-cert
    text: Holds a fictional Cloud Practitioner certification
    match: [certification|certified, cloud]
    status: done
    evidence: https://example.com/alex/credentials
  - id: terraform
    text: Used Terraform in a lab
    match: [terraform]
    status: in_progress
    evidence: https://github.com/example-alex/tf-lab
  - id: spanish
    text: Professional working proficiency in Spanish
    match: [spanish]
    status: done
    evidence: https://example.com/alex/languages
"""


@pytest.fixture
def ledger(tmp_path):
    p = tmp_path / "claims.yaml"
    p.write_text(LEDGER_YAML, encoding="utf-8")
    return load_ledger(p)


def verdicts(text, ledger):
    return [(f.verdict, f.claim_id) for f in check_text(text, ledger)]


# -- resume-style sentences have no "I" -------------------------------------------------


def test_resume_style_bullet_is_a_claim(ledger):
    assert verdicts("Built a Kubernetes platform that serves users.", ledger) == [
        (Verdict.UNSUPPORTED, None)
    ]


def test_resume_style_bullet_supported_by_ledger(ledger):
    assert verdicts("Built a fleet device management tool.", ledger) == [(Verdict.OK, "fleet-tool")]


def test_bullet_list_lines_are_judged_separately(ledger):
    text = "- Built a fleet device tool\n- Led a Kubernetes migration\n"
    assert verdicts(text, ledger) == [
        (Verdict.OK, "fleet-tool"),
        (Verdict.UNSUPPORTED, None),
    ]


# -- invented numbers on an otherwise true claim ----------------------------------------


def test_invented_metric_is_blocked_even_when_the_claim_is_real(ledger):
    [f] = check_text("I built a fleet device management tool that saved $2M.", ledger)
    assert f.verdict is Verdict.UNVERIFIED_FIGURE
    assert "2m" in f.reason


def test_number_in_ledger_text_is_allowed(ledger):
    assert verdicts("I built a fleet device tool for 300 devices.", ledger) == [
        (Verdict.OK, "fleet-tool")
    ]


def test_number_listed_under_facts_is_allowed(ledger):
    assert verdicts("I built a fleet device tool with 99.5% uptime.", ledger) == [
        (Verdict.OK, "fleet-tool")
    ]


def test_number_formatting_is_normalised():
    assert figures("saved 5,000 hours and 90 %") == {"5000", "90%"}


def test_years_used_as_dates_are_not_metrics(ledger):
    assert verdicts("In 2024 I built a fleet device tool.", ledger) == [(Verdict.OK, "fleet-tool")]


def test_a_bare_year_like_count_is_still_a_metric(ledger):
    [f] = check_text("I built a fleet device tool that handled 2000 tickets.", ledger)
    assert f.verdict is Verdict.UNVERIFIED_FIGURE


def test_wrote_verb_is_recognised(ledger):
    [f] = check_text("The fleet device tool I wrote cut costs by 90%.", ledger)
    assert f.verdict is Verdict.UNVERIFIED_FIGURE


# -- attributes: certifications, experience, fluency ------------------------------------


def test_unlisted_certification_is_blocked(ledger):
    assert verdicts("I hold an AWS Solutions Architect certification.", ledger) == [
        (Verdict.UNSUPPORTED, None)
    ]


def test_listed_certification_passes(ledger):
    assert verdicts("I am certified in Cloud fundamentals.", ledger) == [(Verdict.OK, "aws-cert")]


def test_years_of_experience_need_a_ledger_entry_and_a_matching_number(ledger):
    [f] = check_text("I have 8 years of experience with Terraform.", ledger)
    # Terraform is only in progress and "8" is not in the entry: either failure is correct.
    assert not f.ok


def test_unlisted_language_is_blocked(ledger):
    assert verdicts("I am fluent in German.", ledger) == [(Verdict.UNSUPPORTED, None)]


def test_listed_language_passes(ledger):
    assert verdicts("I am fluent in Spanish.", ledger) == [(Verdict.OK, "spanish")]


def test_attribute_in_progress_entry_is_an_overclaim(ledger):
    [f] = check_text("I have used Terraform for 2 years.", ledger)
    assert f.verdict is Verdict.OVERCLAIM
    assert "stated as a fact" in f.reason


# -- the original behaviour still holds -------------------------------------------------


def test_plain_enthusiasm_is_not_a_claim(ledger):
    assert check_text("I am excited to apply. My goal is to learn.", ledger) == []


def test_sample_letters_unchanged_by_the_new_rules():
    ok = check_file(SAMPLE / "cover_letter_ok.md", SAMPLE / "claims.yaml")
    assert len(ok) == 3 and all(f.ok for f in ok)


def test_facts_must_be_a_list(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("claims:\n- {id: a, match: [x], facts: '99'}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a list"):
        load_ledger(p)


# -- documented limitations: these pass today, and say so on purpose ---------------------


@pytest.mark.parametrize(
    "sentence",
    [
        "Our team built a fleet device tool.",  # plural subject is treated as team work
        "My Kubernetes platform serves users.",  # possessive claim with no verb or attribute word
        "The platform handles heavy traffic.",  # no first-person claim
    ],
)
def test_known_limitation_not_detected(sentence):
    assert claim_tense(sentence) is None, (
        "if this starts failing, the checker got stricter: update docs/SECURITY.md"
    )


# -- a true claim must not carry an unproven one -----------------------------------------


def test_compound_sentence_fails_if_any_mentioned_entry_fails(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text(
        "claims:\n"
        "- {id: fleet, match: [fleet], status: done, evidence: http://x}\n"
        "- {id: k8s, match: [kubernetes], status: planned, evidence: http://y}\n",
        encoding="utf-8",
    )
    [f] = check_text("I built a fleet tool and a Kubernetes platform.", load_ledger(p))
    assert (f.verdict, f.claim_id) == (Verdict.OVERCLAIM, "k8s")


def test_compound_sentence_passes_when_every_mentioned_entry_is_supported(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text(
        "claims:\n"
        "- {id: fleet, match: [fleet], status: done, evidence: http://x}\n"
        "- {id: k8s, match: [kubernetes], status: done, evidence: http://y}\n",
        encoding="utf-8",
    )
    [f] = check_text("I built a fleet tool and a Kubernetes platform.", load_ledger(p))
    assert f.ok


def test_known_limitation_unlisted_item_inside_a_supported_sentence(ledger):
    """Documented in docs/SECURITY.md: only ledger entries can be enforced.

    A second claim bundled into one sentence passes if the ledger never mentions it. The same
    claim as its own sentence is caught. If this test starts failing, the checker got stricter:
    update the docs.
    """
    assert verdicts("I built a fleet device tool and a payments platform.", ledger) == [
        (Verdict.OK, "fleet-tool")
    ]
    assert verdicts("I also built a payments platform.", ledger) == [(Verdict.UNSUPPORTED, None)]
