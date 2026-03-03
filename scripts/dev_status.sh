#!/bin/sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "== Docker =="
docker compose -f docker-compose.yaml ps
echo

echo "== API health =="
if curl -s http://127.0.0.1:6235/health >/dev/null 2>&1; then
  curl -s http://127.0.0.1:6235/health
  echo
else
  echo "API not reachable on http://127.0.0.1:6235"
fi
echo

echo "== Ollama models =="
if curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  curl -s http://127.0.0.1:11434/api/tags
  echo
else
  echo "Ollama not reachable on http://127.0.0.1:11434"
fi
