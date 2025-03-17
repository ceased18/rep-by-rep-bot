import os
import logging
import requests
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class USDAFoodDataAPI:
    def __init__(self):
        self.api_key = os.environ.get('USDA_API_KEY')
        if not self.api_key:
            raise ValueError("USDA_API_KEY not found in environment variables")
        self.base_url = 'https://api.nal.usda.gov/fdc/v1'

    def get_food_macros(self, food_name: str) -> Optional[Dict]:
        """
        Fetch nutritional data for a food item from USDA FoodData Central API.
        Returns macronutrient data (protein, carbs, fats, calories) if found.
        """
        try:
            # Search for the food item
            search_url = f"{self.base_url}/foods/search"
            params = {
                'api_key': self.api_key,
                'query': food_name,
                'dataType': ['Survey (FNDDS)', 'SR Legacy', 'Foundation'],  # Include all reliable datasets
                'pageSize': 1,  # Get only the best match
                'sortBy': 'score'  # Sort by relevance
            }

            logger.debug(f"Searching for food item: {food_name}")
            response = requests.get(search_url, params=params)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Fetched data for {food_name}: {data.get('totalHits')} results found")

            if not data.get('foods'):
                logger.warning(f"No data found for {food_name}")
                # Return default values for common food items as fallback
                defaults = {
                    'egg': {'protein': 6.0, 'carbs': 0.6, 'fats': 5.0, 'calories': 70},
                    'bread': {'protein': 4.0, 'carbs': 20.0, 'fats': 2.0, 'calories': 110},
                    'chicken breast': {'protein': 28.0, 'carbs': 0.0, 'fats': 3.6, 'calories': 144},
                    'oatmeal': {'protein': 5.0, 'carbs': 27.0, 'fats': 3.0, 'calories': 150},
                    'rice': {'protein': 4.3, 'carbs': 45.0, 'fats': 0.4, 'calories': 205},
                    'milk': {'protein': 3.4, 'carbs': 5.0, 'fats': 3.6, 'calories': 65},
                    'yogurt': {'protein': 10.0, 'carbs': 4.0, 'fats': 0.4, 'calories': 59},
                    'banana': {'protein': 1.1, 'carbs': 27.0, 'fats': 0.3, 'calories': 105},
                    'apple': {'protein': 0.3, 'carbs': 25.0, 'fats': 0.2, 'calories': 95},
                    'dates': {'protein': 2.5, 'carbs': 75.0, 'fats': 0.4, 'calories': 282},
                    'almonds': {'protein': 21.0, 'carbs': 22.0, 'fats': 49.0, 'calories': 579},
                    'protein powder': {'protein': 24.0, 'carbs': 3.0, 'fats': 1.5, 'calories': 120}
                }
                for key in defaults:
                    if key in food_name.lower():
                        logger.info(f"Using default values for {food_name}")
                        return defaults[key]
                return None

            # Extract nutrient data from the first (best) match
            food = data['foods'][0]
            nutrients = food.get('foodNutrients', [])
            logger.debug(f"Found nutrients: {nutrients}")

            # Initialize macros dictionary with default values
            macros = {
                'protein': 0.0,
                'carbs': 0.0,
                'fats': 0.0,
                'calories': 0.0
            }

            # Log all nutrient names for debugging
            nutrient_names = [n.get('nutrientName', '').lower() for n in nutrients]
            logger.debug(f"Available nutrient names: {nutrient_names}")

            # Map nutrient names to our macro categories
            for nutrient in nutrients:
                nutrient_name = nutrient.get('nutrientName', '').lower()
                amount = float(nutrient.get('value', 0))

                if 'protein' in nutrient_name:
                    macros['protein'] = round(amount, 1)
                elif 'carbohydrate' in nutrient_name and 'fiber' not in nutrient_name:
                    macros['carbs'] = round(amount, 1)
                elif 'total lipid' in nutrient_name or 'total fat' in nutrient_name:
                    macros['fats'] = round(amount, 1)
                elif any(term in nutrient_name for term in ['energy', 'calories', 'kcal']):
                    macros['calories'] = round(amount, 1)

            logger.info(f"Processed macros for {food_name}: {macros}")

            # Verify we have some data
            if all(v == 0.0 for v in macros.values()):
                logger.warning(f"All nutrient values are 0 for {food_name}")

            return macros

        except requests.RequestException as e:
            logger.error(f"API request failed for {food_name}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error processing data for {food_name}: {str(e)}")
            return None

    def format_macros(self, macros: Dict) -> str:
        """Format macronutrient data into a readable string"""
        if not macros:
            return "(Nutrition data unavailable)"
        formatted = f"(Protein: {macros['protein']}g, Carbs: {macros['carbs']}g, Fats: {macros['fats']}g, Calories: {int(macros['calories'])})"
        logger.debug(f"Formatted macros: {formatted}")
        return formatted