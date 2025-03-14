import os
import logging
import discord
from discord.ext import commands
import json
import hashlib

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
            help_command=None,
            application_id=os.getenv('APPLICATION_ID')
        )
        self.thread_mappings = {}

    async def setup_hook(self):
        try:
            # Load cogs first
            await self.load_extension("cogs.commands")
            await self.load_extension("cogs.events")
            logger.info("Cogs loaded successfully")

            # Force sync commands
            logger.info("Syncing slash commands...")
            try:
                synced = await self.tree.sync()
                logger.info(f"Command registration status: updated (synced {len(synced)} commands)")
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
        logger.info(f'Logged in as {self.user.name}')
        await self.change_presence(activity=discord.Game(name="Type /help"))

        # Generate invite link with proper permissions
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