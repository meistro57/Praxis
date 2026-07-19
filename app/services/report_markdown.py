import os
import json
import logging
from typing import Any, Optional
from app.services.report_model import ReportData
from app.services.indexes import PraxisIndexes
from app.services.feedback import FeedbackAggregator
from app.models.enums import ObservationOutcome

logger = logging.getLogger(__name__)

class MarkdownReportBuilder:
    def __init__(self, data: ReportData, config: Any):
        self.data = data
        self.config = config
        self.indexes = PraxisIndexes()
        
        # Sort protocols alphabetically by keystone concept
        # Requirement 5: Protocols are ordered by concept (alphabetical), never suitability score
        self.data.protocols.sort(key=lambda x: x.keystone_concept.lower())

    def _load_template(self, filename: str) -> str:
        """Load markdown template from report_templates/."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(project_root, "report_templates", filename)
        if not os.path.exists(path):
            logger.warning(f"Template not found at: {path}. Using fallback.")
            return f"<!-- Template {filename} missing -->"
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def build_markdown(self, index_terms_path: Optional[str] = None) -> str:
        """Assemble the complete Markdown report book."""
        # Build indexes first
        self.indexes.build(
            protocols=self.data.protocols,
            observations=self.data.observations,
            reflections=self.data.reflections,
            register_entries=self.data.register_entries,
            index_terms_path=index_terms_path
        )

        md = []

        # TITLE PAGE
        md.append(f"# {self.data.title}")
        md.append("**Program Export Book**")
        md.append(f"Generated: {self.data.generated_at}")
        md.append(f"Scope: {self.data.scope}")
        md.append("\n---\n")

        # EPISTEMIC NOTICE (Mandatory - Requirement 1)
        notice_content = self._load_template("epistemic_notice.md")
        md.append("# Epistemic Notice")
        md.append(notice_content)
        md.append("\n---\n")

        # HOW TO READ
        how_to_read = self._load_template("how_to_read.md")
        md.append(how_to_read)
        md.append("\n---\n")

        # TABLE OF CONTENTS
        md.append("# Table of Contents")
        md.append("- [Part I — Program Summary](#part-i-program-summary)")
        md.append("  - [1. Run Provenance](#1-run-provenance)")
        md.append("  - [2. Funnel Summary](#2-funnel-summary)")
        md.append("  - [3. Distributions](#3-distributions)")
        md.append("  - [4. Observation Coverage](#4-observation-coverage)")
        md.append("- [Part II — Approved Protocols](#part-ii-approved-protocols)")
        for p in self.data.protocols:
            anchor = p.title.lower().replace(" ", "-").replace(",", "").replace(".", "")
            md.append(f"  - [{p.title}](#{anchor})")
        md.append("- [Part III — Observations and Reflections](#part-iii-observations-and-reflections)")
        md.append("- [Part IV — Candidates for Human Review](#part-iv-candidates-for-human-review)")
        md.append("- [Appendix A — Non-Actionable Register](#appendix-a-non-actionable-register)")
        md.append("- [Appendix B — Safety Decision Log](#appendix-b-safety-decision-log)")
        md.append("- [Appendix C — Failure Log](#appendix-c-failure-log)")
        md.append("- [Appendix D — Configuration Snapshot](#appendix-d-configuration-snapshot)")
        md.append("- [Indexes](#indexes)")
        md.append("  - [Index of Concepts](#index-of-concepts)")
        md.append("  - [Index of Practice Modes](#index-of-practice-modes)")
        md.append("  - [Index of Risk Tiers](#index-of-risk-tiers)")
        md.append("  - [Index of Outcomes](#index-of-outcomes)")
        md.append("  - [Index of Keystone IDs](#index-of-keystone-ids)")
        md.append("  - [Index of Source Traditions](#index-of-source-traditions)")
        md.append("  - [Index of Confounds](#index-of-confounds)")
        if self.indexes.keywords:
            md.append("  - [Index of Keywords](#index-of-keywords)")
        md.append("\n---\n")

        # PART I — PROGRAM SUMMARY
        md.append("# Part I — Program Summary")
        
        md.append("## 1. Run Provenance")
        md.append(f"- **Keystone Collection Name:** `{self.data.keystone_collection}`")
        md.append(f"- **Scope of Extraction:** `{self.data.scope}`")
        md.append(f"- **Run IDs included:** {', '.join(self.data.run_ids) if self.data.run_ids else 'None'}")
        md.append(f"- **Actionability Model:** `{self.config.actionability_model}`")
        md.append(f"- **Practice Condenser Model:** `{self.config.condenser_model}`")
        md.append(f"- **Critic Model:** `{self.config.critic_model}`")
        md.append(f"- **Embeddings Model:** `{self.config.embed_model}`")
        
        md.append("\n## 2. Funnel Summary")
        md.append("| Metric | Count |")
        md.append("|---|---|")
        for k, v in self.data.funnel_counts.items():
            md.append(f"| {k.replace('_', ' ').title()} | {v} |")

        md.append("\n## 3. Distributions")
        
        md.append("\n### Practice Modes")
        md.append("| Mode | Count |")
        md.append("|---|---|")
        for k, v in self.data.distributions.modes.items():
            md.append(f"| {k} | {v} |")
            
        md.append("\n### Risk Tiers")
        md.append("| Risk Tier | Count |")
        md.append("|---|---|")
        for k, v in self.data.distributions.risk_tiers.items():
            md.append(f"| Tier {k} | {v} |")

        md.append("\n### Keystone Concepts")
        md.append("| Concept | Count |")
        md.append("|---|---|")
        for k, v in sorted(self.data.distributions.concepts.items()):
            md.append(f"| {k} | {v} |")

        md.append("\n## 4. Observation Coverage")
        # List protocols and their count of observations
        # Stated explicitly (Requirement 4)
        md.append("| Protocol Title | Observation Count | Status |")
        md.append("|---|---|---|")
        for p in self.data.protocols:
            p_obs = [o for o in self.data.observations if o.protocol_id == p.protocol_id]
            status = "Covered" if p_obs else "**No observations recorded**"
            md.append(f"| {p.title} | {len(p_obs)} | {status} |")
            
        md.append("\n---\n")

        # PART II — APPROVED PROTOCOLS (Chapter layout - Section 28.4)
        md.append("# Part II — Approved Protocols")
        
        for p in self.data.protocols:
            anchor = p.title.lower().replace(" ", "-").replace(",", "").replace(".", "")
            md.append(f"## {p.title}")
            md.append(f"- **Protocol ID:** `{p.protocol_id}`")
            md.append(f"- **Version:** `{p.protocol_version}`")
            md.append(f"- **Status:** `{p.status.value}`")
            if p.supersedes:
                md.append(f"- **Supersedes:** `{p.supersedes}`")
            
            md.append("\n### Source Keystone")
            md.append(f"- **Concept:** {p.keystone_concept}")
            md.append(f"- **Statement:** *\"{p.keystone_statement}\"*")
            md.append(f"- **Convergence Score:** {p.keystone_convergence}")
            
            md.append("\n### Working Hypothesis")
            md.append(f"> **Hypothesis Under Test:** {p.working_hypothesis}")

            md.append("\n### Parameters")
            md.append(f"- **Practice Mode:** `{p.practice_mode.value}`")
            md.append(f"- **Risk Tier:** `{p.risk_tier.value}`")
            md.append(f"- **Purpose:** {p.purpose}")
            md.append(f"- **Duration (minutes per session):** {p.duration_minutes}")
            md.append(f"- **Duration (days):** {p.duration_days}")
            md.append(f"- **Frequency:** {p.frequency}")

            md.append("\n### Protocol Steps")
            for idx, step in enumerate(p.steps, 1):
                md.append(f"{idx}. {step}")

            md.append("\n### Measurements")
            md.append("| Name | Type | Scale | When |")
            md.append("|---|---|---|---|")
            for m in p.measurements:
                scale_val = m.scale if m.scale else "N/A"
                when_val = ", ".join(m.when) if m.when else "N/A"
                md.append(f"| {m.name} | {m.type} | {scale_val} | {when_val} |")

            md.append("\n### Confounds to Notice")
            for conf in p.confounds_to_notice:
                md.append(f"- {conf}")

            # Visually prominent blocks for stop conditions and interpretation limits (Requirements 2, 3)
            md.append("\n> [!IMPORTANT]\n> **Stop Conditions**")
            for stop in p.stop_conditions:
                md.append(f"> - {stop}")
                
            md.append("\n> [!NOTE]\n> **Interpretation Limits**")
            for lim in p.interpretation_limits:
                md.append(f"> - {lim}")

            md.append("\n### Provenance")
            md.append(f"- **Source IDs:** {', '.join(p.provenance.source_ids) if p.provenance.source_ids else 'None'}")
            md.append(f"- **Member Reflection IDs:** {', '.join(p.provenance.reflection_ids) if p.provenance.reflection_ids else 'None'}")
            md.append(f"- **Actionability Model:** `{p.provenance.actionability_model}`")
            md.append(f"- **Condenser Model:** `{p.provenance.condenser_model}`")
            md.append(f"- **Critic Model:** `{p.provenance.critic_model}`")
            md.append(f"- **Prompt Versions:** `{p.provenance.prompt_versions}`")
            md.append(f"- **Content Hash:** `{p.content_hash}`")

            md.append("\n### Safety and Critic Record")
            md.append(f"- **Safety Flags:** {', '.join(p.safety_flags) if p.safety_flags else 'None'}")
            md.append(f"- **Critic Verdict:** `{p.critic_verdict.value}`")
            md.append(f"- **Critic Notes:** {'; '.join(p.critic_notes) if p.critic_notes else 'None'}")

            # Observations recorded against this protocol
            p_obs = [o for o in self.data.observations if o.protocol_id == p.protocol_id]
            md.append("\n### Program Observations")
            if p_obs:
                md.append("| Observation ID | Completed At | Outcome | Completion Ratio |")
                md.append("|---|---|---|---|")
                for o in p_obs:
                    # Anchor link to observation in Part III
                    md.append(f"| [{o.observation_id[:8]}](#obs-{o.observation_id}) | {o.completed_at} | `{o.outcome.value}` | {o.completion_ratio:.2f} |")
            else:
                # Explicit no observations statement (Requirement 4)
                md.append("*No observations recorded against this protocol.*")
                
            md.append("\n---\n")

        # PART III — OBSERVATIONS AND REFLECTIONS
        md.append("# Part III — Observations and Reflections")
        
        for p in self.data.protocols:
            p_obs = [o for o in self.data.observations if o.protocol_id == p.protocol_id]
            if not p_obs:
                continue
            
            md.append(f"## Observations for: {p.title}")
            
            for o in p_obs:
                md.append(f"### <a id=\"obs-{o.observation_id}\"></a>Observation {o.observation_id}")
                md.append(f"- **Started At:** {o.started_at if o.started_at else 'N/A'}")
                md.append(f"- **Completed At:** {o.completed_at}")
                md.append(f"- **Outcome:** `{o.outcome.value}`")
                md.append(f"- **Completion Ratio:** {o.completion_ratio:.2f}")
                md.append(f"- **Notes:** *\"{o.notes}\"*")
                md.append(f"- **Confounds Observed:** {', '.join(o.confounds_observed) if o.confounds_observed else 'None'}")
                md.append(f"- **Adverse Effects:** {', '.join(o.adverse_effects) if o.adverse_effects else 'None'}")
                md.append(f"- **Deviations:** {', '.join(o.deviations_from_protocol) if o.deviations_from_protocol else 'None'}")
                md.append(f"- **Context:** state=`{o.observer_context.self_reported_state}`, setting=`{o.observer_context.setting}`")
                md.append(f"- **Content Hash:** `{o.content_hash}`")
                
                # Corresponding Reflection
                ref = next((r for r in self.data.reflections if r.observation_id == o.observation_id), None)
                if ref:
                    md.append("\n#### Praxis Reflection")
                    md.append(f"- **Reflection ID:** `{ref.reflection_id}`")
                    md.append(f"- **Summary:** {ref.summary}")
                    md.append(f"- **What Changed:** {', '.join(ref.what_changed) if ref.what_changed else 'None'}")
                    md.append(f"- **What Did Not Change:** {', '.join(ref.what_did_not_change) if ref.what_did_not_change else 'None'}")
                    md.append(f"- **Confounds noted by LLM:** {', '.join(ref.confounds) if ref.confounds else 'None'}")
                    md.append(f"- **Interpretation:** *\"{ref.interpretation}\"*")
                    md.append("- **Epistemic Limits:**")
                    for lim in ref.epistemic_limits:
                        md.append(f"  - {lim}")
                    md.append(f"- **Feedback Recommendation:** `{ref.feedback_recommendation.value}`")
                    md.append(f"- **Recommendation Reason:** *\"{ref.feedback_reason}\"*")
                    md.append(f"- **Human Review Required:** `{ref.human_review_required}`")
                    md.append(f"- **Model/Prompt Version:** `{ref.model}` / `{ref.prompt_version}`")
            md.append("\n---\n")

        # PART IV — CANDIDATES FOR HUMAN REVIEW
        md.append("# Part IV — Candidates for Human Review")
        
        # Adverse outcomes first (Requirement 7)
        adverse_obs = [o for o in self.data.observations if o.outcome == ObservationOutcome.ADVERSE]
        md.append("## 1. Adverse Outcomes")
        if adverse_obs:
            md.append("| Protocol Title | Observation ID | Adverse Effects | Notes |")
            md.append("|---|---|---|---|")
            for o in adverse_obs:
                proto = next((p for p in self.data.protocols if p.protocol_id == o.protocol_id), None)
                p_title = proto.title if proto else "Unknown Protocol"
                md.append(f"| {p_title} | [{o.observation_id[:8]}](#obs-{o.observation_id}) | {', '.join(o.adverse_effects)} | {o.notes} |")
        else:
            md.append("*No adverse outcomes logged.*")

        md.append("\n## 2. Aggregated Feedback Recommendations")
        # Compile aggregates using FeedbackAggregator (Requirements 6, 8)
        aggregator = FeedbackAggregator(self.config)
        
        has_aggregates = False
        for p in self.data.protocols:
            p_obs = [o for o in self.data.observations if o.protocol_id == p.protocol_id]
            if not p_obs:
                continue
            has_aggregates = True
            
            aggregate = aggregator.aggregate_observations(p.keystone_id, p.protocol_id, p_obs)
            
            md.append(f"### Aggregate for: {p.title}")
            md.append(f"- **Total Observations:** {aggregate.observation_count}")
            md.append(f"- **Completion Rate:** {aggregate.completion_rate * 100:.1f}%")
            
            # Format outcomes with denominator (Requirement 8)
            outcome_strings = []
            for outcome, count in aggregate.outcome_counts.items():
                outcome_strings.append(f"{outcome}: {count} of {aggregate.observation_count}")
            md.append(f"- **Outcomes:** {', '.join(outcome_strings)}")
            
            md.append(f"- **Adverse Rate:** {aggregate.adverse_rate * 100:.1f}%")
            md.append(f"- **Common Confounds:** {', '.join(aggregate.common_confounds) if aggregate.common_confounds else 'None'}")
            
            # Phrasing must use only bounded aggregate description, and recommendation
            md.append(f"- **Summary Finding:** *{aggregate.description}*")
            md.append(f"- **Recommendation:** `{aggregate.recommendation.value}`")
            md.append(f"- **Human Review Required:** `{aggregate.human_review_required}`")
            
        if not has_aggregates:
            md.append("*No aggregates compiled (zero observations).*")
            
        md.append("\n---\n")

        # APPENDIX A — NON-ACTIONABLE REGISTER (Mandatory - Requirement 4 & 9)
        md.append("# Appendix A — Non-Actionable Register")
        md.append("> **Note on Prohibited Domains:** In accordance with safety parameters, all Keystone records implicating disease causation, the origin of illness, healing, cure, remedy, recovery, longevity, lifespan, aging, medication, medical treatment, therapy, diagnosis, psychosomatic or mind-body disease mechanisms are strictly pre-filtered and excluded. The complete register of excluded/refused candidates is documented below.")
        
        if self.data.register_entries:
            md.append("| Keystone ID | Concept | Statement | Stage | Rejection Reason | Matched Rules |")
            md.append("|---|---|---|---|---|---|")
            for reg in self.data.register_entries:
                rules = ", ".join(reg.matched_rules) if reg.matched_rules else "None"
                md.append(f"| {reg.keystone_id} | {reg.keystone_concept} | *\"{reg.keystone_statement}\"* | `{reg.stage}` | {reg.reason} | `{rules}` |")
        else:
            md.append("*No records refused.*")

        md.append("\n---\n")

        # APPENDIX B — SAFETY DECISION LOG
        md.append("# Appendix B — Safety Decision Log")
        # Show safety outcomes
        md.append("| Protocol ID | Title | Mode | Risk Tier | Safety Verdict | Matched Prohibited Rules |")
        md.append("|---|---|---|---|---|---|")
        for p in self.data.protocols:
            verdict = "Approved"
            if "requires_human_review" in p.safety_flags:
                verdict = "**Requires Human Review**"
            md.append(f"| {p.protocol_id[:8]} | {p.title} | {p.practice_mode.value} | {p.risk_tier.value} | {verdict} | {', '.join(p.safety_flags) if p.safety_flags else 'None'} |")
        md.append("\n---\n")

        # APPENDIX C — FAILURE LOG
        md.append("# Appendix C — Failure Log")
        if self.data.failures:
            md.append("| Timestamp | Stage | Keystone/Protocol ID | Exception Class | Error Message | Recoverable |")
            md.append("|---|---|---|---|---|---|")
            for f in self.data.failures:
                ref_id = f.keystone_id or f.protocol_id or "N/A"
                md.append(f"| {f.timestamp} | `{f.stage}` | `{ref_id}` | `{f.exception_class}` | {f.error_message} | `{f.recoverable}` |")
        else:
            md.append("*No execution failures logged.*")

        md.append("\n---\n")

        # APPENDIX D — CONFIGURATION SNAPSHOT
        md.append("# Appendix D — Configuration Snapshot")
        md.append("```json")
        md.append(json.dumps(self.data.config_snapshot, indent=2))
        md.append("```")
        md.append("\n---\n")

        # INDEXES
        md.append("# Indexes")
        
        md.append("## Index of Concepts")
        for key in sorted(self.indexes.concepts.keys()):
            targets = ", ".join(f"[{e.label}](#{e.target_id.lower().replace(' ', '-').replace(',', '').replace('.', '') if e.section == 'protocol' else 'obs-' + e.target_id})" for e in self.indexes.concepts[key])
            md.append(f"- **{key}**: {targets}")

        md.append("\n## Index of Practice Modes")
        for key in sorted(self.indexes.modes.keys()):
            targets = ", ".join(f"[{e.label}](#{e.target_id.lower().replace(' ', '-').replace(',', '').replace('.', '')})" for e in self.indexes.modes[key])
            md.append(f"- **{key}**: {targets}")

        md.append("\n## Index of Risk Tiers")
        for key in sorted(self.indexes.risk_tiers.keys()):
            targets = ", ".join(f"[{e.label}](#{e.target_id.lower().replace(' ', '-').replace(',', '').replace('.', '')})" for e in self.indexes.risk_tiers[key])
            md.append(f"- **{key}**: {targets}")

        md.append("\n## Index of Outcomes")
        for key in sorted(self.indexes.outcomes.keys()):
            targets = ", ".join(f"[{e.label}](#obs-{e.target_id})" for e in self.indexes.outcomes[key])
            md.append(f"- **{key}**: {targets}")

        md.append("\n## Index of Keystone IDs")
        for key in sorted(self.indexes.keystone_ids.keys()):
            links = []
            for e in self.indexes.keystone_ids[key]:
                if e.section == "protocol":
                    links.append(f"[{e.label}](#{e.target_id.lower().replace(' ', '-').replace(',', '').replace('.', '')})")
                elif e.section == "observation":
                    links.append(f"[{e.label}](#obs-{e.target_id})")
                elif e.section == "register":
                    links.append(f"[{e.label}](#appendix-a-non-actionable-register)")
            md.append(f"- **{key}**: {', '.join(links)}")

        md.append("\n## Index of Source Traditions")
        for key in sorted(self.indexes.sources.keys()):
            targets = ", ".join(f"[{e.label}](#{e.target_id.lower().replace(' ', '-').replace(',', '').replace('.', '')})" for e in self.indexes.sources[key])
            md.append(f"- **{key}**: {targets}")

        md.append("\n## Index of Confounds")
        for key in sorted(self.indexes.confounds.keys()):
            links = []
            for e in self.indexes.confounds[key]:
                if e.section == "protocol":
                    links.append(f"[{e.label}](#{e.target_id.lower().replace(' ', '-').replace(',', '').replace('.', '')})")
                elif e.section == "observation":
                    links.append(f"[{e.label}](#obs-{e.target_id})")
            md.append(f"- **{key}**: {', '.join(links)}")

        if self.indexes.keywords:
            md.append("\n## Index of Keywords")
            for key in sorted(self.indexes.keywords.keys()):
                targets = ", ".join(f"[{e.label}](#{e.target_id.lower().replace(' ', '-').replace(',', '').replace('.', '')})" for e in self.indexes.keywords[key])
                md.append(f"- **{key}**: {targets}")

        return "\n".join(md)
