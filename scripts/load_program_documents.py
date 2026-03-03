import json
from datetime import datetime
from pathlib import Path

from sqlmodel import delete, select

from app.db import create_db_and_tables, get_session
from app.models import DocumentChunk, ProgramDocument


SOURCE_PATH = (
    Path(__file__).resolve().parents[1]
    / "source"
    / "1503_markdown_program_descriptions_v2.json"
)

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150


def parse_document_identity(document_id: str) -> tuple[int, int]:
    match_iteration_id, program_description_id = document_id.split("|")
    return int(match_iteration_id), int(program_description_id)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    normalized = text.strip()
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunk = normalized[start:end]

        if end < len(normalized):
            split_idx = max(chunk.rfind("\n\n"), chunk.rfind("\n"), chunk.rfind(". "))
            if split_idx > chunk_size // 2:
                end = start + split_idx + 1
                chunk = normalized[start:end]

        chunks.append(chunk.strip())

        if end >= len(normalized):
            break

        start = max(end - overlap, start + 1)

    return [chunk for chunk in chunks if chunk]


def iter_program_documents():
    documents = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))

    for record in documents:
        document_id = record["id"]
        match_iteration_id, program_description_id = parse_document_identity(document_id)
        metadata = record.get("metadata", {})
        content = record.get("page_content", "").strip()

        if not content:
            continue

        yield {
            "document_id": document_id.replace("|", "-"),
            "match_iteration_id": match_iteration_id,
            "program_description_id": program_description_id,
            "source_url": metadata.get("source", ""),
            "content_language": "fr" if "Jumelage" in content or "Programme" in content else "en",
            "content": content,
            "content_length": len(content),
        }


def upsert_program_documents() -> tuple[int, int]:
    create_db_and_tables()
    documents_upserted = 0
    chunks_inserted = 0

    with get_session() as session:
        for row in iter_program_documents():
            existing = session.exec(
                select(ProgramDocument).where(ProgramDocument.document_id == row["document_id"])
            ).first()

            if existing is None:
                session.add(ProgramDocument(**row))
            else:
                existing.match_iteration_id = row["match_iteration_id"]
                existing.program_description_id = row["program_description_id"]
                existing.source_url = row["source_url"]
                existing.content_language = row["content_language"]
                existing.content = row["content"]
                existing.content_length = row["content_length"]
                existing.updated_at = datetime.utcnow()

                session.exec(
                    delete(DocumentChunk).where(DocumentChunk.document_id == row["document_id"])
                )

            # Ensure the parent program_document row exists before inserting child chunks.
            session.flush()

            for idx, chunk in enumerate(chunk_text(row["content"])):
                session.add(
                    DocumentChunk(
                        document_id=row["document_id"],
                        chunk_index=idx,
                        chunk_text=chunk,
                        chunk_char_count=len(chunk),
                    )
                )
                chunks_inserted += 1

            documents_upserted += 1

        session.commit()

    return documents_upserted, chunks_inserted


if __name__ == "__main__":
    document_count, chunk_count = upsert_program_documents()
    print(
        f"Loaded {document_count} program documents and {chunk_count} chunks from {SOURCE_PATH.name}"
    )
