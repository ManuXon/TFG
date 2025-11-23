# Use a lightweight Python image
FROM python:3.11-slim

# --- Install system dependencies for Pillow & WordCloud ---
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    libpng-dev \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend source code (including utils + scripts)
COPY src/ ./src

# Copy entrypoint script from project root
COPY docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x ./docker-entrypoint.sh

# Expose FastAPI port
EXPOSE 8000

# Use entrypoint to run precompute at startup, then launch uvicorn
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
