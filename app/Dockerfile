FROM node:20-alpine AS ui-build
WORKDIR /ui
COPY ui/package.json ui/package-lock.json* ./
RUN npm install
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
RUN pip install --no-cache-dir -e .
RUN python scripts/generate_fixtures.py || true
RUN python scripts/generate_scale_fixtures.py || true
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
EXPOSE 10000
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
