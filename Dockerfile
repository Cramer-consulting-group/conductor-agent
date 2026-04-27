FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# System deps (keep minimal; add build tools only if needed)
RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# IMPORTANT: shell-form so $PORT expands on Cloud Run/Render
CMD uvicorn api.server:app --host 0.0.0.0 --port ${PORT}
