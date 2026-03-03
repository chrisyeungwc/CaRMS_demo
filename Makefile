PYTHONPATH_VALUE=.
PYTHON=PYTHONPATH=$(PYTHONPATH_VALUE) python3
API_HOST?=127.0.0.1
API_PORT?=6235
API_BASE_URL?=http://$(API_HOST):$(API_PORT)

.PHONY: db-up db-down load-discipline load-program-master load-content load-documents load-embeddings create-views load-all api dev-up dev-status test test-integration

db-up:
	docker compose -f docker-compose.yaml up -d

db-down:
	docker compose -f docker-compose.yaml down

load-discipline:
	$(PYTHON) scripts/load_discipline.py

load-program-master:
	$(PYTHON) scripts/load_program_master.py

load-content:
	$(PYTHON) scripts/load_program_description_content.py

load-documents:
	$(PYTHON) scripts/load_program_documents.py

load-embeddings:
	$(PYTHON) scripts/load_chunk_embeddings.py

create-views:
	$(PYTHON) scripts/create_api_views.py

load-all: load-discipline load-program-master load-content load-documents create-views

api:
	$(PYTHON) -m uvicorn app.main:app --host $(API_HOST) --port $(API_PORT)

dev-up:
	sh scripts/dev_up.sh

dev-status:
	sh scripts/dev_status.sh

test:
	$(PYTHON) -m pytest

test-integration:
	API_BASE_URL=$(API_BASE_URL) $(PYTHON) -m pytest tests/integration
