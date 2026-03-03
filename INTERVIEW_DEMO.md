# Interview Demo Script

## Goal

Use this project demo to show that the portfolio is a small but credible data platform, not just a chatbot.

Suggested framing:

`I used the public CaRMS data to build a PostgreSQL and Python-based internal data API, then prepared a document retrieval layer for semantic search and Q&A.`

## 1. Open With The Problem

Suggested talk track:

`The public CaRMS dataset is useful because it combines relatively clean program metadata with messy long-form text. I treated it as a miniature data platform problem: ingest the raw files, normalize them into PostgreSQL, expose internal-style APIs, and then prepare a retrieval layer for downstream search and Q&A.`

## 2. Show The Source Data

Mention the main files:

- `1503_discipline.xlsx`
- `1503_program_master.xlsx`
- `1503_program_descriptions_x_section.csv`
- `1503_markdown_program_descriptions_v2.json`

Key point:

`I separated structured metadata from long-form document content, instead of trying to solve everything with one document pipeline.`

## 3. Show The Database Design

Tables to mention:

- `discipline`
- `program_master`
- `program_description_content`
- `program_document`
- `document_chunk`

Suggested explanation:

- `discipline` is the lookup table
- `program_master` is the clean metadata backbone
- `program_description_content` stores section-level wide content for APIs and reporting
- `program_document` stores full markdown documents
- `document_chunk` prepares the retrieval layer for search and Q&A

## 4. Show Join Quality

Suggested talk track:

`Before building APIs, I verified that program_master.program_stream_id and program_description_content.program_description_id form a clean one-to-one join for all 815 records. That let me build an API-ready SQL view confidently.`

## 5. Show The Internal API

Suggested endpoints to demo:

- `GET /disciplines`
- `GET /programs?discipline=Family%20Medicine&content_language=en&limit=5`
- `GET /programs/1503-27447`
- `GET /programs/1503-27447/sections`
- `GET /reports/completeness`

Suggested explanation:

`I wanted the API to look like something an internal analyst or application team could actually use, so I kept list endpoints lightweight and put heavy section content into detail endpoints.`

## 6. Show Reporting / Data Quality

Use:

- `GET /reports/completeness`

Suggested talk track:

`This endpoint is there to show data quality and operational reporting, not just retrieval. For example, I can immediately quantify which sections are commonly missing, such as FAQ or return of service.`

## 7. Show Retrieval

Use:

- `POST /search/semantic`

Example:

```bash
curl -X POST "http://127.0.0.1:6235/search/semantic" \
  -H "Content-Type: application/json" \
  -d '{"query":"rural training","limit":3,"discipline":"Family Medicine","content_language":"en"}'
```

Suggested explanation:

`This is the retrieval layer over chunked markdown documents. Right now it uses a lightweight database retrieval approach so the MVP stays stable and testable.`

## 8. Show Q&A Progression

Use:

- `POST /ask-preview`
- `POST /ask`

Suggested explanation:

`I implemented ask-preview first so I could demo end-to-end retrieval and citations without blocking on local LLM dependencies. Then I added /ask, which can use LangChain when installed or fall back to the Ollama HTTP API if a local model is available.`

## 9. Close With Engineering Tradeoffs

Suggested talk track:

`I deliberately kept the first version practical. I prioritized clean ingestion, join validation, API design, and document retrieval before layering on full LLM orchestration. That mirrors how I would build production data infrastructure: reliable data first, downstream AI second.`

`The posting mentions Dagster, but I intentionally did not add it yet because this portfolio dataset is effectively one-time/static. For the MVP, reproducible Python loaders and make targets were enough, and adding orchestration earlier would have increased complexity more than value.`

## 10. If They Ask What Comes Next

Good next steps to mention:

- add pgvector embeddings
- evaluate retrieval quality across English and French content
- add more reporting endpoints
- add automated tests around parsing and API responses
- add a comparison endpoint for programs

## 11. Scope Judgment And Tradeoffs

Use these points if they ask why the project is shaped this way.

### Scope Judgment

- `I treated this as a data platform MVP, not as a full production platform.`
- `I focused first on ingestion quality, relational modeling, join validation, and API shape before adding orchestration or heavier AI layers.`
- `Because the dataset is effectively static portfolio data, I kept orchestration lightweight with Python loaders and make targets instead of introducing Dagster prematurely.`
- `That let me spend time on the parts that actually demonstrate judgment: data structure, API design, retrieval behavior, and testing.`

### Data Modeling Judgment

- `I separated clean metadata from long-form document content instead of forcing everything into one table or one document workflow.`
- `program_master became the metadata backbone, program_description_content supported reporting and section-level APIs, and program_document/document_chunk supported retrieval.`
- `Before building APIs, I validated that the key join between program_master and program_description_content was clean for all records.`

### API Design Tradeoffs

- `I kept list endpoints lightweight and pushed heavier content into detail endpoints, because that is closer to how internal APIs are usually consumed.`
- `I added /reports/completeness to show operational usefulness, not just search demos.`
- `That makes the project look more like internal data infrastructure and less like a thin chatbot wrapper.`

### Search And AI Tradeoffs

- `I did not start with a full LLM-first design. I built retrieval and citations first.`
- `ask-preview came before ask because it is more stable for demo and easier to reason about.`
- `For semantic search, I added embeddings support but preserved fallback behavior so the API still works when the embedding path is not ready.`

### Testing Judgment

- `I added unit-style tests for API shaping and chunking logic, and live integration tests for the running API.`
- `I made the /ask integration test conditional because it depends on local Ollama runtime stability, not only API correctness.`
- `That avoids flaky failures caused by local model contention while still keeping meaningful coverage on the actual service contract.`

### How To Answer “Why Not Dagster Yet?”

- `Because the current dataset is one-time/static, not a daily pipeline.`
- `For this MVP, Dagster would increase architectural surface area without improving the core demonstration much.`
- `If the project became a recurring or scheduled pipeline, Dagster would be a sensible next step, but it was not the highest-value addition for this version.`

### Good Closing Line

- `The main tradeoff throughout the project was choosing infrastructure that matched the actual problem size. I tried to avoid both under-engineering the data model and over-engineering the orchestration.`
