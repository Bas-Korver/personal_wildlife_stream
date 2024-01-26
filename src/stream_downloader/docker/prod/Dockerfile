FROM python:3.11-bullseye as builder

RUN pip install poetry==1.7.1

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN touch README.md && poetry install --no-root && rm -rf $POETRY_CACHE_DIR

FROM python:3.11-slim-bullseye as runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY ./ /app/stream_downloader

ENTRYPOINT ["uvicorn", "app.stream_downloader.download_stream:app"]
CMD ["--host", "0.0.0.0", "--port", "8001"]