"""OpenAI API integration for image analysis and recommendations."""
import base64
from typing import Dict, List, Optional
from openai import OpenAI
from config import OPENAI_API_KEY
from datetime import datetime, timedelta
import re


class OpenAIService:
    """Handles OpenAI API calls for image analysis and recommendations."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.client = OpenAI(api_key=OPENAI_API_KEY)
    
    def analyze_meal_image(self, image_path: str) -> Dict:
        """
        Analyze a meal image using OpenAI Vision API and extract nutrition directly from LLM.
        
        Args:
            image_path: Path to the image file
        
        Returns:
            Dictionary with 'food_items' list (with nutrients) and 'analysis' text
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
                    "content": "You are a nutrition expert analyzing meal photos. For each food you identify, provide its nutritional values per 100g based on standard nutrition databases."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze this meal image and provide detailed nutrition information.

For EACH food item visible, provide:
1. Food name
2. Estimated quantity in grams
3. Complete nutrition values for that quantity (calories, protein_g, carbohydrates_g, fiber_g, fat_g, folate_mcg, iron_mg, calcium_mg, vitamin_d_iu, vitamin_c_mg, vitamin_a_mcg, vitamin_b12_mcg, zinc_mg, omega3_g)

Format your response as a JSON-like structure or clear list. For example:
- Steak (200g): 542 calories, 52g protein, 38g fat, 5.2mg iron, 10.6mg zinc, 5.8mcg B12
- Asparagus (50g): 10 calories, 1.1g protein, 1.1g fiber, 26mcg folate, 1.1mg iron
- Cherry tomatoes (30g): 5 calories, 0.3g protein, 4.1mg vitamin C

Be accurate and comprehensive. Use standard nutrition database values."""
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
            max_tokens=1000
        )
        
        analysis_text = response.choices[0].message.content
        
        # Parse the response to extract food items with nutrients
        food_items = self._parse_food_items_with_nutrients(analysis_text)
        
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
        import re
        food_items = []
        lines = analysis_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Remove bullet points and common prefixes
            line = re.sub(r'^[-•\d.)]+\s*', '', line)
            line = line.strip()
            
            # Pattern 1: "food name - approximately 200g (100g)" or similar
            # Extract the first quantity mentioned (usually the actual estimate)
            match = re.search(r'(.+?)\s*[-–—]\s*(?:approximately\s*)?(\d+)\s*g', line, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                quantity = int(match.group(2))
                # Clean up name - remove extra descriptions
                name = re.sub(r'\s*\([^)]*\)\s*', '', name)  # Remove parenthetical notes
                name = re.sub(r'\s*-\s*.*$', '', name)  # Remove everything after dash
                name = name.strip()
                if name:
                    food_items.append({"name": name, "quantity": quantity})
                continue
            
            # Pattern 2: "150g food name"
            match = re.search(r'(\d+)\s*g\s+(.+)', line, re.IGNORECASE)
            if match:
                quantity = int(match.group(1))
                name = match.group(2).strip()
                # Clean up name
                name = re.sub(r'\s*\([^)]*\)\s*', '', name)
                name = re.sub(r'\s*-\s*.*$', '', name)
                name = name.strip()
                if name:
                    food_items.append({"name": name, "quantity": quantity})
                continue
            
            # Pattern 3: "food name (150g)" or "food name (3 pieces) (30g)"
            # Try to get the last quantity in parentheses
            match = re.findall(r'\((\d+)\s*g\)', line, re.IGNORECASE)
            if match:
                quantity = int(match[-1])  # Use last quantity found
                # Extract food name (everything before first parenthesis)
                name = re.split(r'\(', line)[0].strip()
                name = re.sub(r'\s*-\s*.*$', '', name)
                name = name.strip()
                if name:
                    food_items.append({"name": name, "quantity": quantity})
                continue
            
            # Pattern 4: "food name - description" (try to extract food name)
            if ' - ' in line or '–' in line:
                name = re.split(r'[-–—]', line)[0].strip()
                # Try to find quantity in the description part
                quantity_match = re.search(r'(\d+)\s*g', line, re.IGNORECASE)
                quantity = int(quantity_match.group(1)) if quantity_match else 100
                name = re.sub(r'\s*\([^)]*\)\s*', '', name)
                if name and len(name) > 2:
                    food_items.append({"name": name, "quantity": quantity})
                continue
            
            # Pattern 5: Just food name (default to 100g)
            if line and len(line) > 2:
                # Remove parenthetical notes
                clean_line = re.sub(r'\s*\([^)]*\)\s*', '', line)
                clean_line = clean_line.strip()
                # Skip if it looks like a description or instruction
                if not any(word in clean_line.lower() for word in ['format', 'provide', 'list', 'item', 'food']):
                    food_items.append({"name": clean_line, "quantity": 100})
        
        # If no items found, try to extract from text more loosely
        if not food_items:
            # Look for food mentions with quantities
            food_quantity_pattern = re.findall(r'(\d+)\s*g\s+([a-z]+(?:\s+[a-z]+)*)', analysis_text.lower())
            for quantity, food in food_quantity_pattern:
                food_items.append({"name": food, "quantity": int(quantity)})
        
        # Clean up food names - remove common prefixes/suffixes
        for item in food_items:
            name = item["name"].lower()
            # Remove common descriptive words that aren't part of food name
            name = re.sub(r'\b(sliced|diced|chopped|grilled|roasted|cooked|raw|fresh|approximately|about|around)\b', '', name)
            name = re.sub(r'\s+', ' ', name).strip()
            item["name"] = name
        
        return food_items if food_items else [{"name": "unidentified meal", "quantity": 100}]
    
    def _parse_food_items_with_nutrients(self, analysis_text: str) -> List[Dict[str, any]]:
        """
        Parse food items with nutrition values directly from LLM response.
        
        Args:
            analysis_text: JSON or text response from OpenAI with food and nutrition data
        
        Returns:
            List of food item dictionaries with 'name', 'quantity', and 'nutrients'
        """
        import json
        import re
        
        food_items = []
        
        # Try to parse as JSON first
        try:
            data = json.loads(analysis_text)
            # Handle different JSON structures
            if isinstance(data, dict):
                if "foods" in data:
                    items = data["foods"]
                elif "items" in data:
                    items = data["items"]
                else:
                    items = [data]
                
                for item in items:
                    food_item = {
                        "name": item.get("name", item.get("food", "")),
                        "quantity": item.get("quantity", item.get("grams", 100))
                    }
                    # Extract nutrients
                    nutrients = {}
                    for key in ["calories", "protein_g", "carbohydrates_g", "fiber_g", "fat_g",
                               "folate_mcg", "iron_mg", "calcium_mg", "vitamin_d_iu", "vitamin_c_mg",
                               "vitamin_a_mcg", "vitamin_b12_mcg", "zinc_mg", "omega3_g"]:
                        if key in item:
                            nutrients[key] = float(item[key])
                    food_item["nutrients"] = nutrients
                    food_items.append(food_item)
                return food_items
        except:
            pass  # Fall through to text parsing
        
        # Parse from text format
        lines = analysis_text.split('\n')
        current_food = None
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Pattern: "Food name (quantity): nutrients"
            # Example: "Steak (200g): 542 calories, 52g protein, 38g fat, 5.2mg iron"
            match = re.search(r'^[-•]?\s*(.+?)\s*\((\d+)\s*g\)\s*[:–-]\s*(.+)', line, re.IGNORECASE)
            if match:
                # Save previous food if exists
                if current_food:
                    food_items.append(current_food)
                
                name = match.group(1).strip()
                quantity = int(match.group(2))
                nutrients_text = match.group(3)
                
                # Parse nutrients from text
                nutrients = self._parse_nutrients_from_text(nutrients_text, quantity)
                
                current_food = {
                    "name": name,
                    "quantity": quantity,
                    "nutrients": nutrients
                }
            elif current_food and ':' in line:
                # Continuation line with more nutrients
                nutrients_text = line.split(':', 1)[1] if ':' in line else line
                additional_nutrients = self._parse_nutrients_from_text(nutrients_text, current_food["quantity"])
                current_food["nutrients"].update(additional_nutrients)
        
        # Add last food
        if current_food:
            food_items.append(current_food)
        
        # If still no items, try simpler parsing
        if not food_items:
            # Look for patterns like "200g steak: 542 cal"
            pattern = r'(\d+)\s*g\s+([a-z\s]+?)\s*[:–-]\s*(\d+)\s*cal'
            matches = re.findall(pattern, analysis_text.lower())
            for quantity, name, calories in matches:
                food_items.append({
                    "name": name.strip(),
                    "quantity": int(quantity),
                    "nutrients": {"calories": float(calories)}
                })
        
        return food_items if food_items else [{"name": "unidentified meal", "quantity": 100, "nutrients": {}}]
    
    def _parse_nutrients_from_text(self, text: str, quantity: int) -> Dict[str, float]:
        """
        Parse nutrient values from text description.
        
        Args:
            text: Text containing nutrient information
            quantity: Quantity in grams (to normalize to per-100g if needed)
        
        Returns:
            Dictionary of nutrient values
        """
        import re
        nutrients = {}
        
        # Pattern matching for common nutrients
        patterns = {
            "calories": r'(\d+(?:\.\d+)?)\s*(?:cal|kcal|calories)',
            "protein_g": r'(\d+(?:\.\d+)?)\s*g\s+protein',
            "carbohydrates_g": r'(\d+(?:\.\d+)?)\s*g\s+carbs?',
            "fiber_g": r'(\d+(?:\.\d+)?)\s*g\s+fiber',
            "fat_g": r'(\d+(?:\.\d+)?)\s*g\s+fat',
            "folate_mcg": r'(\d+(?:\.\d+)?)\s*mcg\s+folate',
            "iron_mg": r'(\d+(?:\.\d+)?)\s*mg\s+iron',
            "calcium_mg": r'(\d+(?:\.\d+)?)\s*mg\s+calcium',
            "vitamin_d_iu": r'(\d+(?:\.\d+)?)\s*iu\s+vitamin\s*d',
            "vitamin_c_mg": r'(\d+(?:\.\d+)?)\s*mg\s+vitamin\s*c',
            "vitamin_a_mcg": r'(\d+(?:\.\d+)?)\s*mcg\s+vitamin\s*a',
            "vitamin_b12_mcg": r'(\d+(?:\.\d+)?)\s*mcg\s+(?:vitamin\s*)?b12',
            "zinc_mg": r'(\d+(?:\.\d+)?)\s*mg\s+zinc',
            "omega3_g": r'(\d+(?:\.\d+)?)\s*g\s+omega\s*3'
        }
        
        for nutrient_key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                # If the value seems to be for the full quantity, we keep it as is
                # (LLM should provide values for the actual quantity)
                nutrients[nutrient_key] = value
        
        return nutrients
    
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
    
    def transcribe_voice(self, audio_path: str) -> str:
        """
        Transcribe voice message using OpenAI Whisper API.
        
        Args:
            audio_path: Path to the audio file
        
        Returns:
            Transcribed text
        """
        with open(audio_path, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )
        return transcript.text
    
    def parse_meal_description(self, text: str) -> Dict:
        """
        Parse meal description from text to extract foods and quantities.
        DEPRECATED: Use parse_meal_description_with_nutrients instead.
        """
        return self.parse_meal_description_with_nutrients(text)
    
    def parse_meal_description_with_nutrients(self, text: str) -> Dict:
        """
        Parse meal description from text and extract foods with nutrition values directly from LLM.
        
        Args:
            text: Description of the meal
        
        Returns:
            Dictionary with 'food_items' list (each with nutrients)
        """
        prompt = f"""You are a nutrition expert. Parse this meal description and provide complete nutrition information.

User said: "{text}"

For EACH food item mentioned, provide:
1. Food name
2. Estimated quantity in grams
3. Complete nutrition values for that quantity: calories, protein_g, carbohydrates_g, fiber_g, fat_g, folate_mcg, iron_mg, calcium_mg, vitamin_d_iu, vitamin_c_mg, vitamin_a_mcg, vitamin_b12_mcg, zinc_mg, omega3_g

Format as JSON or clear list. Example:
- Chicken breast (150g): 248 calories, 46.5g protein, 5.4g fat, 1.1mg iron
- Brown rice (100g): 111 calories, 2.6g protein, 23g carbs, 1.8g fiber, 0.4mg iron

Use standard nutrition database values. If quantity not specified, estimate typical serving size."""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a nutrition expert. Provide accurate nutrition values from standard databases."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=600
        )
        
        analysis_text = response.choices[0].message.content
        food_items = self._parse_food_items_with_nutrients(analysis_text)
        
        return {"food_items": food_items, "analysis": analysis_text}
    
    def parse_time_context(self, text: str) -> Optional[datetime]:
        """
        Parse time context from text (e.g., "today's lunch", "yesterday's breakfast").
        
        Args:
            text: Text that may contain time references
        
        Returns:
            Datetime object or None if no time context found
        """
        from datetime import datetime, timedelta
        import re
        
        text_lower = text.lower()
        now = datetime.now()
        
        # Today's meals
        if "today" in text_lower or "this" in text_lower:
            # Default to current time if it's today
            return now
        
        # Yesterday
        if "yesterday" in text_lower:
            yesterday = now - timedelta(days=1)
            # Try to parse meal time
            if "breakfast" in text_lower:
                return yesterday.replace(hour=8, minute=0, second=0, microsecond=0)
            elif "lunch" in text_lower:
                return yesterday.replace(hour=13, minute=0, second=0, microsecond=0)
            elif "dinner" in text_lower or "supper" in text_lower:
                return yesterday.replace(hour=19, minute=0, second=0, microsecond=0)
            return yesterday.replace(hour=12, minute=0, second=0, microsecond=0)
        
        # Days ago
        days_match = re.search(r'(\d+)\s+days?\s+ago', text_lower)
        if days_match:
            days = int(days_match.group(1))
            past_date = now - timedelta(days=days)
            if "breakfast" in text_lower:
                return past_date.replace(hour=8, minute=0, second=0, microsecond=0)
            elif "lunch" in text_lower:
                return past_date.replace(hour=13, minute=0, second=0, microsecond=0)
            elif "dinner" in text_lower or "supper" in text_lower:
                return past_date.replace(hour=19, minute=0, second=0, microsecond=0)
            return past_date.replace(hour=12, minute=0, second=0, microsecond=0)
        
        return None
    
    def answer_nutrition_question(self, question: str, user_id: int, meal_diary, analyzer) -> str:
        """
        Answer nutrition-related questions using context from user's meal diary.
        
        Args:
            question: User's question
            user_id: Telegram user ID
            meal_diary: MealDiary instance
            analyzer: NutritionAnalyzer instance
        
        Returns:
            Answer to the question
        """
        # Get current nutrition status
        try:
            daily_analysis = analyzer.analyze_daily_intake(user_id)
            weekly_analysis = analyzer.analyze_weekly_intake(user_id)
            
            daily_totals = daily_analysis["totals"]
            daily_requirements = daily_analysis["requirements"]
            daily_gaps = daily_analysis["gaps"]
            daily_missing = daily_analysis["missing_nutrients"]
            
            weekly_totals = weekly_analysis["totals"]
            weekly_requirements = weekly_analysis["requirements"]
            weekly_gaps = weekly_analysis["gaps"]
            weekly_missing = weekly_analysis["missing_nutrients"]
            
            # Format context for AI
            context = f"""User's current nutrition status:

DAILY (Today):
- Calories: {daily_totals.get('calories', 0):.0f} / {daily_requirements.get('calories', 0):.0f}
- Protein: {daily_totals.get('protein_g', 0):.1f}g / {daily_requirements.get('protein_g', 0):.1f}g
- Iron: {daily_totals.get('iron_mg', 0):.1f}mg / {daily_requirements.get('iron_mg', 0):.1f}mg
- Folate: {daily_totals.get('folate_mcg', 0):.1f}mcg / {daily_requirements.get('folate_mcg', 0):.1f}mcg
- Calcium: {daily_totals.get('calcium_mg', 0):.1f}mg / {daily_requirements.get('calcium_mg', 0):.1f}mg

Missing nutrients today: {', '.join([k.replace('_', ' ').title() for k, v in daily_missing.items() if v > 0]) if daily_missing else 'None'}

WEEKLY (Past 7 days):
- Calories: {weekly_totals.get('calories', 0):.0f} / {weekly_requirements.get('calories', 0):.0f}
- Protein: {weekly_totals.get('protein_g', 0):.1f}g / {weekly_requirements.get('protein_g', 0):.1f}g
- Iron: {weekly_totals.get('iron_mg', 0):.1f}mg / {weekly_requirements.get('iron_mg', 0):.1f}mg

Missing nutrients this week: {', '.join([k.replace('_', ' ').title() for k, v in weekly_missing.items() if v > 0]) if weekly_missing else 'None'}
"""
        except Exception as e:
            context = "User's nutrition data is not available yet."
        
        prompt = f"""You are a friendly, supportive nutritionist helping a pregnant woman. Answer her question based on her current nutrition status.

{context}

User's question: "{question}"

Provide a helpful, encouraging, and specific answer. If she's asking about missing nutrients, be specific about what's missing and suggest foods to add. Keep it conversational and supportive."""
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a friendly, supportive nutritionist specializing in pregnancy nutrition. Provide practical, encouraging advice based on the user's actual nutrition data."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=400,
            temperature=0.7
        )
        
        return response.choices[0].message.content

