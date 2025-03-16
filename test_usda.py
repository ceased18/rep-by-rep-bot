import os
from utils.usda_api import USDAFoodDataAPI

def test_usda_api():
    try:
        api = USDAFoodDataAPI()
        # Test with a common food item
        test_food = "chicken breast"
        print(f"\nTesting USDA API with food item: {test_food}")
        result = api.get_food_macros(test_food)
        print(f"Result: {result}")
        
        if result:
            formatted = api.format_macros(result)
            print(f"Formatted output: {formatted}")
        else:
            print("No data found")
            
    except Exception as e:
        print(f"Error testing USDA API: {str(e)}")

if __name__ == "__main__":
    test_usda_api()
