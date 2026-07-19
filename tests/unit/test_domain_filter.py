from app.services.domain_filter import check_domain_prefilter
from app.models.enums import RiskTier

def test_domain_filter_allowed(mock_config):
    # Allowed attention/state concept
    reg = check_domain_prefilter(
        keystone_id="ks_1",
        concept="attention and time",
        statement="Focusing on breathing alters the subjective perception of time passing.",
        config=mock_config
    )
    assert reg is None

def test_domain_filter_prohibited(mock_config):
    # Prohibited medical cause statement
    reg = check_domain_prefilter(
        keystone_id="ks_2",
        concept="cancer cure",
        statement="A strict positive mindset can cure pancreatic cancer.",
        config=mock_config
    )
    assert reg is not None
    assert reg.risk_tier == RiskTier.PROHIBITED.value
    assert reg.stage == "domain_filter"
    assert "domain:cure" in reg.reason or "domain:cancer" in reg.reason

    # Prohibited psychosomatic mechanism statement
    reg2 = check_domain_prefilter(
        keystone_id="ks_3",
        concept="mind-body illness",
        statement="Unexpressed anger is the primary origin of stomach ulcers.",
        config=mock_config
    )
    assert reg2 is not None
    assert any("phrase_regex" in r or "domain:illness" in r for r in reg2.matched_rules)

def test_domain_filter_disabled(mock_config):
    mock_config.enforce_domain_prefilter = False
    reg = check_domain_prefilter(
        keystone_id="ks_2",
        concept="cancer cure",
        statement="A strict positive mindset can cure pancreatic cancer.",
        config=mock_config
    )
    assert reg is None
