from django.shortcuts import render
import json
import re
import time
import os
from deep_translator import GoogleTranslator
from rapidfuzz import process, fuzz
import requests
USDA_API_URL = os.getenv("USDA_API_URL", "https://api.nal.usda.gov/fdc/v1/foods/search")
USDA_API_KEY = os.getenv("USDA_API_KEY", "")




#list of some common ingredients that can be mispelled or have variations
household_ingredients = [
    "Cinnamon",
    "Vanilla",
    "Flour",
    "Sugar",
    "Cocoa",
    "Baking Powder",
    "Yeast",
    "Molasses",
    "Turmeric",
    "Cardamom",
    "Coriander",
    "Oregano",
    "Cayenne",
    "Rosemary",
    "Asafoetida",
    "Saffron",
    "Worcestershire Sauce",
    "Mayonnaise",
    "Vinegar",
    "Vinaigrette",
    "Ketchup",
    "Zucchini",
    "Broccoli",
    "Garlic",
    "Potatoes",
    "Tomatoes",
    "Mozzarella",
    "Parmesan",
    "Yogurt",
    "Almond Milk",
    "Paneer",
    "Ghee",
    "Cumin",
    "Mustard Seeds",
    "Fenugreek",
    "Garam Masala",
    "Tamarind",
    "Jaggery",
    "Chickpea Flour",
    "Semolina",
    "Curry Leaves",
    "Lentils",
    "Basmati Rice",
    "Ginger",
    "Cardamom Powder"
]


def convert_from_json(data):
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None
    
    #remove the punctuation from the elements in the list
def clean_elements(elements):
    cleaned_elements = []
    punctuation_pattern = r'[^\w\s]'

    for element in elements:
        # Remove punctuation from the element
        cleaned_element = re.sub(punctuation_pattern, '', element)
        if cleaned_element:  # Ensure the element is not empty after cleaning
            cleaned_elements.append(cleaned_element)

    return cleaned_elements

#translate to english
def translate_to_english(text):
    try:
        translated_text = GoogleTranslator(source='auto', target='en').translate(text)
        return translated_text
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original text if translation fails

#fuzzy matching to find the closest match for an ingredient in the household_ingredients list
def find_closest_ingredient(ingredient):
    closest_match = process.extractOne(ingredient, household_ingredients, scorer=fuzz.token_sort_ratio)
    if closest_match and closest_match[1] >= 80:  # Threshold for a good match
        return closest_match[0]
    return ingredient  # Return original ingredient if no close match is found

#normaize  complete function
def normalize_ingredients(ingredients):
    cleaned_ingredients = clean_elements(ingredients)
    translated_ingredients = [translate_to_english(ingredient) for ingredient in cleaned_ingredients]
    normalized_ingredients = [find_closest_ingredient(ingredient).lower().strip() for ingredient in translated_ingredients]
    return normalized_ingredients

#fetch from usda-api
def fetch_nutri_data(ingredients):
    headers = {
        "Content-Type": "application/json"
    }
    results = []
    for ingredient in ingredients:
        params = {
            "api_key": USDA_API_KEY,
            "query": ingredient,
            "pageSize": 1
        }
        try:
            response = requests.get(USDA_API_URL, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("foods"):
                    results.append(data["foods"][0])  # Append the first result
        except Exception as e:
            print(f"Error fetching data for {ingredient}: {e}")
    return results

 #--------------------------------------------------------------------------------------   
#fetch nutrient data from usda api for a list of ingredients


def fetch_bulk_nutrition(ingredients_list):
    """
    Takes a list of ingredients, queries the USDA API, 
    and returns a dictionary filtered by USDA Nutrient Numbers.
    """
    API_KEY = "YFw0GUa0QFV3mEJghVVPTqvbYMKkim0sU3jMdTAp" 
    search_url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={API_KEY}"
    
    # 1. Define our targets using the STRING nutrientNumber
    TARGET_NUTRIENTS = {
    # 1. Glycemic & Insulin Drivers
    "205": "Carbohydrates (g)",
    "291": "Dietary Fiber (g)",         # Correct USDA Number for Fiber
    "269": "Total Sugars (g)",          # Correct USDA Number for Sugars
    
    # 2. Fatty Acids (Hormonal & Anti-inflammatory)
    "629": "EPA (20:5 n-3) (g)",        # Correct USDA Number
    "621": "DHA (22:6 n-3) (g)",        # Correct USDA Number
    "646": "Polyunsaturated Fats (g)",  # Correct USDA Number
    "606": "Saturated Fats (g)",        # Correct USDA Number
    
    # 3. Key Regulatory Minerals
    "304": "Magnesium (mg)",            # Correct USDA Number
    "309": "Zinc (mg)",                 # Correct USDA Number
    # Note: USDA rarely tracks Chromium reliably in basic searches, 
    # but if it does appear, it usually lacks a standard 3-digit number.
    
    # 4. Critical Micronutrients & Vitamins
    "328": "Vitamin D (D2 + D3) (mcg)", # Correct USDA Number
    "417": "Folate (Total) (mcg)",      # Correct USDA Number
    "418": "Vitamin B-12 (mcg)"         # Correct USDA Number
}
    
    master_nutrition_dict = {}

    # 2. Loop through every ingredient
    for ingredient in ingredients_list:
        print(f"Fetching data for: {ingredient}...")
        
        payload = {
            "query": ingredient,
            "dataType": ["Branded", "Survey (FNDDS)","Foundation", "SR Legacy"],
            "pageSize": 1 
        }
        
        try:
            response = requests.post(search_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                foods = data.get("foods", [])
                
                if not foods:
                    print(f"  -> No data found for {ingredient}")
                    master_nutrition_dict[ingredient] = {"error": "Not found"}
                    continue
                
                best_match = foods[0]
                fdc_id = best_match.get("fdcId")
                raw_nutrients = best_match.get("foodNutrients", [])
                
                ingredient_data = {
                    "fdc_id": fdc_id,
                    "matched_name": best_match.get("description"),
                    "nutrients": {}
                }
                
                # 3. The Bouncer: Filter the nutrients by nutrientNumber
                for nutrient in raw_nutrients:
                    # Look specifically for the 'nutrientNumber' string
                    n_num = nutrient.get("nutrientNumber")
                    
                    if n_num in TARGET_NUTRIENTS:
                        friendly_name = TARGET_NUTRIENTS[n_num]
                        value = nutrient.get("value", 0.0)
                        
                        ingredient_data["nutrients"][friendly_name] = value
                
                master_nutrition_dict[ingredient] = ingredient_data
                
            else:
                print(f"  -> API Error for {ingredient}: {response.status_code}")
                
            time.sleep(0.5) 
            
        except Exception as e:
            print(f"  -> Request failed for {ingredient}: {str(e)}")

    return master_nutrition_dict

# ========================================








# TEST IT OUT!
# ==========================================
if __name__ == "__main__":
    my_recipe = ["capsicum", "paneer", "spinach"]
    final_result = fetch_bulk_nutrition(my_recipe)
    
    print("\n--- FINAL MASTER DICTIONARY (Filtered by Number) ---")
    print(json.dumps(final_result, indent=2))


# Example usage
# if __name__ == "__main__":
#     input_list = ["spinach,/", "eggs?", "avocado."]
#     cleaned_list = clean_elements(input_list)
#     print(cleaned_list)  # Output: ['spinach', 'eggs', 'avocado']

#     # Example usage of normalize_ingredients
#     normalized_list = normalize_ingredients(input_list)
#     print(normalized_list)  # Output: ['spinach', 'eggs', 'avocado']
