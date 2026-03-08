FROM python:3.12.9-slim-bookworm

# Install system deps (ffmpeg + libass for subtitle burn-in, yt-dlp for downloads, nodejs for yt-dlp JS challenges)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libass9 \
        fonts-liberation \
        curl \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir yt-dlp

WORKDIR /app

# Copy everything first, then install
COPY . .
RUN pip install --no-cache-dir .

# Create temp directory for video processing
RUN mkdir -p /tmp/hookcut

# Run as non-root user
RUN groupadd -r hookcut && useradd -r -g hookcut -d /app hookcut \
    && chown -R hookcut:hookcut /app \
    && chown -R hookcut:hookcut /tmp/hookcut
USER hookcut

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

CMD ["bash", "start.sh"]
