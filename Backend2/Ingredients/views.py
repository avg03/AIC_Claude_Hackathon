from django.shortcuts import render
import json
import re
from deep_translator import GoogleTranslator
from rapidfuzz import process, fuzz

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


# Example usage
if __name__ == "__main__":
    input_list = ["spinach,/", "eggs?", "avocado."]
    cleaned_list = clean_elements(input_list)
    print(cleaned_list)  # Output: ['spinach', 'eggs', 'avocado']

    # Example usage of normalize_ingredients
    normalized_list = normalize_ingredients(input_list)
    print(normalized_list)  # Output: ['spinach', 'eggs', 'avocado']
