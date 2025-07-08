from graphiti_core import Graphiti
from graphiti_core.llm_client.gemini_client import GeminiClient, LLMConfig
from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
from graphiti_core.cross_encoder.gemini_reranker_client import GeminiRerankerClient
# from graphiti_core.driver.falkordb_driver import FalkorDriver
from app.core.config import settings

# Google API key configuration
api_key = settings.GOOGLE_API_KEY

# # Falkor driver for graph DB
# falkor_driver = FalkorDriver(
#     host="localhost",
#     port=6379
# )

# Initialize Graphiti with Gemini clients
graphiti = Graphiti(
    uri=settings.NEO4J_URI,
    user=settings.NEO4J_USER, 
    password=settings.NEO4J_PASSWORD,
    llm_client=GeminiClient(
        config=LLMConfig(
            api_key=api_key,
            model="gemini-2.0-flash"
        )
    ),
    embedder=GeminiEmbedder(
        config=GeminiEmbedderConfig(
            api_key=api_key,
            embedding_model="embedding-001"
        )
    ),
    cross_encoder=GeminiRerankerClient(
        config=LLMConfig(
            api_key=api_key,
            model="gemini-2.0-flash-exp"
        )
    )
)

async def build_indices_and_constraints():
    try:
        # Initialize the graph database with graphiti's indices. This only needs to be done once.
        await graphiti.build_indices_and_constraints()
        
    finally:
        # Close the connection
        await graphiti.close()
        print('\nIndices and constraints are built. Connection closed.')
