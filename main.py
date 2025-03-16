import os
import logging
from bot import RamadanBot

# Setup logging
logging.basicConfig(level=logging.DEBUG)  # Temporarily increase logging level
logger = logging.getLogger(__name__)

try:
    # Get environment variables
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise ValueError("DISCORD_TOKEN not found in environment variables")

    # Create and run bot
    logger.info("Starting Discord bot...")
    bot = RamadanBot()
    # Run the bot without a log handler to prevent duplicate logs
    bot.run(token, log_handler=None)
except Exception as e:
    logger.error(f"Bot crashed: {str(e)}")
    raise