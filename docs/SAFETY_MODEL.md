# Safety Model and Operational Boundaries

Praxis operates under a strict, multi-layered safety envelope designed to prevent theoretical research from translating into harmful real-world behaviors.

---

## 1. The Non-Treatment Boundary

Praxis is strictly an exploration platform for personal practices.
* **No Medical/Therapeutic Claims:** Praxis does not design or recommend interventions for physical disease, mental illness, injury, or psychological disorders.
* **No Clinical Diagnoses:** Praxis does not attempt to diagnose symptoms or assess clinical conditions.
* **No Substance Administration:** No practices involving ingestion of substances (herbal, chemical, dietary) are allowed.

---

## 2. Prohibited Domains and Pre-Filters

To enforce the non-treatment boundary, a deterministic pre-filter screens all Keystone candidates before they are ever sent to the LLM.

### Prohibited Categories
1. **Medical and Pathological:** Keywords relating to cancer, cardiovascular disease, infectious agents, prescription medication, surgeries, etc.
2. **Psychiatric and Clinical:** Keywords relating to major depressive disorder, schizophrenia, trauma, panic, clinical anxiety, psychotherapies.
3. **Invasive or Dangerous:** Practices involving fasting, extreme temperatures, sleep deprivation, or hyperventilation.

### Filter Rationale
Using LLMs to filter dangerous content is susceptible to prompt injections and model drift. By running a deterministic keyword screen with general word boundaries, we ensure that clinical/medical terms are caught with zero-tolerance.

---

## 3. Risk Tiers

Every practice is classified into a Risk Tier during actionability assessment:

| Tier | Category | Description | Policy |
| :--- | :--- | :--- | :--- |
| **0** | Minimal | Practices involving minor changes in attention, expectation, or routine. | Automatically Approved if pass gates. |
| **1** | Low | Practices requiring small physical adjustments or timing modifications. | Approved with a warning label. |
| **2** | Moderate | Minor lifestyle changes or physical demands. | HELD for human review. |
| **3** | High | Significant physical strain, invasive behaviors, or medical overlap. | REJECTED immediately. |

---

## 4. The LLM Critic Gate

Even if a draft passes the deterministic filters, it must face the `CriticGate` LLM evaluation. The critic evaluates the draft on:
* **Overreach:** Does the protocol claim that the practice proves a grand metaphysical reality?
* **Self-Sealing Logic:** Does the protocol suggest that "if you fail, it's because you didn't believe enough"?
* **Provenance Issues:** Does the protocol deviate from the original Keystone concept?

If the critic identifies any of these issues, the protocol is rejected or revised.

---

## 5. False-Positive Preference

> [!IMPORTANT]
> Praxis prioritizes safety over yield. If a practice is on the boundary of being therapeutic or carries ambiguous risk, the system is calibrated to reject it. We explicitly prefer false positives (safe practices rejected) over false negatives (harmful practices approved).

---

## 6. Adverse Outcome Workflow

If a participant logs an observation with a non-empty `adverse_effects` list:
1. The outcome logger records the event in Qdrant with a high severity flag.
2. The reflection engine is immediately triggered.
3. If an adverse effect is confirmed, the engine marks the practice as requiring immediate human review and flags the protocol state as `held`.
4. A warning warning banner is emitted in the subsequent Report Book compile.
