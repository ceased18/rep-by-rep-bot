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
        self.command_hash_file = 'command_hash.json'

    def _get_command_hash(self):
        """Generate a hash of the current command definitions"""
        commands = [
            {'name': 'help', 'description': 'Show available commands and usage information'},
            {'name': 'rift_taps', 'description': 'Learn about the RIFT & TAPS methodology'},
            {'name': 'ask', 'description': 'Ask a question about bodybuilding during Ramadan'}
        ]
        return hashlib.md5(json.dumps(commands, sort_keys=True).encode()).hexdigest()

    def _load_command_hash(self):
        """Load the previously saved command hash"""
        try:
            with open(self.command_hash_file, 'r') as f:
                return json.load(f)['hash']
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None

    def _save_command_hash(self, hash_value):
        """Save the current command hash"""
        with open(self.command_hash_file, 'w') as f:
            json.dump({'hash': hash_value}, f)

    async def setup_hook(self):
        # Load cogs first
        try:
            await self.load_extension("cogs.commands")
            await self.load_extension("cogs.events")
            logger.info("Cogs loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load cogs: {str(e)}")
            raise

        # Check if commands need to be synced
        current_hash = self._get_command_hash()
        saved_hash = self._load_command_hash()

        if current_hash == saved_hash:
            logger.info("Command registration status: skipped (no changes detected)")
            return

        # Sync commands with rate limit handling
        try:
            logger.info("Syncing slash commands...")
            synced = await self.tree.sync()
            self._save_command_hash(current_hash)
            logger.info(f"Command registration status: updated (synced {len(synced)} commands)")
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limit error
                logger.warning(f"Command registration status: rate-limited (retry after {e.retry_after} seconds)")
                # Continue with existing commands
            else:
                logger.error(f"Command registration status: failed (HTTP error {e.status})")
        except Exception as e:
            logger.error(f"Command registration status: failed ({str(e)})")

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
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
    # Get environment variables
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise ValueError("DISCORD_TOKEN not found in environment variables")

    # Create and run bot
    bot = RamadanBot()
    bot.run(token)

if __name__ == "__main__":
    main()