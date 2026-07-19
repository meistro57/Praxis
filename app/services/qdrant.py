import logging
from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from app.models.failure import QdrantWriteError, ConfigurationError

logger = logging.getLogger(__name__)

class QdrantService:
    def __init__(self, config: Any, client: Optional[QdrantClient] = None):
        self.config = config
        if client is not None:
            self.client = client
        else:
            # Detect in-memory test mode or use configured URL/API Key
            url = self.config.qdrant_url
            if url == ":memory:" or not url:
                logger.info("Initializing in-memory Qdrant client.")
                self.client = QdrantClient(":memory:")
            else:
                logger.info(f"Connecting to Qdrant at {url}")
                self.client = QdrantClient(
                    url=url,
                    api_key=self.config.qdrant_api_key or None,
                    timeout=30.0
                )

    def verify_or_create_collections(self) -> None:
        """
        Verify that the necessary collections exist, and create them if missing.
        Validates vector dimension matches config.embed_dim for vector collections.
        """
        # Vector collections
        vector_collections = {
            self.config.praxis_protocols_collection: "Protocols",
            self.config.praxis_reflections_collection: "Reflections",
        }
        for name, label in vector_collections.items():
            self._ensure_vector_collection(name, label)

        # Payload-only collections
        payload_collections = {
            self.config.praxis_observations_collection: "Observations",
            self.config.praxis_failures_collection: "Failures",
        }
        for name, label in payload_collections.items():
            self._ensure_payload_collection(name, label)

    def _ensure_vector_collection(self, collection_name: str, label: str) -> None:
        """Create vector collection if missing, else check dimension compatibility."""
        try:
            exists = self.client.collection_exists(collection_name)
        except AttributeError:
            # Fallback for older qdrant-client versions
            try:
                self.client.get_collection(collection_name)
                exists = True
            except Exception:
                exists = False

        if exists:
            # Validate size
            info = self.client.get_collection(collection_name)
            vector_config = info.config.params.vectors
            
            # Extract size from VectorParams or Dict
            if isinstance(vector_config, dict):
                # Multiple named vectors or single dict config
                if "size" in vector_config:
                    existing_size = vector_config["size"]
                else:
                    existing_size = None
            elif hasattr(vector_config, "size"):
                existing_size = vector_config.size
            else:
                existing_size = None

            if existing_size is not None and existing_size != self.config.embed_dim:
                raise ConfigurationError(
                    f"Dimension mismatch in existing collection '{collection_name}': "
                    f"Found {existing_size}, but config requires {self.config.embed_dim}."
                )
            logger.info(f"Verified vector collection '{collection_name}' ({label}).")
        else:
            logger.info(f"Creating vector collection '{collection_name}' ({label})...")
            try:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.config.embed_dim,
                        distance=qmodels.Distance.COSINE
                    )
                )
            except Exception as e:
                raise QdrantWriteError(f"Failed to create collection '{collection_name}': {e}") from e

    def _ensure_payload_collection(self, collection_name: str, label: str) -> None:
        """Create payload-only collection if missing."""
        try:
            exists = self.client.collection_exists(collection_name)
        except AttributeError:
            try:
                self.client.get_collection(collection_name)
                exists = True
            except Exception:
                exists = False

        if exists:
            logger.info(f"Verified payload-only collection '{collection_name}' ({label}).")
        else:
            logger.info(f"Creating payload-only collection '{collection_name}' ({label})...")
            try:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config={}  # Empty dictionary means no vectors config
                )
            except Exception as e:
                raise QdrantWriteError(f"Failed to create collection '{collection_name}': {e}") from e

    def upsert_point(
        self,
        collection_name: str,
        point_id: str,
        payload: Dict[str, Any],
        vector: Optional[List[float]] = None
    ) -> None:
        """Upsert a single point into a Qdrant collection (guarded by dry_run)."""
        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would upsert point {point_id} to collection '{collection_name}'")
            return

        try:
            # Convert UUID string to standard format or integer
            # Qdrant allows UUID strings or 64-bit integers as point IDs.
            # PointStruct is the standard class.
            point = qmodels.PointStruct(
                id=point_id,
                vector=vector if vector is not None else {},
                payload=payload
            )
            self.client.upsert(
                collection_name=collection_name,
                points=[point],
                wait=True
            )
            logger.debug(f"Upserted point {point_id} into '{collection_name}'.")
        except Exception as e:
            raise QdrantWriteError(f"Failed to upsert point {point_id} into '{collection_name}': {e}") from e

    def get_point_by_id(self, collection_name: str, point_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the payload of a point by ID."""
        try:
            # retrieve is standard for retrieving specific points
            points = self.client.retrieve(
                collection_name=collection_name,
                ids=[point_id],
                with_payload=True,
                with_vectors=False
            )
            if points:
                return points[0].payload
            return None
        except Exception as e:
            logger.error(f"Error retrieving point {point_id} from '{collection_name}': {e}")
            return None

    def scroll_collection(self, collection_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Scroll all points in a collection, returning their payloads."""
        try:
            points, _ = self.client.scroll(
                collection_name=collection_name,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            return [p.payload for p in points if p.payload]
        except Exception as e:
            logger.error(f"Error scrolling collection '{collection_name}': {e}")
            return []

    def close(self) -> None:
        """Closes the client connection."""
        try:
            self.client.close()
        except Exception:
            pass
