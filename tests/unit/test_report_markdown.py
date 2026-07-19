import pytest
import os
from app.models.enums import PracticeMode, RiskTier, ObservationOutcome, ProtocolStatus, CriticVerdict
from app.models.protocol import PraxisProtocol, ProtocolProvenance
from app.models.observation import ObservationRecord
from app.models.failure import RegisterEntry
from app.services.report_model import ReportData, DistributionSummary
from app.services.report_markdown import MarkdownReportBuilder

@pytest.fixture
def sample_report_data(mock_config):
    p = PraxisProtocol(
        protocol_id="proto_1",
        protocol_version=1,
        supersedes=None,
        status=ProtocolStatus.APPROVED,
        keystone_id="ks_1",
        keystone_concept="observer state",
        keystone_statement="Interpretation is partly constrained by the observer's physiological state.",
        keystone_convergence=0.78,
        title="Two-State Interpretation",
        working_hypothesis="Changing physiological state may alter interpretation.",
        purpose="Compare interpretations before and after a brief settling period.",
        practice_mode=PracticeMode.OBSERVATION,
        risk_tier=RiskTier.MINIMAL,
        duration_minutes=8,
        duration_days=1,
        frequency="once",
        steps=[
            "Record the first interpretation.",
            "Breathe normally for three minutes.",
            "Record a second interpretation."
        ],
        measurements=[],
        confounds_to_notice=["fatigue"],
        stop_conditions=["The exercise noticeably increases distress."],
        interpretation_limits=["One observation cannot establish a general rule."],
        safety_flags=[],
        critic_verdict=CriticVerdict.PASS,
        critic_notes=[],
        provenance=ProtocolProvenance(source_ids=[], reflection_ids=[]),
        created_at="2026-07-19T10:00:00Z",
        content_hash="hash_p1"
    )

    o = ObservationRecord(
        observation_id="obs_1",
        protocol_id="proto_1",
        protocol_version=1,
        keystone_id="ks_1",
        outcome=ObservationOutcome.SUPPORTED,
        completion_ratio=1.0,
        notes="Notes",
        confounds_observed=["fatigue"],
        completed_at="2026-07-19T10:00:00Z",
        created_at="2026-07-19T10:00:00Z",
        content_hash="hash_o1"
    )

    reg = RegisterEntry(
        keystone_id="ks_cancer",
        keystone_concept="cancer cure",
        keystone_statement="Positive thinking cures cancer.",
        stage="domain_filter",
        reason="Statement implicates a prohibited domain: disease causation.",
        matched_rules=["domain:disease", "domain:cure"],
        risk_tier=RiskTier.PROHIBITED.value,
        created_at="2026-07-19T10:00:00Z"
    )

    counts = {
        "scanned": 2,
        "adapted": 1,
        "domain_rejected": 1,
        "pre_filter_rejected": 0,
        "classified": 1,
        "non_actionable": 0,
        "prohibited": 0,
        "below_suitability": 0,
        "drafted": 1,
        "safety_rejected": 0,
        "critic_revised": 0,
        "critic_rejected": 0,
        "held": 0,
        "approved": 1,
        "written": 1,
        "failed": 0
    }

    dist = DistributionSummary(
        modes={"observation": 1},
        risk_tiers={"0": 1},
        concepts={"observer state": 1}
    )

    return ReportData(
        title="Praxis Report Book",
        generated_at="2026-07-19T10:00:00Z",
        keystone_collection="keystones",
        scope="all",
        funnel_counts=counts,
        distributions=dist,
        protocols=[p],
        observations=[o],
        reflections=[],
        register_entries=[reg],
        failures=[],
        config_snapshot=mock_config.get_redacted_summary()
    )

def test_markdown_report_safeguards(sample_report_data, mock_config):
    builder = MarkdownReportBuilder(sample_report_data, mock_config)
    md = builder.build_markdown()

    # Requirement 1: Epistemic Notice must be present
    assert "# Epistemic Notice" in md
    assert "**About this book.**" in md

    # Requirement 3: Stop conditions repeated in protocol chapter
    assert "Stop Conditions" in md
    assert "The exercise noticeably increases distress." in md

    # Requirement 2: Interpretation limits repeated in protocol chapter
    assert "Interpretation Limits" in md
    assert "One observation cannot establish a general rule." in md

    # Requirement 4: Appendix A is mandatory and present
    assert "# Appendix A — Non-Actionable Register" in md
    assert "Positive thinking cures cancer." in md

    # Requirement 8: Aggregate figures must state denominator
    # E.g. "supported: 1 of 1"
    assert "supported: 1 of 1" in md

    # Check that it doesn't contain banned validation words in aggregate findings
    # (e.g. "validated", "proven", "confirmed", "works", "effective")
    from app.services.feedback import BANNED_WORDS
    for word in BANNED_WORDS:
        # Avoid checking inside standard templates or code snippets if any
        # But verify aggregate sections specifically
        assert f"aggregate finding: {word}" not in md.lower()

def test_markdown_report_determinism(sample_report_data, mock_config):
    builder1 = MarkdownReportBuilder(sample_report_data, mock_config)
    md1 = builder1.build_markdown()

    builder2 = MarkdownReportBuilder(sample_report_data, mock_config)
    md2 = builder2.build_markdown()

    # Must be byte-identical
    assert md1 == md2

def test_golden_file_markdown(sample_report_data, mock_config):
    builder = MarkdownReportBuilder(sample_report_data, mock_config)
    md = builder.build_markdown()
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    golden_path = os.path.join(project_root, "tests", "fixtures", "expected_book.md")
    
    # If the golden file doesn't exist, create it once (bootstrap)
    if not os.path.exists(golden_path):
        os.makedirs(os.path.dirname(golden_path), exist_ok=True)
        with open(golden_path, "w", encoding="utf-8") as f:
            f.write(md)
            
    with open(golden_path, "r", encoding="utf-8") as f:
        expected = f.read()
        
    assert md == expected
