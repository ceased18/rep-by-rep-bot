import os
from flask import Flask
import threading
import logging
from bot import main as bot_main

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot running"

def run_bot():
    """Run the Discord bot in a separate thread"""
    try:
        bot_main()
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}")

logger.info("Bot entry point loaded: main.py")

if __name__ == "__main__":
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
