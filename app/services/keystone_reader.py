import logging
from typing import Any, Generator
from datetime import datetime, timezone
from app.models.keystone import KeystoneRecord
from app.models.failure import SchemaMappingError, KeystoneReadError, FailureRecord
from app.models.enums import RejectionStage
from app.services.qdrant import QdrantService

logger = logging.getLogger(__name__)

class KeystoneReader:
    def __init__(self, qdrant_service: QdrantService, config: Any):
        self.qdrant_service = qdrant_service
        self.config = config

    def stream_keystones(self) -> Generator[KeystoneRecord, None, None]:
        """
        Scroll through the configured Keystone collection in Qdrant,
        adapting each point into a KeystoneRecord. Reports schema errors to praxis_failures.
        """
        collection_name = self.config.keystones_collection
        logger.info(f"Streaming Keystones from collection '{collection_name}'...")
        
        try:
            offset = None
            while True:
                # scroll returns (List[Record], Optional[Offset])
                res = self.qdrant_service.client.scroll(
                    collection_name=collection_name,
                    limit=100,
                    with_payload=True,
                    with_vectors=False,
                    offset=offset
                )
                
                # Check results
                if not res or len(res) < 2:
                    break
                points, next_offset = res
                
                if not points:
                    break

                for point in points:
                    point_id_str = str(getattr(point, "id", "unknown"))
                    try:
                        record = KeystoneRecord.from_qdrant(point, self.config)
                        # Log warning if any schema warnings are present
                        if record.schema_warnings:
                            logger.warning(
                                f"Keystone {record.id} mapped with schema warnings: {record.schema_warnings}"
                            )
                        yield record
                    except SchemaMappingError as e:
                        logger.error(f"Schema mapping error for point '{point_id_str}': {e}")
                        
                        # Create FailureRecord for this record mapping failure
                        fail_rec = FailureRecord(
                            stage=RejectionStage.FAILURE.value,
                            keystone_id=point_id_str,
                            exception_class="SchemaMappingError",
                            error_message=str(e),
                            timestamp=datetime.now(timezone.utc).isoformat(),
                            recoverable=True
                        )
                        
                        # Upsert directly to praxis_failures collection
                        self.qdrant_service.upsert_point(
                            collection_name=self.config.praxis_failures_collection,
                            point_id=fail_rec.failure_id,
                            payload=fail_rec.model_dump()
                        )

                if next_offset is None:
                    break
                offset = next_offset

        except Exception as e:
            if isinstance(e, SchemaMappingError):
                raise
            logger.error(f"Keystone read operation failed: {e}")
            raise KeystoneReadError(
                f"Failed to read from Keystone collection '{collection_name}': {e}"
            ) from e
