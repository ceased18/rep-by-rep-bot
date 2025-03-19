import os
import asyncio
from openai import OpenAI
import logging
import time
import re
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

class AssistantManager:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.assistant_id = os.getenv('ASSISTANT_ID')
        logger.info("AssistantManager initialized with OpenAI client")

    def _sanitize_text(self, text):
        """Sanitize text by removing markdown and special characters"""
        return text.replace('*', '').replace('_', '').replace('`', '').strip()

    async def _create_thread(self):
        """Create a new thread for conversation"""
        thread = self.client.beta.threads.create()
        logger.info(f"Created new thread: {thread.id}")
        return thread.id

    async def _get_assistant_response(self, thread_id, message):
        """Get response from assistant"""
        try:
            # Add user message to thread
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message
            )
            logger.info(f"Added user message to thread {thread_id}")

            # Run the assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )
            logger.info(f"Started assistant run: {run.id}")

            # Wait for completion
            while True:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                if run.status == 'completed':
                    break
                elif run.status == 'failed':
                    logger.error(f"Assistant run failed: {run.last_error}")
                    raise Exception("Assistant run failed")
                await asyncio.sleep(1)

            # Get assistant's response
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id
            )
            response = messages.data[0].content[0].text.value
            logger.info(f"Got assistant response for thread {thread_id}")
            return response

        except Exception as e:
            logger.error(f"Error getting assistant response: {str(e)}")
            raise

    async def generate_meal_plan(self, user_data):
        """Generate a personalized meal plan based on user data"""
        try:
            # Create new thread
            thread_id = await self._create_thread()

            # Calculate BMR using Harris-Benedict equation
            weight_kg = user_data['weight'] * 0.453592  # Convert lbs to kg
            height_cm = user_data['height'] * 2.54  # Convert inches to cm

            if user_data['gender'] == 'male':
                bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * user_data['age'])
            else:
                bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * user_data['age'])

            # Activity multiplier
            activity_multipliers = {
                'sedentary': 1.2,
                'light': 1.375,
                'moderate': 1.55,
                'very active': 1.725,
                'extra active': 1.9
            }
            tdee = bmr * activity_multipliers[user_data['activity']]

            # Adjust calories based on goal
            if user_data['goal'] == 'cut':
                calories = tdee - 500  # 500 calorie deficit
            elif user_data['goal'] == 'bulk':
                calories = tdee + 500  # 500 calorie surplus
            else:  # maintain
                calories = tdee

            # Calculate macros
            protein_per_lb = 1.0 if user_data['goal'] == 'maintain' else 1.2
            protein = user_data['weight'] * protein_per_lb
            fats = (calories * 0.25) / 9  # 25% of calories from fat
            carbs = (calories - (protein * 4 + fats * 9)) / 4  # Remaining calories from carbs

            # Prepare prompt for meal plan generation
            prompt = f"""Generate a detailed meal plan for a {user_data['age']}-year-old {user_data['gender']} with the following specifications:

Current Stats:
- Weight: {user_data['weight']} lbs
- Height: {user_data['height']} inches
- Activity Level: {user_data['activity']}
- Job Physical Demand: {user_data['job_demand']}
- Body Fat: {user_data['body_fat']}

Goals:
- Primary Goal: {user_data['goal']}
- Duration: {user_data['duration']} months
- Meals per day: {user_data['meals_count']}

Dietary Requirements:
- Preferences: {user_data['diet']}
- Allergies: {user_data['allergies']}
- Health Conditions: {user_data['health_conditions']}

Daily Caloric Target: {calories:.0f} calories
Macronutrient Split:
- Protein: {protein:.0f}g ({protein * 4:.0f} calories)
- Carbs: {carbs:.0f}g ({carbs * 4:.0f} calories)
- Fats: {fats:.0f}g ({fats * 9:.0f} calories)

Please provide a detailed meal plan that:
1. Distributes meals throughout the day based on the schedule: {user_data['schedule']}
2. Includes specific portion sizes in grams/ounces
3. Lists all ingredients with exact measurements
4. Provides preparation instructions
5. Includes timing recommendations for each meal
6. Accounts for dietary restrictions and preferences
7. Provides alternatives for common ingredients if needed

Format the output as follows:
[Meal 1]
- Food item 1 (portion)
- Food item 2 (portion)
Total: X calories, Xg protein, Xg carbs, Xg fats

[Meal 2]
...

Please ensure all portions are precise and the total daily calories match the target within 50 calories."""

            # Get meal plan from assistant
            meal_plan = await self._get_assistant_response(thread_id, prompt)
            logger.info(f"Generated meal plan for user {user_data['name']}")

            return thread_id, meal_plan

        except Exception as e:
            logger.error(f"Error generating meal plan: {str(e)}")
            raise

    async def explain_rift_taps(self):
        """Explain the RIFT & TAPS methodology"""
        try:
            thread_id = await self._create_thread()
            prompt = """Please explain the RIFT & TAPS methodology for bodybuilding during Ramadan, including:
1. What RIFT & TAPS stands for
2. The core principles
3. How to implement it
4. Benefits and considerations
5. Common mistakes to avoid

Format the response in a clear, structured way with emojis for better readability."""
            
            response = await self._get_assistant_response(thread_id, prompt)
            logger.info("Generated RIFT & TAPS explanation")
            return thread_id, response

        except Exception as e:
            logger.error(f"Error explaining RIFT & TAPS: {str(e)}")
            raise

    async def ask_question(self, question):
        """Answer a specific question about bodybuilding during Ramadan"""
        try:
            thread_id = await self._create_thread()
            prompt = f"""Please answer this question about bodybuilding during Ramadan: {question}

Provide a detailed, accurate response based on the RIFT & TAPS methodology and best practices.
Include specific examples and practical tips where relevant.
Format the response in a clear, easy-to-read way with appropriate emojis."""
            
            response = await self._get_assistant_response(thread_id, prompt)
            logger.info(f"Answered question: {question}")
            return thread_id, response

        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            raise

    async def continue_conversation(self, thread_id, message):
        """Continue conversation with consistent formatting"""
        logger.info(f"Continuing conversation in thread: {thread_id}")
        response = await self._get_assistant_response(
            thread_id,
            message
        )
        return response