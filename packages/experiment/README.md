# TCC Experiment - Alucinação em Tool Calling

Experimento controlado para medir degradação de tool calling em LLMs sob contexto poluído.

## Pré-requisitos

- Python 3.11+
- Docker e Docker Compose
- Ollama instalado localmente

---

## Setup Passo a Passo

### 1. Instalar o uv

O `uv` é um gerenciador de pacotes Python ultra-rápido (escrito em Rust).

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Verificar instalação:**
```bash
uv --version
```

> **Nota:** Após instalar, reinicie o terminal ou execute `source ~/.bashrc` (ou `~/.zshrc`).

---

### 2. Clonar e Navegar até o Projeto

```bash
cd /caminho/para/tcc-ceds/packages/experiment
```

---

### 3. Criar Ambiente Virtual e Instalar Dependências

O `uv` gerencia tudo automaticamente:

```bash
# Criar venv e instalar dependências (um comando só!)
uv sync

# Para incluir dependências de desenvolvimento:
uv sync --all-extras
```

Isso irá:
- Criar um `.venv/` automaticamente
- Instalar todas as dependências do `pyproject.toml`
- Criar um `uv.lock` com versões exatas (reprodutibilidade)

---

### 4. Ativar o Ambiente Virtual

```bash
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

**Ou use `uv run` para executar comandos sem ativar:**
```bash
uv run python script.py
uv run pytest
```

---

### 5. Subir a Infraestrutura (Postgres)

```bash
# Na raiz do projeto
cd ../../infra
docker compose up -d

# Verificar se está rodando
docker compose ps
```

**Acessos:**
| Serviço | URL | Credenciais |
|---------|-----|-------------|
| PostgreSQL | `localhost:5432` | `tcc` / `tcc_secret` |
| pgAdmin | `http://localhost:5050` | `admin@local.dev` / `admin` |

---

### 6. Instalar Modelos no Ollama

```bash
# Verificar se Ollama está rodando
ollama --version

# Baixar modelos necessarios (unicos com tool calling + sensiveis ao adversarial)
ollama pull qwen3:4b
ollama pull qwen3:8b

# Listar modelos instalados
ollama list
```

---

### 7. Configurar Variáveis de Ambiente

Criar arquivo `.env` na pasta `packages/experiment/`:

```bash
# .env
DATABASE_URL=postgresql://tcc:tcc_secret@localhost:5432/llm_experiments
OLLAMA_HOST=http://localhost:11434
LOG_LEVEL=INFO
```

---

### 8. Verificar Instalação

```bash
# Rodar testes
uv run pytest

# Verificar tipos
uv run mypy src/

# Verificar linting
uv run ruff check src/

# Formatar código
uv run ruff format src/
```

---

## Comandos Úteis do uv

| Comando | Descrição |
|---------|-----------|
| `uv sync` | Instala dependências do pyproject.toml |
| `uv sync --all-extras` | Instala incluindo dev dependencies |
| `uv add <pacote>` | Adiciona uma dependência |
| `uv add --dev <pacote>` | Adiciona dependência de dev |
| `uv remove <pacote>` | Remove uma dependência |
| `uv run <comando>` | Executa comando no venv |
| `uv lock` | Atualiza o lock file |
| `uv pip list` | Lista pacotes instalados |
| `uv pip show <pacote>` | Mostra info de um pacote |

---

## Estrutura do Projeto

```
packages/experiment/
├── src/
│   └── tcc_experiment/
│       ├── __init__.py
│       ├── cli.py              # Interface de linha de comando
│       ├── config.py           # Configurações
│       ├── database/
│       │   ├── __init__.py
│       │   ├── connection.py   # Pool de conexões
│       │   ├── models.py       # Modelos Pydantic
│       │   └── repository.py   # Operações CRUD
│       ├── prompt/
│       │   ├── __init__.py
│       │   ├── generator.py    # Gerador de prompts poluídos
│       │   └── templates.py    # Templates base
│       ├── runner/
│       │   ├── __init__.py
│       │   ├── base.py         # Interface abstrata
│       │   └── ollama.py       # Implementação Ollama
│       ├── evaluator/
│       │   ├── __init__.py
│       │   └── classifier.py   # Classificador STC/FNC/FWT/FH
│       └── tools/
│           ├── __init__.py
│           ├── registry.py     # Registro de tools
│           └── definitions.py  # Definições das tools
├── tests/
│   ├── __init__.py
│   ├── test_prompt_generator.py
│   ├── test_classifier.py
│   └── conftest.py             # Fixtures pytest
├── scripts/
│   └── run_experiment.py       # Script principal
├── .env                        # Variáveis de ambiente (não commitado)
├── pyproject.toml              # Configuração do projeto
├── uv.lock                     # Lock file (versões exatas)
└── README.md                   # Este arquivo
```

---

## Executando o Experimento

```bash
# Teste rapido (1 execucao)
uv run tcc-experiment quick-test --model qwen3:4b --pollution 40

# Teste rapido nas 3 dificuldades
uv run tcc-experiment quick-test-all --model qwen3:4b --pollution 40

# Experimento customizado
uv run tcc-experiment run \
  --name "Test v3" \
  --models "qwen3:4b,qwen3:8b" \
  --iterations 20 \
  --difficulty adversarial \
  --tool-set expanded \
  --context-placement system

# Experimento completo v3 (todas as combinacoes)
uv run tcc-experiment run-all --dry-run  # ver total primeiro
uv run tcc-experiment run-all --models "qwen3:4b,qwen3:8b" --iterations 20

# Ver resultados
uv run tcc-experiment results --experiment-id <uuid>

# Exportar para CSV
uv run tcc-experiment export --experiment-id <uuid> --output results.csv
```

---

## Troubleshooting

### uv não encontrado após instalação
```bash
# Adicionar ao PATH (adicione ao ~/.zshrc ou ~/.bashrc)
export PATH="$HOME/.cargo/bin:$PATH"
source ~/.zshrc
```

### Erro de conexão com Postgres
```bash
# Verificar se container está rodando
docker ps | grep tcc-ceds-db

# Ver logs
docker logs tcc-ceds-db
```

### Erro de conexão com Ollama
```bash
# Verificar se Ollama está rodando
curl http://localhost:11434/api/tags

# Se não estiver, iniciar
ollama serve
```

### Limpar e reinstalar dependências
```bash
rm -rf .venv uv.lock
uv sync --all-extras
```

---

## Links Úteis

- [uv Documentation](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.ai/)
- [Pydantic](https://docs.pydantic.dev/)
- [Typer](https://typer.tiangolo.com/)
