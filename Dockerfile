FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    DJANGO_SETTINGS_MODULE=signals.settings.prod

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

# collectstatic + product thumbnails at build time — dummy SECRET_KEY is fine,
# no DB needed. Thumbnails are baked into the image (Render has no volume).
RUN DJANGO_SECRET_KEY=build-time-placeholder uv run python manage.py collectstatic --no-input \
    && DJANGO_SECRET_KEY=build-time-placeholder uv run python manage.py generate_thumbnails

EXPOSE 8000

CMD ["sh", "-c", "uv run python manage.py migrate --no-input && uv run python manage.py import_price_grid --clear && uv run python manage.py link_product_images && uv run gunicorn signals.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 60"]
