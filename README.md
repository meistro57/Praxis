# Praxis
<img width="364" height="389" alt="image" src="https://github.com/user-attachments/assets/7be0e9d4-8058-4314-aac0-80182d1bcd52" />

Praxis is the embodied experiment layer of the Meta-Bridge pipeline. It translates selected, provenance-backed Keystone propositions into minimal, reversible, low-risk practices and records what happens when those propositions encounter lived experience.

---

## 1. Project Purpose & Boundary

Praxis bridges theoretical insights and lived observation. Instead of accepting abstract conceptual models at face value, Praxis acts as a compiler that reads Keystone propositions and spits out safe, actionable behavioral protocols.

### What Praxis Does
* **Filters:** Evaluates incoming propositions against strict domain and risk boundaries.
* **Classifies:** Scores candidate propositions on actionability, burden, observability, and reversibility.
* **Drafts:** Translates eligible concepts into step-by-step practical guides.
* **Reviews:** Validates drafts using a multi-phase safety pipeline (Deterministic Safety + LLM Critic).
* **Tracks:** Logs participant observations and aggregates feedback.
* **Reports:** Compiles comprehensive experimental program report books (HTML/PDF/Markdown).

### What Praxis Does NOT Do (Safety Boundary)
* **No Medical Treatment:** Praxis explicitly excludes medical, therapeutic, diagnostic, or psychiatric interventions.
* **No Metaphysical Testing:** Praxis will not generate protocols attempting to verify survival of bodily death, remote influence, or non-empirical causal claims.
* **No Irreversible Actions:** All practices must be fully reversible, low-risk, and limited in scope.
* **No Canon Mutation:** Praxis records observational data and proposes modifications, but never directly alters or overwrites the foundational canonical models.

---

## 2. Pipeline Architecture

Below is the conceptual architecture showing how a candidate proposition flows through the Praxis funnel to become an active protocol:

```mermaid
graph TD
    K[Keystone Proposition] --> DF[Domain Pre-Filter]
    DF -->|Pass| AC[Actionability Classifier]
    DF -->|Fail| R1[Rejection Register]
    AC -->|Suitability >= Threshold| PC[Practice Condenser]
    AC -->|Suitability < Threshold| R2[Rejection Register]
    PC --> SG[Deterministic Safety Gate]
    SG -->|Violates Safety| R3[Rejection Register]
    SG -->|Pass| CG[LLM Critic Gate]
    CG -->|Fail| R4[Rejection Register]
    CG -->|Pass| PW[Protocol Writer]
    PW --> DB[(Qdrant Vector DB)]
```

---

## 3. Expected Yield and Calibration

The Keystone collection consists overwhelmingly of metaphysical propositions about the nature of reality, consciousness, death, and cosmic order. Most of them cannot responsibly become experiments.

> [!IMPORTANT]
> **Expect an approval rate in the range of 5–15% of eligible Keystones.** A run over several hundred Keystones producing twenty to forty approved protocols is the system working correctly, not failing.
>
> A low approval count is never grounds to lower `MIN_PRAXIS_SUITABILITY`, raise `MAX_ALLOWED_RISK_TIER`, disable `ENFORCE_DOMAIN_PREFILTER`, or soften any safety/critic rule.

---

## 4. Setup and Installation

### Dependencies
This project uses a split dependency model to isolate formatting and report generation libraries (like ReportLab):
* **Core dependencies:** Listed in `requirements.txt`.
* **Development/Linting dependencies:** Listed in `requirements-dev.txt`.
* **Report generation dependencies:** Listed in `requirements-report.txt`.

### Installation
Run the bootstrapper script to configure your environment:
```bash
chmod +x setup.sh
./setup.sh
```

### Environment Settings (`.env`)
Create a `.env` file in the root directory (automatically copied from `.env.example` by `setup.sh`):
```ini
ACTIONABILITY_MODEL=deepseek/deepseek-r1
CONDENSER_MODEL=deepseek/deepseek-r1
CRITIC_MODEL=google/gemma-3-27b-it
REFLECTION_MODEL=deepseek/deepseek-r1

OPENROUTER_API_KEY=your_key_here
EMBED_API_KEY=your_key_here

QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Optional Direct DeepSeek Routing (Bypasses OpenRouter for DeepSeek models)
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_REASONER_MODEL=deepseek-reasoner
```

---

## 5. Command Line Interface (CLI)

The top-level execution point is `run.py`.

### Connection Probe
Verify Qdrant connection and inspect collections:
```bash
python run.py probe
```

### Generate Protocols
Assess and generate protocols from seeded Keystones:
```bash
# Process all candidates
python run.py generate

# Process up to 10 candidates
python run.py generate --limit 10

# Process in dry-run mode (no writes to Qdrant)
python run.py generate --limit 10 --dry-run

# Run for a specific Keystone ID
python run.py generate --keystone-id <id>

# Filter by minimum convergence
python run.py generate --min-convergence 0.80
```

### Classify Only
Score/classify Keystones for actionability and suitability without generating drafts:
```bash
python run.py classify --limit 10 --dry-run
```

### Log Observations
Log an outcome observation against an active protocol:
```bash
python run.py log-observation --protocol-id <id> --file path/to/observation.json
```

### Reflect on Observations
Trigger LLM reflection on logged observations:
```bash
python run.py reflect --observation-id <id>
```

### List and Inspect Items
List items stored in Qdrant collections or show details:
```bash
# List generated protocols (with optional status filter)
python run.py list protocols
python run.py list protocols --status approved

# List the Appendix A Refused/Non-Actionable Register
python run.py list register

# List qualitative reflections and feedback recommendations
python run.py list feedback

# Show full JSON payload of a specific protocol
python run.py show protocol <protocol_id>

# Show full JSON payload of a specific reflection
python run.py show reflection <reflection_id>
```

### Validate Payloads
Validate a local JSON payload against Pydantic schemas:
```bash
python run.py validate protocol examples/protocol_example.json
```

### Export Results
Export collections to static JSON files:
```bash
python run.py export protocols --out data/protocols.json
python run.py export observations --out data/observations.json
python run.py export reflections --out data/reflections.json
```

### Generate Report Book
Compile HTML and PDF books summarizing the experimental program:
```bash
python run.py report --out data/praxis_book.md --pdf --html
```

---

## 6. Optional Direct DeepSeek Routing
When `DEEPSEEK_API_KEY` is provided, Praxis will automatically route DeepSeek models (e.g. models matching `deepseek`) directly to the native DeepSeek API endpoint (`https://api.deepseek.com` by default) instead of routing them through OpenRouter. 

During direct routing, the client automatically handles compatibility layers, including:
* **Model ID translation:** Converts OpenRouter model names like `deepseek/deepseek-r1` or `deepseek/deepseek-chat` to native API identifiers like `deepseek-reasoner` or `deepseek-chat`.
* **DeepSeek Contract Compliance:** Omits `temperature` parameter for `deepseek-reasoner` model requests, preventing native DeepSeek API schema validation errors.

---

## 7. Data Collection Descriptions

Praxis manages data across several logical Qdrant collections:
* **`keystones`**: The input candidate propositions from the Meta-Bridge pipeline.
* **`praxis_protocols`**: Approved and active experimental practices.
* **`praxis_observations`**: Participant logs containing execution outcomes, durations, and adverse effects.
* **`praxis_reflections`**: Synthesized evaluations of observations, recommending repeats, adaptations, or halts.
* **`praxis_failures`**: The rejection register detailing exactly which candidates failed at which stage.
