FROM python:3.12-slim

# Install system deps (ffmpeg for video processing)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy everything first, then install
COPY . .
RUN pip install --no-cache-dir .

# Create temp directory for video processing
RUN mkdir -p /tmp/hookcut

EXPOSE 8000

CMD ["bash", "start.sh"]
