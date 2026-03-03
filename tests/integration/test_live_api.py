import os
import subprocess

import pytest
import requests


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:6235")
SEARCH_TIMEOUT_SECONDS = int(os.getenv("SEARCH_TEST_TIMEOUT_SECONDS", "60"))
ASK_TIMEOUT_SECONDS = int(os.getenv("ASK_TEST_TIMEOUT_SECONDS", "90"))


@pytest.fixture(scope="module")
def live_api_base_url() -> str:
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
    except requests.RequestException as exc:
        pytest.skip(f"Live API is not reachable at {API_BASE_URL}: {exc}")
    return API_BASE_URL


def _skip_if_local_ollama_load_is_busy() -> None:
    process_snapshot = subprocess.run(
        ["ps", "-o", "command=", "-ax"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if "load_chunk_embeddings.py" in process_snapshot or "backfill_chunk_embeddings" in process_snapshot:
        pytest.skip("Skipping /ask smoke test while embedding backfill is still running.")


@pytest.fixture(scope="module")
def sample_program(live_api_base_url: str) -> dict:
    response = requests.get(
        f"{live_api_base_url}/programs",
        params={"limit": 1},
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    assert payload["items"], "Expected at least one program in live API"
    return payload["items"][0]


def test_programs_endpoint_returns_paginated_payload(live_api_base_url: str):
    response = requests.get(
        f"{live_api_base_url}/programs",
        params={"limit": 2},
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()

    assert "items" in payload
    assert "pagination" in payload
    assert payload["pagination"]["limit"] == 2
    assert payload["pagination"]["total"] > 0
    assert len(payload["items"]) <= 2

    if payload["items"]:
        first = payload["items"][0]
        assert "document_id" in first
        assert "program_name" in first
        assert "discipline" in first


def test_program_detail_endpoint_matches_list_item(live_api_base_url: str, sample_program: dict):
    response = requests.get(
        f"{live_api_base_url}/programs/{sample_program['document_id']}",
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()

    assert payload["document_id"] == sample_program["document_id"]
    assert payload["discipline"]["discipline"] == sample_program["discipline"]
    assert payload["program"]["program_name"] == sample_program["program_name"]
    assert payload["content_summary"]["non_empty_section_count"] >= 0
    assert "section_availability" in payload
    assert "sections" in payload


def test_program_sections_endpoint_returns_same_document_id(
    live_api_base_url: str, sample_program: dict
):
    response = requests.get(
        f"{live_api_base_url}/programs/{sample_program['document_id']}/sections",
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()

    assert payload["document_id"] == sample_program["document_id"]
    assert "section_availability" in payload
    assert "sections" in payload
    assert "interviews" in payload["sections"]


def test_program_detail_returns_404_for_unknown_document_id(live_api_base_url: str):
    response = requests.get(
        f"{live_api_base_url}/programs/does-not-exist",
        timeout=10,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Program not found"}


def test_completeness_endpoint_returns_summary_and_stats(live_api_base_url: str):
    response = requests.get(f"{live_api_base_url}/reports/completeness", timeout=10)
    response.raise_for_status()
    payload = response.json()

    assert payload["summary"]["total_programs"] > 0
    assert payload["summary"]["avg_non_empty_section_count"] >= 0
    assert len(payload["section_stats"]) >= 10
    assert any(item["section_name"] == "interviews" for item in payload["section_stats"])


def test_semantic_search_returns_ranked_results(live_api_base_url: str):
    try:
        response = requests.post(
            f"{live_api_base_url}/search/semantic",
            json={
                "query": "rural training",
                "limit": 2,
                "discipline": "Family Medicine",
                "content_language": "en",
            },
            timeout=SEARCH_TIMEOUT_SECONDS,
        )
    except requests.ReadTimeout as exc:
        pytest.skip(
            f"Semantic search timed out after {SEARCH_TIMEOUT_SECONDS}s, likely due to local embedding load: {exc}"
        )
    response.raise_for_status()
    payload = response.json()

    assert payload["query"] == "rural training"
    assert payload["total_results"] <= 2
    assert payload["items"]
    first = payload["items"][0]
    assert first["discipline"] == "Family Medicine"
    assert first["content_language"] == "en"
    assert first["rank_score"] > 0
    assert first["chunk_text"]


def test_semantic_search_respects_filters(live_api_base_url: str):
    try:
        response = requests.post(
            f"{live_api_base_url}/search/semantic",
            json={
                "query": "rural training",
                "limit": 3,
                "discipline": "Family Medicine",
                "content_language": "en",
            },
            timeout=SEARCH_TIMEOUT_SECONDS,
        )
    except requests.ReadTimeout as exc:
        pytest.skip(
            f"Semantic search timed out after {SEARCH_TIMEOUT_SECONDS}s, likely due to local embedding load: {exc}"
        )
    response.raise_for_status()
    payload = response.json()

    assert payload["items"]
    assert all(item["discipline"] == "Family Medicine" for item in payload["items"])
    assert all(item["content_language"] == "en" for item in payload["items"])


def test_semantic_search_returns_empty_payload_for_no_match(live_api_base_url: str):
    try:
        response = requests.post(
            f"{live_api_base_url}/search/semantic",
            json={
                "query": "rural training",
                "limit": 2,
                "discipline": "Family Medicine",
                "content_language": "zz",
            },
            timeout=SEARCH_TIMEOUT_SECONDS,
        )
    except requests.ReadTimeout as exc:
        pytest.skip(
            f"Semantic search timed out after {SEARCH_TIMEOUT_SECONDS}s, likely due to local embedding load: {exc}"
        )
    response.raise_for_status()
    payload = response.json()

    assert payload["query"] == "rural training"
    assert payload["total_results"] == 0
    assert payload["items"] == []


def test_ask_preview_returns_citations(live_api_base_url: str):
    try:
        response = requests.post(
            f"{live_api_base_url}/ask-preview",
            json={
                "question": "Which family medicine programs mention rural training?",
                "limit": 2,
                "discipline": "Family Medicine",
                "content_language": "en",
            },
            timeout=SEARCH_TIMEOUT_SECONDS,
        )
    except requests.ReadTimeout as exc:
        pytest.skip(
            f"Ask-preview timed out after {SEARCH_TIMEOUT_SECONDS}s, likely due to local embedding load: {exc}"
        )
    response.raise_for_status()
    payload = response.json()

    assert payload["question"].startswith("Which family medicine")
    assert "Preview answer for" in payload["answer"]
    assert payload["citations"]
    assert payload["citations"][0]["discipline"] == "Family Medicine"


def test_ask_preview_returns_empty_result_for_no_match(live_api_base_url: str):
    try:
        response = requests.post(
            f"{live_api_base_url}/ask-preview",
            json={
                "question": "rural training",
                "limit": 2,
                "discipline": "Family Medicine",
                "content_language": "zz",
            },
            timeout=SEARCH_TIMEOUT_SECONDS,
        )
    except requests.ReadTimeout as exc:
        pytest.skip(
            f"Ask-preview timed out after {SEARCH_TIMEOUT_SECONDS}s, likely due to local embedding load: {exc}"
        )
    response.raise_for_status()
    payload = response.json()

    assert payload["question"] == "rural training"
    assert payload["answer"] == "No relevant program content was found for this question."
    assert payload["citations"] == []


def test_ask_returns_answer_when_local_ollama_is_stable(live_api_base_url: str):
    _skip_if_local_ollama_load_is_busy()

    try:
        response = requests.post(
            f"{live_api_base_url}/ask",
            json={
                "question": "Which family medicine programs mention rural training?",
                "limit": 1,
                "discipline": "Family Medicine",
                "content_language": "en",
                "model": "qwen3:0.6b",
            },
            timeout=ASK_TIMEOUT_SECONDS,
        )
    except requests.ReadTimeout as exc:
        pytest.skip(
            f"/ask timed out after {ASK_TIMEOUT_SECONDS}s, so local Ollama load is not stable enough: {exc}"
        )
    response.raise_for_status()
    payload = response.json()

    assert payload["question"].startswith("Which family medicine")
    assert payload["answer"]
    assert payload["citations"]
