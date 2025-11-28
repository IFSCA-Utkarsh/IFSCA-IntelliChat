import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.core.config import settings
from backend.core.logging import setup_logging
from backend.core.logger import interaction_logger
from backend.api import auth, chat, documents
from backend.rag.vectorstore import get_vectorstore

logger = setup_logging()
app = FastAPI(title="IFSCA IntelliChat", version="Utkarsh", docs_url="/docs")

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    return {"message": "IFSCA IntelliChat backend is running"}

@app.get("/health")
async def health():
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, tags=["auth"])
app.include_router(chat.router, tags=["chat"])
app.include_router(documents.router, tags=["documents"])

@app.on_event("startup")
async def startup_event():
    logger.info("Loading vectorstore and initializing LLM...")
    await asyncio.to_thread(get_vectorstore)
    from backend.rag.rag_pipeline import get_llm, get_reranker
    await get_llm()
    await get_reranker()  # Warm up reranker
    interaction_logger.cleanup_old_logs()
    logger.info("Backend ready")

async def periodic_cleanup():
    while True:
        await asyncio.sleep(3600)
        interaction_logger.cleanup_old_logs()

@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(periodic_cleanup())