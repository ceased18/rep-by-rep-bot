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

            # Modify user message to encourage compact formatting
            user_message = (
                "Please provide your response with minimal spacing:\n"
                "- For bullet points, use single line breaks (no extra blank lines)\n"
                "- For headings, add only one blank line before and after\n"
                "- Keep responses concise and well-organized\n\n"
                f"{prompt}"
            )
            sanitized_message = self._sanitize_text(user_message)

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

    async def generate_meal_plan(self, user_data):
        """Generate a formatted meal plan"""
        logger.info(f"Generating meal plan for {user_data['name']}")
        thread_id = await self._create_thread()

        # Format user data for prompt
        user_info = "\n".join(f"{k}: {v}" for k, v in user_data.items())
        prompt = (
            f"Generate a personalized meal plan with these exact sections:\n\n"
            f"**Total Daily Macronutrients:**\n"
            f"- List protein, carbs, and fats with target amounts\n\n"
            f"**Suhoor - 45 min before Fajr:**\n"
            f"- List each food item with exact serving size (e.g., '3 large eggs', '2 slices bread')\n"
            f"- Include portion weights where relevant (e.g., '6 oz chicken breast')\n\n"
            f"**Iftar - At Maghrib:**\n"
            f"- List each food item with exact serving size\n"
            f"- Include portion weights where relevant\n\n"
            f"**Post-Taraweeh:**\n"
            f"- List each food item with exact serving size\n"
            f"- Include portion weights where relevant\n\n"
            f"**Total Micronutrients:**\n"
            f"- List essential vitamins and minerals\n\n"
            f"User Data:\n{user_info}\n\n"
            f"Important:\n"
            f"1. Format each meal as a distinct section with its own header\n"
            f"2. Each food item should be on its own line starting with '-'\n"
            f"3. Include specific quantities for all items\n"
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