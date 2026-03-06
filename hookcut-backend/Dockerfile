FROM python:3.12-slim

# Install system deps (ffmpeg + libass for subtitle burn-in, yt-dlp for downloads, nodejs for yt-dlp JS challenges)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libass9 \
        fonts-liberation \
        nodejs \
    && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir yt-dlp

WORKDIR /app

# Copy everything first, then install
COPY . .
RUN pip install --no-cache-dir .

# Create temp directory for video processing
RUN mkdir -p /tmp/hookcut

EXPOSE 8000

CMD ["bash", "start.sh"]
