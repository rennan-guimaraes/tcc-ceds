"""Gerenciamento de conexões com o banco de dados.

Utiliza psycopg3 com connection pooling para eficiência.
"""

from collections.abc import Generator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from tcc_experiment.config import get_settings

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    """Retorna o pool de conexões singleton.

    Cria o pool na primeira chamada e reutiliza nas subsequentes.

    Returns:
        ConnectionPool: Pool de conexões com o PostgreSQL.
    """
    global _pool

    if _pool is None:
        settings = get_settings()
        _pool = ConnectionPool(
            str(settings.database_url),
            min_size=2,
            max_size=10,
            kwargs={"row_factory": dict_row},
        )

    return _pool


@contextmanager
def get_connection() -> Generator[psycopg.Connection, None, None]:
    """Context manager para obter uma conexão do pool.

    Yields:
        Connection: Conexão com o banco de dados.

    Example:
        >>> with get_connection() as conn:
        ...     with conn.cursor() as cur:
        ...         cur.execute("SELECT 1")
        ...         result = cur.fetchone()
    """
    pool = get_pool()
    with pool.connection() as conn:
        yield conn


def close_pool() -> None:
    """Fecha o pool de conexões.

    Deve ser chamado ao finalizar a aplicação.
    """
    global _pool

    if _pool is not None:
        _pool.close()
        _pool = None
