# Preparing the virtual environment.
FROM python:3.11-bookworm as builder

RUN pip install poetry==1.8.3

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN touch README.md 

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install

# Building the final image and copy the virtual environment.
FROM python:3.11-slim-bookworm as runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    APT_CACHE_DIR=/var/cache/apt

RUN --mount=type=cache,target=$APT_CACHE_DIR apt-get update --fix-missing \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY ./stream_downloader /app/stream_downloader
WORKDIR /app/stream_downloader

ENTRYPOINT ["python", "-m", "download_stream"]