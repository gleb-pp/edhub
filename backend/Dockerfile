FROM python:3.13-slim
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import socket; s=socket.socket(); s.connect(('127.0.0.1',8000))"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
