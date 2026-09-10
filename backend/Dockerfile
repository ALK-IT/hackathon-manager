FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

FROM base AS production-dependencies

RUN python -m venv /opt/venv

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM production-dependencies AS development-dependencies

COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

FROM base AS runtime-base

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --no-create-home --home-dir /app --shell /usr/sbin/nologin app

WORKDIR /app

COPY --from=production-dependencies /opt/venv /opt/venv
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"]

FROM runtime-base AS development

COPY --from=development-dependencies /opt/venv /opt/venv
USER app

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"]

FROM runtime-base AS runtime

USER app

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn src.main:app --host 0.0.0.0 --port 8000"]
