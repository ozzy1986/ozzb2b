FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src
RUN pip install --upgrade pip setuptools wheel && pip install .

RUN groupadd --system app && useradd --system --gid app --home /app app \
    && chown -R app:app /app
USER app

CMD ["celery", "-A", "ozzb2b_scraper.tasks", "worker", "--loglevel=INFO", "--concurrency=2"]
