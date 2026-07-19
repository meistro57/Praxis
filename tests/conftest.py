import pytest
from config import Settings
from app.services.qdrant import QdrantService
from app.services.embeddings import EmbeddingService
from app.services.llm_client import LLMClient
from unittest.mock import MagicMock

@pytest.fixture
def mock_config():
    """Returns a test settings configuration object pointing to memory."""
    return Settings(
        QDRANT_URL=":memory:",
        QDRANT_API_KEY="test_key",
        KEYSTONES_COLLECTION="test_keystones",
        PRAXIS_PROTOCOLS_COLLECTION="test_protocols",
        PRAXIS_OBSERVATIONS_COLLECTION="test_observations",
        PRAXIS_REFLECTIONS_COLLECTION="test_reflections",
        PRAXIS_FAILURES_COLLECTION="test_failures",
        OPENROUTER_API_KEY="test_openrouter",
        EMBED_API_KEY="test_embed",
        MIN_KEYSTONE_CONVERGENCE=0.75,
        REQUIRE_KEYSTONE_CRITIC_PASS=True
    )

@pytest.fixture(autouse=True)
def mock_qdrant_client_singleton(mock_config):
    import qdrant_client
    from unittest.mock import patch
    
    local_client = qdrant_client.QdrantClient(location=":memory:")
    local_client.close = lambda: None
    
    # Pre-create collections
    svc = QdrantService(mock_config)
    svc.client = local_client
    svc.verify_or_create_collections()
    svc._ensure_vector_collection(mock_config.keystones_collection, "Keystones")
    
    with patch("qdrant_client.QdrantClient", return_value=local_client), \
         patch("app.services.qdrant.QdrantClient", return_value=local_client):
        yield local_client

@pytest.fixture
def qdrant_service(mock_config):
    """Returns a QdrantService pointing to the mocked singleton client."""
    svc = QdrantService(mock_config)
    yield svc
    svc.close()

@pytest.fixture
def mock_llm_client(mock_config):
    """Returns a mocked LLM client."""
    client = MagicMock(spec=LLMClient)
    client.config = mock_config
    return client

@pytest.fixture
def mock_embedding_service(mock_config):
    """Returns a mocked embedding service returning a dummy vector."""
    service = MagicMock(spec=EmbeddingService)
    service.config = mock_config
    service.embed_text.return_value = [0.1] * 3072
    return service

@pytest.fixture(autouse=True)
def mock_embeddings_global():
    from unittest.mock import patch
    with patch("app.services.embeddings.EmbeddingService.embed_text", return_value=[0.1] * 3072):
        yield
