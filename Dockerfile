FROM python:3.11-slim

# Prevents Python from buffering stdout/stderr and writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source (only the app package to keep image small)
COPY lp_jira_sync_app/ ./lp_jira_sync_app/
# Copy configuration file
COPY config.yaml ./config.yaml

# The application listens on port 8000
EXPOSE 8000

# Start FastAPI app with uvicorn
CMD ["uvicorn", "lp_jira_sync_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
