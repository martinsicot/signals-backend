FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

RUN uv run python manage.py collectstatic --no-input --settings=signals.settings.prod

EXPOSE 8000

CMD ["sh", "-c", "uv run python manage.py migrate --no-input && uv run gunicorn signals.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 60"]
