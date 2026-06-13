from openai import AzureOpenAI
from src.services.embeddings import generate_embedding
from src.services.vector_store import search_similar_chunks
from dotenv import load_dotenv

import os
import logging

load_dotenv()

logger = logging.getLogger(__name__)
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

def answer_question(question: str, paper_id: str) -> dict:
    logger.info(f"Answering: '{question}' for paper {paper_id}")

    question_embedding = generate_embedding(question)

    relevant_chunks = search_similar_chunks(
        query_embedding=question_embedding,
        paper_id=paper_id,
        limit=5
    )

    if not relevant_chunks:
        return {
            "answer": (
                "I couldn't find relevant content in this "
                "paper to answer your question."
            ),
            "sources": []
        }

    context_parts = []
    for chunk in relevant_chunks:
        context_parts.append(
            f"[Page {chunk['page_number']}]\n{chunk['text']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    system_prompt = """
You are a research assistant helping users
understand academic papers.

Rules:
- Answer based ONLY on the provided context
- Always mention which page the information comes from
- If the answer is not in the context, say so clearly
- Be concise but thorough
- Use simple language to explain complex concepts
"""

    user_prompt = f"""
Context from the paper:

{context}

Question: {question}

Answer the question based on the context above.
"""

    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,   # ← only change: was "gpt-4o-mini"
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=1000
    )

    answer = response.choices[0].message.content

    sources = [
        {
            "page_number": chunk["page_number"],
            "text": chunk["text"][:200] + "...",
            "score": round(chunk["score"], 3)
        }
        for chunk in relevant_chunks
    ]

    return {
        "answer": answer,
        "sources": sources
    }