# ── Stage 1: Build dependencies ─────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md ./
COPY cyberresilient/ cyberresilient/
RUN pip install --no-cache-dir --prefix=/install .

# ── Stage 2: Production image ───────────────────────────────
FROM python:3.11-slim

LABEL maintainer="Osayande <osayande-infosec>" \
      description="CyberResilient - Enterprise Cybersecurity Training Toolkit" \
      version="2.0.0"

# Install curl for healthcheck, then clean up
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (security best practice)
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create directories and set ownership
RUN mkdir -p /app/reports /app/instance && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Initialise DB with seed data on first run
RUN python -m cyberresilient.cli init --seed || true

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true", \
    "--browser.gatherUsageStats=false"]
