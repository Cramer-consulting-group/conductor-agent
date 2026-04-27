# Conductor Voice Agent
# Production deployment with Gunicorn on Cloud Run / Render / Docker

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

COPY . .

RUN mkdir -p temp_audio logs data/chroma_db

ENV PORT=8080
EXPOSE 8080

# Shell form so ${PORT} is expanded at runtime (Cloud Run / Render inject PORT).
CMD exec gunicorn api.server:app \
    --bind 0.0.0.0:${PORT} \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120
