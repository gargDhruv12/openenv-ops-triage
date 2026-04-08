FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY . /app
RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import os,urllib.request; urllib.request.urlopen(f\"http://localhost:{os.getenv('PORT','7860')}/health\")"

CMD ["sh", "-c", "uvicorn server.app:app --host 0.0.0.0 --port ${PORT:-7860}"]
