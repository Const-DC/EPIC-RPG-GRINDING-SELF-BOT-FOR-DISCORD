import asyncio
import os
import random
import json
import subprocess
import discord
from discord.ext import tasks
from dotenv import load_dotenv
import sys
import logging
from datetime import datetime, timedelta


class RPGBot:
    def __init__(self):
        self.setup_environment()
        self.load_config()
        self.setup_logging()
        self.client = discord.Client()
        self.channel_id = "channel id"

        # Bot state variables
        self.heal_user = False
        self.no_horse = True
        self.last_hunt_time = None
        self.last_adventure_time = None

        # Setup event handlers
        self.setup_events()

    def setup_environment(self):
        """Setup the basic environment and folders"""
        os.makedirs("bot_history", exist_ok=True)
        if os.name == 'nt':  # Windows
            os.system("cls")
        else:  # Unix/Linux/Mac
            os.system("clear")

    def setup_logging(self):
        """Configure logging system"""
        logging.basicConfig(
            filename='bot_history/bot.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            encoding='utf-8'
        )

        # Also log to console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logging.getLogger().addHandler(console_handler)

    def resource_path(self, relative_path):
        """Get the correct path for resources (PyInstaller compatibility)"""
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.resource_path("config.json")) as file:
                self.config = json.load(file)
                logging.info("Config loaded successfully")
        except FileNotFoundError:
            logging.error("Config.json file not found!")
            print("❌ config.json file not found in the directory!")
            sys.exit(1)
        except json.JSONDecodeError:
            logging.error("Invalid JSON format in config.json")
            print("❌ Invalid JSON format in config.json file!")
            sys.exit(1)

    def install_missing_packages(self):
        """Install required packages if missing"""
        package_variable = ["asyncio", "discord.py-self", "dotenv"]

        for package in package_variable:
            try:
                if package == "asyncio":
                    import asyncio
                elif package == "discord.py-self":
                    import discord
                elif package == "dotenv":
                    import dotenv
                print(f"✅ {package} is already installed.")
            except ImportError:
                try:
                    print(f"⚠️ {package} not found. Installing...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                    print(f"✅ {package} installed successfully!")
                except subprocess.CalledProcessError as e:
                    logging.error(f"Failed to install {package}: {e}")

    def setup_events(self):
        """Setup Discord client event handlers"""

        @self.client.event
        async def on_ready():
            await self.on_ready()

        @self.client.event
        async def on_message(message):
            await self.on_message(message)

    async def on_ready(self):
        """Called when bot is ready"""
        print(f"Logged in as {self.client.user}")
        logging.info(f"Bot logged in as {self.client.user}")

        # Start all loops
        self.daily_loop.start()
        self.grinding_loop.start()
        self.adventure_loop.start()
        self.quest_loop.start()
        self.miniboss_loop.start()
        self.horse_loop.start()

        logging.info(" loops started successfully")

    async def on_message(self, message):
        """Handle incoming messages"""
        if message.author == self.client.user:
            return

        if not message.author.bot:
            return

        msg_content = message.content.lower()

        # Handle healing logic
        if any(phrase in msg_content for phrase in ["remaining hp", "lost hp", "your hp"]):
            self.heal_user = True
            await self.handle_healing()

        # Handle horse management
        await self.handle_horse_messages(msg_content)

        # Handle events
        await self.handle_events(message, msg_content)

    async def handle_healing(self):
        """Handle healing when HP is low"""
        if not self.heal_user:
            return

        channel = self.client.get_channel(self.channel_id)
        if not channel:
            logging.error("Channel not found for healing")
            return

        try:
            await asyncio.sleep(random.uniform(1.5, 3.5))
            await channel.send("rpg heal")
            logging.info("Sent healing command")

            await asyncio.sleep(random.uniform(1, 2))
            await channel.send("rpg buy life potion")
            logging.info("Attempted to buy life potion")

            self.heal_user = False
        except Exception as e:
            logging.error(f"Error in healing: {e}")

    async def handle_horse_messages(self, msg_content):
        """Handle horse-related messages"""
        if "you don't have enough coins to level up your horse" in msg_content:
            print("❌ Not enough coins for horse. Pausing horse management.")
            self.no_horse = False
            logging.warning("Insufficient coins for horse management")

        elif any(phrase in msg_content for phrase in ["you bought a horse", "you already have a horse"]):
            print("🐴 Horse acquired successfully!")
            self.no_horse = False
            logging.info("Horse management completed - horse acquired")

        elif "you don't have a horse" in msg_content:
            print("🟡 No horse detected. Will attempt to buy one.")
            self.no_horse = True
            logging.info("No horse found - will attempt purchase")

    async def handle_events(self, message, msg_content):
        """Handle special events"""
        if not self.config["commands"]["events"]["active"]:
            return

        channel = self.client.get_channel(self.channel_id)
        if not channel:
            return

        try:
            if "it's raining coins" in msg_content:
                await channel.send("CATCH")
                logging.info("Participated in coin rain event")

            if ":moneybag: everyone got" in msg_content:
                logging.info("Coin rain event completed successfully")

        except Exception as e:
            logging.error(f"Error handling events: {e}")

    async def send_command_safely(self, command, delay_range=(1, 3)):
        """Safely send a command to the channel with error handling"""
        channel = self.client.get_channel(self.channel_id)
        if not channel:
            logging.error(f"Channel not found when sending: {command}")
            return False

        try:
            await asyncio.sleep(random.uniform(*delay_range))
            await channel.send(command)
            logging.info(f"Successfully sent command: {command}")
            return True
        except Exception as e:
            logging.error(f"Failed to send command '{command}': {e}")
            return False

    # Task loops
    @tasks.loop(hours=24)
    async def daily_loop(self):
        """Daily rewards collection"""
        await self.send_command_safely("rpg daily")

    @tasks.loop(minutes=1)
    async def grinding_loop(self):
        """Main grinding loop"""
        if not self.config["commands"]["grinding"]["active"]:
            return

        # Add some variation to prevent detection
        if random.random() < 0.1:  # 10% chance to skip
            return

        success = await self.send_command_safely("rpg hunt", (1, 4))
        if success:
            self.last_hunt_time = datetime.now()

    @tasks.loop(hours=1)
    async def adventure_loop(self):
        """Adventure/battle loop"""
        if not self.config["commands"]["battling"]["active"]:
            return

        # Add random delay to make it more natural
        extra_delay = random.randint(0, 300)  # 0-5 minutes extra delay
        await asyncio.sleep(extra_delay)

        success = await self.send_command_safely("rpg adventure", (2, 5))
        if success:
            self.last_adventure_time = datetime.now()

    @tasks.loop(minutes=30)
    async def quest_loop(self):
        """Quest management loop"""
        if not self.config["commands"]["auto_quests"]["active"]:
            return

        # Add randomization
        if random.random() < 0.3:  # 30% chance to skip
            return

        success = await self.send_command_safely("rpg quest", (3, 7))
        if success:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await self.send_command_safely("yes", (0.5, 1))

    @tasks.loop(hours=16)
    async def miniboss_loop(self):
        """Miniboss battle loop"""
        if not self.config["commands"]["auto_miniboss"]["active"]:
            return

        await self.send_command_safely("rpg miniboss", (7, 15))

    @tasks.loop(minutes=2)
    async def horse_loop(self):
        """Horse management loop"""
        if not self.config["commands"]["horse"]["active"] or not self.no_horse:
            return

        await self.send_command_safely("rpg buy horse", (3, 8))

    def run(self):
        """Start the bot"""
        load_dotenv()
        token = os.getenv("TOKEN")

        if not token:
            logging.error("No bot token found in environment variables")
            print("❌ Please set your bot token in the .env file")
            return

        try:
            print(" Starting RPG Bot...")
            self.install_missing_packages()
            self.client.run(token)
        except discord.LoginFailure:
            logging.error("Invalid bot token")
            print("❌ Invalid bot token. Please check your .env file")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            print(f"❌ An error occurred: {e}")


# Run the bot
if __name__ == "__main__":
    bot = RPGBot()
    bot.run()
