# Task Tracker — backend API image.
# Runs the FastAPI app with Uvicorn. Storage is in-memory, so the container is
# stateless: stopping it clears all tasks (by design for this project's scope).

FROM python:3.12-slim

# Sensible Python defaults for containers.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    APP_ENV=production

WORKDIR /app

# Install dependencies first so this layer is cached across code changes.
COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the application code (see .dockerignore for what is excluded).
COPY app ./app
COPY frontend ./frontend

# Run as a non-root user.
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Liveness probe against the /health endpoint (no curl needed in the image).
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import os,urllib.request,sys; \
url='http://127.0.0.1:%s/health' % os.environ.get('PORT','8000'); \
sys.exit(0 if urllib.request.urlopen(url, timeout=3).status == 200 else 1)"

# Shell form so ${PORT} is expanded at runtime and can be overridden with -e PORT=...
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
