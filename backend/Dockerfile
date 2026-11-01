FROM python:3.11-slim

# Pin the dependency installer; runtime packages come from uv.lock.
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /usr/local/bin/uv
ENV PYTHONUNBUFFERED=1
ENV UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
ENV PATH="/app/.venv/bin:$PATH"
COPY ./app ./app

RUN useradd --uid 10001 --create-home appuser && mkdir -p /data && chown -R appuser:appuser /data /app
ENV DATABASE_URL="sqlite:////data/operations.db"
ENV TELEMETRY_DB="/data/telemetry.db"
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('PORT', '8000') + '/health', timeout=2)" || exit 1
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
