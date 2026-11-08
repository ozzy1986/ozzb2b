FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Pull Debian security updates for packages baked into the base image
# (e.g. zlib1g); the CI Trivy gate fails on HIGH/CRITICAL with a fix out.
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src
# pip/setuptools/wheel are build-time only; dropping them keeps their
# vendored copies (msgpack, urllib3, setuptools) out of the runtime image.
RUN pip install --upgrade pip setuptools wheel && pip install . \
    && pip uninstall -y setuptools wheel pip

RUN groupadd --system app && useradd --system --gid app --home /app app \
    && chown -R app:app /app
USER app

CMD ["celery", "-A", "ozzb2b_scraper.tasks", "worker", "--loglevel=INFO", "--concurrency=2"]
