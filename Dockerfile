# CortexMesh — Controller + Agent + Frontend
FROM python:3.11-slim

# Metadados
LABEL maintainer="CortexMesh Contributors"
LABEL description="Universal Platform for Multi-Machine Orchestration"
LABEL version="0.1.0"

# Dependências de sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (cache de camadas)
COPY pyproject.toml README.md ./

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi>=0.100.0 \
    "uvicorn[standard]>=0.20.0" \
    "sqlalchemy[asyncio]>=2.0.0" \
    aiosqlite>=0.19.0 \
    pydantic>=2.0.0 \
    httpx>=0.25.0 \
    typer>=0.9.0 \
    python-multipart>=0.0.6

# Copiar código
COPY cortexmesh ./cortexmesh
COPY apps ./apps

# Instalar o pacote cortexmesh (cria o comando cortexctl)
RUN pip install --no-cache-dir -e .

# Criar diretório de dados
RUN mkdir -p /app/data

# Variáveis de ambiente
ENV DATABASE_URL=sqlite+aiosqlite:///./data/cortexmesh.db
ENV PYTHONUNBUFFERED=1
ENV CORTEXMESH_HOST=0.0.0.0
ENV CORTEXMESH_PORT=8000

# Expor portas
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Comando de arranque
CMD ["cortexctl", "controller", "--host", "0.0.0.0", "--port", "8000"]
