import discord
from discord.ext import commands
import logging
from utils.assistant import AssistantManager
from utils.pdf_generator import generate_meal_plan_pdf
import asyncio
import re
import os

logger = logging.getLogger(__name__)

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.assistant = AssistantManager()

    async def _get_or_create_thread(self, message, name):
        """Create a new thread or get existing one"""
        # Find existing threads owned by the user
        existing_threads = [t for t in message.channel.threads if t.owner_id == message.author.id]
        if existing_threads:
            return existing_threads[0]
        return await message.channel.create_thread(name=name)

    @commands.command(name='help')
    async def help_command(self, ctx):
        help_text = ("Commands: /help, /rift_taps, /mealplan, !ask <question>. "
                    "Chat in threads! Note: I don't have web search access.")
        await ctx.send(help_text)

    @commands.command(name='rift_taps')
    async def rift_taps(self, ctx):
        thread = await self._get_or_create_thread(ctx.message, f"RIFT-TAPS-{ctx.author.name}")
        response = await self.assistant.explain_rift_taps()
        await thread.send(response)

    @commands.command(name='mealplan')
    async def mealplan(self, ctx):
        thread = await self._get_or_create_thread(ctx.message, f"Meal-Plan-{ctx.author.name}")

        # Ask for user details
        prompt = ("Answer: Weight (lbs), Height (ft'in or inches), Goal (cut/bulk/maintain), "
                 "Diet (e.g., halal), Allergies?")
        await thread.send(prompt)

        def check(m):
            return m.author == ctx.author and m.channel == thread

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

        except asyncio.TimeoutError:
            await thread.send("Response time exceeded. Please try again.")
        except Exception as e:
            logger.error(f"Error in mealplan command: {e}")
            await thread.send("An error occurred. Please try again.")

    @commands.command(name='ask')
    async def ask(self, ctx, *, question):
        thread = await self._get_or_create_thread(ctx.message, f"Question-{ctx.author.name}")

        # Check if question requires web access
        web_keywords = ['today', 'current', '2024', '2025', 'this year', 'next year']
        needs_web = any(keyword in question.lower() for keyword in web_keywords)

        response = await self.assistant.ask_question(question)

        if needs_web:
            response += ("\n\nNote: I don't have web access, but based on the Team Akib guide, "
                        "this is my best answer. For current info, please check online!")

        await thread.send(response)

async def setup(bot):
    await bot.add_cog(Commands(bot))