import os
from dotenv import load_dotenv
import logging
import discord
from discord.ext import commands
import asyncio

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.DEBUG)  # Temporarily increase logging level
logger = logging.getLogger(__name__)

# Bot configuration
intents = discord.Intents.all()  # Using all intents for proper functionality

class RamadanBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=['/', '!'],
            intents=intents,
            help_command=None,
            application_id=os.getenv('APPLICATION_ID')
        )
        self.thread_mappings = {}
        logger.info("Bot initialized with application ID: %s", os.getenv('APPLICATION_ID'))

    async def setup_hook(self):
        """Initialize bot and sync commands"""
        try:
            # Load cogs first
            logger.info("Loading cogs...")
            await self.load_extension("cogs.commands")
            await self.load_extension("cogs.events")
            logger.info("Cogs loaded successfully")

            # Sync commands to Discord...
            logger.info("Syncing commands to Discord...")
            try:
                synced = await self.tree.sync()
                logger.info(f"Command registration status: updated (synced {len(synced)} commands)")

                # Log each synced command
                for command in synced:
                    logger.info(f"Synced command: {command.name}")

            except discord.HTTPException as e:
                if e.status == 429:  # Rate limit error
                    logger.warning(f"Command registration status: rate-limited (retry after {e.retry_after} seconds)")
                else:
                    logger.error(f"Command registration status: failed (HTTP error {e.status})")
                    raise
            except Exception as e:
                logger.error(f"Command registration status: failed ({str(e)})")
                raise

        except Exception as e:
            logger.error(f"Failed to setup bot: {str(e)}")
            raise

    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f'Logged in as {self.user.name}')

        # Verify command registration
        commands = self.tree.get_commands()
        logger.info(f"Registered commands: {[cmd.name for cmd in commands]}")

        # Update presence
        await self.change_presence(activity=discord.Game(name="Type /help"))

        # Generate invite link
        permissions = discord.Permissions(
            view_channel=True,
            send_messages=True,
            create_public_threads=True,
            send_messages_in_threads=True,
            manage_messages=True,
            add_reactions=True,
            mention_everyone=True
        )
        invite_link = discord.utils.oauth_url(
            self.user.id,
            permissions=permissions,
            scopes=["bot", "applications.commands"]
        )
        logger.info(f'Invite link: {invite_link}')

    async def on_error(self, event_method: str, *args, **kwargs):
        """Global error handler"""
        logger.error(f"Error in {event_method}: ", exc_info=True)

    async def on_connect(self):
        """Called when the client connects to Discord"""
        logger.info("Connected to Discord Gateway")

    async def on_disconnect(self):
        """Called when the client disconnects from Discord"""
        logger.warning("Disconnected from Discord Gateway")

    async def on_resumed(self):
        """Called when the client resumes a session"""
        logger.info("Resumed Discord session")

if __name__ == "__main__":
    try:
        # Get environment variables
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            raise ValueError("DISCORD_TOKEN not found in environment variables")

        # Create and run bot
        bot = RamadanBot()
        logger.info("Starting Discord bot...")
        bot.run(token, log_handler=None)  # Disable discord.py's logging handler to avoid duplicates
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}")
        raise