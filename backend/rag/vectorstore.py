import logging
from pathlib import Path
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from backend.core.config import settings
import threading

logger = logging.getLogger(__name__)

_embeddings = HuggingFaceEmbeddings(
    model_name=settings.EMBED_MODEL,
    model_kwargs={"device": "cuda" if settings.USE_GPU_FOR_EMBEDDINGS else "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

_vectorstore = None
_init_lock = threading.Lock()

def get_vectorstore():
    """
    Returns a singleton Chroma instance.
    - Loads from persistent dir if exists.
    - Creates a valid empty collection using a dummy document if needed.
    """
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    with _init_lock:
        if _vectorstore is None:
            Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
            _vectorstore = Chroma(
                collection_name=settings.COLLECTION_NAME,
                persist_directory=settings.CHROMA_PERSIST_DIR,
                embedding_function=_embeddings,
                collection_metadata={"hnsw:space": "cosine"}  # For proper cosine similarity
            )
            logger.info(f"Loaded or created Chroma collection at {settings.CHROMA_PERSIST_DIR}")

            # Check if empty and initialize with dummy if needed
            if _vectorstore._collection.count() == 0:
                dummy_doc = Document(page_content="init", metadata={"source": "init"})
                ids = _vectorstore.add_documents([dummy_doc])
                _vectorstore.delete(ids)
                logger.info("Initialized empty Chroma collection")

        return _vectorstore