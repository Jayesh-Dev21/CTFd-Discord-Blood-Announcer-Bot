import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import requests
import json
from datetime import datetime 
import pyfiglet

# ==========================
# --- Configuration ---
# ==========================
os.makedirs("data", exist_ok=True)

SOLVES_FILE = "data/solves.json"
BLOOD_FILE = "data/blood.json"

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CH_ID")) # discord channel id to Announceme bloods
CTF_BASE_URL = os.getenv("CTF_BASE_URL")  # CTFd base url, for the routes to CTFd API
AUTH_TOKEN = os.getenv("ACCESS_TOKEN")   # CTFd access tokens, to use the CTFd API

# Cache user Discord tags to minimize API calls
USER_CACHE = {} # cache space

# ==========================
# --- Helper Functions ---
# ==========================

def get_challenge_name(cid):
    url = f"{CTF_BASE_URL}/api/v1/challenges/{cid}/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {AUTH_TOKEN}"
    }

    try:
        res = requests.get(url, headers=headers)
        data = res.json()
        return data.get("name")
    except Exception as e:
        print(f"[ERROR] Could not fetch challenge name: {e}")
        return None


def get_discord_tag(uid):
    # Fetch the user's Discord username from the CTF API and cache it
    if uid in USER_CACHE:
        return USER_CACHE[uid]

    url = f"{CTF_BASE_URL}/api/v1/users/{uid}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {AUTH_TOKEN}"
    }

    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        data = res.json().get("data", {})

        discord_tag = None
        for field in data.get("fields", []):
            if field.get("name", "").lower() == "discord username":
                discord_tag = field.get("value")
                break

        USER_CACHE[uid] = discord_tag
        return discord_tag

    except Exception as e:
        print(f"[ERROR] Could not fetch Discord tag for user {uid}: {e}")
        USER_CACHE[uid] = None
        return None


def get_solves():
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {AUTH_TOKEN}"
    }

    all_solves = []
    page = 1

    while True:
        url = f"{CTF_BASE_URL}/api/v1/submissions?type=correct&page={page}"
        try:
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            data = res.json()

            solves = data.get("data", [])
            if not solves:
                break  # stop when no more pages

            for item in solves:
                all_solves.append({
                    "user_id": item["user"]["id"],
                    "username": item["user"]["name"],
                    "challenge_id": item["challenge"]["id"],
                    "challenge_name": item["challenge"]["name"],
                    "time": item["date"]
                })

            print(f"[INFO] Page {page} fetched ({len(solves)} solves)")
            page += 1

        except Exception as e:
            print(f"[ERROR] Page {page} failed: {e}")
            break

    print(f"[DONE] Total solves fetched: {len(all_solves)}")
    return all_solves


def load_json(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f, indent=4)
    with open(file, "r") as f:
        return json.load(f)


def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)


def parse_time(timestr):
    try:
        if isinstance(timestr, str) and timestr.endswith("Z"):
            timestr = timestr.replace("Z", "+00:00")
        return datetime.fromisoformat(timestr)
    except Exception:
        return timestr

# ==========================
# ----- Announcement -------
# ==========================

def get_blood_announcement(place):
    return {
        1: "🥇 🩸 **First Blood!** 🩸",
        2: "🥈 🩸 **Second Blood!** 🩸",
        3: "🥉 🩸 **Third Blood!** 🩸"
    }.get(place, None)


# ==========================
# --- Discord Bot Setup ---
# ==========================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="/", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    check_for_updates.start()


# =========================
# -- Custom Bot Commands --
# =========================

# @bot.command()
# async def hello(ctx):
#    await ctx.send(f"Hello, {ctx.author.mention}!")


# ===============================
# --- Blood Announcement Loop ---
# ===============================

@tasks.loop(minutes=1)
async def check_for_updates():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("Channel not found. Check CH_ID in .env")
        return

    current_solves = get_solves()
    if not current_solves:
        return

    # Group solves by challenge id
    solves_by_challenge = {}
    for s in current_solves:
        cid = str(s["challenge_id"])
        solves_by_challenge.setdefault(cid, []).append(s)

    blood_tracker = load_json(BLOOD_FILE)
    changed = False

    for cid, solves in solves_by_challenge.items():
        # sort solves chronologically and remove duplicates by same user
        for s in solves:
            s["_parsed_time"] = parse_time(s["time"])
        solves.sort(key=lambda x: (isinstance(x["_parsed_time"], datetime), x["_parsed_time"]))

        unique = []
        seen_users = set()
        for s in solves:
            uid = s["user_id"]
            if uid not in seen_users:
                seen_users.add(uid)
                unique.append(s)

        first_three = unique[:3]
        new_user_ids = [s["user_id"] for s in first_three]

        stored = blood_tracker.get(cid, {}).get("solvers", [])
        stored_user_ids = [entry.get("user_id") for entry in stored]

        newly_added = [uid for uid in new_user_ids if uid not in stored_user_ids]

        for uid in newly_added:
            solve_entry = next((s for s in first_three if s["user_id"] == uid), None)
            if not solve_entry:
                continue

            place = first_three.index(solve_entry) + 1
            announcement = get_blood_announcement(place)
            discord_tag = get_discord_tag(uid)

            # Try to find member by their Discord tag (if available)
            member_mention = None
            if discord_tag and hasattr(channel.guild, "members"):
                member = discord.utils.find(
                    lambda m: m.name == discord_tag or (m.display_name == discord_tag),
                    channel.guild.members
                )
                if member:
                    member_mention = member.mention

            # Building the message
            if announcement:
                if discord_tag and member_mention:
                    msg = (
                        f"{announcement}\n`{solve_entry['username']}` "
                        f"({member_mention}) solved challenge `{solve_entry['challenge_name']}`"
                    )
                elif discord_tag:
                    msg = (
                        f"{announcement}\n`{solve_entry['username']}` "
                        f"(Discord: **{discord_tag}**) solved challenge `{solve_entry['challenge_name']}`"
                    )
                else:
                    msg = (
                        f"{announcement}\n`{solve_entry['username']}` "
                        f"solved challenge `{solve_entry['challenge_name']}`"
                    )
            else:
                msg = f"`{solve_entry['username']}` solved challenge `{solve_entry['challenge_name']}`"

            try:
                await channel.send(msg)
                print(f"✅ Announced: challenge {cid}, place {place}, user {uid}, discord: {discord_tag}")
            except Exception as e:
                print(f"[ERROR] Could not send announcement: {e}")

        # Update stored solvers
        new_stored = [
            {"place": i + 1, "user_id": s["user_id"], "username": s["username"], "time": s["time"]}
            for i, s in enumerate(first_three)
        ]
        if new_stored != stored:
            blood_tracker[cid] = {"solvers": new_stored}
            changed = True

    if changed:
        save_json(BLOOD_FILE, blood_tracker)


# ==========================
# --- Main Entrypoint ---
# ==========================

if __name__ == "__main__":
    f = pyfiglet.figlet_format("CTFd Discord Blood - Announcer", font="slant")
    print(f)
    if not os.path.exists(SOLVES_FILE):
        print("Creating initial solves file...")
        initial_data = get_solves()
        save_json(SOLVES_FILE, initial_data)

    if not os.path.exists(BLOOD_FILE):
        save_json(BLOOD_FILE, {})

    bot.run(BOT_TOKEN)

