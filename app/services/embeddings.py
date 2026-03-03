import os

import requests


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")


class EmbeddingError(RuntimeError):
    pass


def _extract_embeddings(payload: dict) -> list[list[float]]:
    embeddings = payload.get("embeddings")
    if isinstance(embeddings, list) and embeddings:
        return embeddings
    raise EmbeddingError("Embedding response did not include embeddings.")


def embed_texts(texts: list[str], model: str | None = None) -> list[list[float]]:
    selected_model = model or OLLAMA_EMBED_MODEL
    if not texts:
        return []

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            json={"model": selected_model, "input": texts},
            timeout=120,
        )
        response.raise_for_status()
        return _extract_embeddings(response.json())
    except requests.RequestException as exc:
        raise EmbeddingError(
            f"Ollama embedding request failed for model '{selected_model}'."
        ) from exc


def embed_query(text: str, model: str | None = None) -> list[float]:
    embeddings = embed_texts([text], model=model)
    if not embeddings or not embeddings[0]:
        raise EmbeddingError("No embedding returned for query.")
    return embeddings[0]


def to_vector_literal(values: list[float]) -> str:
    if not values:
        raise EmbeddingError("Cannot build a vector literal from an empty embedding.")
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"
