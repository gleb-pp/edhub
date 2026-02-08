FROM python:3.13-slim AS base
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock* /app/

FROM base AS prod
RUN poetry install --without dev --no-root --no-interaction --no-ansi
COPY --chown=appuser:appuser src/ src/
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import socket; s=socket.socket(); s.connect(('127.0.0.1',8000))"
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS test
RUN poetry install --with dev --no-root --no-interaction --no-ansi
COPY --chown=appuser:appuser src/ src/
COPY --chown=appuser:appuser tests/ tests/
USER appuser
