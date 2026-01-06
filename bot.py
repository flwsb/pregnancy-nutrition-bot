"""Main Telegram bot for pregnancy nutrition tracking."""
import logging
import tempfile
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai_service import OpenAIService
from nutrition_db import NutritionDB
from meal_diary import MealDiary
from analyzer import NutritionAnalyzer
from config import TELEGRAM_BOT_TOKEN

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class PregnancyNutritionBot:
    """Main bot class for handling Telegram interactions."""
    
    def __init__(self):
        """Initialize bot services."""
        self.openai_service = OpenAIService()
        self.nutrition_db = NutritionDB()
        self.meal_diary = MealDiary()
        self.analyzer = NutritionAnalyzer()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        from pregnancy_profile import pregnancy_profile
        week = pregnancy_profile.get_current_week()
        trimester = pregnancy_profile.get_trimester_name()
        
        welcome_message = f"""
👋 Willkommen beim Schwangerschafts-Ernährungs-Tracker!

🤰 Du bist in Woche {week} ({trimester} Trimester) - ich bin hier um dir zu helfen!

Ich analysiere Fotos von deinen Mahlzeiten und tracke deine Nährstoffaufnahme.

📸 **So funktioniert's:**
• Schick mir ein Foto deiner Mahlzeit
• Oder beschreibe mir was du gegessen hast
• Ich analysiere es und tracke die Nährstoffe
• Du kannst auch Sprachnachrichten schicken!

💡 **Befehle:**
/start - Diese Willkommensnachricht
/diary - Heutige Ernährungsübersicht
/weekly - Wöchentlicher Ernährungsbericht
/help - Hilfe anzeigen

Schick mir einfach ein Foto von deiner nächsten Mahlzeit! 📷
"""
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
📖 **Hilfe - Schwangerschafts-Ernährungs-Tracker**

**Befehle:**
/start - Willkommensnachricht
/diary - Heutige Ernährungsübersicht
/weekly - Wöchentlicher Bericht
/help - Diese Hilfe

**So funktioniert's:**
1. 📸 Foto von deiner Mahlzeit schicken
2. 🤖 KI analysiert die Mahlzeit
3. 📊 Nährstoffe werden automatisch getrackt
4. 💡 Personalisierte Empfehlungen erhalten

**Du kannst auch:**
• Mahlzeiten mit Text beschreiben ("Ich hatte Hähnchen mit Reis")
• Sprachnachrichten schicken
• Fragen stellen ("Welche Nährstoffe fehlen mir?")
• Nach deiner Schwangerschaftswoche fragen

**Tipps:**
• Mach klare Fotos mit guter Beleuchtung
• Zeig alle Bestandteile der Mahlzeit
• Schau regelmäßig in dein Tagebuch

Fragen? Schreib mir einfach eine Nachricht!
"""
        await update.message.reply_text(help_text)
    
    async def diary_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /diary command - show daily summary."""
        user_id = update.effective_user.id
        
        try:
            analysis = self.analyzer.analyze_daily_intake(user_id)
            summary = self.analyzer.format_daily_summary(analysis)
            await update.message.reply_text(summary)
        except Exception as e:
            logger.error(f"Error getting diary: {e}")
            await update.message.reply_text(
                "❌ Sorry, I couldn't retrieve your diary. Please try again later."
            )
    
    async def weekly_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /weekly command - show weekly summary."""
        user_id = update.effective_user.id
        
        try:
            analysis = self.analyzer.analyze_weekly_intake(user_id)
            summary = self.analyzer.format_weekly_summary(analysis)
            await update.message.reply_text(summary)
        except Exception as e:
            logger.error(f"Error getting weekly report: {e}")
            await update.message.reply_text(
                "❌ Sorry, I couldn't retrieve your weekly report. Please try again later."
            )
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages - conversational responses and meal descriptions."""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "there"
        text = update.message.text
        
        # Check if it's a nutrition question (English + German)
        text_lower = text.lower()
        is_nutrition_question = any(phrase in text_lower for phrase in [
            # English
            'nutrient', 'missing', 'what should i eat', 'what am i missing',
            'what do i need', 'recommendation', 'suggestion', 'what nutrients',
            'deficient', 'low in', 'need more', 'pregnancy week', 'trimester',
            # German
            'nährstoff', 'fehlt', 'was soll ich essen', 'was fehlt mir',
            'was brauche ich', 'empfehlung', 'vorschlag', 'welche nährstoffe',
            'mangel', 'brauche mehr', 'schwangerschaftswoche', 'welche woche',
            'woche bin ich', 'trimester', 'wie weit', 'wie lange noch'
        ])
        
        # Check if it's a meal description (English + German)
        is_meal_description = any(phrase in text_lower for phrase in [
            # English
            'ate', 'had', 'eating', 'meal', 'breakfast', 'lunch', 'dinner',
            'snack', 'food', 'chicken', 'rice', 'salad', 'soup',
            # German
            'gegessen', 'hatte', 'esse', 'mahlzeit', 'frühstück', 'mittagessen',
            'abendessen', 'snack', 'essen', 'hähnchen', 'reis', 'salat', 'suppe',
            'brot', 'ei', 'eier', 'joghurt', 'obst', 'gemüse'
        ])
        
        if is_nutrition_question:
            # Answer nutrition questions with context
            try:
                response = await update.message.reply_text("💭 Lass mich deinen Ernährungsstatus prüfen...")
                answer = self.openai_service.answer_nutrition_question(
                    text, user_id, self.meal_diary, self.analyzer
                )
                await response.edit_text(answer)
            except Exception as e:
                logger.error(f"Error answering nutrition question: {e}", exc_info=True)
                await update.message.reply_text(
                    "❌ Entschuldigung, ich konnte deinen Ernährungsstatus nicht analysieren. Versuch es nochmal oder nutze /diary für deine Übersicht."
                )
        
        elif is_meal_description:
            # Parse meal description and log it
            try:
                processing_msg = await update.message.reply_text(
                    "🍽️ Ich analysiere deine Mahlzeit..."
                )
                
                # Parse time context
                meal_timestamp = self.openai_service.parse_time_context(text)
                
                # Parse meal description - ask LLM for nutrients too
                result = self.openai_service.parse_meal_description_with_nutrients(text)
                food_items = result["food_items"]
                
                if not food_items:
                    await processing_msg.edit_text(
                        "❌ Ich konnte keine Lebensmittel erkennen. Kannst du deine Mahlzeit genauer beschreiben?"
                    )
                    return
                
                # Aggregate nutrients from LLM-provided data
                nutrients = self._aggregate_nutrients_from_items(food_items)
                
                # Save to diary
                meal_id = self.meal_diary.add_meal(user_id, food_items, nutrients, meal_timestamp)
                
                # Format response
                food_list = "\n".join([
                    f"• {item['name']} ({item.get('quantity', 100)}g)"
                    for item in food_items
                ])
                
                time_info = ""
                if meal_timestamp and meal_timestamp.date() != datetime.now().date():
                    time_info = f"\n📅 Eingetragen für: {meal_timestamp.strftime('%d.%m.%Y um %H:%M')}\n"
                
                response = f"✅ Mahlzeit erfolgreich gespeichert!{time_info}\n\n"
                response += f"📝 Erkannte Lebensmittel:\n{food_list}\n\n"
                response += f"📊 Wichtige Nährstoffe:\n"
                response += f"• Kalorien: {nutrients.get('calories', 0):.0f} kcal\n"
                response += f"• Protein: {nutrients.get('protein_g', 0):.1f}g\n"
                response += f"• Eisen: {nutrients.get('iron_mg', 0):.1f}mg\n"
                response += f"• Folsäure: {nutrients.get('folate_mcg', 0):.1f}mcg\n"
                response += f"• Kalzium: {nutrients.get('calcium_mg', 0):.1f}mg\n\n"
                response += f"💡 Frag mich 'Welche Nährstoffe fehlen mir?' für personalisierte Empfehlungen!"
                
                await processing_msg.edit_text(response)
                
            except Exception as e:
                logger.error(f"Error processing meal description: {e}", exc_info=True)
                await update.message.reply_text(
                    "❌ Entschuldigung, ich konnte deine Mahlzeit nicht verarbeiten. Kannst du es anders beschreiben?"
                )
        
        else:
            # General conversation - use AI to respond
            try:
                from pregnancy_profile import pregnancy_profile, LANGUAGE_INSTRUCTION
                profile_context = pregnancy_profile.get_context_string()
                
                # Get context about user's nutrition
                try:
                    daily_analysis = self.analyzer.analyze_daily_intake(user_id)
                    nutrition_context = f"Die Nutzerin hat heute {daily_analysis['meal_count']} Mahlzeiten eingetragen."
                except:
                    nutrition_context = "Die Nutzerin fängt gerade erst an."
                
                prompt = f"""Du bist eine freundliche, unterstützende Ernährungsberaterin für Schwangere.

{LANGUAGE_INSTRUCTION}

WICHTIG: Du KENNST bereits alle Informationen über die Schwangerschaft - beantworte Fragen DIREKT ohne nachzufragen!

{profile_context}

{nutrition_context}

Nutzerin sagte: "{text}"

Antworte natürlich und hilfreich auf Deutsch. Wenn sie fragt was du kannst, erkläre:
- Mahlzeitenfotos analysieren
- Mahlzeiten-Beschreibungen verstehen (Text oder Sprache)
- Fragen zur Ernährung beantworten
- Nährstoffe tracken und fehlende vorschlagen
- Fragen zur Schwangerschaftswoche beantworten

Halte es gesprächig, ermutigend und unterstützend. Sei kurz (2-3 Sätze max)."""

                ai_response = self.openai_service.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": f"Du bist eine freundliche, unterstützende Ernährungsberaterin für Schwangerschaft. {LANGUAGE_INSTRUCTION} Du kennst alle Informationen über diese Nutzerin - beantworte Fragen direkt!"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=200,
                    temperature=0.7
                )
                
                response = ai_response.choices[0].message.content
                await update.message.reply_text(response)
                
            except Exception as e:
                logger.error(f"Error in conversational response: {e}", exc_info=True)
                await update.message.reply_text(
                    f"Hallo {user_name}! 👋\n\nIch kann dir bei der Ernährung helfen! Schick mir:\n"
                    "• 📸 Ein Foto deiner Mahlzeit\n"
                    "• 🗣️ Eine Sprachnachricht mit deiner Mahlzeit\n"
                    "• 💬 Text mit was du gegessen hast\n"
                    "• ❓ Fragen wie 'Welche Nährstoffe fehlen mir?'\n\n"
                    "Frag mich 'Welche Nährstoffe fehlen mir?' für personalisierte Empfehlungen!"
                )
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages - analyze meal images with context awareness."""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "there"
        
        # Check for caption (time context)
        caption = update.message.caption or ""
        meal_timestamp = None
        if caption:
            meal_timestamp = self.openai_service.parse_time_context(caption)
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            "🔍 Ich analysiere deine Mahlzeit... Einen Moment bitte."
        )
        
        try:
            # Get the photo file
            photo = update.message.photo[-1]  # Get highest resolution
            file = await context.bot.get_file(photo.file_id)
            
            # Download photo to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_path = Path(tmp_file.name)
                await file.download_to_drive(tmp_path)
            
            try:
                # Analyze image - LLM provides nutrients directly
                result = self.openai_service.analyze_meal_image(tmp_path)
                food_items = result["food_items"]
                
                # Aggregate nutrients from all food items (LLM provides nutrients per item)
                nutrients = self._aggregate_nutrients_from_items(food_items)
                
                # Save to diary with custom timestamp if provided
                meal_id = self.meal_diary.add_meal(user_id, food_items, nutrients, meal_timestamp)
                
                # Format response
                food_list = "\n".join([
                    f"• {item['name']} ({item.get('quantity', 100)}g)"
                    for item in food_items
                ])
                
                time_info = ""
                if meal_timestamp and meal_timestamp.date() != datetime.now().date():
                    time_info = f"\n📅 Eingetragen für: {meal_timestamp.strftime('%d.%m.%Y um %H:%M')}\n"
                
                response = f"✅ Mahlzeit erfolgreich gespeichert!{time_info}\n\n"
                response += f"📝 Erkannte Lebensmittel:\n{food_list}\n\n"
                response += f"📊 Wichtige Nährstoffe:\n"
                response += f"• Kalorien: {nutrients.get('calories', 0):.0f} kcal\n"
                response += f"• Protein: {nutrients.get('protein_g', 0):.1f}g\n"
                response += f"• Eisen: {nutrients.get('iron_mg', 0):.1f}mg\n"
                response += f"• Folsäure: {nutrients.get('folate_mcg', 0):.1f}mcg\n"
                response += f"• Kalzium: {nutrients.get('calcium_mg', 0):.1f}mg\n\n"
                response += f"💡 Frag mich 'Welche Nährstoffe fehlen mir?' für personalisierte Empfehlungen!"
                
                await processing_msg.edit_text(response)
                
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        
        except Exception as e:
            logger.error(f"Error processing photo: {e}", exc_info=True)
            await processing_msg.edit_text(
                "❌ Entschuldigung, ich konnte dein Foto nicht analysieren. Versuch es mit einem klareren Bild."
            )
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages - transcribe and process."""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "dort"
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            "🎤 Ich transkribiere deine Sprachnachricht..."
        )
        
        try:
            # Get the voice file
            voice = update.message.voice
            file = await context.bot.get_file(voice.file_id)
            
            # Download voice to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as tmp_file:
                tmp_path = Path(tmp_file.name)
                await file.download_to_drive(tmp_path)
            
            try:
                # Transcribe voice
                transcribed_text = self.openai_service.transcribe_voice(str(tmp_path))
                
                # Update processing message
                await processing_msg.edit_text(f"📝 Du hast gesagt: \"{transcribed_text}\"\n\nIch verarbeite das...")
                
                # Check if it's a question or meal description (English + German)
                text_lower = transcribed_text.lower()
                is_nutrition_question = any(phrase in text_lower for phrase in [
                    # English
                    'nutrient', 'missing', 'what should i eat', 'what am i missing',
                    'what do i need', 'recommendation', 'suggestion', 'what nutrients',
                    'pregnancy week', 'trimester',
                    # German
                    'nährstoff', 'fehlt', 'was soll ich essen', 'was fehlt mir',
                    'was brauche ich', 'empfehlung', 'vorschlag', 'welche nährstoffe',
                    'schwangerschaftswoche', 'welche woche', 'woche bin ich', 'trimester'
                ])
                
                is_meal_description = any(phrase in text_lower for phrase in [
                    # English
                    'ate', 'had', 'eating', 'meal', 'breakfast', 'lunch', 'dinner',
                    'snack', 'food', 'chicken', 'rice', 'salad', 'soup',
                    # German
                    'gegessen', 'hatte', 'esse', 'mahlzeit', 'frühstück', 'mittagessen',
                    'abendessen', 'snack', 'essen', 'hähnchen', 'reis', 'salat', 'suppe',
                    'brot', 'ei', 'eier', 'joghurt', 'obst', 'gemüse'
                ])
                
                if is_nutrition_question:
                    # Answer nutrition question
                    answer = self.openai_service.answer_nutrition_question(
                        transcribed_text, user_id, self.meal_diary, self.analyzer
                    )
                    await processing_msg.edit_text(answer)
                
                elif is_meal_description:
                    # Parse meal description and log it - LLM provides nutrients
                    meal_timestamp = self.openai_service.parse_time_context(transcribed_text)
                    result = self.openai_service.parse_meal_description_with_nutrients(transcribed_text)
                    food_items = result["food_items"]
                    
                    if not food_items:
                        await processing_msg.edit_text(
                            "❌ Ich konnte keine Lebensmittel erkennen. Kannst du deine Mahlzeit genauer beschreiben?"
                        )
                        return
                    
                    # Aggregate nutrients from LLM-provided data
                    nutrients = self._aggregate_nutrients_from_items(food_items)
                    
                    # Save to diary
                    meal_id = self.meal_diary.add_meal(user_id, food_items, nutrients, meal_timestamp)
                    
                    # Format response
                    food_list = "\n".join([
                        f"• {item['name']} ({item.get('quantity', 100)}g)"
                        for item in food_items
                    ])
                    
                    time_info = ""
                    if meal_timestamp and meal_timestamp.date() != datetime.now().date():
                        time_info = f"\n📅 Eingetragen für: {meal_timestamp.strftime('%d.%m.%Y um %H:%M')}\n"
                    
                    response = f"✅ Mahlzeit erfolgreich gespeichert!{time_info}\n\n"
                    response += f"📝 Erkannte Lebensmittel:\n{food_list}\n\n"
                    response += f"📊 Wichtige Nährstoffe:\n"
                    response += f"• Kalorien: {nutrients.get('calories', 0):.0f} kcal\n"
                    response += f"• Protein: {nutrients.get('protein_g', 0):.1f}g\n"
                    response += f"• Eisen: {nutrients.get('iron_mg', 0):.1f}mg\n"
                    response += f"• Folsäure: {nutrients.get('folate_mcg', 0):.1f}mcg\n"
                    response += f"• Kalzium: {nutrients.get('calcium_mg', 0):.1f}mg\n\n"
                    response += f"💡 Frag mich 'Welche Nährstoffe fehlen mir?' für personalisierte Empfehlungen!"
                    
                    await processing_msg.edit_text(response)
                
                else:
                    # General conversation - respond conversationally
                    try:
                        from pregnancy_profile import pregnancy_profile, LANGUAGE_INSTRUCTION
                        profile_context = pregnancy_profile.get_context_string()
                        
                        prompt = f"""Du bist eine freundliche, unterstützende Ernährungsberaterin für Schwangere.

{LANGUAGE_INSTRUCTION}

WICHTIG: Du KENNST bereits alle Informationen über die Schwangerschaft - beantworte Fragen DIREKT!

{profile_context}

Sie hat dir gerade eine Sprachnachricht geschickt: "{transcribed_text}"

Antworte natürlich und hilfreich auf Deutsch. Falls unklar, stelle Rückfragen. Kurz halten (2-3 Sätze)."""

                        ai_response = self.openai_service.client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {
                                    "role": "system",
                                    "content": f"Du bist eine freundliche, unterstützende Ernährungsberaterin für Schwangerschaft. {LANGUAGE_INSTRUCTION}"
                                },
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ],
                            max_tokens=200,
                            temperature=0.7
                        )
                        
                        response = ai_response.choices[0].message.content
                        await processing_msg.edit_text(response)
                    except:
                        await processing_msg.edit_text(
                            "Ich hab dich gehört! Erzähl mir mehr über was du Hilfe brauchst - "
                            "beschreib eine Mahlzeit, frag nach Nährstoffen oder stell mir Fragen!"
                        )
                
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        
        except Exception as e:
            logger.error(f"Error processing voice: {e}", exc_info=True)
            await processing_msg.edit_text(
                "❌ Entschuldigung, ich konnte deine Sprachnachricht nicht verarbeiten. Versuch es nochmal oder schreib mir eine Textnachricht."
            )
    
    def _aggregate_nutrients_from_items(self, food_items: List[Dict]) -> Dict[str, float]:
        """
        Aggregate nutrients from food items that already contain nutrition data from LLM.
        
        Args:
            food_items: List of food items, each potentially containing 'nutrients' dict
        
        Returns:
            Aggregated nutrient dictionary
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
            # If item has nutrients directly from LLM, use them
            if "nutrients" in item and item["nutrients"]:
                for nutrient, value in item["nutrients"].items():
                    if nutrient in total_nutrients:
                        total_nutrients[nutrient] += value
            # Otherwise, fall back to database lookup (for backward compatibility)
            elif "name" in item:
                item_nutrients = self.nutrition_db.estimate_nutrients([item])
                for nutrient, value in item_nutrients.items():
                    if nutrient in total_nutrients:
                        total_nutrients[nutrient] += value
        
        return total_nutrients
    
    def run(self):
        """Start the bot."""
        # Create application
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Register handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("diary", self.diary_command))
        application.add_handler(CommandHandler("weekly", self.weekly_command))
        application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        application.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        # Handle text messages (must be last to catch non-command text)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        
        # Start bot
        logger.info("Bot starting...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main entry point."""
    bot = PregnancyNutritionBot()
    bot.run()


if __name__ == "__main__":
    main()

