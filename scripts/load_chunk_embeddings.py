from sqlalchemy import text

from app.db import create_db_and_tables, get_session
from app.services.embeddings import OLLAMA_EMBED_MODEL, embed_texts, to_vector_literal


BATCH_SIZE = 32


SELECT_PENDING_CHUNKS_SQL = """
select chunk_id, chunk_text
from document_chunk
where embedding is null
order by chunk_id
limit :limit
"""


UPDATE_CHUNK_EMBEDDING_SQL = """
update document_chunk
set embedding = cast(:embedding as vector)
where chunk_id = :chunk_id
"""


COUNT_PENDING_CHUNKS_SQL = """
select count(*) as pending_count
from document_chunk
where embedding is null
"""


def backfill_chunk_embeddings(batch_size: int = BATCH_SIZE) -> int:
    create_db_and_tables()
    updated = 0

    with get_session() as session:
        pending = session.connection().execute(text(COUNT_PENDING_CHUNKS_SQL)).scalar_one()
        print(
            f"Embedding model: {OLLAMA_EMBED_MODEL}. Pending document_chunk rows: {pending}"
        )

        while True:
            rows = session.connection().execute(
                text(SELECT_PENDING_CHUNKS_SQL), {"limit": batch_size}
            ).mappings().all()
            if not rows:
                break

            embeddings = embed_texts([row["chunk_text"] for row in rows])
            for row, embedding in zip(rows, embeddings, strict=True):
                session.connection().execute(
                    text(UPDATE_CHUNK_EMBEDDING_SQL),
                    {
                        "chunk_id": row["chunk_id"],
                        "embedding": to_vector_literal(embedding),
                    },
                )
                updated += 1

            session.commit()
            print(f"Embedded {updated} chunks so far...")

    return updated


if __name__ == "__main__":
    count = backfill_chunk_embeddings()
    print(f"Updated embeddings for {count} chunks.")
