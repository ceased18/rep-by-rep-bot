import os
import discord
from discord.ext import commands, tasks
import pytz
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Validate environment variables
        self.guided_members_role_id = os.getenv('GUIDED_MEMBERS_ROLE_ID')
        if not self.guided_members_role_id:
            raise ValueError("GUIDED_MEMBERS_ROLE_ID environment variable is not set")

        self.check_in_channel_id = os.getenv('CHECK_IN_CHANNEL_ID')
        if not self.check_in_channel_id:
            raise ValueError("CHECK_IN_CHANNEL_ID environment variable is not set")

        try:
            self.guided_members_role_id = int(self.guided_members_role_id)
            self.check_in_channel_id = int(self.check_in_channel_id)
        except ValueError as e:
            raise ValueError(f"Invalid Discord ID format: {str(e)}")

        self.daily_checkin.start()
        logger.info("Events cog initialized successfully")

    def cog_unload(self):
        self.daily_checkin.cancel()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            # Assign role
            role = member.guild.get_role(self.guided_members_role_id)
            if not role:
                logger.error(f"Could not find role with ID {self.guided_members_role_id}")
                return

            await member.add_roles(role)
            logger.info(f"Assigned role to new member {member.name}")

            # Send welcome DM
            welcome_msg = (f"Welcome {member.mention} to Rep by Rep! 💪 "
                         f"Use /help to start. Check-ins at 8 PM EST!")
            await member.send(welcome_msg)
            logger.info(f"Sent welcome message to {member.name}")

        except discord.Forbidden:
            logger.error(f"Failed to send DM to {member.name} - Missing permissions")
        except Exception as e:
            logger.error(f"Error in on_member_join for {member.name}: {str(e)}")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bot messages
        if message.author.bot:
            return

        # Handle messages in threads
        if isinstance(message.channel, discord.Thread):
            if message.channel.id in self.bot.thread_mappings:
                try:
                    # Forward message to Assistant
                    response = await self.bot.get_cog('Commands').assistant.continue_conversation(
                        self.bot.thread_mappings[message.channel.id],
                        message.content
                    )
                    await message.channel.send(response)
                    logger.debug(f"Processed thread message in {message.channel.name}")
                except Exception as e:
                    logger.error(f"Error processing thread message: {str(e)}")
                    await message.channel.send("Sorry, I encountered an error processing your message. Please try again.")

    @tasks.loop(minutes=1)
    async def daily_checkin(self):
        now = datetime.now(pytz.timezone('America/New_York'))

        # Check if it's 8 PM EST
        if now.hour == 20 and now.minute == 0:
            try:
                channel = self.bot.get_channel(self.check_in_channel_id)
                if not channel:
                    logger.error(f"Could not find channel with ID {self.check_in_channel_id}")
                    return

                message = (
                    f"<@&{self.guided_members_role_id}> Time for your daily check-in! 💪\n"
                    "**RIFT & TAPS Progress**\n"
                    "React: 💧 Hydration, 🍎 Timing, 🏋️ Workout\n"
                    "Answer below..."
                )
                check_in_msg = await channel.send(message)

                # Add reactions
                reactions = ['💧', '🍎', '🏋️']
                for reaction in reactions:
                    await check_in_msg.add_reaction(reaction)

                logger.info("Daily check-in message posted successfully")

            except Exception as e:
                logger.error(f"Error posting daily check-in: {str(e)}")

    @daily_checkin.before_loop
    async def before_daily_checkin(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Events(bot))