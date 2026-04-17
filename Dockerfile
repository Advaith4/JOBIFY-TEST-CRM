# Stage 1: Builder
FROM python:3.10-slim AS builder

WORKDIR /app
COPY requirements.txt .

# Install dependencies into a virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.10-slim

# Create a non-root user
RUN adduser --disabled-password --gecos '' jobify_user

WORKDIR /app
# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy source code and static assets
COPY ./src ./src
COPY ./static ./static
COPY ./data ./data 

# Set secure permissions
RUN chown -R jobify_user:jobify_user /app

USER jobify_user

EXPOSE 8000

# Run Uvicorn in production mode
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
