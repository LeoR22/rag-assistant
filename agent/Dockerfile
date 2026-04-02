FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
COPY uv.lock .

RUN uv sync --frozen

COPY src/ ./src/
COPY .env.example .env

EXPOSE 8001

CMD ["uv", "run", "python", "src/main.py"]