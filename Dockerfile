# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    DOCKER_CONTAINER=true

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy requirements and source code
COPY requirements.txt .
COPY src/ ./src/
COPY static/ ./static/
COPY doc_sage.sqlite* ./
COPY env.example .env
COPY *.md ./

# Create necessary directories
RUN mkdir -p static/persist static/temp_files static/sample_documents data

# Set permissions
RUN chmod -R 755 /app

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run initialization and then the application
CMD ["sh", "-c", "cd src && python init_app.py && streamlit run app.py --server.port=8501 --server.address=0.0.0.0"]
