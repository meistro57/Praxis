from app.models.keystone import KeystoneRecord
from app.services.candidate_selector import check_standard_prefilter

def test_standard_prefilter_allowed(mock_config):
    rec = KeystoneRecord(
        id="ks_1",
        concept="cognitive bias",
        statement="Expectation influences sensory perception in simple visual tasks.",
        convergence=0.78,
        critic_verdict="pass"
    )
    reg = check_standard_prefilter(rec, mock_config)
    assert reg is None

def test_standard_prefilter_low_convergence(mock_config):
    rec = KeystoneRecord(
        id="ks_2",
        concept="cognitive bias",
        statement="Expectation influences sensory perception.",
        convergence=0.60,
        critic_verdict="pass"
    )
    reg = check_standard_prefilter(rec, mock_config)
    assert reg is not None
    assert "convergence" in reg.reason.lower()

def test_standard_prefilter_failed_critic(mock_config):
    rec = KeystoneRecord(
        id="ks_3",
        concept="cognitive bias",
        statement="Expectation influences sensory perception.",
        convergence=0.80,
        critic_verdict="fail"
    )
    reg = check_standard_prefilter(rec, mock_config)
    assert reg is not None
    assert "critic" in reg.reason.lower()

def test_standard_prefilter_boilerplate(mock_config):
    rec = KeystoneRecord(
        id="ks_4",
        concept="citation",
        statement="Copyright 1999 by Meta-Bridge Publishing. All rights reserved.",
        convergence=0.80,
        critic_verdict="pass"
    )
    reg = check_standard_prefilter(rec, mock_config)
    assert reg is not None
    assert "boilerplate" in reg.reason.lower()

def test_standard_prefilter_historical(mock_config):
    rec = KeystoneRecord(
        id="ks_5",
        concept="history",
        statement="Immanuel Kant died in 1804 in Konigsberg.",
        convergence=0.80,
        critic_verdict="pass"
    )
    reg = check_standard_prefilter(rec, mock_config)
    assert reg is not None
    assert "historical" in reg.reason.lower()
