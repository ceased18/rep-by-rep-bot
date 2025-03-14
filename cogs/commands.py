import discord
from discord import app_commands
from discord.ext import commands
import logging
from utils.assistant import AssistantManager
from utils.message_utils import send_long_message
from utils.pdf_generator import generate_meal_plan_pdf
import asyncio
import os
import re

logger = logging.getLogger(__name__)

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.assistant = AssistantManager()
        self.bot.thread_mappings = {}  # Initialize thread mapping

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
        help_text = ("Commands: /help, /rift_taps, /mealplan, !ask <question>. "
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

    @app_commands.command(name='mealplan', description='Get a personalized Ramadan meal plan')
    async def mealplan(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Create thread for meal plan
        thread_name = f"Meal Plan for {interaction.user.name}"
        thread = await self._get_or_create_thread(interaction, thread_name)
        logger.info(f"Created meal plan thread: {thread_name}")

        try:
            # Send initial questions
            initial_questions = ("Let's create your personalized meal plan 📝\n"
                               "Answer these and separate by a comma:\n"
                               "- Name\n"
                               "- Gender (male/female)\n"
                               "- Age\n"
                               "- Weight (lbs)\n"
                               "- Height (ft'in ex. 5'10)\n"
                               "- Goal (cut/bulk/maintain)\n"
                               "- Dietary preferences (ex. halal, vegan, Mediterranean)\n"
                               "- Allergies?")
            await thread.send(initial_questions)
            await interaction.followup.send(f"Created a thread for your meal plan! Check {thread.mention}")

            def check(m):
                return m.author == interaction.user and m.channel == thread

            # Get first response
            response = await self.bot.wait_for('message', timeout=300.0, check=check)
            first_input = [item.strip() for item in response.content.split(',')]
            logger.info(f"Parsed first input: {first_input}")

            if len(first_input) < 8:
                await thread.send("Please provide all required information and separate by commas.")
                return

            # Send follow-up questions
            followup_questions = ("Great! To make a really good meal plan can you also answer these:\n"
                                "- Duration of meal plan in months for your goals (ex. 5 months)\n"
                                "- Daily activity (ex. 10,000 steps or 30 mins cardio)\n"
                                "- Job Physical Demand (Active or Sedentary)\n"
                                "- Health conditions or eating disorders\n"
                                "- Previous experience with meal plans? (yes or no)\n"
                                "- Your schedule?\n"
                                "- Number of meals you want?\n"
                                "- Body Fat Percentage")
            await thread.send(followup_questions)

            # Get second response
            response = await self.bot.wait_for('message', timeout=300.0, check=check)
            second_input = [item.strip() for item in response.content.split(',')]
            logger.info(f"Parsed second input: {second_input}")

            if len(second_input) < 8:
                await thread.send("Please provide all required information and separate by commas.")
                return

            # Convert height to inches
            height = first_input[4]
            if "'" in height:
                ft, inches = height.split("'")
                height_inches = int(ft) * 12 + int(inches.replace('"', ''))
            else:
                height_inches = int(height)

            # Prepare user data
            user_data = {
                'name': first_input[0],
                'gender': first_input[1],
                'age': int(first_input[2]),
                'weight': float(first_input[3]),
                'height': height_inches,
                'goal': first_input[5],
                'diet': first_input[6],
                'allergies': first_input[7],
                'duration': second_input[0],
                'activity': second_input[1],
                'job_demand': second_input[2],
                'health_conditions': second_input[3],
                'experience': second_input[4],
                'schedule': second_input[5],
                'meals_count': second_input[6],
                'body_fat': second_input[7]
            }

            await thread.send("Generating your personalized meal plan... 🔄")

            # Generate meal plan using Assistant
            openai_thread_id, meal_plan = await self.assistant.generate_meal_plan(user_data)
            self.bot.thread_mappings[thread.id] = openai_thread_id

            try:
                # Generate PDF
                pdf_path = generate_meal_plan_pdf(meal_plan, user_data['name'])
                await thread.send(file=discord.File(pdf_path))
                os.remove(pdf_path)  # Clean up

                # Send meal plan text and encourage questions
                await send_long_message(thread, meal_plan)
                await thread.send("\nFeel free to ask questions about your meal plan! 🍽️")

            except Exception as pdf_error:
                logger.error(f"Error generating PDF: {str(pdf_error)}")
                await thread.send("I encountered an error generating the PDF. Here's your meal plan in text format:")
                await send_long_message(thread, meal_plan)

        except asyncio.TimeoutError:
            await thread.send("Response time exceeded. Please try again.")
        except Exception as e:
            logger.error(f"Error in mealplan command: {str(e)}")
            await thread.send("An error occurred while creating your meal plan. Please try again.")


async def setup(bot):
    await bot.add_cog(Commands(bot))