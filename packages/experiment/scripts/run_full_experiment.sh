#!/usr/bin/env bash
# Execucao completa do experimento com num_ctx corrigido
# 7 modelos (3-8B) de 4 providers, 6 niveis de poluicao, 20 iteracoes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$PROJECT_DIR/experiment_$(date +%Y%m%d_%H%M%S).log"

cd "$PROJECT_DIR"

echo "=== Experimento iniciado em $(date) ===" | tee "$LOG_FILE"
echo "Log: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

uv run tcc-experiment run \
  --name "Experimento H1+H2 - multi-provider" \
  --models "qwen3:4b,qwen3:8b,qwen2.5:7b,llama3.1:8b,llama3.2:3b,phi4-mini,granite3.2:8b" \
  --pollution-levels "0,20,40,60,80,100" \
  --iterations 20 \
  --hypothesis "H1" \
  --no-db \
  2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "=== Experimento finalizado em $(date) ===" | tee -a "$LOG_FILE"
