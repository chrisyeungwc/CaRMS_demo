import os

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_db_session
from app.schemas import AskRequest, AskResponse, SearchChunkResult, SearchRequest, SearchResponse
from app.services.search import search_chunks


router = APIRouter(tags=["search"])

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")


def build_preview_answer(question: str, citations: list[SearchChunkResult]) -> str:
    if not citations:
        return "No relevant program content was found for this question."

    intro = f"Preview answer for: {question}"
    summary_lines = []

    for item in citations[:3]:
        snippet = " ".join(item.chunk_text.split())[:240].strip()
        summary_lines.append(
            (
                f"- {item.program_name} ({item.document_id}): "
                f"{snippet}..."
            )
        )

    return "\n".join([intro, *summary_lines])


def build_context(citations: list[SearchChunkResult]) -> str:
    return "\n\n".join(
        [
            (
                f"[{item.document_id} | {item.discipline} | {item.school_name} | "
                f"{item.program_site} | chunk {item.chunk_index}]\n{item.chunk_text}"
            )
            for item in citations
        ]
    )


def build_ask_prompt(question: str, context: str) -> str:
    return (
        "Answer using only the provided CaRMS program content. "
        "Prefer naming the programs or sites that appear in the provided context. "
        "If the context supports only one or a few examples, say that clearly instead of generalizing. "
        "If the context is insufficient to answer fully, say so explicitly. "
        "Keep the answer concise, factual, and grounded in the retrieved content.\n\n"
        "Format:\n"
        "1. Start with a direct answer sentence.\n"
        "2. Then list 1-3 supporting program examples from the context.\n"
        "3. Do not mention information that is not present in the context.\n\n"
        f"Question:\n{question}\n\n"
        f"Context:\n{context}\n"
    )


def call_ollama_http(model: str, prompt: str) -> str:
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("response", "").strip()


@router.post("/search/semantic", response_model=SearchResponse)
def semantic_search(
    request: SearchRequest, session: Session = Depends(get_db_session)
) -> SearchResponse:
    results = search_chunks(
        session=session,
        query=request.query,
        limit=request.limit,
        discipline=request.discipline,
        content_language=request.content_language,
    )
    items = [SearchChunkResult.model_validate(result) for result in results]
    return SearchResponse(query=request.query, total_results=len(items), items=items)


@router.post("/ask-preview", response_model=AskResponse)
def ask_preview(request: AskRequest, session: Session = Depends(get_db_session)) -> AskResponse:
    results = search_chunks(
        session=session,
        query=request.question,
        limit=request.limit,
        discipline=request.discipline,
        content_language=request.content_language,
    )
    citations = [SearchChunkResult.model_validate(result) for result in results]
    answer = build_preview_answer(request.question, citations)
    return AskResponse(question=request.question, answer=answer, citations=citations)


@router.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest, session: Session = Depends(get_db_session)) -> AskResponse:
    results = search_chunks(
        session=session,
        query=request.question,
        limit=request.limit,
        discipline=request.discipline,
        content_language=request.content_language,
    )
    citations = [SearchChunkResult.model_validate(result) for result in results]

    if not citations:
        return AskResponse(
            question=request.question,
            answer="No relevant program content was found for this question.",
            citations=[],
        )

    context = build_context(citations)
    prompt = build_ask_prompt(request.question, context)

    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_ollama import ChatOllama
        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Answer using only the provided CaRMS program content. "
                    "Prefer naming the programs or sites that appear in the provided context. "
                    "If the context supports only one or a few examples, say that clearly instead of generalizing. "
                    "If the context is insufficient to answer fully, say so explicitly. "
                    "Keep the answer concise, factual, and grounded in the retrieved content. "
                    "Start with a direct answer sentence, then list 1-3 supporting program examples from the context.",
                ),
                (
                    "human",
                    "Question:\n{question}\n\nContext:\n{context}",
                ),
            ]
        )
        chain = prompt_template | ChatOllama(model=request.model)
        response = chain.invoke({"question": request.question, "context": context})
        answer = getattr(response, "content", str(response))
    except ImportError:
        try:
            answer = call_ollama_http(request.model, prompt)
        except requests.RequestException as exc:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Ollama is not reachable. Ensure the Ollama app is open and "
                    f"the model '{request.model}' is available."
                ),
            ) from exc

    return AskResponse(question=request.question, answer=answer, citations=citations)
