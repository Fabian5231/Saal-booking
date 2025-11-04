# Multi-stage Build für kleineres Image
FROM python:3.11-slim as builder

# System-Dependencies für PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies installieren
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
RUN pip install --no-cache-dir --user gunicorn

# Production Stage
FROM python:3.11-slim

# System-Dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Non-root User erstellen
RUN useradd -m -u 1000 appuser

# Arbeitsverzeichnis
WORKDIR /app

# Python Dependencies von builder kopieren
COPY --from=builder /root/.local /home/appuser/.local

# App-Code kopieren
COPY --chown=appuser:appuser . .

# Logs und Instance-Verzeichnisse erstellen
RUN mkdir -p logs instance && chown -R appuser:appuser logs instance

# User wechseln
USER appuser

# Path anpassen
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Port exposieren
EXPOSE 8000

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Gunicorn mit optimierten Settings
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "sync", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
