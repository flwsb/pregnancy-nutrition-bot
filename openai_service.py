"""OpenAI API integration for image analysis and recommendations."""
import base64
from typing import Dict, List, Optional
from openai import OpenAI
from config import OPENAI_API_KEY
from datetime import datetime, timedelta
import re
from pregnancy_profile import pregnancy_profile, LANGUAGE, LANGUAGE_INSTRUCTION


class OpenAIService:
    """Handles OpenAI API calls for image analysis and recommendations."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.client = OpenAI(api_key=OPENAI_API_KEY)
    
    def classify_user_intent(self, text: str) -> str:
        """
        Use LLM to classify user intent. Returns one of:
        - 'meal_log': User wants to LOG a meal they ate (e.g., "Ich hatte Hähnchen mit Reis")
        - 'question': User is asking a question or wants information (e.g., "Was habe ich gegessen?", "Welche Nährstoffe fehlen?")
        - 'greeting': User is greeting or just chatting
        
        Args:
            text: User's message
        
        Returns:
            Intent classification string
        """
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Classify the user's intent into exactly ONE of these categories:
- meal_log: User is TELLING you about a meal they want to LOG (stating what they ate/are eating as a fact to record)
- question: User is ASKING something - a question about nutrition, what they've eaten, recommendations, pregnancy, or anything else
- greeting: User is greeting, saying hello, or casual chat

IMPORTANT distinctions:
- "Ich hatte Hähnchen zum Mittag" = meal_log (stating a meal to record)
- "Was habe ich heute gegessen?" = question (asking about past meals)
- "Wie ist meine Ernährung?" = question (asking for evaluation)
- "Zum Frühstück gab es Müsli" = meal_log (reporting breakfast)
- "Welche Nährstoffe fehlen mir?" = question (asking about nutrients)

Respond with ONLY the category name, nothing else."""
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            max_tokens=10,
            temperature=0
        )
        
        intent = response.choices[0].message.content.strip().lower()
        
        # Normalize response
        if "meal" in intent or "log" in intent:
            return "meal_log"
        elif "question" in intent or "ask" in intent:
            return "question"
        elif "greet" in intent or "hello" in intent:
            return "greeting"
        else:
            # Default to question to avoid accidentally logging meals
            return "question"
    
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
        
        # Step 1: Identify foods in the image
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a nutrition expert. Identify foods in the image and estimate portions."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What foods do you see in this meal? List each food with estimated quantity in grams. Be specific about the food type (e.g., 'grilled beef steak' not just 'meat')."
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
        
        foods_identified = response.choices[0].message.content
        
        # Step 2: Get nutrition for the identified foods
        nutrition_response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a nutrition database. Return ONLY valid JSON with nutrition data.
Use this exact format:
{"foods": [{"name": "food name", "quantity_g": 100, "calories": 200, "protein_g": 20, "carbs_g": 10, "fat_g": 5, "fiber_g": 2, "iron_mg": 2.5, "calcium_mg": 50, "folate_mcg": 30, "vitamin_c_mg": 10, "zinc_mg": 3}]}"""
                },
                {
                    "role": "user",
                    "content": f"""Based on these foods identified in a meal, provide complete nutrition data as JSON:

{foods_identified}

Return ONLY the JSON object, no other text. Include all foods with their estimated quantities and full nutritional values."""
                }
            ],
            max_tokens=1000
        )
        
        nutrition_text = nutrition_response.choices[0].message.content
        
        # Parse the JSON response
        food_items = self._parse_nutrition_json(nutrition_text, foods_identified)
        
        return {
            "food_items": food_items,
            "analysis": foods_identified
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
    
    def _parse_nutrition_json(self, nutrition_text: str, fallback_text: str) -> List[Dict[str, any]]:
        """
        Parse nutrition JSON from LLM response.
        
        Args:
            nutrition_text: JSON response from OpenAI
            fallback_text: Original food identification text for fallback
        
        Returns:
            List of food item dictionaries with 'name', 'quantity', and 'nutrients'
        """
        import json
        import re
        
        food_items = []
        
        # Clean up the response - extract JSON if wrapped in markdown
        clean_text = nutrition_text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()
        
        # Try to parse as JSON
        try:
            data = json.loads(clean_text)
            
            # Handle different JSON structures
            items = []
            if isinstance(data, dict):
                if "foods" in data:
                    items = data["foods"]
                elif "items" in data:
                    items = data["items"]
                elif "meal" in data:
                    items = data["meal"] if isinstance(data["meal"], list) else [data["meal"]]
                else:
                    # Try to find any list in the data
                    for key, value in data.items():
                        if isinstance(value, list):
                            items = value
                            break
                    if not items:
                        items = [data]
            elif isinstance(data, list):
                items = data
            
            for item in items:
                if not isinstance(item, dict):
                    continue
                    
                # Extract name
                name = item.get("name", item.get("food", item.get("item", "")))
                if not name:
                    continue
                
                # Extract quantity
                quantity = item.get("quantity_g", item.get("quantity", item.get("grams", item.get("amount_g", 100))))
                if isinstance(quantity, str):
                    # Extract number from string like "200g"
                    match = re.search(r'(\d+)', quantity)
                    quantity = int(match.group(1)) if match else 100
                
                # Extract nutrients - check various key formats
                nutrients = {}
                nutrient_mappings = {
                    "calories": ["calories", "kcal", "energy", "cal"],
                    "protein_g": ["protein_g", "protein", "proteins"],
                    "carbohydrates_g": ["carbs_g", "carbohydrates_g", "carbohydrates", "carbs"],
                    "fiber_g": ["fiber_g", "fiber", "fibre"],
                    "fat_g": ["fat_g", "fat", "fats", "total_fat"],
                    "iron_mg": ["iron_mg", "iron"],
                    "calcium_mg": ["calcium_mg", "calcium"],
                    "folate_mcg": ["folate_mcg", "folate", "folic_acid"],
                    "vitamin_c_mg": ["vitamin_c_mg", "vitamin_c", "vitaminC"],
                    "vitamin_d_iu": ["vitamin_d_iu", "vitamin_d", "vitaminD"],
                    "vitamin_a_mcg": ["vitamin_a_mcg", "vitamin_a", "vitaminA"],
                    "vitamin_b12_mcg": ["vitamin_b12_mcg", "vitamin_b12", "b12"],
                    "zinc_mg": ["zinc_mg", "zinc"],
                    "omega3_g": ["omega3_g", "omega3", "omega_3"]
                }
                
                for standard_key, possible_keys in nutrient_mappings.items():
                    for key in possible_keys:
                        if key in item:
                            try:
                                value = item[key]
                                if isinstance(value, (int, float)):
                                    nutrients[standard_key] = float(value)
                                elif isinstance(value, str):
                                    # Extract number from string
                                    match = re.search(r'([\d.]+)', value)
                                    if match:
                                        nutrients[standard_key] = float(match.group(1))
                            except:
                                pass
                            break
                
                food_items.append({
                    "name": name,
                    "quantity": int(quantity),
                    "nutrients": nutrients
                })
            
            if food_items:
                return food_items
                
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"Error parsing nutrition JSON: {e}")
        
        # Fallback: Try to parse the original food identification text
        return self._parse_food_items_fallback(fallback_text)
    
    def _parse_food_items_fallback(self, text: str) -> List[Dict[str, any]]:
        """
        Fallback parser for when JSON parsing fails.
        """
        import re
        food_items = []
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove bullet points
            line = re.sub(r'^[-•*\d.)]+\s*', '', line)
            
            # Try to find food with quantity
            # Pattern: "Food name - approximately 200g" or "200g of food name" or "food name (200g)"
            patterns = [
                r'(.+?)\s*[-–]\s*(?:approximately\s*)?(\d+)\s*g',  # "Steak - approximately 200g"
                r'(\d+)\s*g\s+(?:of\s+)?(.+)',  # "200g of steak"
                r'(.+?)\s*\((\d+)\s*g\)',  # "Steak (200g)"
                r'(.+?)\s*:\s*(\d+)\s*g',  # "Steak: 200g"
            ]
            
            found = False
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    if pattern.startswith(r'(\d+)'):  # quantity first pattern
                        quantity, name = int(groups[0]), groups[1].strip()
                    else:
                        name, quantity = groups[0].strip(), int(groups[1])
                    
                    if name and len(name) > 1:
                        food_items.append({
                            "name": name,
                            "quantity": quantity,
                            "nutrients": {}  # Will need to estimate
                        })
                        found = True
                        break
            
            # If no pattern matched but line looks like a food
            if not found and len(line) > 2 and not any(x in line.lower() for x in ['total', 'summary', 'note']):
                food_items.append({
                    "name": line[:50],  # Limit length
                    "quantity": 100,
                    "nutrients": {}
                })
        
        return food_items if food_items else [{"name": "meal", "quantity": 100, "nutrients": {}}]
    
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
        # Get pregnancy context
        profile_context = pregnancy_profile.get_context_string()
        trimester_focus = pregnancy_profile.get_trimester_focus_nutrients()
        
        # Format missing nutrients for the prompt
        missing_list = []
        for nutrient, deficit in missing_nutrients.items():
            if deficit > 0:
                nutrient_name = nutrient.replace("_", " ").title()
                missing_list.append(f"- {nutrient_name}: {deficit:.1f} units below target")
        
        missing_text = "\n".join(missing_list) if missing_list else "None - you're meeting all targets!"
        
        prompt = f"""You are a nutritionist helping a pregnant woman optimize her diet.

{LANGUAGE_INSTRUCTION}

{profile_context}

{trimester_focus}

Current daily intake:
- Calories: {daily_totals.get('calories', 0):.0f} / {requirements.get('calories', 0):.0f}
- Protein: {daily_totals.get('protein_g', 0):.1f}g / {requirements.get('protein_g', 0):.1f}g
- Iron: {daily_totals.get('iron_mg', 0):.1f}mg / {requirements.get('iron_mg', 0):.1f}mg
- Folate: {daily_totals.get('folate_mcg', 0):.1f}mcg / {requirements.get('folate_mcg', 0):.1f}mcg
- Calcium: {daily_totals.get('calcium_mg', 0):.1f}mg / {requirements.get('calcium_mg', 0):.1f}mg

Nutrients that need attention:
{missing_text}

Provide 2-3 specific, practical meal or snack suggestions that would help address the missing nutrients, considering her current trimester. Be encouraging and pregnancy-appropriate. Keep it concise (2-3 sentences per suggestion)."""

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
                    "content": f"You are a friendly, supportive nutritionist specializing in pregnancy nutrition. {LANGUAGE_INSTRUCTION} Provide practical, encouraging advice."
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
                language="de"  # German transcription
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
        # Ask LLM to return nutrition data as JSON
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a nutrition database. Return ONLY valid JSON with nutrition data.
Use this exact format:
{"foods": [{"name": "food name", "quantity_g": 100, "calories": 200, "protein_g": 20, "carbs_g": 10, "fat_g": 5, "fiber_g": 2, "iron_mg": 2.5, "calcium_mg": 50, "folate_mcg": 30, "vitamin_c_mg": 10, "zinc_mg": 3}]}"""
                },
                {
                    "role": "user",
                    "content": f"""Extract foods and their complete nutrition from this meal description:

"{text}"

Return ONLY the JSON object. Estimate quantities if not specified. Use standard nutrition values."""
                }
            ],
            max_tokens=800
        )
        
        nutrition_text = response.choices[0].message.content
        food_items = self._parse_nutrition_json(nutrition_text, text)
        
        return {"food_items": food_items, "analysis": text}
    
    def parse_time_context(self, text: str) -> Optional[datetime]:
        """
        Parse time context from text (e.g., "today's lunch", "yesterday's breakfast").
        Supports both English and German time expressions.
        
        Args:
            text: Text that may contain time references
        
        Returns:
            Datetime object or None if no time context found
        """
        from datetime import datetime, timedelta
        import re
        
        text_lower = text.lower()
        now = datetime.now()
        
        # Helper function to determine meal time
        def get_meal_time(text_lower: str, base_date: datetime) -> datetime:
            # Breakfast (English + German)
            if any(term in text_lower for term in ["breakfast", "frühstück", "fruehstueck"]):
                return base_date.replace(hour=8, minute=0, second=0, microsecond=0)
            # Lunch (English + German)
            elif any(term in text_lower for term in ["lunch", "mittagessen", "mittag"]):
                return base_date.replace(hour=13, minute=0, second=0, microsecond=0)
            # Dinner (English + German)
            elif any(term in text_lower for term in ["dinner", "supper", "abendessen", "abend"]):
                return base_date.replace(hour=19, minute=0, second=0, microsecond=0)
            # Snack (English + German)
            elif any(term in text_lower for term in ["snack", "zwischenmahlzeit", "snacks"]):
                return base_date.replace(hour=15, minute=0, second=0, microsecond=0)
            return base_date.replace(hour=12, minute=0, second=0, microsecond=0)
        
        # Today's meals (English + German: "heute")
        if any(term in text_lower for term in ["today", "this", "heute", "jetzt", "gerade"]):
            return get_meal_time(text_lower, now)
        
        # Yesterday (English + German: "gestern")
        if any(term in text_lower for term in ["yesterday", "gestern"]):
            yesterday = now - timedelta(days=1)
            return get_meal_time(text_lower, yesterday)
        
        # Day before yesterday (German: "vorgestern")
        if "vorgestern" in text_lower:
            day_before = now - timedelta(days=2)
            return get_meal_time(text_lower, day_before)
        
        # Days ago (English + German: "vor X tagen")
        days_match = re.search(r'(\d+)\s+days?\s+ago', text_lower)
        if not days_match:
            days_match = re.search(r'vor\s+(\d+)\s+tag', text_lower)
        if days_match:
            days = int(days_match.group(1))
            past_date = now - timedelta(days=days)
            return get_meal_time(text_lower, past_date)
        
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
        # Get pregnancy context
        profile_context = pregnancy_profile.get_context_string()
        trimester_focus = pregnancy_profile.get_trimester_focus_nutrients()
        
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
            nutrition_context = f"""CURRENT NUTRITION STATUS:

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
            nutrition_context = "Nutrition data is not available yet (no meals logged)."
        
        prompt = f"""You are a friendly, supportive nutritionist helping a pregnant woman. Answer her question based on her profile and current nutrition status.

{LANGUAGE_INSTRUCTION}

IMPORTANT: You already KNOW all the pregnancy information below - use it directly to answer questions. Do NOT ask the user for information you already have.

{profile_context}

{trimester_focus}

{nutrition_context}

User's question: "{question}"

Provide a helpful, encouraging, and specific answer considering her pregnancy stage. If she's asking about pregnancy week, due date, or trimester - you KNOW this information, answer directly! If she's asking about missing nutrients, be specific about what's missing and suggest foods to add. Keep it conversational and supportive."""
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a friendly, supportive nutritionist specializing in pregnancy nutrition. {LANGUAGE_INSTRUCTION} You have complete knowledge of this user's pregnancy profile and nutrition status - answer questions directly without asking for information you already have."
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

