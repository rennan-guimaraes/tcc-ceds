"""Configurações centralizadas do experimento.

Utiliza pydantic-settings para carregar configurações de variáveis
de ambiente e arquivos .env automaticamente.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações do experimento.

    Attributes:
        database_url: URL de conexão com o PostgreSQL.
        ollama_host: URL do servidor Ollama.
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR).
        default_iterations: Número padrão de iterações por condição.
        pollution_levels: Níveis de poluição a testar (%).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql://tcc:tcc_secret@localhost:5432/llm_experiments",
        description="URL de conexão com o PostgreSQL",
    )

    # Ollama
    ollama_host: str = Field(
        default="http://localhost:11434",
        description="URL do servidor Ollama",
    )

    ollama_num_ctx: int = Field(
        default=32768,
        ge=2048,
        description="Tamanho da janela de contexto do Ollama (tokens)",
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Nível de log",
    )

    # Experiment defaults
    default_iterations: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Número padrão de iterações por condição",
    )

    pollution_levels: list[float] = Field(
        default=[0.0, 20.0, 40.0, 60.0],
        description="Níveis de poluição a testar (%)",
    )

    # Tool calling
    target_tool: str = Field(
        default="get_stock_price",
        description="Nome da tool correta para o cenário",
    )

    # Difficulty
    difficulty_level: str = Field(
        default="neutral",
        description="Nível de dificuldade (neutral, counterfactual, adversarial)",
    )


@lru_cache
def get_settings() -> Settings:
    """Retorna instância singleton das configurações.

    Returns:
        Settings: Instância das configurações carregadas.
    """
    return Settings()
