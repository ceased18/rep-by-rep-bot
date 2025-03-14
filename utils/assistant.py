import os
from openai import OpenAI
import logging
import time

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
            # Add message to thread
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
                assistant_id=self.assistant_id
            )

            # Wait for completion with timeout
            start_time = time.time()
            timeout = 30  # 30 seconds timeout
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

                time.sleep(0.5)

            # Get messages
            messages = self.client.beta.threads.messages.list(thread_id=thread_id)
            response = messages.data[0].content[0].text.value
            logger.debug(f"Received response from Assistant: {response[:100]}...")
            return response

        except Exception as e:
            logger.error(f"Error getting assistant response: {str(e)}")
            raise

    async def explain_rift_taps(self):
        logger.info("Generating RIFT & TAPS explanation")
        thread_id = await self._create_thread()
        return await self._get_assistant_response(
            thread_id,
            "Explain the RIFT & TAPS methodology for Ramadan training."
        )

    async def generate_meal_plan(self, user_data):
        logger.info(f"Generating meal plan for user data: {user_data}")
        thread_id = await self._create_thread()
        prompt = (
            f"Generate a meal plan following RIFT & TAPS methodology for:\n"
            f"Weight: {user_data['weight']} lbs\n"
            f"Height: {user_data['height']} inches\n"
            f"Goal: {user_data['goal']}\n"
            f"Diet: {user_data['diet']}\n"
            f"Allergies: {user_data['allergies']}"
        )
        return await self._get_assistant_response(thread_id, prompt)

    async def ask_question(self, question):
        logger.info(f"Processing question: {question}")
        thread_id = await self._create_thread()
        return await self._get_assistant_response(thread_id, question)

    async def continue_conversation(self, thread_id, message):
        logger.debug(f"Continuing conversation in thread {thread_id}")
        return await self._get_assistant_response(thread_id, message)