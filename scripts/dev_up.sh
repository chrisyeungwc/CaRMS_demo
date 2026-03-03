#!/bin/sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "Starting CaRMS PostgreSQL..."
docker compose -f docker-compose.yaml up -d

echo "CaRMS API"
echo "Run this in a separate terminal if the API is not already running:"
echo "make api"
echo
echo "Docs: http://127.0.0.1:6235/docs"
echo "Health: http://127.0.0.1:6235/health"
echo
echo "For /ask, ensure Ollama is running:"
echo "ollama serve"
