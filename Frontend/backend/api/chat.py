"""Chat endpoint for RAG-based question answering."""
import logging
import threading
import os
import requests
import numpy as np
import re
from fastapi import Depends, APIRouter, HTTPException
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from langchain_huggingface import HuggingFaceEmbeddings
from backend.api.auth import get_current_user
from backend.rag.memory import ConversationMemory
from backend.rag.vectorstore import get_vectorstore
from backend.core.config import settings
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize tokenizer and embeddings
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3-8b")
embeddings = HuggingFaceEmbeddings(
    model_name=settings.EMBED_MODEL,
    model_kwargs={"device": "cuda" if settings.USE_GPU_FOR_EMBEDDINGS and torch.cuda.is_available() else "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

def check_ollama_connection(base_url: str) -> bool:
    try:
        response = requests.get(base_url, timeout=5)
        return response.status_code == 200
    except requests.RequestException as e:
        logger.error(f"Ollama connection check failed: {e}")
        return False

# Initialize LLM
if not check_ollama_connection(settings.OLLAMA_HOST):
    logger.error(f"Cannot connect to Ollama server at {settings.OLLAMA_HOST}.")
    llm = None
else:
    llm = OllamaLLM(model=settings.LLM_MODEL, temperature=0, base_url=settings.OLLAMA_HOST, num_ctx=8192)
    logger.info("Ollama LLM initialized successfully.")

user_memories = {}
memory_lock = threading.Lock()

def get_user_memory(user_id: str):
    with memory_lock:
        if user_id not in user_memories:
            user_memories[user_id] = ConversationMemory(max_turns=5)
        return user_memories[user_id]

def validate_question(question: str) -> bool:
    """Guardrail: Validate question input."""
    if not question or len(question.strip()) == 0:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="Question too long (max 500 characters)")
    if re.search(r"[\;\{\}\<\>]|(ignore\s+previous|execute\s+code)", question, re.IGNORECASE):
        raise HTTPException(status_code=400, detail="Invalid question format")
    return True

def is_relevant_question(question: str, department: str) -> bool:
    """Guardrail: Ensure question relates to IFSCA or department."""
    keywords = ["regulation", "circular", "IFSCA", "payment", "market", department.lower()]
    return any(kw in question.lower() for kw in keywords)

def compute_confidence(docs, answer: str, context_text: str) -> float:
    """Compute confidence score based on retrieval and alignment."""
    if not docs:
        return 0.0
    similarity_scores = [doc.metadata.get("score", 0.5) for doc in docs]
    retrieval_score = np.mean(similarity_scores)
    if not context_text or not answer.strip():
        alignment_score = 0.0
    else:
        try:
            answer_emb = embeddings.embed_query(answer)
            context_emb = embeddings.embed_query(context_text)
            alignment_score = np.dot(answer_emb, context_emb) / (np.linalg.norm(answer_emb) * np.linalg.norm(context_emb))
            alignment_score = max(0.0, min(1.0, alignment_score))
        except Exception as e:
            logger.error(f"Alignment score computation failed: {e}")
            alignment_score = 0.5
    confidence = (0.6 * retrieval_score + 0.4 * alignment_score) * 100
    return round(confidence, 2)

@router.post("/api/chat")
async def chat_endpoint(body: dict, user: dict = Depends(get_current_user)):
    user_id = user["user_id"]
    department = user["department"]
    try:
        question = body.get("question")
        validate_question(question)
        if not is_relevant_question(question, department):
            raise HTTPException(status_code=400, detail="Question must relate to IFSCA regulations or your department")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request body: {str(e)}")

    logger.info(f"User {user_id} from {department} asked: {question}")

    vs = get_vectorstore()
    search_query = f"{question} relevant to {department} department rules, regulations, and circulars"
    try:
        docs_with_scores = vs.similarity_search_with_score(search_query, k=settings.TOP_K, filter={"department": department})
        docs = [doc for doc, score in docs_with_scores]
        for doc, score in docs_with_scores:
            doc.metadata["score"] = 1 - score
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail="Vector search failed")

    sources = [
        {
            "source_id": doc.metadata.get("source_id", "Unknown"),
            "file_name": doc.metadata.get("file_name", "Unknown"),
            "page": doc.metadata.get("page", 1)
        }
        for doc in docs
    ]
    for source in sources:
        if not source["file_name"] or not isinstance(source["page"], int):
            logger.warning(f"Invalid source metadata: {source}")
            source["file_name"] = "Unknown"
            source["page"] = 1
    context_text = "\n\n".join(doc.page_content for doc in docs)

    memory = get_user_memory(user_id)
    history_text = memory.get_history_text()
    logger.info(f"Conversation history for {user_id}: {history_text}")

    template = """You are a helpful assistant for IFSCA-related queries, specializing in rules, regulations, circulars, and master circulars.
The user is from the {department} department. Tailor responses to be relevant to {department} activities, prioritizing department-specific rules and regulations.
Use the provided context and conversation history to answer the question accurately.
Cite specific sections, definitions, or clauses from the context where relevant.
The conversation history contains only user questions, not assistant responses, to keep the prompt concise.
If the question contains references like 'that' or 'it', focus on the *most recent* user question in the conversation history to resolve the reference.
If the context lacks relevant information, respond: 'The provided context does not contain enough information to answer this question.'
If the history is 'None' and the question refers to 'that' or 'it', respond: 'No prior context is available to answer this question.'
Provide neutral, fact-based responses without favoring any department or entity. Base answers strictly on the provided context.

Format your answer in the style of rules, regulations, circulars, or master circulars: Use numbered sections, subsections, clauses, definitions, and short, precise statements. Do not use paragraphs or essays; structure like legal documents with headings like 'Short title and commencement', 'Definitions', etc.

Conversation history (only user questions, most recent is most relevant for references like 'that' or 'it'):
{history}

Context from documents (rules, regulations, circulars):
{context}

Question: {question}

Answer:"""

    prompt = PromptTemplate(
        input_variables=["department", "history", "context", "question"],
        template=template,
    ).format(department=department, history=history_text, context=context_text, question=question)

    prompt_tokens = len(tokenizer.encode(prompt))
    logger.info(f"Prompt token count: {prompt_tokens}")
    if prompt_tokens > 7500:
        logger.warning("Prompt exceeds safe limit; reducing context")
        docs = docs[:5]
        context_text = "\n\n".join(doc.page_content for doc in docs)
        sources = [
            {
                "source_id": doc.metadata.get("source_id", "Unknown"),
                "file_name": doc.metadata.get("file_name", "Unknown"),
                "page": doc.metadata.get("page", 1)
            }
            for doc in docs
        ]
        prompt = PromptTemplate(input_variables=["department", "history", "context", "question"], template=template).format(department=department, history=history_text, context=context_text, question=question)

    logger.debug(f"Prompt sent to LLM:\n{prompt}")

    if llm is None:
        answer_text = "Cannot connect to the LLM server. Please ensure the Ollama server is running."
        logger.error(answer_text)
        confidence = 0.0
    else:
        try:
            res = llm.invoke(prompt)
            answer_text = getattr(res, "content", None) or getattr(res, "response", None) or str(res)
            if not answer_text.strip() or "error" in answer_text.lower():
                answer_text = "The provided context does not contain enough information to answer this question."
                confidence = 0.0
            else:
                confidence = compute_confidence(docs, answer_text, context_text)
            answer_text += "\n\n**Disclaimer**: This response is based on provided documents and is for informational purposes only. It does not constitute legal or professional advice."
        except Exception as e:
            logger.error(f"LLM error: {e}")
            answer_text = "Failed to process the request due to an LLM error."
            confidence = 0.0

    memory.add_exchange(question)
    return {
        "question": question,
        "answer": answer_text.strip(),
        "confidence": confidence,
        "sources": sources
    }