FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
        libglib2.0-0 \
        libgomp1 \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /usr/local/bin/uv

RUN useradd -m -u 1000 user \
    && mkdir -p /home/user/app \
    && chown user:user /home/user/app

USER user
ENV HOME=/home/user \
    PATH="/home/user/.local/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/home/user/app/.venv \
    HF_HOME=/home/user/app/modelos/huggingface \
    TRANSFORMERS_CACHE=/home/user/app/modelos/huggingface \
    HF_HUB_CACHE=/home/user/app/modelos/huggingface/hub

WORKDIR /home/user/app

COPY --chown=user:user pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY --chown=user:user app ./app
COPY --chown=user:user dados ./dados
COPY --chown=user:user scripts ./scripts
RUN uv sync --frozen --no-dev

RUN uv run --frozen --no-dev python scripts/baixar_modelos.py

EXPOSE 7860
CMD ["uv", "run", "--frozen", "--no-dev", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
