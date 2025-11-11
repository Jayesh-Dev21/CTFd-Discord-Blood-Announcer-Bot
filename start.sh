#!/usr/bin/env bash

figlet "Start.sh" -f slant

if command -v figlet >/dev/null 2>&1; then
    figlet "SETUP" -f slant
else
    echo "======== SETUP ========"
fi

echo
echo "Initializing environment..."
echo

if [ -f .env ]; then
    echo ".env already exists. Skipping setup."
else
    echo "No .env found. Creating one from template..."
    cp .env_example .env
    echo "Created new .env."
    
    echo
    echo "Enter configuration values:"
    echo "(Nothing is printed while typing tokens for security)"
    echo

    read -p "CTF Base URL (example: https://daily.iitbhucybersec.in): " CTF_BASE_URL
    read -p "Discord Channel ID: " CH_ID

    echo -n "CTFd Access Token: "
    read -s ACCESS_TOKEN
    echo

    echo -n "Discord Bot Token: "
    read -s BOT_TOKEN
    echo

    # Write to .env
    {
        echo "CTF_BASE_URL=${CTF_BASE_URL}"
        echo "CH_ID=${CH_ID}"
        echo "ACCESS_TOKEN=${ACCESS_TOKEN}"
        echo "BOT_TOKEN=${BOT_TOKEN}"
    } > .env

    echo
    echo "✅ .env configured successfully."
    echo
fi

# Load env
source .env

figlet "Building & Running Bot" -f slant
echo "Starting Docker container..."
echo

# Stop old container if it exists
sudo docker stop ctfd-blood-bot 2>/dev/null || true
sudo docker rm ctfd-blood-bot 2>/dev/null || true

# Ensure persistent storage folder exists
mkdir -p data

# Build docker image
docker build -t ctfd-blood-bot .

# Run container
sudo docker run -d \
  --name ctfd-blood-bot \
  --restart no \
  -v $(pwd)/data:/app/data \
  -e BOT_TOKEN="${BOT_TOKEN}" \
  -e CH_ID="${CH_ID}" \
  -e CTF_BASE_URL="${CTF_BASE_URL}" \
  -e ACCESS_TOKEN="${ACCESS_TOKEN}" \
  ctfd-blood-bot

echo "✅ Bot started and data is persistent."

figlet "DONE /|\ Running " -f slant
