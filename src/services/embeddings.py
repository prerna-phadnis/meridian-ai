from openai import AzureOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

EMBEDDING_MODEL = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")  # ← fixed: was AZURE_OPENAI_DEPLOYMENT_NAME
EMBEDDING_DIMENSIONS = 1536


def generate_embedding(text: str) -> list[float]:
    text = text.replace("\n", " ").strip()

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )

    return response.data[0].embedding


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    cleaned = [t.replace("\n", " ").strip() for t in texts]

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=cleaned
    )

    return [item.embedding for item in response.data]