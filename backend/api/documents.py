# backend/api/documents.py
import urllib.parse
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from backend.core.config import settings

router = APIRouter()


@router.get("/api/files/{file_name:path}")
async def get_pdf(file_name: str):
    """
    Serves clean, official PDFs from RAGData2 only.
    This is what users download when they click source links.
    """
    file_name = urllib.parse.unquote(file_name)
    base_dir = Path(settings.rag_data_dir_abs2)  # ← ONLY RAGData2

    file_path = (base_dir / file_name).resolve()

    # Security: prevent directory traversal
    try:
        file_path.relative_to(base_dir)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"PDF not found: {file_name} (in RAGData2)")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=file_name
    )