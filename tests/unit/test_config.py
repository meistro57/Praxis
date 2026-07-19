import pytest
from config import Settings

def test_settings_validation_ranges():
    # Invalid convergence
    with pytest.raises(ValueError):
        Settings(MIN_KEYSTONE_CONVERGENCE=-0.1)
    with pytest.raises(ValueError):
        Settings(MIN_KEYSTONE_CONVERGENCE=1.5)

    # Invalid max_protocol_minutes
    with pytest.raises(ValueError):
        Settings(MAX_PROTOCOL_MINUTES=0)

    # Invalid steps range
    with pytest.raises(ValueError):
        Settings(MIN_PROTOCOL_STEPS=5, MAX_PROTOCOL_STEPS=3)

    # Invalid risk tier
    with pytest.raises(ValueError):
        Settings(MAX_ALLOWED_RISK_TIER=4)

    # Invalid report order
    with pytest.raises(ValueError):
        Settings(REPORT_ORDER="coherence")

def test_settings_redaction():
    s = Settings(
        OPENROUTER_API_KEY="secret_openrouter_key",
        QDRANT_API_KEY="secret_qdrant_key",
        DEEPSEEK_API_KEY="",
        REPORT_TITLE="Test Report"
    )
    summary = s.get_redacted_summary()
    assert summary["OPENROUTER_API_KEY"] == "***REDACTED***"
    assert summary["QDRANT_API_KEY"] == "***REDACTED***"
    assert summary["DEEPSEEK_API_KEY"] is None
    assert summary["REPORT_TITLE"] == "Test Report"
