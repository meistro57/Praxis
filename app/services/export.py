import os
import json
import logging
from typing import Any
from app.services.qdrant import QdrantService
from app.models.failure import ReportGenerationError

logger = logging.getLogger(__name__)

class Exporter:
    def __init__(self, qdrant_service: QdrantService, config: Any):
        self.qdrant_service = qdrant_service
        self.config = config

    def export_collection(self, target: str, output_path: str) -> None:
        """
        Scroll a Qdrant collection and save payload data to output_path.
        target must be 'protocols', 'observations', or 'reflections'.
        """
        if target == "protocols":
            collection_name = self.config.praxis_protocols_collection
        elif target == "observations":
            collection_name = self.config.praxis_observations_collection
        elif target == "reflections":
            collection_name = self.config.praxis_reflections_collection
        else:
            raise ValueError(f"Unknown export target: {target}")

        logger.info(f"Scrolling collection '{collection_name}' for export...")
        payloads = self.qdrant_service.scroll_collection(
            collection_name=collection_name,
            limit=10000
        )

        if self.config.dry_run:
            logger.info(
                f"[DRY RUN] Would write {len(payloads)} items to '{output_path}'"
            )
            return

        # Ensure parent directory exists
        out_dir = os.path.dirname(output_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(payloads, f, indent=2, ensure_ascii=False)
            logger.info(
                f"Successfully exported {len(payloads)} records to '{output_path}'"
            )
        except Exception as e:
            logger.error(f"Failed to write export to '{output_path}': {e}")
            raise ReportGenerationError(f"Export failed: {e}") from e
