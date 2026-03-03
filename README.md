# CaRMS Residency Data Platform Demo

Portfolio MVP built from public-facing CaRMS residency program data. The project is structured as a small internal-style data platform using the stack highlighted in the CaRMS Junior Data Scientist posting: `PostgreSQL + Python + SQLModel + FastAPI`, with a retrieval layer for semantic search and Q&A.

This repo is intentionally framed as a small internal-style data platform rather than a chatbot-only demo.

## Live Demo

- Render API docs: `https://carms-api.onrender.com/docs`

Public deployment currently demonstrates:

- browsing and detail APIs
- reporting endpoint
- `POST /search/semantic`
- `POST /ask-preview`

The public deployment demonstrates API design and retrieval behavior rather than full production orchestration.

## What This Project Does

- loads discipline, program metadata, section-level content, and markdown program documents into PostgreSQL
- exposes FastAPI endpoints for program browsing, detail views, and completeness reporting
- chunks long-form markdown program descriptions for retrieval
- supports retrieval-driven search and two Q&A modes:
  - `POST /ask-preview`: stable rule-based preview answer for demo use
  - `POST /ask`: local Ollama-backed answer generation path

## Stack

- `PostgreSQL`
- `Python 3.11`
- `SQLModel / SQLAlchemy`
- `FastAPI`
- `Docker Compose`
- `pytest`
- semantic search / retrieval over document chunks
- local `Ollama` integration for `/ask`

## Data Model

Core tables:

- `discipline`
- `program_master`
- `program_description_content`
- `program_document`
- `document_chunk`

API-ready SQL view:

- `program_api_dataset`

The SQL view abstracts normalized relational tables into an API-consumable dataset for downstream services.

Current dataset size:

- `37` disciplines
- `815` programs
- `25,486` document chunks

## API Surface

- `GET /health`
- `GET /disciplines`
- `GET /programs`
- `GET /programs/{document_id}`
- `GET /programs/{document_id}/sections`
- `GET /reports/completeness`
- `POST /search/semantic`
- `POST /ask-preview`
- `POST /ask`

## Demo Notes

- The hosted demo prioritizes stability and deterministic behavior.
- `POST /ask-preview` is recommended for public testing.
- `POST /ask` is implemented but intended for local experimentation with Ollama.
- Public deployment uses the simpler PostgreSQL retrieval path rather than the local embeddings-backed path.

## Why No Dagster Yet

The original job posting mentions `Dagster`, but this repo does not currently implement it.

That is an intentional scope decision for this MVP:

- the public CaRMS source data used here is effectively static portfolio data
- the ingestion flow is already reproducible with Python loader scripts and `make` targets
- the project prioritizes relational modeling, API design, retrieval behavior, and tests before orchestration

If this project evolved into a recurring or scheduled pipeline, Dagster would be a sensible next step. The design keeps orchestration decoupled from modeling and API layers.

## Local Run

```bash
make db-up
make load-all
make api
```

Local defaults:

- API: `http://127.0.0.1:6235/docs`
- PostgreSQL: `127.0.0.1:5433`

## Testing

Automated checks include:

- unit-style tests in `tests/`
- live integration tests in `tests/integration/`

Recent local status:

- embeddings backfill completed: `25,486 / 25,486`
- `/ask` smoke test succeeded locally
- live integration suite: `11 passed` (API contract and retrieval path validation)

## Local Ollama Path

`POST /ask` is available for local experimentation when Ollama is running and a local model is installed.

Example:

```bash
curl -X POST "http://127.0.0.1:6235/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"Which family medicine programs mention rural training?","limit":2,"model":"qwen3:0.6b"}'
```

Important limitation:

- `/ask` is retrieval-grounded Q&A, not a full warehouse aggregation interface
- count / metadata questions are better handled by dedicated query logic in a later version

## Relevance To The Role

This project demonstrates:

- PostgreSQL data modeling over semi-structured source data
- repeatable Python ingestion scripts
- SQLModel / FastAPI API development
- testing and API contract validation
- retrieval-oriented search and Q&A preparation

The goal is to show practical data platform judgment: reliable data first, downstream AI second.
