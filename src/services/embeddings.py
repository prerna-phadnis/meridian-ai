from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logger = logging.getLogger(__name__)

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# Gemini embedding model
# text-embedding-004 was shut down by Google on Jan 14, 2026 — replaced by gemini-embedding-001
EMBEDDING_MODEL = "gemini-embedding-001"

# gemini-embedding-001 defaults to 3072 dims, but supports MRL truncation.
# We pin to 768 to stay compatible with your existing Qdrant collection
# (if you ever want better recall, bump this to 1536 or 3072 — but you'll
# need to recreate your Qdrant collection with the new vector size and
# re-embed everything).
EMBEDDING_DIMENSIONS = 768


def generate_embedding(text: str) -> list[float]:
    """
    Converts text to vector using Gemini embedding model
    """
    cleaned = text.replace("\n", " ").strip()

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=cleaned,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=EMBEDDING_DIMENSIONS,
        )
    )

    return response.embeddings[0].values


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Converts multiple texts to vectors.
    Gemini supports batch embedding.
    """
    cleaned = [t.replace("\n", " ").strip() for t in texts]

    embeddings = []

    # Gemini embedding in batches of 20
    batch_size = 20

    for i in range(0, len(cleaned), batch_size):
        batch = cleaned[i:i + batch_size]

        # Send the whole batch in one call instead of looping per-text —
        # gemini-embedding-001 accepts a list for `contents` and returns
        # embeddings in the same order.
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=EMBEDDING_DIMENSIONS,
            )
        )

        embeddings.extend([e.values for e in response.embeddings])

        logger.info(
            f"Embedded batch {i // batch_size + 1} "
            f"({len(embeddings)}/{len(cleaned)})"
        )

    return embeddings