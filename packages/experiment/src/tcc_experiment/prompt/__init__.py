"""Módulo de geração de prompts com poluição."""

from tcc_experiment.prompt.generator import (
    GeneratedPrompt,
    PromptGenerator,
    create_generator,
)
from tcc_experiment.prompt.templates import (
    STOCK_PRICE_TEMPLATE,
    DifficultyLevel,
    PromptTemplate,
    get_template,
    get_template_for_difficulty,
    list_templates,
)

__all__ = [
    "DifficultyLevel",
    "GeneratedPrompt",
    "PromptGenerator",
    "PromptTemplate",
    "STOCK_PRICE_TEMPLATE",
    "create_generator",
    "get_template",
    "get_template_for_difficulty",
    "list_templates",
]
