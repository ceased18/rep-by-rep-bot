import os
import logging
import discord
from discord.ext import commands
import pytz
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class RamadanBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=['/', '!'],
            intents=intents,
            help_command=None
        )
        # Store thread mappings
        self.thread_mappings = {}
        
    async def setup_hook(self):
        # Load cogs
        await self.load_extension("cogs.commands")
        await self.load_extension("cogs.events")
        
    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        await self.change_presence(activity=discord.Game(name="Type /help"))

def main():
    # Get environment variables
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise ValueError("DISCORD_TOKEN not found in environment variables")

    # Create and run bot
    bot = RamadanBot()
    bot.run(token)

if __name__ == "__main__":
    main()
