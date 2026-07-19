from typing import Dict, List
from pydantic import BaseModel

class BookManifest(BaseModel):
    book_id: str            # stable ID from content hash of included record IDs
    generated_at: str       # ISO-8601 UTC
    scope: str              # "all" | "run" | "since"
    run_ids: List[str]
    keystone_collection: str
    protocol_ids: List[str]
    observation_ids: List[str]
    reflection_ids: List[str]
    register_entry_count: int
    counts: Dict[str, int]  # the §18 funnel
    config_snapshot: Dict   # redacted
    content_hash: str
