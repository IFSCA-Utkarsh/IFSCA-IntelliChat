import asyncio
import time
import numpy as np
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from backend.rag.vectorstore import get_vectorstore
from backend.rag.memory import AsyncConversationMemory
from backend.core.config import settings
import logging
from sentence_transformers import CrossEncoder
import torch

logger = logging.getLogger(__name__)

_llm = None
_llm_lock = asyncio.Lock()
_reranker = None
_reranker_lock = asyncio.Lock()

async def get_llm():
    global _llm
    if _llm is not None:
        return _llm
    async with _llm_lock:
        if _llm is None:
            _llm = OllamaLLM(
                model=settings.LLM_MODEL,
                temperature=0,
                base_url=settings.OLLAMA_HOST,
                num_ctx=8192
            )
            await _llm.ainvoke("Hello")
    return _llm

async def get_reranker():
    global _reranker
    if _reranker is not None:
        return _reranker
    async with _reranker_lock:
        if _reranker is None:
            device = "cuda" if torch.cuda.is_available() and settings.USE_GPU_FOR_EMBEDDINGS else "cpu"
            _reranker = CrossEncoder(settings.RERANK_MODEL, device=device)
    return _reranker

vs = get_vectorstore()

async def _score_faithfulness(llm: OllamaLLM, context: str, question: str, answer: str) -> float:
    faith_template = """Based on the Context, is the Answer factually grounded and relevant to the Question? Respond ONLY with 'Yes' or 'No'.

Context: {context}
Question: {question}
Answer: {answer}

Response:"""
    prompt = PromptTemplate.from_template(faith_template).format(
        context=context[:2000], question=question, answer=answer
    )
    try:
        response = await llm.ainvoke(prompt)
        return 1.0 if "yes" in response.strip().lower() else 0.0
    except Exception as e:
        logger.warning(f"Faithfulness failed: {e}")
        return 0.5

async def create_rag_pipeline(user_id: str, department: str, memory: AsyncConversationMemory):
    llm = await get_llm()

    async def process_query(question: str) -> dict:
        start = time.time()
        search_query = f"{question} {department} department IFSCA regulations circulars"

        try:
            docs_scores = await asyncio.to_thread(
                vs.similarity_search_with_relevance_scores, search_query, k=settings.INITIAL_K
            )
            if not docs_scores:
                docs_scores = await asyncio.to_thread(
                    vs.similarity_search_with_relevance_scores, question, k=settings.INITIAL_K
                )
            docs = [d for d, s in docs_scores]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            docs = []

        # Reranking
        if docs:
            reranker = await get_reranker()
            pairs = [[question, d.page_content] for d in docs]
            rerank_scores = await asyncio.to_thread(reranker.predict, pairs, batch_size=16)
            sorted_idx = np.argsort(rerank_scores)[::-1]
            docs = [docs[i] for i in sorted_idx[:settings.TOP_K]]
            scores = rerank_scores[sorted_idx[:settings.TOP_K]].tolist()
            if scores:
                min_s, max_s = min(scores), max(scores)
                if max_s > min_s:
                    scores = [(s - min_s) / (max_s - min_s) for s in scores]
                else:
                    scores = [1.0] * len(scores)
        else:
            scores = []

        # Build sources — NOW FROM RAGData2!
        sources = []
        for d in docs:
            sources.append({
                "source_id": d.metadata.get("source_id"),
                "file_name": d.metadata["file_name"],
                "page": d.metadata.get("page", 1),
                "download_url": f"/api/files/{d.metadata['file_name']}"
            })

        context = "\n\n".join(d.page_content for d in docs) if docs else ""
        history = await memory.get_history_text()

        template = """You are IFSCA_Utkarsh_RAG_Assistant for the {department} department.

Answer **only** the current question using the Context below.
Do **not** refer to previous topics unless explicitly mentioned.

Context:
{context}

History (user questions only, newest last):
{history}

Current question: {question}
"""

        prompt = PromptTemplate.from_template(template).format(
            department=department, context=context, history=history, question=question
        )

        try:
            response = await llm.ainvoke(prompt)
            answer = response.strip()

            if not docs or "cannot answer" in answer.lower():
                answer = "I cannot answer this based on available regulations. Contact: compliance@ifsca.gov.in"
                confidence = 0.0
            else:
                retrieval_rel = np.mean(scores) if scores else 0.0
                faithfulness = await _score_faithfulness(llm, context, question, answer)

                pages = [s["page"] for s in sources]
                diversity = 1.0 - (np.var(pages) / (np.mean(pages) + 1e-6)) if pages else 0.0
                diversity = max(0.0, min(1.0, diversity))

                confidence = round(0.5 * retrieval_rel + 0.3 * faithfulness + 0.2 * diversity, 3)
                confidence = max(0.0, min(1.0, confidence))
        except Exception as e:
            logger.error(f"LLM failed: {e}")
            answer = "Service temporarily unavailable."
            confidence = 0.0

        await memory.add_exchange(question)

        return {
            "user_id": user_id,
            "department": department,
            "question": question,
            "answer": answer,
            "confidence": float(confidence),
            "sources": sources,
            "time_taken_seconds": round(time.time() - start, 3)
        }

    return process_query