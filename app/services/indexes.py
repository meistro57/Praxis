import os
from typing import Dict, List, Optional
from app.models.protocol import PraxisProtocol
from app.models.observation import ObservationRecord
from app.models.reflection import PraxisReflection
from app.models.failure import RegisterEntry

class IndexEntry:
    def __init__(self, label: str, target_id: str, section: str):
        self.label = label
        self.target_id = target_id  # protocol_id, observation_id, register_entry (keystone_id)
        self.section = section      # 'protocol', 'observation', 'register'

class PraxisIndexes:
    def __init__(self):
        self.concepts: Dict[str, List[IndexEntry]] = {}
        self.modes: Dict[str, List[IndexEntry]] = {}
        self.risk_tiers: Dict[str, List[IndexEntry]] = {}
        self.outcomes: Dict[str, List[IndexEntry]] = {}
        self.keystone_ids: Dict[str, List[IndexEntry]] = {}
        self.sources: Dict[str, List[IndexEntry]] = {}
        self.confounds: Dict[str, List[IndexEntry]] = {}
        self.keywords: Dict[str, List[IndexEntry]] = {}

    def build(
        self,
        protocols: List[PraxisProtocol],
        observations: List[ObservationRecord],
        reflections: List[PraxisReflection],
        register_entries: List[RegisterEntry],
        index_terms_path: Optional[str] = None
    ) -> None:
        # Reset indexes
        self.concepts.clear()
        self.modes.clear()
        self.risk_tiers.clear()
        self.outcomes.clear()
        self.keystone_ids.clear()
        self.sources.clear()
        self.confounds.clear()
        self.keywords.clear()

        # Helper to add entries
        def add_entry(index_dict: Dict[str, List[IndexEntry]], key: str, entry: IndexEntry):
            clean_key = key.strip()
            if not clean_key:
                return
            if clean_key not in index_dict:
                index_dict[clean_key] = []
            # Avoid duplicate target IDs under same key
            if not any(e.target_id == entry.target_id for e in index_dict[clean_key]):
                index_dict[clean_key].append(entry)

        # 1. Index protocols
        for p in protocols:
            p_label = f"Protocol: {p.title}"
            
            # Concepts
            add_entry(self.concepts, p.keystone_concept, IndexEntry(p_label, p.protocol_id, "protocol"))
            
            # Modes
            practice_mode_str = getattr(p.practice_mode, "value", str(p.practice_mode))
            add_entry(self.modes, practice_mode_str, IndexEntry(p_label, p.protocol_id, "protocol"))
            
            # Risk Tiers
            risk_tier_str = f"Risk Tier {getattr(p.risk_tier, 'value', str(p.risk_tier))}"
            add_entry(self.risk_tiers, risk_tier_str, IndexEntry(p_label, p.protocol_id, "protocol"))
            
            # Keystone IDs
            add_entry(self.keystone_ids, p.keystone_id, IndexEntry(p_label, p.protocol_id, "protocol"))
            
            # Source traditions
            for src in p.provenance.source_ids:
                add_entry(self.sources, src, IndexEntry(p_label, p.protocol_id, "protocol"))
                
            # Confounds to notice
            for conf in p.confounds_to_notice:
                add_entry(self.confounds, conf, IndexEntry(p_label, p.protocol_id, "protocol"))

        # 2. Index observations
        for obs in observations:
            obs_label = f"Observation: {obs.observation_id[:8]}"
            
            # Outcomes
            outcome_str = getattr(obs.outcome, "value", str(obs.outcome))
            add_entry(self.outcomes, outcome_str, IndexEntry(obs_label, obs.observation_id, "observation"))
            
            # Keystone IDs
            add_entry(self.keystone_ids, obs.keystone_id, IndexEntry(obs_label, obs.observation_id, "observation"))
            
            # Confounds observed
            for conf in obs.confounds_observed:
                add_entry(self.confounds, conf, IndexEntry(obs_label, obs.observation_id, "observation"))

        # 3. Index register entries
        for reg in register_entries:
            reg_label = f"Refusal: {reg.keystone_concept}"
            add_entry(self.keystone_ids, reg.keystone_id, IndexEntry(reg_label, reg.keystone_id, "register"))

        # 4. Optional curated keyword index
        if index_terms_path and os.path.exists(index_terms_path):
            try:
                with open(index_terms_path, "r", encoding="utf-8") as f:
                    keywords_to_find = [line.strip().lower() for line in f if line.strip()]
                
                # Check for keywords in statement/hypothesis/title
                for p in protocols:
                    p_label = f"Protocol: {p.title}"
                    combined_text = f"{p.title} {p.working_hypothesis} {p.keystone_statement} {p.keystone_concept}".lower()
                    for kw in keywords_to_find:
                        if kw in combined_text:
                            add_entry(self.keywords, kw, IndexEntry(p_label, p.protocol_id, "protocol"))
            except Exception:
                # Log error but don't fail report compilation completely
                pass
