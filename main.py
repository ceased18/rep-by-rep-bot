import os
from flask import Flask
import threading
import logging
from bot import RamadanBot

# Setup logging
logging.basicConfig(level=logging.DEBUG)  # Temporarily increase logging level
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot running"

def run_bot():
    """Run the Discord bot in a separate thread"""
    try:
        # Get environment variables
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            raise ValueError("DISCORD_TOKEN not found in environment variables")

        # Create and run bot
        bot = RamadanBot()
        logger.info("Starting Discord bot...")
        bot.run(token)
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}")
        raise

if __name__ == "__main__":
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("Bot thread started")

    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)