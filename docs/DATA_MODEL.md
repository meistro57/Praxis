# Data Model and Field Semantics

This document describes the JSON schemas and field semantics for the main data entities managed by the Praxis pipeline.

---

## 1. Keystone Record

A `KeystoneRecord` represents a canonical proposition derived from the Meta-Bridge pipeline. It serves as the primary input to the Praxis generation pipeline.

```json
{
  "id": "c16fd9d6-512b-586b-80a5-f852cc5967aa",
  "concept": "attention span",
  "statement": "Visual focus exercises stabilize attention duration.",
  "one_liner": "Visual focus improves attention.",
  "convergence": 0.85,
  "critic_verdict": "pass",
  "source_ids": ["src_1"],
  "created_at": "2026-07-19T10:00:00Z"
}
```

### Field Semantics
* `id`: Stable UUIDv5 string generated from the normalized statement.
* `concept`: Short label of the psychological or cognitive concept.
* `statement`: Full canonical claim text.
* `convergence`: Empirical consensus score (0.0 to 1.0) from the Meta-Bridge pipeline.
* `critic_verdict`: Safety/correctness verdict from prior pipeline steps.
* `source_ids`: List of primary source record IDs backing this claim.

---

## 2. Actionability Assessment

Produced by the classifier when evaluating a Keystone candidate's suitability.

```json
{
  "keystone_id": "c16fd9d6-512b-586b-80a5-f852cc5967aa",
  "status": "eligible",
  "practice_mode": "observation",
  "risk_tier": 0,
  "actionability_score": 9.0,
  "reversibility_score": 8.5,
  "observability_score": 9.0,
  "burden_score": 8.5,
  "rationale": "Highly actionable personal focus practice.",
  "disallowed_reasons": [],
  "open_questions": [],
  "model": "gpt-4",
  "prompt_version": "v1"
}
```

### Field Semantics
* `status`: Rejection or eligibility status (`eligible`, `non_actionable`, `prohibited`).
* `practice_mode`: Protocol type (`observation` or `experiment`).
* `risk_tier`: Assigned risk level (0 to 3).
* `actionability_score`: Score indicating ease of execution (0 to 10).
* `reversibility_score`: Score indicating ease of stopping with no lasting effects (0 to 10).
* `observability_score`: Score indicating how visible the outcomes are (0 to 10).
* `burden_score`: Score indicating the time/effort overhead (0 to 10).

---

## 3. Praxis Protocol

The completed, approved experimental practice stored in the database.

```json
{
  "protocol_id": "b28cd9f3-42ab-52ab-90a1-a832cc5967bb",
  "protocol_version": 1,
  "supersedes": null,
  "status": "approved",
  "title": "Visual Focus Stabilization",
  "working_hypothesis": "Staring at a spot stabilizes attention.",
  "purpose": "Measure focus duration.",
  "practice_mode": "observation",
  "risk_tier": 0,
  "duration_minutes": 5,
  "duration_days": 3,
  "frequency": "daily",
  "steps": [
    "Sit in front of a dot.",
    "Stare for 5 minutes.",
    "Record focus breaks."
  ],
  "measurements": [],
  "confounds_to_notice": [],
  "stop_conditions": [],
  "interpretation_limits": [],
  "keystone_id": "c16fd9d6-512b-586b-80a5-f852cc5967aa",
  "keystone_concept": "attention span",
  "actionability_score": 9.0,
  "suitability_score": 5.8,
  "critic_verdict": "pass",
  "critic_notes": ["Looks safe and clean."],
  "created_at": "2026-07-19T10:00:00Z"
}
```

---

## 4. Observation Record

Logged by participants recording execution results.

```json
{
  "observation_id": "obs_9f8d7c6b",
  "protocol_id": "b28cd9f3-42ab-52ab-90a1-a832cc5967bb",
  "protocol_version": 1,
  "observer_id": "obs_user_1",
  "logged_at": "2026-07-19T11:00:00Z",
  "completion_ratio": 1.0,
  "outcome": "supported",
  "adverse_effects": [],
  "notes": "Focused easily throughout.",
  "measurement_values": {},
  "confounds_observed": []
}
```

### Field Semantics
* `completion_ratio`: Proportion of steps completed (0.0 to 1.0).
* `outcome`: Participant self-report outcome (`supported`, `unsupported`, `ambiguous`).
* `adverse_effects`: Descriptions of any negative physical/cognitive reactions.
