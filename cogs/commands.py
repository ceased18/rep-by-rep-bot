import discord
from discord import app_commands
from discord.ext import commands
import logging
from utils.assistant import AssistantManager
from utils.message_utils import send_long_message
import asyncio
import re
import os

logger = logging.getLogger(__name__)

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.assistant = AssistantManager()
        self.bot.thread_mappings = {} # Initialize thread mapping

    async def _get_or_create_thread(self, interaction, name):
        """Create a new thread or get existing one"""
        # Find existing threads owned by the user
        existing_threads = [t for t in interaction.channel.threads if t.owner_id == interaction.user.id]
        if existing_threads:
            return existing_threads[0]

        # Create a new public thread that will show in the sidebar
        thread = await interaction.channel.create_thread(
            name=name,
            type=discord.ChannelType.public_thread,
            auto_archive_duration=1440  # Archive after 24 hours of inactivity
        )
        logger.info(f"Thread created and formatted for {interaction.command.name}: {name}")
        return thread

    @app_commands.command(name='help', description='Show available commands and usage information')
    async def help_command(self, interaction: discord.Interaction):
        help_text = ("Commands: /help, /rift_taps, !ask <question>. "
                    "Chat in threads! Note: I don't have web search access.")
        await interaction.response.send_message(help_text)

    @app_commands.command(name='rift_taps', description='Learn about the RIFT & TAPS methodology')
    async def rift_taps(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Create public thread with proper name
        thread_name = f"RIFT & TAPS for {interaction.user.name}"
        thread = await self._get_or_create_thread(interaction, thread_name)
        logger.info(f"Thread created and formatted for rift_taps: {thread_name}")

        # Send initial wait message
        initial_message = "Let's explore RIFT & TAPS! 💪\nPlease wait a few seconds for processing."
        await thread.send(initial_message)
        logger.info(f"Initial thread message sent: {initial_message}")

        # Get and store response for real-time chat
        openai_thread_id, response = await self.assistant.explain_rift_taps()
        self.bot.thread_mappings[thread.id] = openai_thread_id

        # Send the formatted response
        await send_long_message(thread, response)
        await thread.send("\nFeel free to ask any follow-up questions about RIFT & TAPS! 👓")

        # Send main channel confirmation with thread mention
        await interaction.followup.send(
            f"Created a thread to explain RIFT & TAPS. Check {thread.mention}! 💪"
        )

    @app_commands.command(name='ask', description='Ask a question about bodybuilding during Ramadan')
    async def ask(self, interaction: discord.Interaction, *, question: str):
        await interaction.response.defer()
        thread = await self._get_or_create_thread(interaction, f"Question from {interaction.user.name}")
        logger.info(f"Thread created and formatted for ask: {thread.name}")

        # Send welcome message with question and emoji
        await thread.send(f"Let's answer your question: **{question}** ❓")
        await thread.send("Here's what I found based on Team Akib's guide...")

        # Get and store response for real-time chat
        openai_thread_id, response = await self.assistant.ask_question(question)
        self.bot.thread_mappings[thread.id] = openai_thread_id

        # Check if question requires web access
        web_keywords = ['today', 'current', '2024', '2025', 'this year', 'next year']
        needs_web = any(keyword in question.lower() for keyword in web_keywords)

        if needs_web:
            response += ("\n\nNote: I don't have web access, but based on the Team Akib guide, "
                        "this is my best answer. For current info, please check online! 🌐")

        await send_long_message(thread, response)
        await thread.send("\nFeel free to ask follow-up questions! I'm here to help! 💪")
        await interaction.followup.send(f"Created a thread for your question. Check {thread.mention}! 🤔")

async def setup(bot):
    await bot.add_cog(Commands(bot))