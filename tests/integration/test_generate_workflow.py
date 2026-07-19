from unittest.mock import patch
from app.workflows.generate_protocols import GenerateProtocolsWorkflow
from app.models.enums import CriticVerdict, RiskTier
from app.models.actionability import ActionabilityAssessment
from app.models.protocol import ProtocolDraft
from app.services.critic import CriticResponse

def test_generate_protocols_workflow_success(qdrant_service, mock_embedding_service, mock_config):
    # Seed 1 keystone point in Qdrant
    keystone_payload = {
        "concept": "attention span",
        "statement": "Visual focus exercises stabilize attention duration.",
        "one_liner": "Visual focus improves attention.",
        "convergence": 0.85,
        "critic_verdict": "pass",
        "source_ids": ["src_1"],
        "created_at": "2026-07-19T10:00:00Z"
    }
    qdrant_service.upsert_point(
        collection_name=mock_config.keystones_collection,
        point_id="c16fd9d6-512b-586b-80a5-f852cc5967aa",
        payload=keystone_payload
    )

    # Instantiate mock LLM completions
    mock_assessment = ActionabilityAssessment(
        keystone_id="c16fd9d6-512b-586b-80a5-f852cc5967aa",
        status="eligible",
        practice_mode="observation",
        risk_tier=0,
        actionability_score=9.0,
        reversibility_score=8.5,
        observability_score=9.0,
        burden_score=8.5,
        rationale="Highly actionable",
        disallowed_reasons=[],
        open_questions=[],
        model="gpt-4",
        prompt_version="v1"
    )
    mock_draft = ProtocolDraft(
        title="Visual Focus Stabilization",
        working_hypothesis="Staring at a spot stabilizes attention.",
        purpose="Measure focus duration.",
        practice_mode="observation",
        risk_tier=0,
        duration_minutes=5,
        duration_days=3,
        frequency="daily",
        steps=["Sit in front of a dot.", "Stare for 5 minutes.", "Record focus breaks."],
        measurements=[],
        confounds_to_notice=[],
        stop_conditions=[],
        interpretation_limits=[]
    )
    mock_critic = CriticResponse(
        verdict=CriticVerdict.PASS,
        risk_tier=RiskTier.MINIMAL,
        problems=[],
        notes=["Looks safe and clean."],
        overreach_detected=False,
        self_sealing_logic_detected=False,
        provenance_problem_detected=False
    )

    # Patch LLM client generate_completions method to return these models sequentially
    with patch("app.services.llm_client.LLMClient.generate_completions") as mock_complete:
        mock_complete.side_effect = [mock_assessment, mock_draft, mock_critic]
        
        workflow = GenerateProtocolsWorkflow(mock_config)
        # Inject the mock embedding service
        workflow.protocol_writer.embeddings = mock_embedding_service
        
        # Run workflow
        workflow.run(limit=10)
        
        # Verify protocol was generated and stored in Qdrant
        protocols = qdrant_service.scroll_collection(mock_config.praxis_protocols_collection)
        assert len(protocols) == 1
        proto = protocols[0]
        assert proto["title"] == "Visual Focus Stabilization"
        assert proto["status"] == "approved"
        assert proto["keystone_concept"] == "attention span"
        assert proto["protocol_version"] == 1
