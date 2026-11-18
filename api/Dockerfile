# ---- API image: Python + Flask, served by gunicorn ----
FROM python:3.12-slim

# Don't write .pyc files, flush logs immediately (so `docker compose logs` is live)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements FIRST - this layer is cached as long as requirements.txt
# doesn't change, so code edits don't re-install all packages.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the source code
COPY app.py .

# Security: don't run as root inside the container
RUN useradd --create-home appuser
USER appuser

EXPOSE 5000

# Container-level healthcheck (python is already in the image, no curl needed)
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

# gunicorn = production WSGI server (Flask's built-in server is for dev only)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
