FROM python:3.10-slim

WORKDIR /worker

# Install libpq-dev for PostgreSQL dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY worker.py .

CMD ["python", "worker.py"]