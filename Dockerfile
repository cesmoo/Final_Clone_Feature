FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    chromium \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
[span_1](start_span)RUN pip install --no-cache-dir -r requirements.txt[span_1](end_span)

COPY . .

CMD ["python", "topup.py"]
