# CTFd Discord Blood Announcer Bot

This bot announces the first, second, and third unique solvers ("bloods") for every challenge on a CTFd instance. It polls CTFd, detects new solve events, persists minimal state to avoid duplicates, and posts formatted announcements into a Discord channel.

Important: This repository currently runs as a Discord bot only — webhook posting mode is not implemented.

## Features
- Announces the first three unique solvers (First / Second / Third Blood) per challenge.
- Mentions Discord users if they have a CTFd user field named exactly `Discord Username`.
- Persists announced bloods to disk (data/blood.json) to avoid duplicate posts across restarts.
- Lightweight Python implementation with an optional Dockerized runner (recommended).
- Automatic Docker build/run via start.sh (recommended for persistent deployments).

## Requirements
- Python 3.8+
- A CTFd instance and an API access token with permission to read solves and users
- A Discord bot token with permission to Send Messages in the target channel
- Docker (optional but recommended for deployment)

## Configuration

Create a `.env` file in the repository root (or use .env_example) and set the following variables:

```
CTF_BASE_URL=https://your-ctfd-url
ACCESS_TOKEN=your_ctfd_api_token
BOT_TOKEN=your_discord_bot_token
CH_ID=123456789012345678
```

Notes:
- The CTFd user field for tagging must be named exactly: `Discord Username`.
- This project currently announces up to 3 bloods per challenge (fixed).
- Poll interval is currently fixed to 60 seconds in the code.

## Quickstart — Local (development)

1. Clone the repo
   git clone https://github.com/Jayesh-Dev21/CTFd-Discord-Blood-Announcer-Bot.git
   cd CTFd-Discord-Blood-Announcer-Bot

2. Create and activate a virtual environment
   python3 -m venv venv
   source venv/bin/activate   # Linux/macOS
   .\venv\Scripts\Activate.ps1 # Windows PowerShell

3. Install dependencies
   pip install -r src/requirements.txt

4. Add configuration
   cp .env_example .env
   # Edit .env and set CTF_BASE_URL, ACCESS_TOKEN, BOT_TOKEN, CH_ID

5. Run the bot
   python discord_runner.py

## Quickstart — Docker (recommended)

The included start.sh automates the Docker build and run and mounts the data directory so state persists between restarts.

1. Make sure .env exists at repo root (start.sh will prompt to create one if missing)
2. Run:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

What start.sh does:
- Prompts for .env values if .env is missing
- Builds the Docker image
- Runs the container with auto-restart enabled
- Mounts `data/` to the host so `data/blood.json` and `data/solves.json` persist

If you prefer to run Docker manually:
docker build -t ctfd-blood-bot .
docker run -d --env-file .env --restart unless-stopped -v "$(pwd)/data:/app/data" --name ctfd-blood-bot ctfd-blood-bot

Dockerfile entrypoint (if you need to reference it):
CMD ["python", "discord_runner.py"]

## Files & Structure
- discord_runner.py — Bot entrypoint (runs the Discord bot and polling loop)
- src/requirements.txt — Python dependencies
- start.sh — Automated build + run script (Docker + persistence)
- Dockerfile — Container build definition
- data/blood.json — Persisted announced bloods
- data/solves.json — Cached solves (used to reduce repeat API work)
- .env_example — Example environment file

## Message format
Example announcement posted to Discord:
🥇 🩸 First Blood!
username solved "Challenge Name" — Team/Category — 2025-11-10 20:05 UTC

And a top-3 style update when applicable:
Top 3 bloods for "Challenge Name":
1) user1 — time
2) user2 — time
3) user3 — time

(Formatting and templates live in the code and can be adjusted there.)

## Troubleshooting
- No messages in Discord:
  - Confirm BOT_TOKEN and CH_ID are correct.
  - Ensure the bot is invited to the server and has Send Message permission in the channel.
- Duplicate messages:
  - Confirm that `data/blood.json` exists and is writable. This file stores already-announced bloods.
- API errors (401 / 403):
  - Verify ACCESS_TOKEN and CTF_BASE_URL are correct and the token has read permissions.

## Security & Best Practices
- Never commit `.env` or secrets to the repository. Add .env to .gitignore.
- Give the Discord bot minimal required permissions (Send Messages, Embed Links).
- Keep ACCESS_TOKEN and BOT_TOKEN private.

## Limitations / Current behavior
- Webhook posting mode is not implemented — only Discord bot token mode is supported.
- Number of bloods announced is fixed to 3.
- Poll interval is fixed to 60 seconds (adjust code if you need different timing).
- Matching Discord users requires the `Discord Username` CTFd field.

## Contributing
Contributions are welcome. Please open issues or pull requests on GitHub. If you add webhook support or make the number of announced bloods configurable, update this README accordingly.

## License
This project is licensed under the MIT License. See LICENSE for details.

## Support
Open an issue at:
https://github.com/Jayesh-Dev21/CTFd-Discord-Blood-Announcer-Bot/issues
