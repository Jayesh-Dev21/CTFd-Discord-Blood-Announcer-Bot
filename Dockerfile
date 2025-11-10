FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    curl \
    iputils-ping \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN mkdir -p /app/data

# Copy dependency list and install
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot source code
COPY ./src .

CMD ["python", "discord_runner.py"]

