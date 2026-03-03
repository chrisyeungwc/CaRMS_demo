import requests
from fastapi import HTTPException

from app.api import programs as programs_api
from app.api import search as search_api
from app.main import healthcheck
from app.schemas import AskRequest, SearchRequest
from tests.fakes import FakeResult, FakeSession


PROGRAM_ROW = {
    "document_id": "1503-27447",
    "match_iteration_id": 1503,
    "program_description_id": 27447,
    "discipline_id": 17,
    "discipline": "Family Medicine",
    "school_id": 4,
    "school_name": "University of Alberta",
    "program_site": "Edmonton",
    "program_stream": "Regular",
    "program_stream_name": "Regular Stream",
    "master_program_name": "Family Medicine - Edmonton",
    "program_name": "Family Medicine - Edmonton",
    "raw_program_name": "Family Medicine",
    "content_language": "en",
    "n_program_description_sections": 12,
    "non_empty_section_count": 10,
    "section_text_total_chars": 1234,
    "has_interviews": True,
    "has_return_of_service": False,
    "has_faq": True,
    "source_url": "https://example.test/program",
    "source_document_url": "https://example.test/document",
    "has_program_contacts": True,
    "has_general_instructions": True,
    "has_supporting_documentation_information": True,
    "has_review_process": True,
    "has_selection_criteria": True,
    "has_program_highlights": True,
    "has_program_curriculum": True,
    "has_training_sites": True,
    "has_additional_information": False,
    "has_summary_of_changes": False,
    "program_contacts": "contact",
    "general_instructions": "general",
    "supporting_documentation_information": "docs",
    "review_process": "review",
    "interviews": "interview details",
    "selection_criteria": "criteria",
    "program_highlights": "highlights",
    "program_curriculum": "curriculum",
    "training_sites": "sites",
    "additional_information": None,
    "return_of_service": None,
    "faq": "faq",
    "summary_of_changes": None,
}


SEARCH_RESULT = {
    "chunk_id": 1,
    "document_id": "1503-27447",
    "chunk_index": 0,
    "chunk_text": "This family medicine program includes rural training and community rotations.",
    "chunk_char_count": 79,
    "source_url": "https://example.test/program",
    "content_language": "en",
    "program_name": "Family Medicine - Edmonton",
    "school_name": "University of Alberta",
    "program_site": "Edmonton",
    "program_stream": "Regular",
    "discipline": "Family Medicine",
    "rank_score": 0.91,
}


def test_healthcheck_returns_ok():
    assert healthcheck() == {"status": "ok"}


def test_list_programs_returns_items_and_pagination():
    def handler(sql, params):
        if "count(*)" in sql:
            return FakeResult(scalar_value=1)
        if "from program_api_dataset" in sql:
            assert params["discipline"] == "Family Medicine"
            assert params["limit"] == 1
            return FakeResult(rows=[PROGRAM_ROW])
        return None

    response = programs_api.list_programs(
        discipline="Family Medicine",
        school_name=None,
        content_language=None,
        has_return_of_service=None,
        offset=0,
        limit=1,
        session=FakeSession([handler]),
    )

    assert response.pagination.total == 1
    assert response.items[0].document_id == "1503-27447"
    assert response.filters.discipline == "Family Medicine"


def test_get_program_raises_404_when_missing():
    try:
        programs_api.get_program("missing-doc", session=FakeSession([lambda sql, params: FakeResult(rows=[])]))
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Program not found"
    else:
        raise AssertionError("Expected get_program() to raise HTTPException for missing records")


def test_semantic_search_returns_items(monkeypatch):
    monkeypatch.setattr(search_api, "search_chunks", lambda **kwargs: [SEARCH_RESULT])

    response = search_api.semantic_search(SearchRequest(query="rural training", limit=1), session=object())

    assert response.total_results == 1
    assert response.items[0].document_id == "1503-27447"


def test_ask_preview_returns_rule_based_summary(monkeypatch):
    monkeypatch.setattr(search_api, "search_chunks", lambda **kwargs: [SEARCH_RESULT])

    response = search_api.ask_preview(
        AskRequest(question="Which family medicine programs mention rural training?", limit=3),
        session=object(),
    )

    assert "Preview answer for" in response.answer
    assert response.citations[0].document_id == "1503-27447"


def test_ask_returns_503_when_ollama_unreachable(monkeypatch):
    monkeypatch.setattr(search_api, "search_chunks", lambda **kwargs: [SEARCH_RESULT])

    def raise_request_error(model, prompt):
        raise requests.RequestException("offline")

    monkeypatch.setattr(search_api, "call_ollama_http", raise_request_error)

    try:
        search_api.ask_question(
            AskRequest(question="Which programs mention rural training?", limit=1, model="qwen3:0.6b"),
            session=object(),
        )
    except HTTPException as exc:
        assert exc.status_code == 503
        assert "Ollama is not reachable" in exc.detail
    else:
        raise AssertionError("Expected ask_question() to raise HTTPException when Ollama is down")
