FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-agentbeats.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements-agentbeats.txt

# Copy application code
COPY . .

# Make run.sh executable
RUN chmod +x run.sh

# Expose port (Cloud Run will set PORT env var)
ENV PORT=8080

# Run the green agent directly
CMD ["./run.sh"]
