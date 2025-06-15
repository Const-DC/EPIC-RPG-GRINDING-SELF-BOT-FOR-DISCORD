import asyncio
import os
import random
from calendar import error
import json
from email import message
import subprocess
import discord
from discord.ext import tasks
from dotenv import load_dotenv
import sys


os.system("cls")

#VARIABLES

heal_user = False

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

with open(resource_path("config.json")) as file:
    config = json.load(file)

load_dotenv()
TOKEN_USER = os.getenv("TOKEN")
client = discord.Client()
channel_id = 1383322889331413085

package_variable = ["asyncio", "discord.py-self", "dotenv" ]

def install_missing_packages():
    for package in package_variable:
        try:
            __import__(package)  # Try importing the package
            print(f"✅ {package} is already installed.")
        except ImportError:
            print(f"⚠️ {package} not found. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} installed successfully!")

install_missing_packages()


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    daily.start()
    auto_loop.start()
    adventure_battle.start()

@tasks.loop(hours=24)
async def daily():
    channel = client.get_channel(channel_id)
    if channel:
        await channel.send("rpg daily")

@tasks.loop(hours=24)
async def start():
    channel = client.get_channel(channel_id)
    if channel:
        await asyncio.sleep(random.randint(1, 3))
        await channel.send("rpg start")

@client.event
async def on_message(message):
    global heal_user  # Use `global` to modify it within the function
    if message.author == client.user:
        return
    if message.author.bot:
        if "remaining hp" in message.content.lower():
            heal_user = True
            await auto_loop2(message)
        else:
            heal_user = False

@tasks.loop(seconds=60)
async def auto_loop():
    if config["commands"]["grinding"]["active"]:
        channel = client.get_channel(channel_id)
        if channel:
            await asyncio.sleep(random.randint(1, 3))
            await channel.send("rpg hunt")
            await asyncio.sleep(60)
    else:
        print("Activate it in the 'Config'")

async def auto_loop2(message):
    global heal_user

    channel = client.get_channel(channel_id)
    if heal_user:
        await asyncio.sleep(random.randint(1, 3))
        await channel.send("rpg heal")
        await asyncio.sleep(random.randint(1, 3))
        await channel.send("rpg buy life potion")

@tasks.loop(seconds=60)
async def adventure_battle():
    if config["commands"]["battling"]["active"]:
        channel = client.get_channel(channel_id)
        if channel:
            await asyncio.sleep(random.randint(1, 3))
            await channel.send("rpg adventure")
            await asyncio.sleep(60)
    else:
        print("Activate it in the 'Config'")

install_missing_packages()
client.run(TOKEN_USER)
