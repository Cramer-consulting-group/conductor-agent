FROM python:3.11-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
    ENV PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1 \
        PORT=8080
    WORKDIR /app
    RUN pip install --no-cache-dir --upgrade pip
    COPY requirements.txt ./
    RUN pip install --no-cache-dir -r requirements.txt
    COPY . .
    EXPOSE 8080
    # Shell form is required for $PORT expansion
    CMD gunicorn --bind 0.0.0.0:$PORT api.server:app -k uvicorn.workers.UvicornWorker
