import os
from openai import OpenAI
import logging
import time
import asyncio

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

            # Add instruction for concise response
            system_instruction = "Please provide a concise response under 1000 characters. Focus on key points only."
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="system",
                content=system_instruction
            )

            # Add user message
            logger.debug(f"Adding message to thread {thread_id}")
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=prompt
            )

            # Run the Assistant
            logger.debug(f"Starting Assistant run on thread {thread_id}")
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id,
                instructions="Keep your response concise, under 1000 characters. Focus on essential information only."
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

            # Get messages
            messages = self.client.beta.threads.messages.list(thread_id=thread_id)
            response = messages.data[0].content[0].text.value

            # Log processing time
            processing_time = time.time() - start_time
            logger.info(f"Processing time for thread {thread_id}: {processing_time:.2f} seconds")

            return response

        except Exception as e:
            logger.error(f"Error getting assistant response: {str(e)}")
            raise

    async def explain_rift_taps(self):
        logger.info("Generating RIFT & TAPS explanation")
        start_time = time.time()
        thread_id = await self._create_thread()
        response = await self._get_assistant_response(
            thread_id,
            "Explain the RIFT & TAPS methodology for Ramadan training briefly and concisely."
        )
        logger.info(f"Processing time for /rift_taps: {time.time() - start_time:.2f} seconds")
        return response

    async def generate_meal_plan(self, user_data):
        logger.info(f"Generating meal plan for user data: {user_data}")
        start_time = time.time()
        thread_id = await self._create_thread()
        prompt = (
            f"Generate a meal plan following RIFT & TAPS methodology for:\n"
            f"Weight: {user_data['weight']} lbs\n"
            f"Height: {user_data['height']} inches\n"
            f"Goal: {user_data['goal']}\n"
            f"Diet: {user_data['diet']}\n"
            f"Allergies: {user_data['allergies']}"
        )
        response = await self._get_assistant_response(thread_id, prompt)
        logger.info(f"Processing time for /meal_plan: {time.time() - start_time:.2f} seconds")
        return response

    async def ask_question(self, question):
        logger.info(f"Processing question: {question}")
        start_time = time.time()
        thread_id = await self._create_thread()
        response = await self._get_assistant_response(
            thread_id,
            f"Answer concisely (under 1000 characters): {question}"
        )
        logger.info(f"Processing time for /ask: {time.time() - start_time:.2f} seconds")
        return response

    async def continue_conversation(self, thread_id, message):
        logger.debug(f"Continuing conversation in thread {thread_id}")
        return await self._get_assistant_response(thread_id, message)