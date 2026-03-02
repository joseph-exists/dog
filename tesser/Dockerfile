FROM ghcr.io/astral-sh/uv:0.9.17 AS uv-bin

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
WORKDIR /app

COPY --from=uv-bin /uv /usr/local/bin/uv
COPY --from=uv-bin /uvx /usr/local/bin/uvx

COPY pyproject.toml uv.lock /app/
COPY src /app/src
COPY examples-other /app/examples-other
COPY scripts/run_tesser_services.sh /app/scripts/run_tesser_services.sh

RUN uv sync --frozen --no-dev --no-install-project
RUN uv pip install --no-cache-dir 'redis>=5.0.0'

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data/jobs /data/artifacts \
    && chmod +x /app/scripts/run_tesser_services.sh \
    && chown -R appuser:appuser /app /data

USER appuser
ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONPATH="/app/src"
ENV TESSERAX_JOBS_ROOT=/data/jobs
ENV TESSERAX_ARTIFACTS_ROOT=/data/artifacts

FROM base AS core
CMD ["python", "-m", "tesserax_service.api", "--host", "0.0.0.0", "--port", "8080", "--jobs-root", "/data/jobs"]

FROM python:3.12-slim AS export
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
WORKDIR /app

COPY --from=uv-bin /uv /usr/local/bin/uv
COPY --from=uv-bin /uvx /usr/local/bin/uvx

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi8 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock /app/
COPY src /app/src
COPY examples-other /app/examples-other
COPY scripts/run_tesser_services.sh /app/scripts/run_tesser_services.sh

RUN uv sync --frozen --no-dev --extra export --no-install-project
RUN uv pip install --no-cache-dir 'redis>=5.0.0'

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data/jobs /data/artifacts \
    && chmod +x /app/scripts/run_tesser_services.sh \
    && chown -R appuser:appuser /app /data

USER appuser
ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONPATH="/app/src"
ENV TESSERAX_JOBS_ROOT=/data/jobs
ENV TESSERAX_ARTIFACTS_ROOT=/data/artifacts

CMD ["sh", "/app/scripts/run_tesser_services.sh"]
