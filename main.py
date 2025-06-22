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
import aiohttp  # New: For making async HTTP requests to the dashboard

# Correct import for dashboard functions
from dashboard import start_dashboard, set_bot_instance


class RPGBot:
    def __init__(self):
        self.setup_environment()
        self.load_config()
        self.setup_logging()
        self.client = discord.Client()
        self.channel_id = 1383322889331413085  # Make sure this is your actual channel ID

        self.dashboard_stats = {
            "start_time": datetime.now(),
            "commands_sent": 0,
            "coins_earned": 0,
            "hoarded_items": 0,
            "heals_avoided": 0,  # Initialize heals avoided stat
            # Snapshots for calculating increments for dashboard
            "last_commands_sent_snapshot": 0,
            "last_coins_earned_snapshot": 0,
            # For hourly efficiency calculation on bot side before sending
            "hourly_coins_increment": 0,
            "hourly_commands_increment": 0
        }

        # Bot state variables
        self.heal_user = False
        self.no_horse = True
        self.last_hunt_time = None
        self.last_adventure_time = None

        # Dashboard integration variables
        self.dashboard_url = "http://localhost:5000/api/update_bot_stats"  # Endpoint to push updates
        self.http_session = None  # aiohttp client session for making requests

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
        # Added aiohttp to the list of packages to check/install
        package_variable = ["asyncio", "discord.py-self", "dotenv", "flask", "aiohttp"]

        for package in package_variable:
            try:
                # Attempt to import to check if installed
                # Using dummy variable names to avoid actual import side-effects or conflicts
                if package == "asyncio":
                    import asyncio_check  # type: ignore
                elif package == "discord.py-self":
                    import discord_check  # type: ignore
                elif package == "dotenv":
                    import dotenv_check  # type: ignore
                elif package == "flask":
                    import flask_check  # type: ignore
                elif package == "aiohttp":  # New check for aiohttp
                    import aiohttp_check  # type: ignore
                logging.info(f"✅ {package} is already installed.")
            except ImportError:
                try:
                    logging.warning(f"⚠️ {package} not found. Installing...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                    logging.info(f"✅ {package} installed successfully!")
                except subprocess.CalledProcessError as e:
                    logging.error(f"Failed to install {package}: {e}")
                    print(f"❌ Failed to install {package}. Please install it manually: pip install {package}")
                    sys.exit(1)
            except Exception as e:
                logging.error(f"An unexpected error occurred while checking/installing {package}: {e}")
                print(f"❌ An unexpected error occurred: {e}")
                sys.exit(1)

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

        # Initialize aiohttp session when bot is ready
        self.http_session = aiohttp.ClientSession()

        # Start all loops
        self.daily_loop.start()
        self.grinding_loop.start()
        self.adventure_loop.start()
        self.quest_loop.start()
        self.miniboss_loop.start()
        self.horse_loop.start()
        self.dashboard_sync_loop.start()  # New: Start dashboard sync loop

        logging.info("All loops started successfully")

    async def on_message(self, message):
        """Handle incoming messages"""
        if message.author == self.client.user:
            return

        # Ensure we only process messages from bots (or specific bots if needed)
        if not message.author.bot:
            return

        # Only process messages in the configured channel
        if message.channel.id != self.channel_id:
            return

        msg_content = message.content.lower()

        # Parse coin rewards from hunt/adventure logs
        if "earned" in msg_content and "coins" in msg_content:
            try:
                words = message.content.split()
                coins_earned = 0
                for i, word in enumerate(words):
                    if word.lower() == "coins" and i > 0 and words[i - 1].isdigit():
                        coins_earned = int(words[i - 1])
                        self.dashboard_stats["coins_earned"] += coins_earned
                        # Calculate coin increment for dashboard
                        new_coins_total = self.dashboard_stats["coins_earned"]
                        coins_increment = new_coins_total - self.dashboard_stats["last_coins_earned_snapshot"]
                        self.dashboard_stats["last_coins_earned_snapshot"] = new_coins_total
                        self.dashboard_stats["hourly_coins_increment"] += coins_increment  # For hourly efficiency

                        logging.info(f"✅ Parsed {coins_earned} coins from message")
                        # Push updated stats to dashboard after parsing coins
                        await self.send_dashboard_update(
                            parsed_message=message.content,
                            decision_made="coins_earned",
                            coins_earned_increment=coins_increment
                        )
                        break
            except Exception as e:
                logging.warning(f"⚠️ Failed to parse coins from message: {message.content}. Error: {e}")

        # --- HOARDED ITEMS LOGIC ---
        if "you now have" in msg_content and "hoarded items" in msg_content:
            try:
                words = message.content.split()
                if "hoarded" in words:
                    hoarded_index = words.index("hoarded")
                    if hoarded_index > 0 and words[hoarded_index - 1].isdigit():
                        hoarded_count = int(words[hoarded_index - 1])
                        self.dashboard_stats["hoarded_items"] = hoarded_count  # Assuming this is total hoarded items
                        logging.info(f"✅ Parsed {hoarded_count} hoarded items from message")
                        await self.send_dashboard_update(parsed_message=message.content,
                                                         decision_made="items_hoarded")  # Push update
            except Exception as e:
                logging.warning(f"⚠️ Failed to parse hoarded items from message: {message.content}. Error: {e}")
        # --- END HOARDED ITEMS LOGIC ---

        # Handle healing logic
        if any(phrase in msg_content for phrase in ["remaining hp", "lost hp", "your hp"]):
            self.heal_user = True
            # Check for critical HP and log as critical failure
            # This is a heuristic based on message content; refine as needed for your bot's messages
            if "low hp" in msg_content or "10% hp" in msg_content or "5% hp" in msg_content or "very low" in msg_content:
                await self.send_dashboard_update(
                    critical_failure={"type": "Low HP Detected", "details": message.content})
            await self.handle_healing()

        # Handle horse management
        await self.handle_horse_messages(msg_content)

        # Handle events
        await self.handle_events(message, msg_content)

    async def send_dashboard_update(self, last_sent_command=None, parsed_message=None,
                                    decision_made=None, critical_failure=None,
                                    coins_earned_increment=0, commands_sent_increment=0):
        """
        Sends the current dashboard_stats and optionally the last sent command,
        parsed message, decisions, critical failures, and increments to the Flask dashboard.
        """
        if not self.http_session:
            logging.error("HTTP session not initialized for dashboard update.")
            return

        # Calculate efficiency score based on available total data
        uptime_seconds = (datetime.now() - self.dashboard_stats["start_time"]).total_seconds()
        uptime_hours = max(uptime_seconds / 3600, 0.001)
        coins_per_command = self.dashboard_stats["coins_earned"] / max(self.dashboard_stats["commands_sent"], 1)
        efficiency_score = min(100, round(coins_per_command * 10, 1))  # Simple heuristic

        payload = {
            "commands_sent": self.dashboard_stats["commands_sent"],
            "coins_earned": self.dashboard_stats["coins_earned"],
            "hoarded_items": self.dashboard_stats["hoarded_items"],
            "heals_avoided": self.dashboard_stats["heals_avoided"],  # Include heals avoided total
            "efficiency_score": efficiency_score,  # Include efficiency score
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "coins_earned_increment": coins_earned_increment,  # New: Increment for hourly tracking on dashboard
            "commands_sent_increment": commands_sent_increment  # New: Increment for hourly tracking on dashboard
        }

        if last_sent_command:
            payload["last_sent_command"] = last_sent_command
            payload["command_time"] = datetime.now().strftime('%H:%M:%S')
        if parsed_message:
            payload["parsed_message"] = parsed_message
            payload["message_time"] = datetime.now().strftime('%H:%M:%S')
        if decision_made:
            payload["decision_made"] = decision_made
            payload["decision_time"] = datetime.now().strftime('%H:%M:%S')
        if critical_failure:
            payload["critical_failure"] = critical_failure
            payload["failure_time"] = datetime.now().strftime('%H:%M:%S')

        try:
            async with self.http_session.post(self.dashboard_url, json=payload) as response:
                if response.status == 200:
                    logging.debug("Dashboard stats updated successfully.")
                else:
                    logging.error(
                        f"Failed to update dashboard stats. Status: {response.status}, Response: {await response.text()}")
        except aiohttp.ClientError as e:
            logging.error(f"Network error sending dashboard update: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred during dashboard update: {e}", exc_info=True)

    async def handle_healing(self):
        """Handle healing when HP is low"""
        if not self.heal_user:
            return

        channel = self.client.get_channel(self.channel_id)
        if not channel:
            logging.error("Channel not found for healing")
            return

        try:
            await self.send_command_safely("rpg heal", (1.5, 3.5))
            await self.send_command_safely("rpg buy life potion", (1, 2))
            self.heal_user = False
            # Increment heals_avoided as a proxy for successful resolution of low HP state
            self.dashboard_stats["heals_avoided"] += 1
            await self.send_dashboard_update(decision_made="healing_completed")  # Report healing decision
        except Exception as e:
            logging.error(f"Error in healing process: {e}")

    async def handle_horse_messages(self, msg_content):
        """Handle horse-related messages"""
        if "you don't have enough coins to level up your horse" in msg_content:
            print("❌ Not enough coins for horse. Pausing horse management.")
            self.no_horse = False  # Set to False as we can't manage horse due to coins
            logging.warning("Insufficient coins for horse management")
            await self.send_dashboard_update(decision_made="horse_level_fail",
                                             critical_failure={"type": "Insufficient Coins (Horse)",
                                                               "details": "Not enough coins to level up horse."})

        elif any(phrase in msg_content for phrase in ["you bought a horse", "you already have a horse"]):
            print("🐴 Horse acquired successfully!")
            self.no_horse = False  # Horse is now acquired
            logging.info("Horse management completed - horse acquired")
            await self.send_dashboard_update(decision_made="horse_acquired")

        elif "you don't have a horse" in msg_content:
            print("🟡 No horse detected. Will attempt to buy one.")
            self.no_horse = True  # Need to buy a horse
            logging.info("No horse found - will attempt purchase")
            await self.send_dashboard_update(decision_made="no_horse_detected")

    async def handle_events(self, message, msg_content):
        """Handle special events"""
        if not self.config["commands"]["events"]["active"]:
            return

        channel = self.client.get_channel(self.channel_id)
        if not channel:
            logging.error("Channel not found for event handling")
            return

        try:
            if "it's raining coins" in msg_content:
                await self.send_command_safely("CATCH")
                logging.info("Participated in coin rain event")
                await self.send_dashboard_update(decision_made="caught_coin_rain")

            if ":moneybag: everyone got" in msg_content:
                logging.info("Coin rain event completed successfully")
                await self.send_dashboard_update(decision_made="coin_rain_completed")

        except Exception as e:
            logging.error(f"Error handling events: {e}")

    async def send_command_safely(self, command, delay_range=(1, 3)):
        """Safely send a command to the channel with error handling and a small delay."""
        channel = self.client.get_channel(self.channel_id)
        if not channel:
            logging.error(f"Channel not found when attempting to send: {command}")
            return False

        try:
            delay = random.uniform(*delay_range)
            await asyncio.sleep(delay)
            await channel.send(command)
            logging.info(f"Successfully sent command: {command} after {delay:.2f}s delay")
            self.dashboard_stats["commands_sent"] += 1

            # Calculate command increment for dashboard
            current_commands = self.dashboard_stats["commands_sent"]
            commands_increment = current_commands - self.dashboard_stats["last_commands_sent_snapshot"]
            self.dashboard_stats["last_commands_sent_snapshot"] = current_commands
            self.dashboard_stats["hourly_commands_increment"] += commands_increment  # For hourly efficiency

            # Determine decision made from command (simple heuristic)
            decision = "command_sent"  # Default decision
            if "heal" in command:
                decision = "bot_healed_command"
            elif "hunt" in command:
                decision = "started_hunt_command"
            elif "adventure" in command:
                decision = "started_adventure_command"
            elif "quest" in command:
                decision = "started_quest_command"
            elif "buy horse" in command:
                decision = "bought_horse_command"
            elif "daily" in command:
                decision = "daily_claimed_command"
            elif "sell all" in command:
                decision = "items_sold_command"
            elif "miniboss" in command:
                decision = "miniboss_attempted_command"
            elif "catch" in command.lower():
                decision = "catch_command"  # for coin rain

            await self.send_dashboard_update(
                last_sent_command=command,
                decision_made=decision,
                commands_sent_increment=commands_increment
                # coins_earned_increment is handled in on_message when coins are parsed
            )
            return True
        except Exception as e:
            logging.error(f"Failed to send command '{command}': {e}")
            # Add critical failure for command sending failure
            await self.send_dashboard_update(
                critical_failure={"type": "Command Send Fail", "details": f"Failed to send '{command}': {e}"})
            return False

    # Task loops
    @tasks.loop(hours=24)
    async def daily_loop(self):
        """Daily rewards collection"""
        logging.info("Executing daily loop: rpg daily")
        await self.send_command_safely("rpg daily")

    @tasks.loop(minutes=1)
    async def grinding_loop(self):
        """Main grinding loop"""
        if not self.config["commands"]["grinding"]["active"]:
            return

        # Add some variation to prevent detection
        if random.random() < 0.1:  # 10% chance to skip a minute
            logging.debug("Grinding loop skipped for a minute (random chance)")
            return

        logging.info("Executing grinding loop: rpg hunt")
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
        logging.info(f"Executing adventure loop: rpg adventure (with {extra_delay}s extra delay)")
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
            logging.debug("Quest loop skipped (random chance)")
            return

        logging.info("Executing quest loop: rpg quest")
        success = await self.send_command_safely("rpg quest", (3, 7))
        if success:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await self.send_command_safely("yes", (0.5, 1))  # Confirming quest
            await self.send_dashboard_update(decision_made="quest_confirmed")  # Decision for echo view

    @tasks.loop(hours=16)
    async def miniboss_loop(self):
        """Miniboss battle loop"""
        if not self.config["commands"]["auto_miniboss"]["active"]:
            return

        logging.info("Executing miniboss loop: rpg miniboss")
        await self.send_command_safely("rpg miniboss", (7, 15))

    @tasks.loop(minutes=2)
    async def horse_loop(self):
        """Horse management loop"""
        # Only run if horse management is active AND we don't have a horse
        if not self.config["commands"]["horse"]["active"] or not self.no_horse:
            logging.debug(
                f"Horse loop skipped. Active: {self.config['commands']['horse']['active']}, No Horse: {self.no_horse}")
            return

        logging.info("Executing horse loop: rpg buy horse")
        await self.send_command_safely("rpg buy horse", (3, 8))

    @tasks.loop(seconds=5)  # Syncs with dashboard's fetch interval
    async def dashboard_sync_loop(self):
        """
        Periodically pushes the bot's current stats to the dashboard.
        Ensures the dashboard is up-to-date even if no commands are sent
        or messages parsed within the 5-second interval.
        Also resets hourly increments for the dashboard's hourly efficiency tracking.
        """
        logging.debug("Synchronizing dashboard stats...")
        # Send current cumulative stats and current interval's increments
        await self.send_dashboard_update(
            coins_earned_increment=self.dashboard_stats["hourly_coins_increment"],
            commands_sent_increment=self.dashboard_stats["hourly_commands_increment"]
        )
        # Reset increments for the next interval
        self.dashboard_stats["hourly_coins_increment"] = 0
        self.dashboard_stats["hourly_commands_increment"] = 0

    def run(self):
        """Start the bot and the dashboard"""
        load_dotenv()
        token = os.getenv("TOKEN")

        if not token:
            logging.error("No bot token found in environment variables")
            print("❌ Please set your bot token in the .env file")
            sys.exit(1)  # Exit if no token

        try:
            print("Starting RPG Bot...")
            self.install_missing_packages()

            # 1. Set the bot instance for the dashboard module
            set_bot_instance(self)

            # 2. Start the dashboard, using its default port (5000) or specify one
            start_dashboard()  # Uses default port 5000

            self.client.run(token)

        except discord.LoginFailure:
            logging.error("Invalid bot token")
            print("❌ Invalid bot token. Please check your .env file")
        except Exception as e:
            logging.error(f"Unexpected error during bot run: {e}", exc_info=True)  # exc_info for full traceback
            print(f"❌ An unexpected error occurred: {e}")
            sys.exit(1)  # Exit on critical error


if __name__ == "__main__":
    bot = RPGBot()
    bot.run()

