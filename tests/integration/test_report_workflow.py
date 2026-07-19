import pytest
import os
from app.workflows.build_report import BuildReportWorkflow
from app.models.enums import ProtocolStatus, ObservationOutcome, FeedbackRecommendation
from app.models.protocol import PraxisProtocol, ProtocolProvenance
from app.models.observation import ObservationRecord
from app.models.reflection import PraxisReflection

@pytest.fixture
def populated_db(qdrant_service, mock_config):
    # Seed protocol
    p = PraxisProtocol(
        protocol_id="c16fd9d6-512b-586b-80a5-f852cc5967bb",
        protocol_version=1,
        supersedes=None,
        status=ProtocolStatus.APPROVED,
        keystone_id="ks_1",
        keystone_concept="time perception",
        keystone_statement="Time passes differently when engaged.",
        keystone_convergence=0.8,
        title="Time perception exercise",
        working_hypothesis="Engagement slows down perception.",
        purpose="Neutral time study",
        practice_mode="observation",
        risk_tier=0,
        duration_minutes=5,
        duration_days=1,
        frequency="once",
        steps=["Step 1", "Step 2", "Step 3"],
        measurements=[],
        confounds_to_notice=[],
        stop_conditions=[],
        interpretation_limits=[],
        safety_flags=[],
        critic_verdict="pass",
        critic_notes=[],
        provenance=ProtocolProvenance(source_ids=[], reflection_ids=[]),
        created_at="2026-07-19T10:00:00Z",
        content_hash="hash"
    )
    qdrant_service.upsert_point(mock_config.praxis_protocols_collection, p.protocol_id, p.model_dump())

    # Seed observation
    o = ObservationRecord(
        observation_id="c16fd9d6-512b-586b-80a5-f852cc5967cc",
        protocol_id=p.protocol_id,
        protocol_version=1,
        keystone_id="ks_1",
        outcome=ObservationOutcome.SUPPORTED,
        completion_ratio=1.0,
        notes="Engaging activity felt shorter.",
        measurement_values={},
        confounds_observed=[],
        adverse_effects=[],
        completed_at="2026-07-19T10:00:00Z",
        created_at="2026-07-19T10:00:00Z",
        content_hash="hash_o"
    )
    qdrant_service.upsert_point(mock_config.praxis_observations_collection, o.observation_id, o.model_dump())

    # Seed reflection
    r = PraxisReflection(
        reflection_id="c16fd9d6-512b-586b-80a5-f852cc5967dd",
        observation_id=o.observation_id,
        protocol_id=p.protocol_id,
        keystone_id="ks_1",
        summary="Consistently observed engagement effects.",
        interpretation="Engaged time felt shorter.",
        feedback_recommendation=FeedbackRecommendation.REPEATED_PRACTICAL_SUPPORT,
        feedback_reason="No significant confounds.",
        human_review_required=False,
        model="gpt-4",
        prompt_version="v1",
        created_at="2026-07-19T10:00:00Z",
        content_hash="hash_r"
    )
    qdrant_service.upsert_point(mock_config.praxis_reflections_collection, r.reflection_id, r.model_dump())
    
    return p, o, r

def test_build_report_workflow_success(populated_db, mock_config, tmp_path):
    report_file = tmp_path / "report.md"
    pdf_file = tmp_path / "report.pdf"
    html_file = tmp_path / "report.html"
    
    workflow = BuildReportWorkflow(mock_config)
    try:
        workflow.run(
            output_path=str(report_file),
            enable_pdf=True,
            enable_html=True
        )
    except ImportError:
        # Retry without PDF if ReportLab is missing
        workflow.run(
            output_path=str(report_file),
            enable_pdf=False,
            enable_html=True
        )
    
    # Verify report markdown file exists and contains sections
    assert os.path.exists(report_file)
    with open(report_file, "r") as f:
        content = f.read()
        assert "# Epistemic Notice" in content
        assert "Time perception exercise" in content
        
    # Verify report HTML file exists
    assert os.path.exists(html_file)
    with open(html_file, "r") as f:
        html_content = f.read()
        assert "<html" in html_content
        assert "Time perception exercise" in html_content

    # If ReportLab is installed, PDF should be generated successfully.
    # Otherwise, it logs a warning but workflow does not crash.
    try:
        import reportlab  # noqa: F401
        assert os.path.exists(pdf_file)
    except ImportError:
        pass
