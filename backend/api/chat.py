import logging
import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from backend.api.auth import get_current_user
from backend.rag.memory import AsyncConversationMemory
from backend.rag.rag_pipeline import create_rag_pipeline
from backend.core.logger import interaction_logger

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory session store
_user_memories: dict[str, AsyncConversationMemory] = {}
_memory_lock = asyncio.Lock()

async def get_user_memory(user_id: str) -> AsyncConversationMemory:
    async with _memory_lock:
        if user_id not in _user_memories:
            _user_memories[user_id] = AsyncConversationMemory(max_turns=5)
        return _user_memories[user_id]

class ChatRequest(BaseModel):
    question: str

@router.post("/api/chat")
async def chat_endpoint(
    body: ChatRequest,
    include_confidence: bool = Query(False, description="Include confidence score"),
    user: dict = Depends(get_current_user)
):
    user_id = user["user_id"]
    department = user["department"]
    question = body.question.strip()

    if not question:
        raise HTTPException(400, "Empty question")

    memory = await get_user_memory(user_id)
    pipeline = await create_rag_pipeline(user_id, department, memory)
    result = await pipeline(question)

    log_entry = {
        "user": user_id,
        "time": datetime.utcnow().isoformat() + "Z",
        "query": result["question"],
        "answer": result["answer"],
        "source": result["sources"],
        "confidence": float(result["confidence"])
    }
    asyncio.create_task(interaction_logger.log_interaction(log_entry))

    response = {
        "question": result["question"],
        "answer": result["answer"],
        "sources": result["sources"]
    }
    if include_confidence:
        response["confidence"] = float(result["confidence"])

    return response