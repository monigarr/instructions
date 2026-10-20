FROM node:24-alpine AS ui-build
WORKDIR /ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci
COPY ui/ ./
RUN npm run build

FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml ./
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY fixtures/ ./fixtures/
COPY --from=ui-build /ui/dist ./ui/dist
# Fixtures are regenerated deterministically from committed sources; a failure
# now fails the build instead of silently shipping a broken image.
RUN pip install --no-cache-dir -e . \
    && python scripts/generate_fixtures.py \
    && python scripts/generate_scale_fixtures.py \
    && useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data/batches \
    && chown -R appuser:appuser /app
USER appuser
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + __import__('os').environ.get('PORT', '8000') + '/health', timeout=3)"
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
