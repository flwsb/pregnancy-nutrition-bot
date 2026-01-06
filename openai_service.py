"""OpenAI API integration for image analysis and recommendations."""
import base64
from typing import Dict, List, Optional
from openai import OpenAI
from config import OPENAI_API_KEY


class OpenAIService:
    """Handles OpenAI API calls for image analysis and recommendations."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.client = OpenAI(api_key=OPENAI_API_KEY)
    
    def analyze_meal_image(self, image_path: str) -> Dict:
        """
        Analyze a meal image using OpenAI Vision API.
        
        Args:
            image_path: Path to the image file
        
        Returns:
            Dictionary with 'food_items' list and 'analysis' text
        """
        # Read image and encode as base64
        with open(image_path, "rb") as f:
            image_bytes = f.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Vision Model Options:
        # - gpt-4o: Best accuracy, ~$2.50-5.00 per 1M input tokens (RECOMMENDED)
        # - gpt-4o-mini: Cheaper, ~$0.60-1.20 per 1M input tokens, lower accuracy
        # - gpt-5.1-mini/gpt-5.2-mini: May not support vision/image inputs (verify in OpenAI docs)
        # Note: Only "o" (omni) models support vision. GPT-5.x models may be text-only.
        response = self.client.chat.completions.create(
            model="gpt-4o",  # Try "gpt-4o-mini" for 4x cost savings if accuracy is acceptable
            messages=[
                {
                    "role": "system",
                    "content": "You are a nutrition expert analyzing meal photos. Identify all foods visible in the image and estimate their quantities in grams. Return a structured list of foods with approximate portions."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please identify all foods in this meal image. For each food item, provide:\n1. The food name\n2. Estimated quantity in grams (e.g., 150g chicken breast, 100g rice)\n\nFormat your response as a clear list that can be parsed."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        analysis_text = response.choices[0].message.content
        
        # Parse the response to extract food items
        food_items = self._parse_food_items(analysis_text)
        
        return {
            "food_items": food_items,
            "analysis": analysis_text
        }
    
    def _parse_food_items(self, analysis_text: str) -> List[Dict[str, any]]:
        """
        Parse food items from OpenAI response text.
        
        Args:
            analysis_text: Text response from OpenAI
        
        Returns:
            List of food item dictionaries with 'name' and 'quantity'
        """
        food_items = []
        lines = analysis_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Try to extract food name and quantity
            # Patterns: "150g chicken breast", "chicken breast (150g)", "100g rice", etc.
            import re
            
            # Pattern 1: "150g food name"
            match = re.search(r'(\d+)\s*g\s+(.+)', line, re.IGNORECASE)
            if match:
                quantity = int(match.group(1))
                name = match.group(2).strip()
                food_items.append({"name": name, "quantity": quantity})
                continue
            
            # Pattern 2: "food name (150g)"
            match = re.search(r'(.+?)\s*\((\d+)\s*g\)', line, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                quantity = int(match.group(2))
                food_items.append({"name": name, "quantity": quantity})
                continue
            
            # Pattern 3: Just food name (default to 100g)
            if line and not line.startswith('-') and len(line) > 2:
                # Remove common prefixes
                clean_line = re.sub(r'^[-•\d.]+\s*', '', line)
                if clean_line:
                    food_items.append({"name": clean_line, "quantity": 100})
        
        # If no items found, try to extract from text more loosely
        if not food_items:
            # Look for any food-like words
            words = re.findall(r'\b([a-z]+(?:\s+[a-z]+)*)\b', analysis_text.lower())
            common_foods = ['chicken', 'salmon', 'fish', 'rice', 'pasta', 'bread', 
                          'egg', 'eggs', 'vegetable', 'salad', 'fruit', 'meat',
                          'broccoli', 'spinach', 'carrot', 'potato', 'tomato']
            for word in words:
                if any(food in word for food in common_foods):
                    food_items.append({"name": word, "quantity": 100})
                    break
        
        return food_items if food_items else [{"name": "unidentified meal", "quantity": 100}]
    
    def generate_recommendations(self, missing_nutrients: Dict[str, float], 
                                daily_totals: Dict[str, float],
                                requirements: Dict[str, float]) -> str:
        """
        Generate personalized meal recommendations using OpenAI Chat API.
        
        Args:
            missing_nutrients: Dictionary of nutrients below requirements
            daily_totals: Current daily nutrient totals
            requirements: Daily nutritional requirements
        
        Returns:
            Recommendation text
        """
        # Format missing nutrients for the prompt
        missing_list = []
        for nutrient, deficit in missing_nutrients.items():
            if deficit > 0:
                nutrient_name = nutrient.replace("_", " ").title()
                missing_list.append(f"- {nutrient_name}: {deficit:.1f} units below target")
        
        missing_text = "\n".join(missing_list) if missing_list else "None - you're meeting all targets!"
        
        prompt = f"""You are a nutritionist helping a pregnant woman optimize her diet. 

Current daily intake:
- Calories: {daily_totals.get('calories', 0):.0f} / {requirements.get('calories', 0):.0f}
- Protein: {daily_totals.get('protein_g', 0):.1f}g / {requirements.get('protein_g', 0):.1f}g
- Iron: {daily_totals.get('iron_mg', 0):.1f}mg / {requirements.get('iron_mg', 0):.1f}mg
- Folate: {daily_totals.get('folate_mcg', 0):.1f}mcg / {requirements.get('folate_mcg', 0):.1f}mcg
- Calcium: {daily_totals.get('calcium_mg', 0):.1f}mg / {requirements.get('calcium_mg', 0):.1f}mg

Nutrients that need attention:
{missing_text}

Provide 2-3 specific, practical meal or snack suggestions that would help address the missing nutrients. Be encouraging and pregnancy-appropriate. Keep it concise (2-3 sentences per suggestion)."""

        # Text Model Options (cost per 1M tokens - input/output):
        # - gpt-4o-mini: $0.15/$0.60 (CHEAPEST - RECOMMENDED)
        # - gpt-5.1-mini: $0.20/$1.60 (2.7x more expensive for output)
        # - gpt-5.2-mini: $0.25/$2.00 (3.3x more expensive for output)
        # GPT-4o-mini is still the most cost-effective for text generation
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",  # Cheapest option. Try "gpt-5.1-mini" if you need better reasoning
            messages=[
                {
                    "role": "system",
                    "content": "You are a friendly, supportive nutritionist specializing in pregnancy nutrition. Provide practical, encouraging advice."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content

