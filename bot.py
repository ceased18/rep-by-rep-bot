import os
import logging
import discord
from discord.ext import commands
import asyncio

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

            # Sync commands with retry logic
            logger.info("Syncing commands to Discord...")
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    synced = await self.tree.sync()
                    logger.info(f"Commands synced successfully. Synced {len(synced)} commands")

                    # Log each synced command
                    for command in synced:
                        logger.info(f"Synced command: {command.name}")

                    break
                except discord.HTTPException as e:
                    if e.status == 429:  # Rate limit
                        if attempt < max_retries - 1:
                            retry_after = e.retry_after
                            logger.warning(f"Rate limited, retrying in {retry_after} seconds...")
                            await asyncio.sleep(retry_after)
                            continue
                    logger.error(f"HTTP error during sync: {e.status} - {e.text}")
                    raise
                except Exception as e:
                    logger.error(f"Error syncing commands (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
                        continue
                    raise

            # Verify commands are registered
            commands = self.tree.get_commands()
            logger.info(f"Available commands after sync: {[cmd.name for cmd in commands]}")

        except Exception as e:
            logger.error("Failed to setup bot: %s", str(e))
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

def main():
    """Main entry point for bot"""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise ValueError("DISCORD_TOKEN not found in environment variables")

    bot = RamadanBot()
    bot.run(token)

if __name__ == "__main__":
    main()