FROM python:3.12-slim

RUN pip install --no-cache-dir uv \
    && useradd --create-home --uid 1000 --shell /usr/sbin/nologin app

WORKDIR /app

COPY --chown=app:app pyproject.toml ./
USER app
RUN uv sync --no-install-project

COPY --chown=app:app . .
RUN uv sync

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
