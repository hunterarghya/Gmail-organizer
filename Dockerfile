FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Gmail OAuth flow
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Gmail tools require a credentials.json in the root
ENV PYTHONUNBUFFERED=1

CMD ["python", "src/main.py"]