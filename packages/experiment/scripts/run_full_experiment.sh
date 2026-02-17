#!/usr/bin/env bash
# Execucao completa do experimento v3 com dimensoes comparativas
# 2 modelos (qwen3:4b, qwen3:8b), todas as combinacoes de dimensoes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$PROJECT_DIR/experiment_$(date +%Y%m%d_%H%M%S).log"

cd "$PROJECT_DIR"

echo "=== Experimento v3 iniciado em $(date) ===" | tee "$LOG_FILE"
echo "Log: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

uv run tcc-experiment run-all \
  --models "qwen3:4b,qwen3:8b" \
  --pollution-levels "0,20,40,60,80,100" \
  --iterations 20 \
  --hypothesis "H1" \
  2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "=== Experimento v3 finalizado em $(date) ===" | tee -a "$LOG_FILE"
