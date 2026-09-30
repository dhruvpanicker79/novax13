# KSHETRA — single-image deploy: the built UI and the API on one origin.
#
# One origin rather than two services because the UI and the API must agree
# about who you are. Splitting them means CORS, a second cold start, and a
# demo that can half-fail; here the redaction the API performs is the same
# redaction the page is subject to.

# ---- stage 1: build the UI -------------------------------------------------
FROM node:20-alpine AS ui
WORKDIR /ui

COPY frontend/package.json ./
RUN npm install --no-audit --no-fund --loglevel=error

COPY frontend/ ./
# The UI reads pipeline artifacts as static JSON from /data, exactly as it
# does in the local demo build. They are baked in rather than fetched at boot
# so the page renders even if the API is still waking from a cold start.
COPY data/demo/ ./public/data/
RUN npm run build

# ---- stage 2: runtime ------------------------------------------------------
FROM python:3.12-slim AS run
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend
WORKDIR /app

# The API touches none of the numeric stack — it reads JSON and hashes it —
# so the runtime image installs the serving deps only. The engine's numpy /
# scipy / shapely / xgboost requirements stay in requirements.txt for the
# pipeline, which is run offline.
COPY requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt

COPY backend/ ./backend/
COPY api/ ./api/
COPY data/demo/ ./data/demo/
COPY data/export/ ./data/export/
COPY --from=ui /ui/dist ./dist

EXPOSE 8000
# Render injects PORT; the default keeps `docker run -p 8000:8000` working.
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
