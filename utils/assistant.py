import os
import asyncio
from openai import OpenAI
import logging
import time
import re

logger = logging.getLogger(__name__)

class AssistantManager:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        self.assistant_id = os.getenv('ASSISTANT_ID')
        if not self.assistant_id:
            raise ValueError("ASSISTANT_ID environment variable is not set")

        self.client = OpenAI(api_key=self.api_key)
        self.threads = {}
        logger.info("AssistantManager initialized successfully")

    def _sanitize_text(self, text):
        """Sanitize text while preserving minimal formatting"""
        try:
            if not text:
                return ""

            # Replace common problematic characters while preserving line breaks
            sanitized = text.replace('\r', '\n')

            # Collapse multiple newlines to maximum of two
            while '\n\n\n' in sanitized:
                sanitized = sanitized.replace('\n\n\n', '\n\n')

            # Process line by line for minimal formatting
            lines = sanitized.split('\n')
            formatted_lines = []
            in_bullet_list = False
            last_line_bullet = False

            for i, line in enumerate(lines):
                stripped_line = line.strip()

                # Handle headers
                if stripped_line.startswith('**') and stripped_line.endswith('**'):
                    # Add blank line before header if not the first line
                    if i > 0 and formatted_lines:
                        formatted_lines.append('')
                    formatted_lines.append(stripped_line)
                    # Single blank line after header
                    formatted_lines.append('')
                    last_line_bullet = False
                # Handle bullet points with minimal spacing
                elif stripped_line.startswith('- ') or stripped_line.startswith('• '):
                    if last_line_bullet:
                        formatted_lines.append(stripped_line)
                    else:
                        formatted_lines.append(stripped_line)
                        last_line_bullet = True

                # Handle regular text
                else:
                    if last_line_bullet:
                        formatted_lines.append('')
                        last_line_bullet = False
                    formatted_lines.append(stripped_line)


            # Join lines and clean up
            sanitized = '\n'.join(line for line in formatted_lines if line is not None)
            sanitized = ' '.join(part for part in sanitized.split(' ') if part)

            return sanitized
        except Exception as e:
            logger.error(f"Error sanitizing text: {str(e)}")
            return "Error processing message"

    async def _create_thread(self):
        """Create a new thread in the OpenAI Assistant"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                thread = self.client.beta.threads.create()
                logger.debug(f"Created new Assistant thread: {thread.id}")
                return thread.id
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to create thread after {max_retries} attempts: {str(e)}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed, retrying: {str(e)}")
                time.sleep(1)

    async def _get_assistant_response(self, thread_id, prompt):
        """Get response from the Assistant with proper formatting"""
        try:
            start_time = time.time()
            sanitized_message = self._sanitize_text(prompt)

            # Add message to thread
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=sanitized_message
            )

            # Run the Assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )

            # Wait for completion
            timeout = 30
            poll_interval = 0.2
            max_poll_interval = 2.0

            while True:
                if time.time() - start_time > timeout:
                    logger.error(f"Assistant run timed out after {timeout} seconds")
                    raise TimeoutError("Assistant response took too long")

                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )

                if run_status.status == 'completed':
                    break
                elif run_status.status in ['failed', 'cancelled', 'expired']:
                    logger.error(f"Assistant run failed with status: {run_status.status}")
                    raise Exception(f"Assistant run failed: {run_status.status}")

                await asyncio.sleep(poll_interval)
                poll_interval = min(poll_interval * 1.5, max_poll_interval)

            # Get messages and format response
            messages = self.client.beta.threads.messages.list(thread_id=thread_id)
            response = self._sanitize_text(messages.data[0].content[0].text.value)

            logger.info(f"Processing time: {time.time() - start_time:.2f} seconds")
            return response

        except Exception as e:
            logger.error(f"Error getting assistant response: {str(e)}")
            raise

    async def generate_meal_plan(self, user_data):
        """Generate a formatted meal plan using comprehensive nutritional guidelines"""
        logger.info(f"Generating meal plan for {user_data['name']}")
        thread_id = await self._create_thread()

        # Parse user metrics
        weight_lbs = float(user_data['weight'])
        weight_kg = weight_lbs * 0.453592
        height_inches = float(user_data['height'])
        height_cm = height_inches * 2.54
        age = int(user_data['age'])
        gender = user_data['gender'].lower()
        goal = user_data['goal'].lower()

        # Create detailed prompt with nutritional guidelines
        prompt = (
            f"Generate a personalized meal plan with comprehensive nutritional calculations and guidelines.\n\n"
            f"Calculate BMR using:\n"
            f"{'Male: 88.362 + (13.397 × weight in kg) + (4.799 × height in cm) - (5.677 × age)' if gender == 'male' else 'Female: 447.593 + (9.247 × weight in kg) + (3.098 × height in cm) - (4.330 × age)'}\n\n"
            "Adjust BMR with activity multiplier:\n"
            "- Sedentary (little/no exercise): 1.2\n"
            "- Lightly active (1-3 days/week): 1.375\n"
            "- Moderately active (3-5 days/week): 1.55\n"
            "- Very active (6-7 days/week): 1.725\n"
            "- Extra active (very intense exercise/sports): 1.9\n\n"
            f"For {goal} goal, use these macro guidelines:\n"
            "Cutting:\n"
            "- If body fat > 25% (male) or > 35% (female): 0.8-0.9g protein per pound\n"
            "- Otherwise: 1.1-1.5g protein per pound\n"
            "- Fats: 0.3-0.4g per pound\n"
            "- Calories: 400-1300 below TDEE\n"
            "Bulking:\n"
            "- Protein: 0.9-1.35g per pound\n"
            "- Fats: 0.3-0.4g per pound\n"
            "- Calories: 150-300 above TDEE\n"
            "Maintenance:\n"
            "- Protein: 1.0-1.2g per pound\n"
            "- Fats: 0.3-0.4g per pound\n"
            "- Calories: At TDEE\n"
            "Remaining calories go to carbohydrates (4 calories per gram)\n\n"
            "Format the meal plan with these exact sections:\n\n"
            "**Total Daily Macronutrients:**\n"
            "- Calculate and list target protein, carbs, and fats based on above formulas\n"
            "- Show daily calorie target\n\n"
            "**Suhoor - 45 min before Fajr:**\n"
            "- Focus on slow-digesting proteins and complex carbs\n"
            "- List each food item with exact serving size\n"
            "- Include portion weights\n"
            "- End with 'Meal Totals' line\n\n"
            "**Iftar - At Maghrib:**\n"
            "- Start with easily digestible foods\n"
            "- Include lean proteins and complex carbs\n"
            "- List specific portions\n"
            "- End with 'Meal Totals' line\n\n"
            "**Post-Taraweeh:**\n"
            "- Focus on protein synthesis and recovery\n"
            "- Keep meals simple and quick to prepare\n"
            "- Include portion sizes\n"
            "- End with 'Meal Totals' line\n\n"
            "**Total Micronutrients:**\n"
            "- Estimate based on food choices\n"
            "- Include: Vitamin A, Vitamin C, Calcium, Iron, others\n"
            "- Show typical values (e.g., 100g broccoli: 89mg Vitamin C)\n"
            "- Include electrolyte recommendations\n\n"
            "**Supplement Recommendations:**\n"
            "- Timing for supplements\n"
            "- Hydration guidelines (minimum 1.25 gallons per day)\n\n"
            f"User Data:\n"
            f"Weight: {weight_lbs}lbs ({weight_kg:.1f}kg)\n"
            f"Height: {height_inches}in ({height_cm:.1f}cm)\n"
            f"Age: {age}\n"
            f"Gender: {gender}\n"
            f"Goal: {goal}\n"
            f"Diet: {user_data['diet']}\n"
            f"Allergies: {user_data['allergies']}\n"
            f"Activity: {user_data['activity']}\n"
            f"Job Demand: {user_data['job_demand']}\n"
            f"Duration: {user_data['duration']}\n"
            f"Experience: {user_data['experience']}\n"
            f"Schedule: {user_data['schedule']}\n"
            f"Meals Count: {user_data['meals_count']}\n"
            f"Body Fat %: {user_data['body_fat']}\n\n"
            "Important Guidelines:\n"
            "1. Each meal should take 30 minutes or less to prepare\n"
            "2. Use accessible, budget-friendly ingredients\n"
            "3. Account for dietary restrictions and preferences\n"
            "4. Format each meal as a distinct section\n"
            "5. List each food item on its own line with '-'\n"
            "6. Include 'Meal Totals' after each meal section\n"
            "7. Emphasize the importance of food weighing\n"
            "8. Show all macros: 'Protein: Xg, Carbs: Yg, Fats: Zg, Calories: W'\n"
        )

        response = await self._get_assistant_response(thread_id, prompt)
        logger.info(f"Applied calculation context for meal plan: {user_data['name']}")
        return thread_id, response

    async def explain_rift_taps(self):
        """Generate a formatted RIFT & TAPS explanation"""
        logger.info("Generating RIFT & TAPS explanation")
        thread_id = await self._create_thread()
        prompt = (
            "Explain the RIFT & TAPS methodology for Ramadan training.\n"
            "Use this exact format:\n"
            "**RIFT Principles:**\n"
            "- List each principle with bullet points\n"
            "- Use a single line break between points\n\n"
            "**TAPS Overview:**\n"
            "- List each component with bullet points\n"
            "- Use a single line break between points\n\n"
            "Important: Use only single line breaks between bullet points, no extra spacing."
        )
        response = await self._get_assistant_response(thread_id, prompt)
        return thread_id, response

    async def ask_question(self, question):
        """Process and format a user question"""
        logger.info(f"Processing question: {question}")
        thread_id = await self._create_thread()
        response = await self._get_assistant_response(thread_id, question)
        return thread_id, response

    async def continue_conversation(self, thread_id, message):
        """Continue conversation with consistent formatting"""
        logger.info(f"Continuing conversation in thread: {thread_id}")
        response = await self._get_assistant_response(
            thread_id,
            message
        )
        return response