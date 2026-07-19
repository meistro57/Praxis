# Guidelines for Autonomous Coding Agents

This repository has a highly disciplined architecture governed by safety guidelines and formal data validation rules. All coding agents modifying this codebase must adhere strictly to the instructions in this document.

---

## 1. Safety Calibration & Verification Constraints

> [!IMPORTANT]
> **Praxis is calibrated for a low yield (5–15% approval rate).**
> A low protocol yield is the safety system working correctly. Under no circumstances may an agent:
> * Lower `MIN_PRAXIS_SUITABILITY` or raise `MAX_ALLOWED_RISK_TIER`.
> * Disable `ENFORCE_DOMAIN_PREFILTER` to increase output volume.
> * Soften deterministic safety filters or critic validation gates.
> * bypass Pydantic validation for LLM outputs.

* **Never Weaken Safety Rules to Pass Tests:** If a test fails because of a safety rejection, the mock data or test case itself is invalid. Adjust the test inputs to be safe, rather than making the safety code more permissive.
* **Deterministic Rules:** Do not replace deterministic regex/keyword boundaries with fuzzy heuristic models or LLM-based decisions. Deterministic screens must run first and fail-fast.

---

## 2. Code Quality and Testing Discipline

* **Preserve Architecture:** Do not introduce bloated frameworks or unnecessary abstractions. Keep the services decoupled, first-class functions simple, and CLI tools declarative.
* **Tests with Every Behavior Change:** If you modify how a workflow parses data, generates reports, or filters records, you MUST add corresponding unit or integration tests in `tests/`.
* **Verification Routine:** Before declaring a task finished, you must execute:
  1. `.venv/bin/ruff check .` to check coding standard and imports.
  2. `.venv/bin/python -m pytest` to run the test suite and ensure all tests pass.
* **No Unused Imports or Code:** All imports must be explicit. Avoid wildcard imports, unused locals, and unused private variables. Use explicit PEP 484 re-exports (`from x import y as y`) in `__init__.py` files.
* **Never Mutate Keystone Records:** Keystone records are read-only canonical data points. Do not add fields, delete fields, or alter payload structures of `KeystoneRecord` instances.

---

## 3. Operations & Safety Policies

* **Zero-Secrets Policy:** Do not hardcode or commit keys, tokens, endpoints, or environment values. Utilize the config settings class in `config.py` which redacts sensitive fields from text logs automatically.
* **Documentation Maintenance:** If interfaces, command-line flags, or environment variables are modified, immediately update `README.md` and files inside `docs/` to maintain alignment.
