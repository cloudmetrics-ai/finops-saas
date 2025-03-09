import os
import time
import psycopg2
import redis

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

def ingest_cloud_data():
    # Placeholder for ingestion logic
    # e.g., connect to AWS / private cloud APIs, fetch usage data, store in Postgres
    print("Ingesting data...")

def main():
    print("Worker service started. Running periodic tasks.")
    r = redis.from_url(REDIS_URL)
    
    while True:
        # Example loop: every 30 seconds, run data ingestion
        ingest_cloud_data()
        time.sleep(30)

if __name__ == "__main__":
    main()