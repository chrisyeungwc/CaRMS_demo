import logging

from sqlalchemy import text
from sqlmodel import Session

from app.services.embeddings import EmbeddingError, embed_query, to_vector_literal


logger = logging.getLogger(__name__)


VECTOR_SEARCH_SQL = """
select
    dc.chunk_id,
    dc.document_id,
    dc.chunk_index,
    dc.chunk_text,
    dc.chunk_char_count,
    pd.source_url,
    pd.content_language,
    pm.program_name,
    pm.school_name,
    pm.program_site,
    pm.program_stream,
    d.discipline,
    1 - (dc.embedding <=> cast(:query_embedding as vector)) as rank_score
from document_chunk dc
join program_document pd
    on pd.document_id = dc.document_id
join program_master pm
    on pm.program_stream_id = pd.program_description_id
join discipline d
    on d.discipline_id = pm.discipline_id
where dc.embedding is not null
  and (:discipline is null or d.discipline = :discipline)
  and (:content_language is null or pd.content_language = :content_language)
order by dc.embedding <=> cast(:query_embedding as vector), chunk_char_count desc, document_id, chunk_index
limit :limit
"""


SEARCH_SQL = """
with ranked_chunks as (
    select
        dc.chunk_id,
        dc.document_id,
        dc.chunk_index,
        dc.chunk_text,
        dc.chunk_char_count,
        pd.source_url,
        pd.content_language,
        pm.program_name,
        pm.school_name,
        pm.program_site,
        pm.program_stream,
        d.discipline,
        ts_rank(
            to_tsvector('simple', dc.chunk_text),
            plainto_tsquery('simple', :query)
        ) as rank_score
    from document_chunk dc
    join program_document pd
        on pd.document_id = dc.document_id
    join program_master pm
        on pm.program_stream_id = pd.program_description_id
    join discipline d
        on d.discipline_id = pm.discipline_id
    where (:discipline is null or d.discipline = :discipline)
      and (:content_language is null or pd.content_language = :content_language)
      and (
            to_tsvector('simple', dc.chunk_text) @@ plainto_tsquery('simple', :query)
            or lower(dc.chunk_text) like '%' || lower(:query) || '%'
          )
)
select
    chunk_id,
    document_id,
    chunk_index,
    chunk_text,
    chunk_char_count,
    source_url,
    content_language,
    program_name,
    school_name,
    program_site,
    program_stream,
    discipline,
    rank_score
from ranked_chunks
order by rank_score desc, chunk_char_count desc, document_id, chunk_index
limit :limit
"""


STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "do",
    "does",
    "for",
    "have",
    "how",
    "in",
    "is",
    "it",
    "me",
    "mention",
    "mentions",
    "of",
    "program",
    "programs",
    "show",
    "tell",
    "that",
    "the",
    "what",
    "which",
}


def normalize_query(query: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() or char.isspace() else " " for char in query)
    tokens = [token for token in cleaned.split() if token and token not in STOPWORDS]
    return " ".join(tokens) if tokens else query.strip()


def search_chunks(
    session: Session,
    query: str,
    limit: int = 5,
    discipline: str | None = None,
    content_language: str | None = None,
) -> list[dict]:
    vector_params = {
        "limit": limit,
        "discipline": discipline,
        "content_language": content_language,
    }

    try:
        query_embedding = embed_query(query)
        vector_rows = session.connection().execute(
            text(VECTOR_SEARCH_SQL),
            {**vector_params, "query_embedding": to_vector_literal(query_embedding)},
        ).mappings().all()
        if vector_rows:
            return [dict(row) for row in vector_rows]
    except EmbeddingError as exc:
        logger.info("Embedding search unavailable, falling back to text retrieval: %s", exc)
    except Exception as exc:  # pragma: no cover
        logger.warning("Vector search failed, falling back to text retrieval: %s", exc)

    normalized_query = normalize_query(query)
    text_params = {
        "query": normalized_query,
        "limit": limit,
        "discipline": discipline,
        "content_language": content_language,
    }
    rows = session.connection().execute(text(SEARCH_SQL), text_params).mappings().all()
    return [dict(row) for row in rows]
