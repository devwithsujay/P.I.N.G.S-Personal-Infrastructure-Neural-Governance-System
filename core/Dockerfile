FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY core/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY core/ /app/core/

RUN mkdir -p /app/data /app/workspace /app/persona

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
