import discord
from discord.ext import commands
import logging
from utils.assistant import AssistantManager
from utils.message_utils import send_long_message
from utils.pdf_generator import generate_meal_plan_pdf
import asyncio
import os
from utils.usda_api import USDAFoodDataAPI
from utils.open_food_facts_api import OpenFoodFactsAPI

logger = logging.getLogger(__name__)

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.assistant = AssistantManager()
        self.bot.thread_mappings = {}
        self.usda_api = USDAFoodDataAPI()
        self.off_api = OpenFoodFactsAPI()
        logger.info("Commands cog initialized with USDA and Open Food Facts API integration")

    async def _get_or_create_thread(self, ctx, name):
        """Create a new thread or get existing one"""
        # Find existing threads owned by the user
        existing_threads = [t for t in ctx.channel.threads if t.owner_id == ctx.author.id]
        if existing_threads:
            return existing_threads[0]

        # Create a new public thread that will show in the sidebar
        thread = await ctx.channel.create_thread(
            name=name,
            type=discord.ChannelType.public_thread,
            auto_archive_duration=1440  # Archive after 24 hours of inactivity
        )
        logger.info(f"Thread created and formatted for {ctx.command.name}: {name}")
        return thread

    @commands.hybrid_command(
        name='help',
        description='Show available commands and usage information'
    )
    async def help_command(self, ctx):
        help_text = ("Commands: /help, /rift_taps, /mealplan, !ask <question>. "
                    "Chat in threads! Note: I don't have web search access.")
        await ctx.send(help_text)

    @commands.hybrid_command(
        name='rift_taps',
        description='Learn about the RIFT & TAPS methodology'
    )
    async def rift_taps(self, ctx):
        await ctx.defer()

        # Create public thread with proper name
        thread_name = f"RIFT & TAPS for {ctx.author.name}"
        thread = await self._get_or_create_thread(ctx, thread_name)
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
        await ctx.send(f"Created a thread to explain RIFT & TAPS. Check {thread.mention}! 💪")

    @commands.hybrid_command(
        name='mealplan',
        description='Get a personalized Ramadan meal plan'
    )
    async def mealplan(self, ctx):
        await ctx.defer()

        # Create thread for meal plan
        thread_name = f"Meal Plan for {ctx.author.name}"
        thread = await self._get_or_create_thread(ctx, thread_name)
        logger.info(f"Created meal plan thread: {thread_name}")

        try:
            # Step 1: Initial Information Collection
            initial_questions = (
                "Let's create your personalized meal plan 📝\n"
                "Please provide the following information, separated by commas:\n"
                "1. Name\n"
                "2. Gender (male/female)\n"
                "3. Age\n"
                "4. Weight (lbs)\n"
                "5. Height (ft'in or inches, e.g., 5'10 or 70)\n"
                "6. Goal (cut/bulk/maintain)\n"
                "7. Dietary preferences (e.g., halal, vegan, Mediterranean)\n"
                "8. Allergies (if none, write 'none')"
            )
            await thread.send(initial_questions)
            await ctx.send(f"Created a thread for your meal plan! Check {thread.mention}")

            def check(m):
                return m.author == ctx.author and m.channel == thread

            # Get first response
            response = await self.bot.wait_for('message', timeout=300.0, check=check)
            first_input = [item.strip() for item in response.content.split(',')]
            logger.info(f"Parsed first input: {first_input}")

            if len(first_input) < 8:
                await thread.send("Please provide all required information and separate by commas.")
                return

            # Step 2: Additional Information Collection
            followup_questions = (
                "Great! Now let's get some additional details to make your meal plan more personalized:\n"
                "Please provide the following, separated by commas:\n"
                "1. Duration of meal plan in months\n"
                "2. Daily activity level (e.g., sedentary, light, moderate, very active, extra active)\n"
                "3. Job physical demand (sedentary/light/moderate/very active)\n"
                "4. Health conditions (if none, write 'none')\n"
                "5. Previous experience with meal plans (yes/no)\n"
                "6. Schedule (e.g., 9-5, shift work, flexible)\n"
                "7. Number of meals per day\n"
                "8. Body fat percentage (if unknown, write 'unknown')"
            )
            await thread.send(followup_questions)

            # Get second response
            response = await self.bot.wait_for('message', timeout=300.0, check=check)
            second_input = [item.strip() for item in response.content.split(',')]
            logger.info(f"Parsed second input: {second_input}")

            if len(second_input) < 8:
                await thread.send("Please provide all required information and separate by commas.")
                return

            # Parse height to inches
            height = first_input[4]
            try:
                height = str(height).strip()
                if "'" in height:
                    ft, inches = height.split("'")
                    height_inches = int(ft.strip()) * 12 + int(inches.replace('"', '').strip())
                else:
                    height_inches = int(height)
            except (ValueError, TypeError) as e:
                logger.error(f"Error parsing height: {str(e)}")
                await thread.send("Invalid height format. Please use format: 5'10 or just inches.")
                return

            # Prepare user data
            user_data = {
                'name': first_input[0],
                'gender': first_input[1].lower(),
                'age': int(first_input[2]),
                'weight': float(first_input[3]),
                'height': height_inches,
                'goal': first_input[5].lower(),
                'diet': first_input[6],
                'allergies': first_input[7],
                'duration': second_input[0],
                'activity': second_input[1].lower(),
                'job_demand': second_input[2].lower(),
                'health_conditions': second_input[3],
                'experience': second_input[4].lower(),
                'schedule': second_input[5],
                'meals_count': int(second_input[6]),
                'body_fat': second_input[7]
            }

            # Validate user data
            if user_data['weight'] <= 0 or user_data['height'] <= 0 or user_data['age'] <= 0:
                await thread.send("Invalid input values. Please provide valid numbers for weight, height, and age.")
                return

            if user_data['gender'] not in ['male', 'female']:
                await thread.send("Invalid gender. Please specify 'male' or 'female'.")
                return

            if user_data['goal'] not in ['cut', 'bulk', 'maintain']:
                await thread.send("Invalid goal. Please specify 'cut', 'bulk', or 'maintain'.")
                return

            if user_data['activity'] not in ['sedentary', 'light', 'moderate', 'very active', 'extra active']:
                await thread.send("Invalid activity level. Please specify: sedentary, light, moderate, very active, or extra active.")
                return

            if user_data['job_demand'] not in ['sedentary', 'light', 'moderate', 'very active']:
                await thread.send("Invalid job demand level. Please specify: sedentary, light, moderate, or very active.")
                return

            if user_data['meals_count'] < 1 or user_data['meals_count'] > 6:
                await thread.send("Invalid number of meals. Please specify between 1 and 6 meals per day.")
                return

            await thread.send("Generating your personalized meal plan... 🔄")
            await thread.send("Fetching nutritional information from USDA and Open Food Facts databases...")

            # Generate meal plan using Assistant
            openai_thread_id, meal_plan = await self.assistant.generate_meal_plan(user_data)
            self.bot.thread_mappings[thread.id] = openai_thread_id

            # Add nutritional data to meal items
            meal_lines = meal_plan.split('\n')
            enhanced_meal_plan = []

            # Track total nutritional values
            total_protein = 0
            total_carbs = 0
            total_fats = 0
            total_calories = 0

            for line in meal_lines:
                if line.strip().startswith('- ') and ':' not in line:  # Food item line
                    food_item = line.strip('- ').split('(')[0].strip()  # Extract food name

                    # Get macros from USDA API
                    macros = self.usda_api.get_food_macros(food_item)
                    if macros:
                        total_protein += macros['protein']
                        total_carbs += macros['carbs']
                        total_fats += macros['fats']
                        total_calories += macros['calories']

                        # Get micronutrients from Open Food Facts API
                        micros = self.off_api.get_micronutrients(food_item)
                        if micros:
                            line = f"{line.strip()} {self.usda_api.format_macros(macros)} {self.off_api.format_micronutrients(micros)}"
                        else:
                            line = f"{line.strip()} {self.usda_api.format_macros(macros)}"
                    
                enhanced_meal_plan.append(line)

            enriched_meal_plan = '\n'.join(enhanced_meal_plan)

            try:
                # Generate PDF with enriched meal plan
                pdf_path = generate_meal_plan_pdf(enriched_meal_plan, user_data['name'])
                await thread.send(file=discord.File(pdf_path))
                os.remove(pdf_path)  # Clean up

                # Send meal plan text and encourage questions
                await send_long_message(thread, enriched_meal_plan)
                await thread.send("\nFeel free to ask questions about your meal plan! 🍽️")

                # Send summary of total nutrition
                summary = (
                    "📊 **Daily Nutrition Summary**\n"
                    f"Total Calories: {total_calories:.0f}\n"
                    f"Total Protein: {total_protein:.1f}g\n"
                    f"Total Carbs: {total_carbs:.1f}g\n"
                    f"Total Fats: {total_fats:.1f}g"
                )
                await thread.send(summary)

            except Exception as pdf_error:
                logger.error(f"Error generating PDF: {str(pdf_error)}")
                await thread.send("I encountered an error generating the PDF. Here's your meal plan in text format:")
                await send_long_message(thread, enriched_meal_plan)

        except asyncio.TimeoutError:
            await thread.send("Response time exceeded. Please try again.")
        except Exception as e:
            logger.error(f"Error in mealplan command: {str(e)}")
            await thread.send("An error occurred while creating your meal plan. Please try again.")

    @commands.hybrid_command(
        name='ask',
        description='Ask a question about bodybuilding during Ramadan'
    )
    async def ask(self, ctx, *, question: str):
        await ctx.defer()
        # Create single thread with proper name
        thread_name = f"Question from {ctx.author.name}"
        thread = await self._get_or_create_thread(ctx, thread_name)
        logger.info(f"Created question thread: {thread_name}")

        # Send welcome message with question and emoji
        await thread.send(f"Let's answer your question: **{question}** ❓")
        await thread.send("Here's what I found based on Team Akib's guide...")
        await ctx.send(f"Created a thread for your question. Check {thread.mention}! 🤔")

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


async def setup(bot):
    await bot.add_cog(Commands(bot))