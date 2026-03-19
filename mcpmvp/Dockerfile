FROM python:3.12

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

ENV PATH="/app/.venv/bin:$PATH"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

COPY ./pyproject.toml ./uv.lock ./README.md /app/
COPY ./*.py /app/
COPY ./*.yaml /app/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

EXPOSE 8080

CMD ["python", "main.py"]
