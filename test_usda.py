import os
import requests

def test_usda_api():
    api_key = "fWpz53ZpphhHI7aX9S7h78rq0XQX7klP6PoOoAHM"
    base_url = 'https://api.nal.usda.gov/fdc/v1'
    
    try:
        # Test with a simple food search
        search_url = f"{base_url}/foods/search"
        params = {
            'api_key': api_key,
            'query': 'apple',
            'pageSize': 1
        }
        
        print("Testing USDA API connection...")
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        print("\nAPI Test Results:")
        print(f"Status Code: {response.status_code}")
        print(f"Total Results Found: {data.get('totalHits', 0)}")
        
        if data.get('foods'):
            print("\nSample Food Data:")
            food = data['foods'][0]
            print(f"Food Name: {food.get('description', 'N/A')}")
            print(f"Food ID: {food.get('fdcId', 'N/A')}")
        else:
            print("\nNo food data found")
            
    except requests.exceptions.RequestException as e:
        print(f"\nError testing API: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Response Text: {e.response.text}")

if __name__ == "__main__":
    test_usda_api()
