"""Módulo de execução de modelos LLM."""

from tcc_experiment.runner.base import BaseRunner, RunnerResult, ToolCallResult
from tcc_experiment.runner.ollama import OllamaRunner

__all__ = [
    "BaseRunner",
    "OllamaRunner",
    "RunnerResult",
    "ToolCallResult",
]
