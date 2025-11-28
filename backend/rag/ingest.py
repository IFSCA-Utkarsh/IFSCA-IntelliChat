# backend/rag/ingest.py
import asyncio
import json
import uuid
import logging
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from backend.core.config import settings
from backend.rag.vectorstore import get_vectorstore

logger = logging.getLogger(__name__)
TRACK_FILE = Path("backend/data/ingested_files.json")


def load_tracked():
    if TRACK_FILE.exists():
        try:
            with open(TRACK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read tracking file: {e}")
    return []


async def ingest_folder(drop: bool = False) -> None:
    embed_folder = Path(settings.rag_data_dir_abs)      # RAGData → for embedding
    clean_folder = Path(settings.rag_data_dir_abs2)     # RAGData2 → for display & download

    logger.info(f"Embedding source folder : {embed_folder}")
    logger.info(f"Clean PDF source folder : {clean_folder}")

    if not embed_folder.exists():
        logger.error("RAGData folder does not exist!")
        return

    pdf_files = list(embed_folder.glob("*.pdf"))
    if not pdf_files:
        logger.warning("No PDF files found in RAGData!")
        return

    tracked = [] if drop else load_tracked()
    existing_names = {item["file_name"] for item in tracked}
    new_entries = []
    all_docs = []

    for pdf_path in pdf_files:
        file_name = pdf_path.name

        if file_name in existing_names and not drop:
            logger.info(f"Skipping (already ingested): {file_name}")
            continue

        # Check clean version exists
        clean_path = clean_folder / file_name
        if not clean_path.exists():
            logger.warning(f"Clean PDF missing in RAGData2: {file_name} → will still show filename")

        sid = str(uuid.uuid4())
        try:
            loader = PyPDFLoader(str(pdf_path))
            pages = await asyncio.to_thread(loader.load)

            for page in pages:
                page.metadata.update({
                    "source_id": sid,
                    "file_name": file_name,        # This is what user sees!
                    "page": page.metadata.get("page", 0) + 1,
                })

            all_docs.extend(pages)
            new_entries.append({"file_name": file_name, "source_id": sid})
            logger.info(f"Loaded: {file_name} → {len(pages)} pages")

        except Exception as e:
            logger.error(f"Failed to load {file_name}: {e}")

    if not all_docs:
        logger.info("No new documents to ingest.")
        return

    # Chunk documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(all_docs)
    logger.info(f"Created {len(chunks)} chunks")

    # Add to vector store
    vs = get_vectorstore()
    await asyncio.to_thread(vs.add_documents, chunks)
    logger.info("All chunks successfully added to Chroma vector store!")

    # Save tracking
    final_tracking = new_entries if drop else (tracked + new_entries)
    TRACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACK_FILE, "w", encoding="utf-8") as f:
        json.dump(final_tracking, f, indent=2)

    logger.info("Ingestion complete!")
    logger.info("ALL SOURCE PDFS IN CHAT WILL NOW COME FROM RAGData2")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest PDFs into Chroma")
    parser.add_argument("--drop", action="store_true", help="Re-ingest everything")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        force=True
    )
    asyncio.run(ingest_folder(drop=args.drop))