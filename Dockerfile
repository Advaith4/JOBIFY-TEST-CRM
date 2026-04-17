# ── Stage 1: Dependency Builder ───────────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /app
COPY requirements.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Production Runtime ───────────────────────────────────────────────
FROM python:3.10-slim

# Non-root user for security
RUN adduser --disabled-password --gecos '' jobify_user

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only what's needed (no venv, no .env, no test files)
COPY ./src ./src
COPY ./agents ./agents
COPY ./tasks ./tasks
COPY ./utils ./utils
COPY ./crew.py ./crew.py
COPY ./static ./static

# Create writable data directory for resume uploads & crewai storage
RUN mkdir -p /app/data && chown -R jobify_user:jobify_user /app

USER jobify_user

EXPOSE 8000

# Production: 2 workers, no reload
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
