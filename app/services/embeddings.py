import logging
from typing import Any, List
import httpx
from app.models.failure import LLMRequestError

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, config: Any):
        self.config = config
        self.timeout = httpx.Timeout(
            connect=5.0,
            read=60.0,
            write=60.0,
            pool=10.0
        )
        self.client = httpx.Client(timeout=self.timeout)

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text using the configured embed model and base URL.
        """
        # If in dry-run or a command not requiring LLM credentials, and key is missing,
        # raise only when called.
        if not self.config.embed_api_key:
            raise LLMRequestError("EMBED_API_KEY is missing. Cannot generate embeddings.")

        url = f"{self.config.embed_base_url.rstrip('/')}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.config.embed_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.config.embed_model,
            "input": text
        }

        try:
            response = self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            response_json = response.json()
            # Standard OpenAI response structure
            return response_json["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise LLMRequestError(f"Embedding request failed: {e}") from e

    def close(self) -> None:
        """Close the underlying HTTPX client."""
        self.client.close()
