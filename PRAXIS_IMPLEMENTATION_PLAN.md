# PRAXIS
## Agent Coder Implementation Plan
**Subtitle:** Embodied Experiment Layer
**Tagline:** *The layer that asks what an idea does when lived.*

---

# 0. Agent Mission

Build a complete, tested, CLI-first Python repository named **Praxis**.

Praxis reads accepted propositions from the existing Keystone Qdrant collection,
determines whether a proposition can responsibly become a small lived experiment,
generates a bounded and observable protocol, passes it through deterministic
safety checks and an independent critic gate, stores approved protocols with full
provenance, accepts structured observation logs, produces feedback records for
later human review, and can emit a complete report book of the entire program.

Praxis is not a belief engine, treatment system, spiritual authority, coaching
bot, or autonomous behaviour manager.

Its job is:

> Translate selected Keystone propositions into minimal, reversible, low-risk,
> observable experiments, then preserve what happened without overstating what
> the result means.

The required end-to-end loop is:

```text
Keystone proposition
        ↓
Actionability classification
        ↓
Practice condensation
        ↓
Deterministic safety gate
        ↓
Independent critic gate
        ↓
Approved Praxis protocol
        ↓
Structured observation
        ↓
Outcome reflection
        ↓
Feedback candidate for human review
        ↓
Report book
```

Do not leave TODO stubs, fake implementations, placeholder methods, or untested
happy-path-only code. The repository must run from a clean clone after
environment setup.

---

# 1. Core Design Principles

## 1.1 Working hypotheses, not instructions

Praxis must never say:

> This proposition is true, so do this.

It must frame every eligible proposition as:

> This proposition appears significant in the source pipeline. Here is a safe way
> to examine what changes when it is treated as a working hypothesis.

## 1.2 Minimum intervention, maximum observability

Every generated protocol must use the least invasive action capable of examining
the proposition. Prefer, in order:

1. observation
2. brief reflection
3. small reversible behaviour
4. low-stakes relational clarification

Do not escalate merely to make a protocol feel profound.

## 1.3 Convergence is evidence, not proof

Keystone convergence scores indicate cross-lens analytical support. They do not
establish objective truth. Praxis must preserve this distinction in prompts,
protocol wording, schemas, documentation, critic rules, summaries, and the
report book.

## 1.4 Full provenance

Every protocol must link to:

- Keystone point ID
- Keystone statement
- Keystone score fields when available
- supporting source IDs when available
- model and prompt versions
- safety and critic decisions
- protocol version
- observation IDs
- reflection IDs

Nothing should become detached from the claim that produced it.

## 1.5 Human review before canon feedback

Praxis may create a feedback candidate such as:

- no canon implication
- generate a new question
- review this Keystone
- review this protocol
- possible contradiction
- repeated practical support

Praxis must **never automatically modify, delete, promote, demote, or rewrite a
Keystone record**.

## 1.6 Safe failure

If the system is uncertain, malformed, missing provenance, or unable to classify
risk, it must reject or hold the candidate. The default failure mode is:

```text
DO NOT GENERATE A PRACTICE
```

Not:

```text
MAKE SOMETHING UP THAT SOUNDS GENTLE
```

## 1.7 Refusal is a first-class output

A proposition that cannot responsibly become an experiment is not a failure of
the system. The register of refusals is part of the product, is preserved with
reasons, and appears in the report book. Praxis is expected to say no far more
often than yes.

---

# 2. V1 Scope

V1 must provide a complete CLI workflow for:

1. probing the Keystone collection and mapping fields
2. selecting Keystone candidates
3. deterministic pre-filtering, including prohibited-domain exclusion
4. LLM actionability classification
5. LLM protocol generation
6. deterministic safety validation
7. independent LLM critic review
8. stable-ID Qdrant upsert
9. protocol listing and inspection
10. structured observation logging
11. observation reflection
12. feedback candidate creation
13. JSON export
14. report book generation
15. dry-run operation
16. unit and integration tests
17. documentation and example fixtures

V1 is CLI-first and headless.

Do not build:

- a web frontend
- a mobile app
- authentication
- autonomous reminders
- push notifications
- social features
- automatic Keystone mutation
- automatic medical or mental-health interpretation
- an agent swarm
- a recommendation feed
- gamification
- wearable integration

---

# 3. Technology Stack

Use:

- Python 3.11+
- `qdrant-client`
- `pydantic` v2
- `python-dotenv`
- `httpx`
- standard `argparse`
- standard `logging`
- `pytest`
- `pytest-cov`
- `ruff`
- `tenacity` for bounded retries
- OpenAI-compatible chat-completions clients through `httpx`

**Optional extra**, isolated in `requirements-report.txt` and never imported at
module load:

- `reportlab` — PDF rendering for the report book only

Do not add LangChain, AutoGen, CrewAI, Celery, Redis, FastAPI, Jinja2, Pandoc,
WeasyPrint, or a frontend in V1. Keep dependencies small and explicit.

---

# 4. Repository Structure

```text
praxis/
├── AGENTS.md
├── README.md
├── CHANGELOG.md
├── LICENSE
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── requirements-report.txt
├── pyproject.toml
├── setup.sh
├── run.py
├── config.py
│
├── app/
│   ├── __init__.py
│   ├── cli.py
│   ├── logging_setup.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── enums.py
│   │   ├── keystone.py
│   │   ├── actionability.py
│   │   ├── protocol.py
│   │   ├── observation.py
│   │   ├── reflection.py
│   │   ├── failure.py
│   │   └── book.py
│   │
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   └── versions.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── qdrant.py
│   │   ├── keystone_reader.py
│   │   ├── candidate_selector.py
│   │   ├── domain_filter.py
│   │   ├── actionability.py
│   │   ├── condenser.py
│   │   ├── safety.py
│   │   ├── critic.py
│   │   ├── protocol_writer.py
│   │   ├── observation_logger.py
│   │   ├── reflector.py
│   │   ├── feedback.py
│   │   ├── embeddings.py
│   │   ├── llm_client.py
│   │   ├── stable_ids.py
│   │   ├── validation.py
│   │   ├── export.py
│   │   ├── report_model.py
│   │   ├── report_markdown.py
│   │   ├── report_html.py
│   │   ├── report_pdf.py
│   │   └── indexes.py
│   │
│   └── workflows/
│       ├── __init__.py
│       ├── generate_protocols.py
│       ├── log_observation.py
│       ├── reflect_observation.py
│       └── build_report.py
│
├── prompts/
│   ├── actionability_v1.md
│   ├── condenser_v1.md
│   ├── critic_v1.md
│   └── reflection_v1.md
│
├── report_templates/
│   ├── epistemic_notice.md
│   └── how_to_read.md
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATA_MODEL.md
│   ├── SAFETY_MODEL.md
│   ├── PROMPT_CONTRACTS.md
│   ├── QDRANT_COLLECTIONS.md
│   ├── FEEDBACK_LOOP.md
│   └── REPORT_BOOK.md
│
├── examples/
│   ├── keystone_example.json
│   ├── protocol_example.json
│   ├── observation_example.json
│   └── reflection_example.json
│
├── data/
│   └── .gitkeep
│
├── logs/
│   └── .gitkeep
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── fixtures/
│   │   ├── keystones.json
│   │   ├── llm_actionability.json
│   │   ├── llm_protocol.json
│   │   ├── llm_critic.json
│   │   ├── llm_reflection.json
│   │   └── expected_book.md
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_models.py
│   │   ├── test_stable_ids.py
│   │   ├── test_candidate_selector.py
│   │   ├── test_domain_filter.py
│   │   ├── test_actionability.py
│   │   ├── test_safety.py
│   │   ├── test_validation.py
│   │   ├── test_protocol_writer.py
│   │   ├── test_observation_logger.py
│   │   ├── test_feedback.py
│   │   ├── test_report_model.py
│   │   ├── test_indexes.py
│   │   └── test_report_markdown.py
│   └── integration/
│       ├── test_generate_workflow.py
│       ├── test_observation_workflow.py
│       ├── test_report_workflow.py
│       └── test_qdrant_optional.py
│
└── .github/
    └── workflows/
        └── test.yml
```

---

# 5. Configuration

Load `.env` in `config.py`. All settings must be environment variables with
sensible defaults.

Required `.env.example`:

```dotenv
# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
KEYSTONES_COLLECTION=keystones
PRAXIS_PROTOCOLS_COLLECTION=praxis_protocols
PRAXIS_OBSERVATIONS_COLLECTION=praxis_observations
PRAXIS_REFLECTIONS_COLLECTION=praxis_reflections
PRAXIS_FAILURES_COLLECTION=praxis_failures

# Keystone field mapping
K_ID_FIELD=
K_CONCEPT_FIELD=concept
K_STATEMENT_FIELD=statement
K_ONE_LINER_FIELD=one_liner
K_CONVERGENCE_FIELD=convergence
K_CENTRALITY_FIELD=centrality
K_COHERENCE_FIELD=coherence
K_SURVIVAL_FIELD=survival
K_SOURCE_IDS_FIELD=source_ids
K_REFLECTION_IDS_FIELD=member_reflection_ids
K_CRITIC_VERDICT_FIELD=critic_verdict
K_MODEL_FIELD=model

# Candidate rules
MIN_KEYSTONE_CONVERGENCE=0.75
REQUIRE_KEYSTONE_CRITIC_PASS=true
MAX_CANDIDATES=0

# Prohibited keystone domains (deterministic, pre-LLM — see §8.1)
ENFORCE_DOMAIN_PREFILTER=true
PROHIBITED_KEYSTONE_DOMAINS=disease,illness,sickness,healing,cure,remedy,longevity,lifespan,aging,medication,medicine,diagnosis,treatment,therapy,psychosomatic,pathology,symptom

# Praxis limits
MAX_PROTOCOL_MINUTES=15
MAX_PROTOCOL_DAYS=7
MAX_PROTOCOL_STEPS=7
MIN_PROTOCOL_STEPS=3
MAX_MEASUREMENTS=5
ALLOW_RELATIONAL_PROTOCOLS=true
ALLOW_CONTEMPLATIVE_PROTOCOLS=true
MAX_ALLOWED_RISK_TIER=1
MIN_PRAXIS_SUITABILITY=0.70

# LLM routing
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
ACTIONABILITY_MODEL=deepseek/deepseek-r1
CONDENSER_MODEL=deepseek/deepseek-r1
CRITIC_MODEL=google/gemma-3-27b-it
REFLECTION_MODEL=deepseek/deepseek-r1
LLM_TIMEOUT=180
LLM_MAX_RETRIES=3

# Optional direct DeepSeek routing
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_REASONER_MODEL=deepseek-reasoner

# Embeddings
EMBED_BASE_URL=https://openrouter.ai/api/v1
EMBED_API_KEY=
EMBED_MODEL=google/gemini-embedding-001
EMBED_DIM=3072

# Report book
REPORT_TITLE=Praxis Report Book
REPORT_ORDER=concept

# Runtime
PRAXIS_WORKERS=4
LOG_LEVEL=INFO
LOG_JSON=false
LOG_RAW_LLM=false
DRY_RUN=false
```

Configuration requirements:

- validate all numeric ranges at import
- `REPORT_ORDER` accepts only `concept` or `keystone_id`; reject any score-based
  ordering value at import
- fail clearly for missing API keys only when an operation requires them
- allow probe, list, show, validate, export, and report commands without LLM
  credentials
- never log API keys
- provide a redacted config summary at startup
- support `--dry-run` overriding `.env`

---

# 6. Input Contract: Keystone Adapter

Do not couple Praxis directly to one exact Keystone payload. Implement
`KeystoneRecord.from_qdrant(point)` as an adapter with configurable field mapping.

The current expected shape resembles:

```json
{
  "concept": "observer state",
  "statement": "Interpretation is partly constrained by the observer's physiological state.",
  "one_liner": "State influences interpretation.",
  "convergence": 0.78,
  "centrality": 0.84,
  "coherence": 0.79,
  "survival": 0.73,
  "n_sources": 18,
  "member_reflection_ids": ["..."],
  "source_ids": ["..."],
  "critic_verdict": "pass",
  "model": "..."
}
```

Required adapter behaviour:

- preserve original Qdrant point ID
- preserve raw payload
- map configurable field names
- tolerate absent optional fields
- reject records missing statement or point ID
- parse numeric strings safely
- normalise critic verdicts
- report schema problems into `praxis_failures`
- include `schema_warnings` rather than silently discarding unknown fields

---

# 7. Data Models

Use strict Pydantic models. Set `extra="forbid"` for all LLM response models.
Use enums instead of free-form status strings.

## 7.1 Enums

```python
class ActionabilityStatus(str, Enum):
    ELIGIBLE = "eligible"
    NON_ACTIONABLE = "non_actionable"
    PROHIBITED = "prohibited"
    NEEDS_HUMAN_REVIEW = "needs_human_review"

class PracticeMode(str, Enum):
    OBSERVATION = "observation"
    CONTEMPLATIVE = "contemplative"
    BEHAVIORAL = "behavioral"
    RELATIONAL = "relational"
    NONE = "none"

class RiskTier(int, Enum):
    MINIMAL = 0
    LOW = 1
    ELEVATED = 2
    PROHIBITED = 3

class CriticVerdict(str, Enum):
    PASS = "pass"
    REVISE = "revise"
    REJECT = "reject"
    HOLD = "hold"

class ProtocolStatus(str, Enum):
    CANDIDATE = "candidate"
    SAFETY_REJECTED = "safety_rejected"
    CRITIC_REJECTED = "critic_rejected"
    APPROVED = "approved"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"

class ObservationOutcome(str, Enum):
    SUPPORTED = "supported"
    NOT_OBSERVED = "not_observed"
    CONTRADICTED = "contradicted"
    INCONCLUSIVE = "inconclusive"
    NOT_COMPLETED = "not_completed"
    ADVERSE = "adverse"

class FeedbackRecommendation(str, Enum):
    NONE = "none"
    NEW_QUESTION = "new_question"
    REVIEW_PROTOCOL = "review_protocol"
    REVIEW_KEYSTONE = "review_keystone"
    POSSIBLE_CONTRADICTION = "possible_contradiction"
    REPEATED_PRACTICAL_SUPPORT = "repeated_practical_support"

class RejectionStage(str, Enum):
    PRE_FILTER = "pre_filter"
    DOMAIN_FILTER = "domain_filter"
    ACTIONABILITY = "actionability"
    SUITABILITY = "suitability"
    SAFETY = "safety"
    CRITIC = "critic"
    FAILURE = "failure"
```

## 7.2 ActionabilityAssessment

```json
{
  "keystone_id": "string",
  "status": "eligible",
  "practice_mode": "observation",
  "risk_tier": 0,
  "actionability_score": 0.88,
  "reversibility_score": 1.0,
  "observability_score": 0.84,
  "burden_score": 0.95,
  "rationale": "string",
  "disallowed_reasons": [],
  "open_questions": [],
  "model": "string",
  "prompt_version": "actionability_v1"
}
```

Scores are workflow triage values, not scientific measurements.

## 7.3 PraxisProtocol

```json
{
  "protocol_id": "stable UUID string",
  "protocol_version": 1,
  "supersedes": null,
  "status": "approved",
  "keystone_id": "source point ID",
  "keystone_concept": "observer state",
  "keystone_statement": "Interpretation is partly constrained...",
  "keystone_convergence": 0.78,
  "working_hypothesis": "Changing physiological state may alter interpretation.",
  "title": "Two-State Interpretation",
  "practice_mode": "observation",
  "risk_tier": 0,
  "purpose": "Compare interpretations before and after a brief settling period.",
  "duration_minutes": 8,
  "duration_days": 1,
  "frequency": "once after a mildly frustrating interaction",
  "steps": [
    "Record the first interpretation in one or two sentences.",
    "Rate emotional intensity from 0 to 10.",
    "Sit quietly and breathe normally for three minutes.",
    "Record a second interpretation.",
    "Compare certainty, emotional tone, and alternative explanations."
  ],
  "measurements": [
    {
      "name": "emotional_intensity",
      "type": "integer",
      "scale": "0-10",
      "when": ["before", "after"]
    }
  ],
  "confounds_to_notice": ["fatigue", "time pressure"],
  "stop_conditions": [
    "The exercise noticeably increases distress.",
    "The situation involves immediate safety concerns."
  ],
  "interpretation_limits": [
    "One observation cannot establish a general rule.",
    "A changed interpretation does not prove which interpretation is correct."
  ],
  "safety_flags": [],
  "critic_verdict": "pass",
  "critic_notes": [],
  "provenance": {
    "source_ids": [],
    "reflection_ids": [],
    "keystone_model": "string",
    "actionability_model": "string",
    "condenser_model": "string",
    "critic_model": "string",
    "prompt_versions": {}
  },
  "created_at": "ISO-8601 UTC",
  "content_hash": "sha256"
}
```

## 7.4 ObservationRecord

```json
{
  "observation_id": "stable UUID string",
  "protocol_id": "string",
  "protocol_version": 1,
  "keystone_id": "string",
  "started_at": "ISO-8601 UTC or null",
  "completed_at": "ISO-8601 UTC",
  "outcome": "inconclusive",
  "completion_ratio": 1.0,
  "measurement_values": {},
  "notes": "string",
  "confounds_observed": [],
  "adverse_effects": [],
  "deviations_from_protocol": [],
  "observer_context": {
    "self_reported_state": "optional string",
    "setting": "optional string"
  },
  "created_at": "ISO-8601 UTC",
  "content_hash": "sha256"
}
```

Do not require real name, diagnosis, demographic data, precise location, or other
sensitive identity information.

## 7.5 PraxisReflection

```json
{
  "reflection_id": "stable UUID string",
  "observation_id": "string",
  "protocol_id": "string",
  "keystone_id": "string",
  "summary": "string",
  "what_changed": ["string"],
  "what_did_not_change": ["string"],
  "confounds": ["string"],
  "interpretation": "string",
  "epistemic_limits": ["string"],
  "feedback_recommendation": "none",
  "feedback_reason": "string",
  "human_review_required": false,
  "model": "string",
  "prompt_version": "reflection_v1",
  "created_at": "ISO-8601 UTC",
  "content_hash": "sha256"
}
```

## 7.6 RegisterEntry

Every keystone considered but not turned into an approved protocol produces one
of these. Register entries are persisted and appear in the report book.

```json
{
  "keystone_id": "string",
  "keystone_concept": "string",
  "keystone_statement": "string",
  "stage": "domain_filter",
  "reason": "Statement implicates a prohibited domain: disease causation.",
  "matched_rules": ["domain:disease", "domain:healing"],
  "risk_tier": 3,
  "created_at": "ISO-8601 UTC"
}
```

## 7.7 BookManifest

```python
class BookManifest(BaseModel):
    book_id: str            # stable ID from content hash of included record IDs
    generated_at: str       # ISO-8601 UTC
    scope: str              # "all" | "run" | "since"
    run_ids: list[str]
    keystone_collection: str
    protocol_ids: list[str]
    observation_ids: list[str]
    reflection_ids: list[str]
    register_entry_count: int
    counts: dict[str, int]  # the §18 funnel
    config_snapshot: dict   # redacted
    content_hash: str
```

---

# 8. Actionability Gate

Implement three layers: a deterministic domain filter, a deterministic
pre-filter, and an LLM classifier. The deterministic layers run first and can
reject without any LLM call.

## 8.1 Deterministic pre-filter

### 8.1.1 Prohibited keystone domains

**This check runs before every other check and before any LLM call.**

A protocol's wording can be entirely innocuous while the hypothesis it examines
is not. A protocol reading *"note a physical sensation, rate emotional intensity,
journal for three minutes"* passes every content rule in §10.1 — but if its
source proposition asserts that illness is caused by emotional state, the
experiment quietly encourages a participant to attribute a physical symptom to
psychological cause. The hazard lives in the hypothesis, not the steps, so it
must be caught at the source record.

Reject any Keystone whose `statement` or `concept` implicates:

- disease causation or the origin of illness
- healing, cure, remedy, or recovery
- longevity, lifespan, or aging
- medication, medical treatment, therapy, or diagnosis
- psychosomatic or mind-body disease mechanisms

Implementation:

- match against `PROHIBITED_KEYSTONE_DOMAINS` using word-boundary matching on a
  normalised, lowercased statement and concept
- supplement with a configurable regex list for phrases the token list misses
- produce `ActionabilityStatus.PROHIBITED`, `RiskTier.PROHIBITED`, a
  `RegisterEntry` with `stage="domain_filter"`, and the matched rules
- controlled by `ENFORCE_DOMAIN_PREFILTER`; when disabled, log a prominent
  warning at startup and record the setting in the run provenance and the report
  book's configuration appendix

This filter is deliberately over-inclusive. A false positive costs one unbuilt
protocol. A false negative costs someone's medical decision.

### 8.1.2 Standard pre-filter

Reject before LLM calls when the Keystone:

- has no statement
- is below `MIN_KEYSTONE_CONVERGENCE`
- lacks required critic pass when configured
- is explicitly marked rejected
- contains only bibliographic, licensing, or boilerplate material
- is a purely historical fact with no meaningful experiential translation
- contains an obviously prohibited domain

The pre-filter must produce a structured reason and a `RegisterEntry`.

## 8.2 LLM classifier

The classifier decides:

- whether the proposition can become a responsible experiment
- the lowest-risk suitable practice mode
- initial risk tier
- reversibility
- observability
- burden
- why the claim may be non-actionable

It must return JSON matching `ActionabilityAssessment`.

The prompt must explicitly instruct:

- do not manufacture actionability
- do not convert metaphysical assertions into factual instructions
- prefer `non_actionable` over a contrived exercise
- never recommend high-risk, diagnostic, therapeutic, illegal, deceptive, or
  irreversible actions
- classify uncertainty as `needs_human_review`
- select the least invasive practice mode
- classify as `non_actionable` any proposition whose examination would require
  the participant to attribute personal misfortune, illness, hardship, or
  suffering to their own inner state

---

# 9. Practice Condenser

The condenser receives only eligible candidates.

Its mission:

> Produce the smallest, safest, most observable protocol that tests the working
> hypothesis without assuming the hypothesis is true.

Protocol rules:

- 3 to 7 steps
- 15 minutes maximum per session
- 7 days maximum total in V1
- plain language
- no mystical authority language
- no promises
- no diagnosis
- no persuasion to believe
- no required third-party participation unless relational mode is explicitly allowed
- no deception
- no irreversible action
- no purchase requirement
- no special equipment
- no sleep, food, medication, substance, or breathing manipulation
- **no framing that attributes the participant's illness, misfortune, poverty,
  hardship, or suffering to their own beliefs, thoughts, emotional state, or
  spiritual condition**
- include measurements
- include confounds
- include stop conditions
- include interpretation limits
- preserve Keystone provenance

Every protocol whose practice mode is contemplative or behavioural must include
at least one stop condition covering worsening mood or increased distress.

The condenser response must validate directly into a strict Pydantic model. Do
not parse prose wrapped around JSON.

---

# 10. Deterministic Safety Gate

The safety gate must be code-first, not LLM-only.

```python
SafetyResult(
    allowed: bool,
    risk_tier: RiskTier,
    flags: list[str],
    reasons: list[str],
    matched_rules: list[str],
)
```

## 10.1 Prohibited protocol content

Reject any protocol involving or encouraging:

### Physical risk

- self-harm
- pain induction
- injury
- weapons
- fire
- electricity
- dangerous tools or machinery
- driving experiments
- climbing or hazardous environments
- breath retention
- hyperventilation
- extreme cold or heat
- fasting
- sleep deprivation
- substance use
- medication changes
- unapproved medical procedures

### Psychological risk

- deliberate panic induction
- trauma exposure
- prolonged sensory deprivation
- attempts to induce dissociation
- attempts to induce hallucinations
- acting on paranoia
- testing whether unseen entities are communicating
- treating dreams, coincidences, voices, or impressions as commands
- escalating obsessive checking
- isolation from ordinary support

### Social and relational risk

- deception
- coercion
- manipulation
- secret tests of another person
- confrontation
- major relationship decisions
- public disclosure of private information
- encouraging dependency on Praxis or an AI

### Financial, legal, and occupational risk

- spending commitments
- investment or gambling
- contracts
- legal decisions
- quitting a job
- workplace safety violations
- violating policy
- illegal activity

### Epistemic overreach

- claiming the practice proves a metaphysical proposition
- treating one result as universal
- presenting correlation as causation
- framing non-completion as resistance or failure
- making the protocol self-sealing
- telling the user that disagreement confirms the claim
- **framing the participant's illness, misfortune, hardship, or suffering as
  caused by their inner state, beliefs, or spiritual condition**
- **implying that a physical symptom has a psychological or spiritual origin**
- **implying that health, recovery, or longevity is earned, deserved, or a
  consequence of correct practice**

## 10.2 Required safety properties

Every approved protocol must be:

- voluntary
- stoppable immediately
- reversible
- low burden
- observable
- time bounded
- non-diagnostic
- non-coercive
- honest about interpretation limits

## 10.3 Implementation method

Use:

1. exact prohibited phrase patterns
2. configurable regex patterns
3. semantic category checks from structured fields
4. numeric limit checks
5. required-field validation
6. risk-tier escalation
7. a final critic model

Do not rely on a single keyword blacklist. Store all safety decisions and matched
rules.

---

# 11. Critic Gate

Use a model independent from the condenser when configured.

```json
{
  "verdict": "pass",
  "risk_tier": 0,
  "revised_protocol": null,
  "problems": [],
  "notes": ["The protocol remains observational and reversible."],
  "overreach_detected": false,
  "self_sealing_logic_detected": false,
  "provenance_problem_detected": false
}
```

Allowed verdicts: `pass`, `revise`, `reject`, `hold`.

Rules:

- `revise` must return a complete replacement protocol draft
- revised drafts must re-enter deterministic safety validation
- maximum two critic revision loops
- `hold` requires human review and must not be written as approved
- malformed critic output is a failure, not a pass
- critic must inspect epistemic wording as well as physical safety
- the critic cannot overturn a deterministic safety rejection

---

# 12. Praxis Suitability

Calculate a triage score only after actionability assessment:

```text
praxis_suitability =
actionability_score
× reversibility_score
× observability_score
× burden_score
× safety_multiplier
```

Where:

```text
risk tier 0 → safety multiplier 1.00
risk tier 1 → safety multiplier 0.85
risk tier 2 → safety multiplier 0.00
risk tier 3 → safety multiplier 0.00
```

This score is not evidence that the Keystone is true. It means only:

> This proposition appears suitable for a bounded lived experiment.

Store every component. Do not allow the score to override a safety rejection. Do
not use the score to order output in any report or listing.

---

# 13. Stable IDs and Versioning

Use UUIDv5 or a UUID derived from SHA-256.

**Protocol ID seed:**

```text
keystone_id + prompt_version + normalised working_hypothesis
+ normalised steps + protocol_version
```

**Observation ID seed:**

```text
protocol_id + completed_at + content_hash
```

**Reflection ID seed:**

```text
observation_id + prompt_version + content_hash
```

**Book ID seed:**

```text
sorted protocol_ids + sorted observation_ids + sorted reflection_ids
+ register entry count + prompt/report version
```

Requirements:

- same content produces same ID
- changed content produces a new ID
- protocol revisions increment `protocol_version`
- revised protocol sets `supersedes`
- never overwrite historical protocol content silently
- Qdrant upserts may update identical IDs but must not collapse distinct versions

---

# 14. Qdrant Collections

## 14.1 `praxis_protocols`

Vector text: title, working hypothesis, purpose, steps, keystone statement.
Payload contains full `PraxisProtocol`.

## 14.2 `praxis_observations`

No embedding required in the first pass unless `--embed-observations` is enabled.
Payload contains full `ObservationRecord`.

## 14.3 `praxis_reflections`

Embed: summary, what changed, what did not change, interpretation, epistemic
limits. Payload contains full `PraxisReflection`.

## 14.4 `praxis_failures`

Store: stage, Keystone ID, protocol ID when known, exception class, safe error
message, retry count, raw model output only when configured, timestamp,
recoverable boolean, structured validation errors, and `RegisterEntry` records.

Never store API keys or request headers.

## 14.5 Collection creation

Create collections only when missing. Validate existing vector size and distance
metric. Fail clearly on dimension mismatch. Do not delete or recreate collections
automatically.

---

# 15. LLM Client

Build one reusable OpenAI-compatible client.

Requirements:

- `httpx.Client`
- explicit connect/read/write timeouts
- bounded retry with exponential backoff
- retry only transient errors
- provider and model routing per operation
- optional direct DeepSeek route
- JSON extraction with strict validation
- preserve raw output for failure diagnostics
- usage and latency logging
- no hidden global mutable session
- thread-safe operation

Do not use native JSON mode unless the selected provider supports it reliably.
Prompt for JSON and validate locally.

---

# 16. Prompt Management

Prompt files live in `/prompts`. Every prompt must have:

- a version constant
- an explicit JSON schema
- role definition
- forbidden behaviours
- epistemic limits
- one valid example
- one rejected example

Record prompt versions in every output object. Prompts are loaded from disk, not
embedded across multiple service files. Tests must verify prompt files exist and
include required contract markers.

---

# 17. CLI Contract

`run.py` delegates to `app.cli.main()`.

```bash
# Inspect input and output collections
python run.py probe

# Score/classify without protocol generation
python run.py classify --limit 10 --dry-run

# Generate protocols
python run.py generate --limit 10 --dry-run
python run.py generate --limit 10
python run.py generate --keystone-id <id>
python run.py generate --min-convergence 0.80

# List and inspect
python run.py list protocols
python run.py list protocols --status approved
python run.py list register
python run.py show protocol <protocol_id>

# Validate payload
python run.py validate protocol examples/protocol_example.json

# Log observation
python run.py log-observation --file examples/observation_example.json
python run.py log-observation \
  --protocol-id <protocol_id> \
  --file examples/observation_example.json

# Reflect
python run.py reflect
python run.py reflect --observation-id <observation_id>

# Feedback
python run.py list feedback
python run.py show reflection <reflection_id>

# Export
python run.py export protocols --out data/protocols.json
python run.py export observations --out data/observations.json
python run.py export reflections --out data/reflections.json

# Report book
python run.py report --out data/praxis_book.md
python run.py report --out data/praxis_book.md --pdf --html
python run.py report --out data/book.md --run-id <run_id>
python run.py report --out data/book.md --since 2026-07-01
python run.py report --out data/book.md --from-exports data/
python run.py report --out data/book.md --index-terms docs/index_terms.txt
python run.py report --out data/book.md --title "Praxis Program One"
```

Global options:

```bash
--dry-run
--verbose
--log-level
--workers
```

CLI requirements:

- meaningful exit codes
- no stack trace by default
- full traceback in debug mode
- progress logging
- final summary counts
- clear skipped/rejected reasons
- `--dry-run` performs no Qdrant writes and no file writes
- never prompt interactively during batch execution

---

# 18. Generate Workflow

```text
1.  Connect to Qdrant
2.  Read configuration
3.  Probe Keystone schema
4.  Stream Keystone points
5.  Adapt each point into KeystoneRecord
6.  Apply prohibited-domain filter
7.  Apply deterministic candidate filter
8.  Run actionability classifier
9.  Calculate Praxis suitability
10. Skip below threshold
11. Generate protocol draft
12. Validate Pydantic schema
13. Run deterministic safety gate
14. Run critic
15. If revise: validate and safety-check revision
16. If pass: embed and upsert
17. If reject/hold/failure: write structured failure/hold record and RegisterEntry
18. Print summary
```

Concurrency:

- default 4 workers
- parallelise LLM-bound candidate processing
- keep counters thread-safe
- Qdrant writes must be guarded or use confirmed thread-safe clients
- one candidate failure must not abort the batch
- Ctrl+C should stop scheduling new work and exit cleanly after in-flight work
  settles

Summary format:

```text
Scanned:
Adapted:
Domain rejected:
Pre-filter rejected:
Classified:
Non-actionable:
Prohibited:
Below suitability:
Drafted:
Safety rejected:
Critic revised:
Critic rejected:
Held:
Approved:
Written:
Failed:
```

---

# 19. Observation Workflow

Observation logging must be primarily deterministic. The user supplies JSON.

1. load approved protocol
2. validate protocol/version
3. validate observation schema
4. validate measurement names against protocol
5. allow missing measurements but record them
6. prohibit arbitrary modification of the original protocol
7. flag deviations
8. set outcome
9. calculate content hash
10. write observation
11. never reinterpret the observation during logging

An `ADVERSE` outcome must:

- preserve the observation
- mark the protocol for human review
- prevent automatic generation of another version from the same Keystone in the
  current run
- create a feedback record
- not make a medical claim

---

# 20. Reflection Workflow

The reflector receives the Keystone statement, approved protocol, observation,
measurements, deviations, and confounds. It produces a bounded interpretation.

The reflection prompt must enforce:

- describe, do not diagnose
- one observation is anecdotal
- subjective change is useful but not universal proof
- do not reward compliance
- do not reinterpret failure as hidden success
- do not claim causation
- explicitly identify confounds
- recommend human review for adverse or contradictory results
- do not update Keystone
- never attribute an outcome to the participant's worthiness, sincerity, belief,
  or effort

Feedback recommendations are advisory records only.

---

# 21. Feedback Aggregation

Implement a deterministic aggregator that can summarise multiple observations for
one protocol or Keystone.

```json
{
  "keystone_id": "string",
  "protocol_id": "string",
  "observation_count": 12,
  "outcome_counts": {
    "supported": 4,
    "not_observed": 3,
    "contradicted": 2,
    "inconclusive": 2,
    "not_completed": 1,
    "adverse": 0
  },
  "completion_rate": 0.92,
  "adverse_rate": 0.0,
  "common_confounds": [],
  "recommendation": "new_question",
  "human_review_required": true
}
```

Do not calculate statistical significance in V1. Do not call repeated subjective
support "validation."

Use language such as:

- practical support observed
- pattern worth review
- no stable pattern observed
- contradictory observations present
- insufficient observations
- adverse outcomes require review

The words `validated`, `proven`, `confirmed`, `works`, and `effective` are
prohibited in generated aggregate text. A test must assert this.

---

# 22. Logging

Use standard Python logging. Provide console logging, rotating file log, optional
JSON log format, run ID, candidate/protocol correlation IDs, model latency, retry
count, stage transitions, rejection reasons, and a final run summary.

Do not log API keys, full environment, sensitive observer notes at INFO level, or
raw model prompts by default. Raw model requests/responses may be logged only at
DEBUG and only when `LOG_RAW_LLM=true`.

---

# 23. Error Handling

```text
PraxisError
ConfigurationError
SchemaMappingError
KeystoneReadError
LLMRequestError
LLMResponseValidationError
SafetyRejection
CriticRejection
QdrantWriteError
ObservationValidationError
ReportGenerationError
```

Rules:

- wrap external service errors with context
- preserve original exception chaining
- retry transient network/provider errors only
- do not retry schema failures
- write batch failures to `praxis_failures`
- return non-zero exit code when the whole command fails
- return zero when a batch completes with isolated recorded failures
- include failure count in summary

---

# 24. Tests

Target at least 90% coverage for deterministic modules.

## 24.1 Unit tests

Test config validation, Keystone field adapter, missing/optional payload fields,
enum parsing, Pydantic strictness, stable ID determinism, stable ID changes on
content changes, candidate thresholds, prohibited-domain matching, critic verdict
normalisation, safety rules, time/day/step limits, prohibited phrase and
semantic-category detection, actionability score bounds, Praxis suitability
calculation, protocol provenance completeness, observation measurement
validation, adverse outcome handling, feedback aggregation, dry-run no-write
guarantee, and redacted logging.

## 24.2 Safety test matrix

Explicit **rejection** fixtures for:

- breath holding
- fasting
- sleep deprivation
- medication changes
- driving
- fire/electricity
- entity communication
- paranoia testing
- self-sealing logic
- deception
- relationship confrontation
- spending
- legal action
- job quitting
- diagnosis
- guaranteed metaphysical proof
- **keystone asserting illness has emotional or spiritual origin**
- **keystone asserting healing follows from belief or alignment**
- **keystone asserting longevity is earned through practice**
- **protocol implying a symptom is caused by unexpressed feeling**
- **protocol implying hardship results from the participant's inner state**

Explicit **allowed** fixtures for:

- brief journaling
- state rating
- neutral observation
- normal breathing without manipulation
- generating alternative interpretations
- one low-stakes clarifying question
- noticing confounds
- short contemplative inquiry

## 24.3 Report book tests

- golden file: fixture records produce byte-identical `expected_book.md`
- determinism: two consecutive generations from identical input are identical
- mandatory sections: Epistemic Notice and Non-Actionable Register are present,
  and no code path can omit them
- ordering: protocol order is concept-alphabetical, never suitability-ordered
- prohibited language: generated aggregate text contains none of the banned
  validation words
- denominators: every generated count string includes its total
- index completeness: every protocol appears in the concept, mode, and risk indexes
- empty program: generating with zero approved protocols exits non-zero
- register completeness: every recorded rejection appears in Appendix A
- PDF renderer test is skipped when `reportlab` is unavailable

## 24.4 Integration tests

Use fake LLM responses and an in-memory/fake Qdrant adapter.

```text
Keystone fixture → classifier fixture → protocol fixture → safety
→ critic fixture → writer

approved protocol → observation fixture → reflection fixture → feedback record
→ report book
```

Optional real-Qdrant tests run only when `RUN_QDRANT_INTEGRATION_TESTS=true`.

## 24.5 CI

```bash
python -m pip install -r requirements-dev.txt
ruff check .
python -m pytest --cov=app --cov-report=term-missing
```

No live LLM or Qdrant requirement in CI.

---

# 25. Documentation

## README.md

Must include project purpose, pipeline diagram, what Praxis does, what Praxis
does not do, safety boundary, expected yield (§27), install, `.env` setup, CLI
examples, collection descriptions, sample protocol, report book description,
provenance explanation, feedback limitation, and relationship to Keystone.

Opening description:

> Praxis is the embodied experiment layer of the Meta-Bridge pipeline. It
> translates selected, provenance-backed Keystone propositions into minimal,
> reversible, low-risk practices and records what happens when those propositions
> encounter lived experience.

## AGENTS.md

Tell coding agents to use complete files, preserve architecture, add tests with
every behaviour change, run Ruff and pytest before finishing, never weaken
deterministic safety rules to make tests pass, never lower `MIN_PRAXIS_SUITABILITY`
or disable `ENFORCE_DOMAIN_PREFILTER` to increase output volume, never allow LLM
output to bypass Pydantic validation, never mutate Keystone, never commit secrets,
update README/docs for interface changes, prefer explicit code over abstraction
for its own sake, and avoid introducing frameworks without demonstrated need.

## SAFETY_MODEL.md

Document prohibited categories, the prohibited-domain pre-filter and its
rationale, risk tiers, deterministic rules, critic role, false-positive
preference, adverse outcome workflow, limitations, and the non-treatment boundary.

## DATA_MODEL.md

Full JSON examples and field semantics.

## FEEDBACK_LOOP.md

Explain why Praxis generates review candidates rather than modifying canon.

## REPORT_BOOK.md

Book structure, epistemic safeguards, index construction, output formats, and the
two-pass PDF build.

---

# 26. Example End-to-End Behaviour

Input Keystone:

```json
{
  "id": "ks_observer_state",
  "concept": "observer state",
  "statement": "Interpretation is partly constrained by the observer's physiological state.",
  "convergence": 0.78,
  "critic_verdict": "pass",
  "source_ids": ["source_a", "source_b"],
  "member_reflection_ids": ["r1", "r2"]
}
```

Expected actionability result:

```json
{
  "keystone_id": "ks_observer_state",
  "status": "eligible",
  "practice_mode": "observation",
  "risk_tier": 0,
  "actionability_score": 0.92,
  "reversibility_score": 1.0,
  "observability_score": 0.88,
  "burden_score": 0.95,
  "rationale": "The proposition can be examined through a brief before-and-after comparison without assuming it is true.",
  "disallowed_reasons": [],
  "open_questions": [],
  "model": "configured model",
  "prompt_version": "actionability_v1"
}
```

Expected protocol concept:

```text
Title: Two-State Interpretation

Working hypothesis:
A brief change in physiological arousal may alter how a mildly frustrating event
is interpreted.

Steps:
1. Write the immediate interpretation.
2. Rate emotional intensity and certainty from 0 to 10.
3. Sit quietly for three minutes and breathe normally.
4. Write a second interpretation.
5. Rate emotional intensity and certainty again.
6. Note whether alternative explanations became easier to generate.

Interpretation limit:
A changed interpretation does not establish which interpretation is correct and
does not prove the Keystone universally true.
```

Expected rejected input — metaphysical:

```text
Consciousness survives bodily death.
```

```json
{
  "status": "non_actionable",
  "practice_mode": "none",
  "risk_tier": 2,
  "rationale": "No direct, low-risk lived experiment can responsibly test this proposition. Praxis must not invent an afterlife-testing protocol."
}
```

Expected rejected input — prohibited domain:

```text
Illness is the body's language for unexpressed pain.
```

```json
{
  "status": "prohibited",
  "practice_mode": "none",
  "risk_tier": 3,
  "stage": "domain_filter",
  "rationale": "Statement implicates disease causation. Praxis does not generate experiments that invite a participant to attribute physical symptoms to emotional or spiritual cause.",
  "matched_rules": ["domain:illness", "domain:psychosomatic"]
}
```

---

# 27. Expected Yield and Calibration

The Keystone collection consists overwhelmingly of metaphysical propositions
about the nature of reality, consciousness, death, and cosmic order. Most of them
cannot responsibly become experiments, and the gates in §8 and §10 are designed
to say so.

**Expect an approval rate in the range of 5–15% of eligible Keystones.** A run
over several hundred Keystones producing twenty to forty approved protocols is
the system working correctly, not failing.

Requirements:

- The README must state the expected yield before a user's first run.
- A low approval count is never grounds to lower `MIN_PRAXIS_SUITABILITY`, raise
  `MAX_ALLOWED_RISK_TIER`, disable `ENFORCE_DOMAIN_PREFILTER`, or soften any
  §10.1 rule. `AGENTS.md` must state this explicitly.
- The run summary must print both the approval count and the total considered, so
  the ratio is always visible.
- Propositions most likely to pass concern attention, interpretation,
  expectation, framing, and self-report — not ontology, cosmology, survival of
  death, causation at a distance, or physical health.

---

# 28. Report Book Generation

## 28.1 Purpose and non-goals

Praxis must be able to emit a **complete, self-contained report book** covering an
experimental program: what was considered, what was refused and why, what was
approved, what happened, and what requires human review.

The book is a **record**, not a manual.

Non-goals:

- It is not a practice guide, curriculum, or recommended program.
- It does not rank protocols by desirability.
- It does not claim any proposition was validated.
- It does not replace the JSON exports in §17; it is generated *from* the same records.

## 28.2 Output formats

| Format | Status | Dependency | Purpose |
|---|---|---|---|
| Markdown | **canonical, required** | stdlib only | complete content, anchor-linked TOC and indexes, git-diffable |
| HTML | optional | stdlib templating | browsable, hyperlinked cross-references |
| PDF | optional extra | `reportlab` | paginated book with page-numbered TOC, page-referenced indexes, running footers |

Markdown is the source of truth. HTML and PDF are renderings of the same assembled
document model — **not** independently generated content.

PDF must use a **two-pass build**: the first pass lays out and records page
numbers, the second emits the TOC and indexes with real page references. A TOC
without page numbers is not acceptable for the PDF target.

Generation must be **deterministic**: identical input data and configuration
produce a byte-identical Markdown file.

## 28.3 Book structure

```text
FRONT MATTER
  Title page
  Epistemic Notice          (mandatory, cannot be suppressed)
  How to Read This Book
  Table of Contents         (auto-generated, depth 3)

PART I — PROGRAM SUMMARY
  1. Run provenance (models, prompt versions, redacted config, collection snapshot)
  2. Funnel table (all §18 summary counters)
  3. Distribution tables: practice mode, risk tier, keystone concept
  4. Observation coverage (protocols with 0 observations stated explicitly)

PART II — APPROVED PROTOCOLS
  One chapter per approved protocol (see 28.4)

PART III — OBSERVATIONS AND REFLECTIONS
  Per-protocol observation tables
  Full reflection records

PART IV — CANDIDATES FOR HUMAN REVIEW
  Adverse outcomes first
  Aggregator output (§21), bounded language only

APPENDIX A — Non-Actionable Register     (mandatory)
APPENDIX B — Safety Decision Log
APPENDIX C — Failure Log
APPENDIX D — Configuration Snapshot (redacted)

INDEXES
```

## 28.4 Protocol chapter layout

Every protocol chapter contains, in order:

1. Title, protocol ID, version, status
2. **Source keystone**: statement, concept, convergence and its components, `n_sources`
3. **Working hypothesis**, explicitly labelled as a hypothesis under test
4. Purpose, practice mode, risk tier, duration, frequency
5. Numbered steps
6. Measurements table
7. Confounds to notice
8. **Stop conditions** — visually prominent block
9. **Interpretation limits** — visually prominent block
10. Provenance: `source_ids`, `member_reflection_ids`, models, prompt versions, content hash
11. Safety and critic record: flags, matched rules, verdict, notes
12. Observations recorded against this protocol, or an explicit "No observations recorded"

## 28.5 Required epistemic safeguards

These are **structural requirements**, not stylistic preferences. A book format
carries more apparent authority than a JSON file; these constraints exist to keep
that authority from being read as endorsement.

1. **The Epistemic Notice is mandatory.** No flag, config value, or CLI option may
   suppress it. It appears in full before any protocol content.
2. **Interpretation limits are repeated in every protocol chapter.** They must not
   be centralised into front matter and referenced.
3. **Stop conditions are repeated in every protocol chapter**, in a visually
   distinct block.
4. **Appendix A is mandatory.** The book must never ship containing only
   approvals. Every Keystone considered and not turned into a protocol appears
   with its rejection reason and stage.
5. **Protocols are ordered by keystone concept (alphabetical), never by
   suitability score.** Scores may be displayed but must not drive order.
6. **No validation language in aggregates.** Only the bounded phrasing from §21.
7. **Adverse outcomes appear twice** — in Part IV and in the relevant protocol's
   own chapter.
8. **Every aggregate figure states its denominator.** "3 supported" is prohibited;
   "3 supported of 12 observations" is required.
9. **Prohibited-domain note.** Appendix A states the excluded domain category
   explicitly, so the absence is visible rather than silent.
10. **PDF running footer** on every page carries a short epistemic reminder.

## 28.6 Indexes

Structured indexes are generated from enum and field values — not from free-text
term extraction.

| Index | Key | Entries point to |
|---|---|---|
| Index of Concepts | `keystone_concept` | protocol chapters |
| Index of Practice Modes | `practice_mode` | protocol chapters |
| Index of Risk Tiers | `risk_tier` | protocol chapters |
| Index of Outcomes | `ObservationOutcome` | observation records |
| Index of Keystone IDs | `keystone_id` | protocols, register entries |
| Index of Source Traditions | `source_ids` | keystones, protocols |
| Index of Confounds | `confounds_to_notice`, `confounds_observed` | protocols, observations |

Optional curated keyword index via `--index-terms docs/index_terms.txt`.

Markdown and HTML indexes use anchor links. PDF indexes use page numbers from the
two-pass build.

## 28.7 CLI requirements

- reads from Qdrant, or from JSON exports with `--from-exports data/`
- `--dry-run` prints the assembled outline and counts, writes nothing
- refuses to generate an empty book; exits non-zero with a clear message
- warns on stdout when zero observations exist across the whole program
- emits `<out>.manifest.json` alongside the book
- never writes outside the given `--out` path and its siblings

## 28.8 Epistemic Notice — required template

`report_templates/epistemic_notice.md` must contain at least these elements.
Wording may be refined; content may not be reduced.

> **About this book.**
>
> This document records a set of small, bounded experiments derived from
> propositions held in a Keystone collection. Those propositions were selected
> because independent analytical lenses converged on them within a text corpus.
> **Convergence across sources is a measure of agreement among texts. It is not
> evidence that a proposition is true.**
>
> Every protocol here treats its source proposition as a *working hypothesis* —
> something to be examined, not something established. A protocol that produces a
> noticeable change does not demonstrate that its proposition is correct, and a
> protocol that produces no change does not demonstrate that it is false. Single
> observations are anecdotes.
>
> Nothing in this book is medical, psychological, legal, or financial advice.
> Nothing here is a treatment, therapy, diagnosis, or remedy. Propositions
> concerning disease causation, healing, longevity, aging, and medication were
> deliberately excluded from experiment generation; see Appendix A.
>
> Every protocol is voluntary and may be stopped at any moment for any reason.
> Stopping is not failure, and non-completion is never evidence of resistance,
> unreadiness, or anything else about the person who stopped.
>
> Appendix A lists every proposition that was considered and refused. It is part
> of the record, and reading it is part of reading this book.

---

# 29. Build Milestones

## Milestone 1: Skeleton and contracts

Repository structure, config, models, enums, CLI skeleton, logging, prompt
loader, and model/config tests.

Acceptance: `python run.py --help`, `ruff check .`, and `python -m pytest` all pass.

## Milestone 2: Keystone ingestion

Qdrant client, probe command, field adapter, candidate selector, schema warnings,
dry-run input listing.

Acceptance: reads the real Keystone collection, maps current records, handles
missing optional fields, does not write.

## Milestone 3: Actionability and safety

Prohibited-domain filter, classifier, Pydantic response validation, deterministic
safety engine, suitability calculation, and the full safety fixture matrix.

Acceptance: all prohibited fixtures reject, all allowed fixtures pass, malformed
LLM output cannot pass, domain-filter fixtures reject before any LLM call.

## Milestone 4: Condenser and critic

Protocol generator, critic, revision loop, protocol validation, stable IDs,
writer, concurrent generation workflow.

Acceptance: `python run.py generate --limit 10 --dry-run` prints valid outcomes
and makes no writes. A live run writes only approved protocols.

## Milestone 5: Observation loop

Observation schema, log command, validation, adverse handling, Qdrant writer.

Acceptance: valid observations write, invalid measurement names flag clearly,
adverse results create review flags.

## Milestone 6: Reflection and feedback

Reflector, feedback records, aggregator, export commands.

Acceptance: reflection never modifies Keystone, feedback uses bounded language,
aggregation counts outcomes correctly.

## Milestone 7: Report book

Document model, Markdown renderer, indexes, register assembly, golden-file test,
optional HTML and PDF renderers.

Acceptance: `python run.py report --dry-run` prints a complete outline; a live run
produces Markdown passing the golden-file, ordering, and mandatory-section tests;
`--pdf` produces a page-numbered TOC or fails clearly when the extra is absent.

## Milestone 8: Documentation and hardening

Full README, AGENTS.md, docs, examples, CI, coverage, clean error messages, setup
script.

Acceptance: clean clone setup works, no secrets committed, all tests pass, agent
provides final file tree and command transcript.

---

# 30. Definition of Done

- [ ] clean clone installs successfully
- [ ] `python run.py --help` works
- [ ] `python run.py probe` inspects Keystone
- [ ] `python run.py generate --limit 10 --dry-run` completes without writes
- [ ] real generation can write approved protocols
- [ ] unsafe candidates are rejected deterministically
- [ ] prohibited-domain Keystones are rejected before any LLM call
- [ ] critic cannot bypass safety
- [ ] every protocol has full provenance
- [ ] stable IDs are deterministic
- [ ] observations validate against protocol definitions
- [ ] adverse observations create review records
- [ ] reflections preserve epistemic limits
- [ ] no process automatically modifies Keystone
- [ ] exports produce valid JSON
- [ ] `python run.py report --out data/praxis_book.md` produces a complete book
- [ ] book contains a Table of Contents, all required indexes, and Appendix A
- [ ] Epistemic Notice cannot be suppressed by any flag or config value
- [ ] book generation is deterministic and covered by a golden-file test
- [ ] `--pdf` produces a page-numbered TOC via two-pass layout, or fails clearly
- [ ] README states the expected yield
- [ ] Ruff passes
- [ ] pytest passes
- [ ] deterministic modules have at least 90% coverage
- [ ] CI passes
- [ ] README and docs are complete
- [ ] no TODOs, placeholders, secrets, or dead code remain

---

# 31. Required Final Agent Report

At completion, the coding agent must return:

1. concise architecture summary
2. complete file tree
3. commands run
4. test results
5. coverage result
6. sample dry-run output
7. sample generated protocol
8. safety cases tested
9. sample report book table of contents
10. known limitations
11. exact next command for the user to run

The agent must not claim completion without running the test suite.

---

# 32. Final Product Statement

Praxis completes the directional loop of the Meta-Bridge pipeline:

```text
Corpus Maximus acquires.
Meta-Bridge interprets.
Vectoreologist maps.
MisfitCrew attacks.
Keystone remembers.
Praxis discovers what happens when an idea leaves the database.
```

The system does not tell people what to believe. It gives selected propositions a
careful encounter with lived reality, records what happened, preserves the
confounds, and sends the result back for human inspection.

That is the product.
