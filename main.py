import os
import discord
import time
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from discord.ext import tasks
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Fetch environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
VOICE_CHANNEL_ID = os.getenv("VOICE_CHANNEL_ID")

# Validate environment variables
if not DISCORD_BOT_TOKEN:
    raise ValueError("❌ DISCORD_BOT_TOKEN is not set in environment variables.")
if not VOICE_CHANNEL_ID:
    raise ValueError("❌ VOICE_CHANNEL_ID is not set in environment variables.")

VOICE_CHANNEL_ID = int(VOICE_CHANNEL_ID)

# Setup Discord client
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
client = discord.Client(intents=intents)

last_price = None

def fetch_price():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,720")
    options.binary_location = shutil.which("chromium")
    service = Service(shutil.which("chromedriver"))

    if not options.binary_location or not service:
        raise Exception("Chromium or Chromedriver not found.")

    driver = webdriver.Chrome(service=service, options=options)
    try:
        print("🌐 Fetching ANA price...")
        driver.get("https://mainnet.nirvana.finance/mint")
        WebDriverWait(driver, 15).until(
            lambda d: d.find_element(By.CLASS_NAME, "DataPoint_dataPointValue__Bzf_E")
        )
        time.sleep(2)
        element = driver.find_element(By.CLASS_NAME, "DataPoint_dataPointValue__Bzf_E")
        price = element.text.replace("USDC", "").replace("$", "").strip()
        print(f"💰 Fetched price: {price}")
        return price
    except Exception as e:
        print(f"❌ Failed to fetch price: {e}")
        return None
    finally:
        driver.quit()

@tasks.loop(seconds=60)
async def update_bot_status():
    global last_price
    if not client.is_ready():
        return
    try:
        price = fetch_price()
        if price and price != last_price:
            await client.change_presence(activity=discord.Game(name=f"ANA: {price}"))
            channel = client.get_channel(VOICE_CHANNEL_ID)
            if isinstance(channel, discord.VoiceChannel):
                await channel.edit(name=f"ANA: {price}")
                print(f"🔁 Updated channel name to ANA: {price}")
                last_price = price
            else:
                print("⚠️ Voice channel not found.")
        else:
            print("⏸️ No price change or failed fetch.")
    except Exception as e:
        print(f"⚠️ Error updating status: {e}")

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    update_bot_status.start()

@client.event
async def on_disconnect():
    print("⚠️ Bot disconnected")

@client.event
async def on_resumed():
    print("🔄 Reconnected to Discord")

print("🚀 Starting bot...")
client.run(DISCORD_BOT_TOKEN)
