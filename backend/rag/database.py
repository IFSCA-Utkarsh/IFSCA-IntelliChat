import os
import shutil
from backend.rag.vectorstore import get_vectorstore
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)

def create_or_get_collection(drop_if_exists: bool = False):
    if drop_if_exists:
        if os.path.exists(settings.CHROMA_PERSIST_DIR):
            shutil.rmtree(settings.CHROMA_PERSIST_DIR)
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)

    return get_vectorstore()