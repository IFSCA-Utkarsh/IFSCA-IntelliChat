from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    CHROMA_PERSIST_DIR: str
    COLLECTION_NAME: str = "ifsca_index"
    EMBED_MODEL: str
    RERANK_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    LLM_MODEL: str
    OLLAMA_HOST: str
    USE_GPU_FOR_EMBEDDINGS: bool = False

    RAG_DATA_DIR: str
    RAG_DATA_DIR2: str

    @property
    def rag_data_dir_abs(self) -> str:
        return str((Path(__file__).parent.parent / self.RAG_DATA_DIR).resolve())

    @property
    def rag_data_dir_abs2(self) -> str:
        return str((Path(__file__).parent.parent / self.RAG_DATA_DIR2).resolve())

    CHUNK_SIZE: int = 2000
    CHUNK_OVERLAP: int = 300
    INITIAL_K: int = 20
    TOP_K: int = 5

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    JWT_SECRET: str
    JWT_EXPIRE_MIN: int = 120

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()