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
        """Sanitize text while preserving formatting"""
        try:
            if not text:
                return ""

            # Replace common problematic characters while preserving line breaks
            sanitized = text.replace('\r', '\n')

            # Collapse multiple newlines to maximum of two
            while '\n\n\n' in sanitized:
                sanitized = sanitized.replace('\n\n\n', '\n\n')

            # Ensure proper spacing around bold headers
            lines = sanitized.split('\n')
            formatted_lines = []
            for i, line in enumerate(lines):
                if line.strip().startswith('**') and line.strip().endswith('**'):
                    # Add blank line before header if it's not the first line
                    if i > 0 and formatted_lines and not formatted_lines[-1].isspace():
                        formatted_lines.append('')
                    formatted_lines.append(line)
                    formatted_lines.append('')  # Add blank line after header
                else:
                    formatted_lines.append(line)

            sanitized = '\n'.join(formatted_lines)

            # Collapse multiple spaces
            sanitized = ' '.join(part for part in sanitized.split(' ') if part)

            logger.debug(f"Sanitized text, preserving formatting")
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
        """Get response from the Assistant"""
        try:
            start_time = time.time()

            # Modify user message to encourage formatted responses
            user_message = (
                "Please provide a well-formatted response with appropriate spacing. "
                "Use bullet points for lists and include blank lines between sections.\n\n"
                f"{prompt}"
            )
            sanitized_message = self._sanitize_text(user_message)
            logger.debug(f"Message content length: {len(sanitized_message)} characters")

            # Add sanitized message to thread
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=sanitized_message
            )

            # Run the Assistant
            logger.debug(f"Starting Assistant run on thread {thread_id}")
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id,
                instructions=self._sanitize_text("Keep your response concise, under 1000 characters. Focus on essential information only.")
            )

            # Wait for completion with optimized polling
            timeout = 30  # 30 seconds timeout
            poll_interval = 0.2  # Start with 200ms polling interval
            max_poll_interval = 2.0  # Maximum 2 second polling interval

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

                # Exponential backoff for polling interval
                await asyncio.sleep(poll_interval)
                poll_interval = min(poll_interval * 1.5, max_poll_interval)

            # Get messages and sanitize response while preserving formatting
            messages = self.client.beta.threads.messages.list(thread_id=thread_id)
            response = self._sanitize_text(messages.data[0].content[0].text.value)

            # Format bullet points if response contains lists
            if '- ' in response or '• ' in response:
                lines = response.split('\n')
                formatted_lines = []
                for line in lines:
                    if line.strip().startswith('- ') or line.strip().startswith('• '):
                        formatted_lines.append('')  # Add space before list item
                    formatted_lines.append(line)
                response = '\n'.join(formatted_lines)

            # Log processing time
            processing_time = time.time() - start_time
            logger.info(f"Processing time for thread {thread_id}: {processing_time:.2f} seconds")

            return response
        except Exception as e:
            logger.error(f"Error getting assistant response: {str(e)}")
            raise

    async def explain_rift_taps(self):
        """Generate a formatted RIFT & TAPS explanation"""
        logger.info("Generating RIFT & TAPS explanation")
        start_time = time.time()
        thread_id = await self._create_thread()
        logger.info(f"Using OpenAI thread ID: {thread_id}")
        prompt = (
            "Explain the RIFT & TAPS methodology for Ramadan training. "
            "Format your response with these sections:\n"
            "1. Start with 'RIFT Principles:' and list each principle as a bullet point\n"
            "2. Follow with 'TAPS Overview:' and list each TAPS component as a bullet point\n"
            "Be concise and clear."
        )
        response = await self._get_assistant_response(thread_id, prompt)

        # Format the response
        sections = response.split('TAPS')
        if len(sections) < 2:
            # Fallback formatting if the response doesn't contain expected sections
            formatted_response = response
            if not formatted_response.count('- '):
                formatted_response = '- ' + formatted_response.replace('\n', '\n- ').replace('- \n', '\n')
            formatted_response = "**RIFT & TAPS Overview**\n" + formatted_response
        else:
            formatted_response = ("**RIFT Principles**\n" + sections[0].replace('RIFT', '').replace(':', '').strip() + 
                               "\n\n**TAPS Overview**\n" + ('TAPS' + sections[1]).replace('Overview', '').replace(':', '').strip())

            # Add bullet points if not present
            if not formatted_response.count('- '):
                formatted_response = formatted_response.replace('\n', '\n- ').replace('- \n', '\n')

        logger.info(f"Formatted explanation sent: {formatted_response[:100]}...")
        return thread_id, formatted_response

    async def generate_meal_plan(self, user_data):
        """Generate a formatted meal plan with macro and micronutrient breakdowns"""
        logger.info(f"Generating meal plan for user data: {user_data}")
        start_time = time.time()
        thread_id = await self._create_thread()
        logger.info(f"Using OpenAI thread ID: {thread_id}")
        prompt = (
            f"Generate a personalized Ramadan meal plan with macro and micronutrient breakdowns for:\n"
            f"Name: {user_data['name']}\n"
            f"Gender: {user_data['gender']}\n"
            f"Age: {user_data['age']}\n"
            f"Weight: {user_data['weight']} lbs\n"
            f"Height: {user_data['height']} inches\n"
            f"Goal: {user_data['goal']}\n"
            f"Diet: {user_data['diet']}\n"
            f"Allergies: {user_data['allergies']}\n"
            f"Duration: {user_data['duration']}\n"
            f"Activity: {user_data['activity']}\n"
            f"Job Physical Demand: {user_data['job_demand']}\n"
            f"Health Conditions: {user_data['health_conditions']}\n"
            f"Previous Experience: {user_data['experience']}\n"
            f"Schedule: {user_data['schedule']}\n"
            f"Meals Count: {user_data['meals_count']}\n"
            f"Body Fat: {user_data['body_fat']}\n\n"
            "Use these calculation guidelines:\n"
            "1. Calculate BMR using Harris-Benedict equation:\n"
            "   - For males: 88.362 + (13.397 × weight in kg) + (4.799 × height in cm) – (5.677 × age)\n"
            "   - For females: 447.593 + (9.247 × weight in kg) + (3.098 × height in cm) – (4.330 × age)\n"
            "2. Adjust BMR with activity multiplier:\n"
            "   - Sedentary: 1.2\n"
            "   - Lightly active: 1.375\n"
            "   - Moderately active: 1.55\n"
            "   - Very active: 1.725\n"
            "3. Calculate macros based on goal:\n"
            "   For cutting:\n"
            "   - If body fat > 25% (male) or > 35% (female): 0.8-0.9g protein/lb\n"
            "   - Otherwise: 1.1-1.5g protein/lb\n"
            "   - Deficit: 400-1300 calories below TDEE based on duration\n"
            "   For bulking:\n"
            "   - Protein: 0.9-1.35g/lb\n"
            "   - Surplus: 150-300 calories above TDEE\n"
            "   For maintenance:\n"
            "   - Protein: 1.0-1.2g/lb\n"
            "   For all goals:\n"
            "   - Fat: 0.3-0.4g/lb\n"
            "   - Remaining calories from carbs\n"
            "4. Provide practical implementation:\n"
            "   - Include exact portion sizes (e.g., '8 oz chicken breast cooked')\n"
            "   - List calorie counts for all components\n"
            "   - Focus on high-protein, budget-friendly options\n"
            "   - Keep prep time under 30 minutes per meal\n"
            "   - Include pre-workout timing (45-30 mins before exercise)\n"
            "   - Allow one cheat meal per week\n"
            "   - Recommend supplements and hydration goals (minimum 1.25 gallons per day)\n\n"
            "Format the response with:\n"
            "1. Total daily macronutrients (protein, carbs, fats)\n"
            "2. Each meal with bold headings (e.g., **Meal 1: Iftar**)\n"
            "3. Macronutrients per meal\n"
            "4. Total micronutrients (vitamins and minerals)\n"
            "Use bullet points for listing items and nutrients."
        )
        response = await self._get_assistant_response(thread_id, prompt)

        # Format the response sections with bold headers
        formatted_response = response
        for section in ["Meal 1:", "Meal 2:", "Meal 3:", "Meal 4:", "Meal 5:", "Total Macronutrients:", "Total Micronutrients:"]:
            formatted_response = formatted_response.replace(section, f"**{section}**")

        # Add bullet points if not present
        if not formatted_response.count('- '):
            formatted_response = formatted_response.replace('\n', '\n- ').replace('- \n', '\n')

        logger.info(f"Formatted meal plan sent: {formatted_response[:100]}...")
        logger.info(f"Applied calculation context for meal plan: {user_data['name']}")
        return thread_id, formatted_response

    async def ask_question(self, question):
        logger.info(f"Processing question: {question}")
        start_time = time.time()
        thread_id = await self._create_thread()
        logger.info(f"Using OpenAI thread ID: {thread_id}")
        response = await self._get_assistant_response(
            thread_id,
            self._sanitize_text(f"Answer concisely (under 1000 characters): {question}")
        )
        logger.info(f"Processing time for /ask: {time.time() - start_time:.2f} seconds")
        return thread_id, response

    async def continue_conversation(self, thread_id, message):
        """Continue conversation with formatted responses"""
        logger.info(f"Continuing conversation in OpenAI thread: {thread_id}")
        response = await self._get_assistant_response(
            thread_id, 
            self._sanitize_text(message + "\nFormat your response using bullet points where applicable.")
        )

        # Format response with bullet points if it contains multiple lines
        if '\n' in response and not response.count('- '):
            formatted_response = '- ' + response.replace('\n', '\n- ').replace('- \n', '\n')
        else:
            formatted_response = response

        logger.info(f"Formatted follow-up sent: {formatted_response[:100]}...")
        return formatted_response