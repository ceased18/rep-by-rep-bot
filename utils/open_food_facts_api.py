import logging
import requests
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class OpenFoodFactsAPI:
    def __init__(self):
        self.base_url = 'https://world.openfoodfacts.org/cgi/search.pl'
        self.fields = [
            'nutriments',
            'product_name',
            'iron_100g',
            'calcium_100g', 
            'vitamin-a_100g',
            'vitamin-c_100g',
            'vitamin-b12_100g',
            'folates_100g',
            'potassium_100g'
        ]

    def get_micronutrients(self, food_name: str) -> Optional[Dict]:
        """
        Fetch micronutrient data for a food item from Open Food Facts API.
        Returns micronutrient data (iron, calcium, vitamins, etc.) if found.
        """
        try:
            # First check if we have default values for this food
            defaults = {
                'egg': {'iron': 1.2, 'calcium': 50, 'vitamin_a': 160, 'vitamin_c': 0, 'vitamin_b12': 0.6, 'folates': 47, 'potassium': 126},
                'chicken breast': {'iron': 0.7, 'calcium': 15, 'vitamin_a': 40, 'vitamin_c': 0, 'vitamin_b12': 0.3, 'folates': 4, 'potassium': 256},
                'rice': {'iron': 0.2, 'calcium': 10, 'vitamin_a': 0, 'vitamin_c': 0, 'vitamin_b12': 0, 'folates': 3, 'potassium': 35},
                'apple': {'iron': 0.1, 'calcium': 6, 'vitamin_a': 54, 'vitamin_c': 4.6, 'vitamin_b12': 0, 'folates': 3, 'potassium': 107},
                'dates': {'iron': 2.5, 'calcium': 75, 'vitamin_a': 0, 'vitamin_c': 0, 'vitamin_b12': 0, 'folates': 6, 'potassium': 282},
                'almonds': {'iron': 3.7, 'calcium': 269, 'vitamin_a': 0, 'vitamin_c': 0, 'vitamin_b12': 0, 'folates': 44, 'potassium': 733},
                'protein powder': {'iron': 4.0, 'calcium': 200, 'vitamin_a': 0, 'vitamin_c': 0, 'vitamin_b12': 1.0, 'folates': 100, 'potassium': 150}
            }

            # Check if we have default values for this food
            for key in defaults:
                if key in food_name.lower():
                    logger.info(f"Using default values for {food_name}")
                    return defaults[key]

            # If no defaults, try the API
            params = {
                'search_terms': food_name,
                'search_simple': 1,
                'action': 'process',
                'json': 1,
                'fields': ','.join(self.fields),
                'page_size': 1  # Get only best match
            }

            logger.debug(f"Searching Open Food Facts for: {food_name}")
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Found {len(data.get('products', []))} results for {food_name}")

            if not data.get('products'):
                logger.warning(f"No data found for {food_name}")
                return None

            # Extract nutrient data from first match
            product = data['products'][0]
            nutrients = product.get('nutriments', {})

            # Initialize micronutrients dictionary
            micronutrients = {
                'iron': round(float(nutrients.get('iron_100g', 0)), 2),
                'calcium': round(float(nutrients.get('calcium_100g', 0)), 2),
                'vitamin_a': round(float(nutrients.get('vitamin-a_100g', 0)), 2),
                'vitamin_c': round(float(nutrients.get('vitamin-c_100g', 0)), 2),
                'vitamin_b12': round(float(nutrients.get('vitamin-b12_100g', 0)), 2),
                'folates': round(float(nutrients.get('folates_100g', 0)), 2),
                'potassium': round(float(nutrients.get('potassium_100g', 0)), 2)
            }

            logger.info(f"Processed micronutrients for {food_name}: {micronutrients}")
            return micronutrients

        except requests.RequestException as e:
            logger.error(f"API request failed for {food_name}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error processing data for {food_name}: {str(e)}")
            return None

    def format_micronutrients(self, micronutrients: Dict) -> str:
        """Format micronutrient data into a readable string"""
        if not micronutrients:
            return "(Micronutrient data unavailable)"

        formatted = (
            f"(Iron: {micronutrients['iron']}mg, "
            f"Calcium: {micronutrients['calcium']}mg, "
            f"Vit.A: {micronutrients['vitamin_a']}IU, "
            f"Vit.C: {micronutrients['vitamin_c']}mg, "
            f"B12: {micronutrients['vitamin_b12']}mcg, "
            f"Folate: {micronutrients['folates']}mcg, "
            f"K: {micronutrients['potassium']}mg)"
        )
        logger.debug(f"Formatted micronutrients: {formatted}")
        return formatted