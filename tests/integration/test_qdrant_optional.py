import os
import json
from unittest.mock import patch
from app.workflows.build_report import BuildReportWorkflow
from app.models.enums import ProtocolStatus, ObservationOutcome
from app.models.protocol import PraxisProtocol, ProtocolProvenance
from app.models.observation import ObservationRecord

def test_report_from_exports(mock_config, tmp_path):
    # Setup exports directory structure
    exports_dir = tmp_path / "exports"
    exports_dir.mkdir()
    
    # 1. Create protocols export
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
    with open(exports_dir / "protocols.json", "w") as f:
        json.dump([p.model_dump()], f)
        
    # 2. Create observations export
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
    with open(exports_dir / "observations.json", "w") as f:
        json.dump([o.model_dump()], f)
        
    # 3. Create empty reflections & failures exports
    with open(exports_dir / "reflections.json", "w") as f:
        json.dump([], f)
    with open(exports_dir / "failures.json", "w") as f:
        json.dump([], f)
        
    # Run build report using the exports directory instead of Qdrant
    report_file = tmp_path / "offline_report.md"
    
    # We patch QdrantService to ensure it's not even instantiated/called
    with patch("app.services.qdrant.QdrantService") as mock_qdrant_cls:
        workflow = BuildReportWorkflow(mock_config)
        workflow.run(
            output_path=str(report_file),
            from_exports_dir=str(exports_dir)
        )
        
        # Qdrant client should not be initialized
        mock_qdrant_cls.assert_not_called()
        
    # Verify the report was built successfully
    assert os.path.exists(report_file)
    with open(report_file, "r") as f:
        content = f.read()
        assert "# Epistemic Notice" in content
        assert "Time perception exercise" in content
