import discord
from discord import app_commands
from discord.ext import commands
import logging
from utils.assistant import AssistantManager
from utils.pdf_generator import generate_meal_plan_pdf
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
        thread = await interaction.channel.create_thread(name=name)
        logger.info(f"Created thread: {name} for command: {interaction.command.name}")
        return thread

    @app_commands.command(name='help', description='Show available commands and usage information')
    async def help_command(self, interaction: discord.Interaction):
        help_text = ("Commands: /help, /rift_taps, /mealplan, !ask <question>. "
                    "Chat in threads! Note: I don't have web search access.")
        await interaction.response.send_message(help_text)

    @app_commands.command(name='rift_taps', description='Learn about the RIFT & TAPS methodology')
    async def rift_taps(self, interaction: discord.Interaction):
        await interaction.response.defer()
        thread = await self._get_or_create_thread(interaction, f"RIFT & TAPS for {interaction.user.name}")

        # Store thread mapping for real-time chat
        response = await self.assistant.explain_rift_taps()
        self.bot.thread_mappings[thread.id] = response

        await send_long_message(thread, response)
        await interaction.followup.send(f"Created a new thread to explain RIFT & TAPS. Check {thread.mention}!")

    @app_commands.command(name='mealplan', description='Get a personalized Ramadan meal plan')
    async def mealplan(self, interaction: discord.Interaction):
        await interaction.response.defer()
        thread = await self._get_or_create_thread(interaction, f"Meal-Plan-{interaction.user.name}")

        # Ask for user details
        prompt = ("Answer: Weight (lbs), Height (ft'in or inches), Goal (cut/bulk/maintain), "
                 "Diet (e.g., halal), Allergies?")
        await thread.send(prompt)
        await interaction.followup.send("Created a new thread for your meal plan! Please provide your details in the thread.")

        def check(m):
            return m.author == interaction.user and m.channel == thread

        try:
            response = await self.bot.wait_for('message', timeout=300.0, check=check)

            # Parse response
            data = response.content.split(',')
            if len(data) < 5:
                await thread.send("Please provide all required information.")
                return

            # Convert height if in ft'in format
            height = data[1].strip()
            if "'" in height:
                ft, inches = height.split("'")
                height = int(ft) * 12 + int(inches.replace('"', ''))

            user_data = {
                'weight': float(data[0]),
                'height': float(height),
                'goal': data[2].strip(),
                'diet': data[3].strip(),
                'allergies': data[4].strip()
            }

            # Generate meal plan using Assistant
            meal_plan = await self.assistant.generate_meal_plan(user_data)

            # Generate and send PDF
            pdf_path = generate_meal_plan_pdf(meal_plan)
            await thread.send(file=discord.File(pdf_path))
            os.remove(pdf_path)  # Clean up

            # Send the meal plan text in a format that handles long messages
            await send_long_message(thread, meal_plan)

        except asyncio.TimeoutError:
            await thread.send("Response time exceeded. Please try again.")
        except Exception as e:
            logger.error(f"Error in mealplan command: {str(e)}")
            await thread.send("An error occurred. Please try again.")

    @app_commands.command(name='ask', description='Ask a question about bodybuilding during Ramadan')
    async def ask(self, interaction: discord.Interaction, *, question: str):
        await interaction.response.defer()
        thread = await self._get_or_create_thread(interaction, f"Question from {interaction.user.name}")

        # Check if question requires web access
        web_keywords = ['today', 'current', '2024', '2025', 'this year', 'next year']
        needs_web = any(keyword in question.lower() for keyword in web_keywords)

        response = await self.assistant.ask_question(question)

        # Store thread mapping for real-time chat
        self.bot.thread_mappings[thread.id] = response

        if needs_web:
            response += ("\n\nNote: I don't have web access, but based on the Team Akib guide, "
                        "this is my best answer. For current info, please check online!")

        await send_long_message(thread, response)
        await interaction.followup.send(f"Created a new thread for your question. Check {thread.mention}!")

async def setup(bot):
    await bot.add_cog(Commands(bot))