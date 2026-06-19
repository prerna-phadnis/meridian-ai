from src.lib.gemini import generate_text_with_system
from src.services.embeddings import generate_embedding
from src.services.vector_store import search_similar_chunks
import logging

logger = logging.getLogger(__name__)


def answer_question(question: str, paper_id: str) -> dict:
    """
    RAG pipeline using Gemini:
    1. Embed question
    2. Search Qdrant
    3. Build context
    4. Ask Gemini
    5. Return answer + sources
    """

    logger.info(f"RAG start - paper: {paper_id}")

    # Step 1: embed question
    question_embedding = generate_embedding(question)
    logger.info("Question embedded ✅")

    # Step 2: search qdrant
    relevant_chunks = search_similar_chunks(
        query_embedding=question_embedding,
        paper_id=paper_id,
        limit=5
    )

    logger.info(f"Found {len(relevant_chunks)} chunks")

    if not relevant_chunks:
        return {
            "answer": (
                "I couldn't find relevant content in this paper "
                "to answer your question. The paper may still be "
                "processing or there was an issue indexing it."
            ),
            "sources": []
        }

    # Step 3: build context
    context_parts = []

    for chunk in relevant_chunks:
        context_parts.append(
            f"[Page {chunk['page_number']}]\n{chunk['text']}"
        )

    context = "\n\n---\n\n".join(context_parts)

    # Step 4: ask Gemini
    system_prompt = """You are a research assistant helping users understand academic papers.

Rules:
- Answer ONLY based on the provided context
- Always cite the page number like (Page X)
- If the answer is not in the context, say so clearly
- Be concise but accurate
- Use simple language to explain complex concepts"""

    user_prompt = f"""Context from the paper:

{context}

Question: {question}"""

    logger.info("Calling Gemini for answer...")

    answer = generate_text_with_system(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=1000
    )

    logger.info("Gemini response received ✅")

    # Step 5: format sources
    sources = [
        {
            "page_number": c["page_number"],
            "text": c["text"][:200] + "...",
            "score": round(c["score"], 3)
        }
        for c in relevant_chunks
    ]

    return {"answer": answer, "sources": sources}