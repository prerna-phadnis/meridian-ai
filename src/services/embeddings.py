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
EMBEDDING_MODEL = "text-embedding-004"
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
            task_type="RETRIEVAL_DOCUMENT"
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

        for text in batch:
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT"
                )
            )

            embeddings.append(response.embeddings[0].values)

        logger.info(
            f"Embedded batch {i // batch_size + 1} "
            f"({len(embeddings)}/{len(cleaned)})"
        )

    return embeddings