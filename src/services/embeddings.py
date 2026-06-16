from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768

def generate_embedding(text: str) -> list[float]:
    text = text.replace("\n", " ").strip()
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text
    )
    return result.embeddings[0].values

def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    cleaned = [t.replace("\n", " ").strip() for t in texts]
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=cleaned
    )
    return [e.values for e in result.embeddings]