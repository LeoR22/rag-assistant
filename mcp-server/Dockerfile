FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml .
COPY uv.lock .

RUN uv sync --frozen

COPY src/ ./src/
COPY .env.example .env

COPY data/ ./data/

EXPOSE 8000

CMD ["uv", "run", "python", "src/server.py"]
