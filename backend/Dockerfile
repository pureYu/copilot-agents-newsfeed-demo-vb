FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed by lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
        libxml2 \
        libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies before copying the full source so Docker
# can cache this layer independently of application code changes.
COPY pyproject.toml .
# Create a minimal package stub so pip can install in editable mode
RUN mkdir -p app && touch app/__init__.py
RUN pip install --no-cache-dir -e .

# Copy the rest of the application
COPY . .

# Persistent data directory for the SQLite database
RUN mkdir -p /app/data

# Strip Windows-style CRLF line endings from the entrypoint (safe no-op on LF files)
# then make it executable.
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
