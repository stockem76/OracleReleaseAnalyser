FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py oracle_scraper.py ./

# Cache lives here; mount a volume at this path to persist across restarts
# and to let an external ingestion job read cache.json directly.
ENV READINESS_DATA_DIR=/data
ENV READINESS_REFRESH_HOURS=6
VOLUME ["/data"]

EXPOSE 8000

CMD ["python", "server.py", "--http"]
