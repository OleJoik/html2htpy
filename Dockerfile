FROM ghcr.io/astral-sh/uv:python3.13-bookworm AS builder
WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN uv sync

FROM python:3.13-slim AS runtime
WORKDIR /app

COPY --from=builder /app/.venv ./.venv
COPY public ./public/
COPY src ./src/

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
