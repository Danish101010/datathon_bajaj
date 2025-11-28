FROM python:3.11-slim

LABEL maintainer="Medical Bill Extraction API"

RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENV PORT=8000
ENV PYTHONUNBUFFERED=1

CMD uvicorn api:app --host 0.0.0.0 --port ${PORT} --workers 1
