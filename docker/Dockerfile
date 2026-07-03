# MetaPilot AI - Backend Dockerfile
# Multi-stage build for a production-ready container

# Stage 1: Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Create directories
RUN mkdir -p /app /data /models /logs /cache /plugins /knowledge

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application files
COPY backend/ ./backend/
COPY .env ./
COPY .env.example ./

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # For browser automation (Playwright)
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    # For audio/video processing
    ffmpeg \
    # For image processing
    libjpeg-dev \
    zlib1g-dev \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Install Playwright browsers
RUN playwright install chromium && \
    playwright install-deps chromium

# Create non-root user for security
RUN useradd -m -u 1000 metapilot && \
    mkdir -p /home/metapilot/.cache /home/metapilot/.config && \
    chown -R metapilot:metapilot /home/metapilot /app /data /models /logs /cache /plugins /knowledge

# Switch to non-root user
USER metapilot

# Set permissions
RUN chmod -R 755 /app && \
    chmod -R 755 /data && \
    chmod -R 755 /models && \
    chmod -R 755 /logs && \
    chmod -R 755 /cache && \
    chmod -R 755 /plugins && \
    chmod -R 755 /knowledge

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health').raise_for_status()" || exit 1

# Environment variables
ENV METAPILOT_ENV=production \
    METAPILOT_HOST=0.0.0.0 \
    METAPILOT_PORT=8000 \
    METAPILOT_LOG_LEVEL=INFO \
    METAPILOT_DATA_DIR=/data \
    METAPILOT_MODELS_DIR=/models \
    METAPILOT_LOGS_DIR=/logs \
    METAPILOT_CACHE_DIR=/cache \
    METAPILOT_PLUGINS_DIR=/plugins \
    METAPILOT_KNOWLEDGE_DIR=/knowledge

# Command to run the application
CMD ["python", "backend/main.py"]
