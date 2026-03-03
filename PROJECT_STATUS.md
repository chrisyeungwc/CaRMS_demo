# Project Status

## MVP Done

- PostgreSQL local environment via Docker Compose
- PostgreSQL image updated for `pgvector` support
- core source ingestion for:
  - `discipline`
  - `program_master`
  - `program_description_content`
  - `program_document`
  - `document_chunk`
- API-ready SQL view:
  - `program_api_dataset`
- FastAPI endpoints:
  - `GET /health`
  - `GET /disciplines`
  - `GET /programs`
  - `GET /programs/{document_id}`
  - `GET /programs/{document_id}/sections`
  - `GET /reports/completeness`
  - `POST /search/semantic`
  - `POST /ask-preview`
  - `POST /ask`
- Ollama-backed `/ask` working with local model `qwen3:0.6b`
- chunk embedding backfill script added
- README updated for local run instructions
- interview walkthrough draft added

## Current Tradeoffs

- `POST /search/semantic` uses embeddings when chunk vectors are populated, otherwise falls back to PostgreSQL text retrieval
- `POST /ask-preview` is rule-based and intended for demo stability
- `POST /ask` uses LangChain if installed, otherwise Ollama HTTP fallback
- Dagster is not implemented in this repo; for this MVP the data load is effectively one-time/static, so orchestration is kept to `make` targets and Python loader scripts
- no deployment packaging beyond local Docker + local API run

## Good Next Steps

- add more tests for loaders and API responses
- add `/programs/compare`
- add bilingual retrieval evaluation notes
- add a small dashboard or Quarto report for stakeholder-facing output
- optionally introduce Dagster later if the project becomes a recurring pipeline rather than a one-time/static portfolio dataset
