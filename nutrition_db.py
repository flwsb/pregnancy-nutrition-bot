"""Nutrition knowledge base and calculations for pregnancy nutrition."""
import json
from pathlib import Path
from typing import Dict, List, Optional
from config import NUTRITION_BASE_PATH


class NutritionDB:
    """Manages pregnancy nutrition requirements and food-to-nutrient mapping."""
    
    def __init__(self):
        """Load nutrition knowledge base from JSON file."""
        self.nutrition_base = self._load_nutrition_base()
        self.requirements = self.nutrition_base["pregnancy_requirements"]
        self.food_nutrients = self.nutrition_base["food_nutrients"]
    
    def _load_nutrition_base(self) -> Dict:
        """Load nutrition base from JSON file."""
        if not NUTRITION_BASE_PATH.exists():
            raise FileNotFoundError(f"Nutrition base not found at {NUTRITION_BASE_PATH}")
        
        with open(NUTRITION_BASE_PATH, 'r') as f:
            return json.load(f)
    
    def get_daily_requirements(self) -> Dict[str, float]:
        """Get daily nutritional requirements for pregnancy."""
        return self.requirements["daily"].copy()
    
    def get_weekly_requirements(self) -> Dict[str, float]:
        """Get weekly nutritional requirements for pregnancy."""
        return self.requirements["weekly"].copy()
    
    def estimate_nutrients(self, food_items: List[Dict[str, any]]) -> Dict[str, float]:
        """
        Estimate nutrients from identified food items.
        
        Args:
            food_items: List of dicts with 'name' and optional 'quantity' (in grams)
        
        Returns:
            Dictionary of nutrient values
        """
        total_nutrients = {
            "calories": 0,
            "protein_g": 0,
            "carbohydrates_g": 0,
            "fiber_g": 0,
            "fat_g": 0,
            "folate_mcg": 0,
            "iron_mg": 0,
            "calcium_mg": 0,
            "vitamin_d_iu": 0,
            "vitamin_c_mg": 0,
            "vitamin_a_mcg": 0,
            "vitamin_b12_mcg": 0,
            "zinc_mg": 0,
            "omega3_g": 0
        }
        
        for item in food_items:
            food_name = item.get("name", "").lower()
            quantity = item.get("quantity", 100)  # Default to 100g if not specified
            
            # Try to find matching food in knowledge base
            food_key = self._find_food_key(food_name)
            if food_key and food_key in self.food_nutrients:
                food_data = self.food_nutrients[food_key]
                multiplier = quantity / 100.0  # Convert to per-100g basis
                
                for nutrient, value in food_data.items():
                    if nutrient in total_nutrients:
                        total_nutrients[nutrient] += value * multiplier
        
        return total_nutrients
    
    def _find_food_key(self, food_name: str) -> Optional[str]:
        """
        Find matching food key from knowledge base using fuzzy matching.
        
        Args:
            food_name: Name of the food item
        
        Returns:
            Matching food key or None
        """
        food_name_lower = food_name.lower()
        
        # Direct match
        for key in self.food_nutrients.keys():
            key_base = key.replace("_100g", "").replace("_100ml", "").replace("_cooked", "")
            if key_base in food_name_lower or food_name_lower in key_base:
                return key
        
        # Keyword matching - expanded list
        keywords = {
            "chicken": "chicken_breast_100g",
            "salmon": "salmon_100g",
            "fish": "salmon_100g",
            "spinach": "spinach_100g",
            "broccoli": "broccoli_100g",
            "egg": "eggs_100g",
            "milk": "milk_100ml",
            "yogurt": "yogurt_100g",
            "bread": "whole_grain_bread_100g",
            "rice": "brown_rice_100g_cooked",
            "lentil": "lentils_100g_cooked",
            "avocado": "avocado_100g",
            "banana": "banana_100g",
            "orange": "orange_100g",
            "almond": "almonds_100g",
            "cheese": "cheese_100g",
            "steak": "beef_steak_100g",
            "beef": "beef_100g",
            "asparagus": "asparagus_100g",
            "tomato": "tomatoes_100g",
            "tomatoes": "tomatoes_100g",
            "cherry tomato": "cherry_tomatoes_100g",
            "cherry tomatoes": "cherry_tomatoes_100g",
            "pork": "pork_100g",
            "turkey": "turkey_100g",
            "carrot": "carrots_100g",
            "carrots": "carrots_100g",
            "potato": "potatoes_100g",
            "potatoes": "potatoes_100g",
            "pasta": "pasta_100g_cooked",
            "quinoa": "quinoa_100g_cooked",
            "sweet potato": "sweet_potato_100g",
            "sweet potatoes": "sweet_potato_100g",
            "bell pepper": "bell_pepper_100g",
            "pepper": "bell_pepper_100g",
            "cucumber": "cucumber_100g",
            "zucchini": "zucchini_100g"
        }
        
        # Try keyword matching (check if any keyword appears in food name)
        for keyword, key in keywords.items():
            if keyword in food_name_lower:
                return key
        
        # Try partial matching - check if food name contains any part of database keys
        for key in self.food_nutrients.keys():
            key_words = key.replace("_100g", "").replace("_100ml", "").replace("_cooked", "").split("_")
            # Check if any word from the key appears in the food name
            for key_word in key_words:
                if len(key_word) > 3 and key_word in food_name_lower:
                    return key
        
        return None
    
    def get_food_suggestions(self, missing_nutrients: Dict[str, float]) -> List[str]:
        """
        Get food suggestions based on missing nutrients.
        
        Args:
            missing_nutrients: Dictionary of nutrients that are below requirements
        
        Returns:
            List of suggested food items
        """
        suggestions = []
        
        # Prioritize foods high in missing nutrients
        nutrient_priority = sorted(
            missing_nutrients.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for nutrient, deficit in nutrient_priority[:3]:  # Top 3 missing nutrients
            if deficit > 0:
                foods = self._find_foods_rich_in(nutrient)
                suggestions.extend(foods[:2])  # Top 2 foods per nutrient
        
        return list(set(suggestions))  # Remove duplicates
    
    def _find_foods_rich_in(self, nutrient: str) -> List[str]:
        """Find foods rich in a specific nutrient."""
        foods_by_nutrient = []
        
        for food_key, nutrients in self.food_nutrients.items():
            if nutrient in nutrients and nutrients[nutrient] > 0:
                foods_by_nutrient.append((food_key, nutrients[nutrient]))
        
        # Sort by nutrient content (descending)
        foods_by_nutrient.sort(key=lambda x: x[1], reverse=True)
        
        # Return food names (cleaned up)
        return [food[0].replace("_100g", "").replace("_100ml", "").replace("_cooked", "").replace("_", " ").title() 
                for food in foods_by_nutrient]

