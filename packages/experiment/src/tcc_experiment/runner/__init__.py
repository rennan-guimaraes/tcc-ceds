"""Módulo de execução de modelos LLM."""

from tcc_experiment.runner.base import BaseRunner, RunnerResult, ToolCallResult
from tcc_experiment.runner.ollama import ContextPlacement, OllamaRunner

__all__ = [
    "BaseRunner",
    "ContextPlacement",
    "OllamaRunner",
    "RunnerResult",
    "ToolCallResult",
]
