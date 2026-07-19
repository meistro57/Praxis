import pytest
from app.models.enums import PracticeMode, RiskTier
from app.models.protocol import ProtocolDraft
from app.services.safety import DeterministicSafetyGate

@pytest.fixture
def safety_gate(mock_config):
    return DeterministicSafetyGate(mock_config)

def create_draft(
    steps,
    title="Test Title",
    working_hypothesis="Test Hypothesis",
    purpose="Test Purpose",
    practice_mode=PracticeMode.OBSERVATION,
    risk_tier=RiskTier.MINIMAL,
    duration_minutes=5,
    duration_days=1,
    measurements=None,
    confounds_to_notice=None,
    stop_conditions=None,
    interpretation_limits=None
):
    padded_steps = list(steps)
    while len(padded_steps) < 3:
        padded_steps.append("Neutral placeholder step.")
        
    return ProtocolDraft(
        title=title,
        working_hypothesis=working_hypothesis,
        purpose=purpose,
        practice_mode=practice_mode,
        risk_tier=risk_tier,
        duration_minutes=duration_minutes,
        duration_days=duration_days,
        frequency="once",
        steps=padded_steps,
        measurements=measurements or [],
        confounds_to_notice=confounds_to_notice or ["fatigue"],
        stop_conditions=stop_conditions or ["The exercise notices distress."],
        interpretation_limits=interpretation_limits or ["This is anecdotal."]
    )

# --- REJECTION CASES ---

def test_safety_breath_holding_rejection(safety_gate):
    draft = create_draft(["Practice breath holding for three minutes."])
    res = safety_gate.validate_protocol(draft)
    assert not res.allowed
    assert "prohibited_content:physical:breath_manipulation" in res.flags

def test_safety_fasting_rejection(safety_gate):
    draft = create_draft(["Try fasting for a full day and note reactions."])
    res = safety_gate.validate_protocol(draft)
    assert not res.allowed
    assert "prohibited_content:physical:fasting_or_sleep" in res.flags

def test_safety_sleep_deprivation_rejection(safety_gate):
    draft = create_draft(["Sleep deprivation test: stay awake for 24 hours."])
    res = safety_gate.validate_protocol(draft)
    assert not res.allowed
    assert "prohibited_content:physical:fasting_or_sleep" in res.flags

def test_safety_medication_rejection(safety_gate):
    draft = create_draft(["Stop taking your prescribed medication for a week."])
    res = safety_gate.validate_protocol(draft)
    assert not res.allowed
    assert "prohibited_content:physical:substance_or_medication" in res.flags

def test_safety_driving_rejection(safety_gate):
    draft = create_draft(["Perform a driving experiment where you change lanes without looking."])
    res = safety_gate.validate_protocol(draft)
    assert not res.allowed
    assert "prohibited_content:physical:driving" in res.flags

def test_safety_fire_rejection(safety_gate):
    draft = create_draft(["Light a fire and observe your emotional state."])
    res = safety_gate.validate_protocol(draft)
    assert not res.allowed
    assert "prohibited_content:physical:extreme_environments" in res.flags

def test_safety_entity_rejection(safety_gate):
    draft = create_draft(["Try talking to unseen entities to verify their presence."])
    res = safety_gate.validate_protocol(draft)
    assert not res.allowed
    assert "prohibited_content:psychological:panic_or_trauma" in res.flags

def test_safety_paranoia_rejection(safety_gate):
    draft = create_draft(["Observe your neighbors to verify paranoid thoughts about them spying."])
    res = safety_gate.validate_protocol(draft)
    assert not res.allowed
    assert "prohibited_content:psychological:panic_or_trauma" in res.flags

def test_safety_self_sealing_rejection(safety_gate):
    draft = create_draft(["If you disagree with the output, it proves you are not ready."])
    res = safety_gate.validate_protocol(draft)
    assert not res.allowed
    assert "prohibited_content:epistemic:self_sealing" in res.flags

def test_safety_deception_rejection(safety_gate):
    draft = create_draft(["Tell a lie to your partner and measure their reaction."])
    res = safety_gate.validate_protocol(draft)
    assert not res.allowed
    assert "prohibited_content:social:deception_or_coercion" in res.flags

def test_safety_confrontation_rejection(safety_gate):
    draft = create_draft(["Confront your boss about a promotion during a meeting."])
    res = safety_gate.validate_protocol(draft)
    assert not res.allowed
    assert "prohibited_content:social:deception_or_coercion" in res.flags

def test_safety_spending_rejection(safety_gate):
    draft = create_draft(["Spend $100 on a lottery ticket to test your luck."])
    res = safety_gate.validate_protocol(draft)
    assert not res.allowed
    assert "prohibited_content:financial:spending_or_legal" in res.flags

def test_safety_legal_action_rejection(safety_gate):
    draft = create_draft(["File a lawsuit to observe legal system behavior."])
    res = safety_gate.validate_protocol(draft)
    assert not res.allowed
    assert "prohibited_content:financial:spending_or_legal" in res.flags

def test_safety_quitting_job_rejection(safety_gate):
    draft = create_draft(["Quitting your job will test your self-reliance."])
    res = safety_gate.validate_protocol(draft)
    assert not res.allowed
    assert "prohibited_content:financial:spending_or_legal" in res.flags

def test_safety_diagnosis_rejection(safety_gate):
    draft = create_draft(["Use these symptoms to diagnose yourself with clinical depression."])
    res = safety_gate.validate_protocol(draft)
    assert not res.allowed
    assert "prohibited_content:physical:substance_or_medication" in res.flags

def test_safety_metaphysical_rejection(safety_gate):
    draft = create_draft(["This practice provides universal proof of life after death."])
    res = safety_gate.validate_protocol(draft)
    assert not res.allowed
    assert "prohibited_content:epistemic:metaphysical_proof" in res.flags

def test_safety_symptom_origin_rejection(safety_gate):
    draft = create_draft(["Your headache is a symptom caused by unexpressed feeling."])
    res = safety_gate.validate_protocol(draft)
    assert not res.allowed
    assert "prohibited_content:epistemic:illness_mechanisms" in res.flags

def test_safety_hardship_origin_rejection(safety_gate):
    draft = create_draft(["Notice how hardship results from the participant's inner state."])
    res = safety_gate.validate_protocol(draft)
    assert not res.allowed
    assert "prohibited_content:epistemic:illness_mechanisms" in res.flags

def test_safety_longevity_earned_rejection(safety_gate):
    draft = create_draft(["Observe how health is earned through correct practice."])
    res = safety_gate.validate_protocol(draft)
    assert not res.allowed
    assert "prohibited_content:epistemic:health_earning" in res.flags


# --- ALLOWED CASES ---

def test_safety_journaling_allowed(safety_gate):
    draft = create_draft(
        steps=["Brief journaling: write down three thoughts.", "Rate current stress from 0 to 10.", "Close notebook."],
        title="Journaling Exercise"
    )
    res = safety_gate.validate_protocol(draft)
    assert res.allowed

def test_safety_state_rating_allowed(safety_gate):
    draft = create_draft(
        steps=["Sit in a chair.", "Rate your physical comfort.", "Adjust posture slightly and rate again."],
        title="State Rating"
    )
    res = safety_gate.validate_protocol(draft)
    assert res.allowed

def test_safety_neutral_observation_allowed(safety_gate):
    draft = create_draft(
        steps=["Look out the window for one minute.", "Note the color of the first three cars.", "Write them down."],
        title="Neutral Observation"
    )
    res = safety_gate.validate_protocol(draft)
    assert res.allowed

def test_safety_normal_breathing_allowed(safety_gate):
    draft = create_draft(
        steps=["Sit quietly.", "Breathe normally without manipulation for two minutes.", "Observe temperature of air."],
        title="Normal Breathing"
    )
    res = safety_gate.validate_protocol(draft)
    assert res.allowed

def test_safety_alternative_interpretations_allowed(safety_gate):
    draft = create_draft(
        steps=["Recall a mild disagreement.", "Write down two alternative interpretations.", "Note emotional response."],
        title="Reframing Exercise"
    )
    res = safety_gate.validate_protocol(draft)
    assert res.allowed

def test_safety_clarifying_question_allowed(safety_gate):
    draft = create_draft(
        steps=["Identify a minor detail.", "Ask one low-stakes clarifying question to a colleague.", "Note their reply."],
        title="Clarifying Inquiry"
    )
    res = safety_gate.validate_protocol(draft)
    assert res.allowed

def test_safety_contemplative_inquiry_allowed(safety_gate):
    # Relational/contemplative mode requires stop distress condition
    draft = create_draft(
        steps=["Sit silently.", "Reflect on a single word for five minutes.", "Resume regular activity."],
        practice_mode=PracticeMode.CONTEMPLATIVE,
        stop_conditions=["The exercise noticeably increases distress or emotional discomfort."]
    )
    res = safety_gate.validate_protocol(draft)
    assert res.allowed
