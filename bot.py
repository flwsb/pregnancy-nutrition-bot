"""Main Telegram bot for pregnancy nutrition tracking."""
import logging
import tempfile
import os
from pathlib import Path
from datetime import datetime
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
        welcome_message = """
👋 Welcome to Pregnancy Nutrition Tracker!

I help you track your nutrition during pregnancy by analyzing photos of your meals.

📸 **How to use:**
• Send me a photo of your meal
• I'll analyze it and log the nutrients
• Use /diary to see today's summary
• Use /weekly to see your weekly report

💡 **Commands:**
/start - Show this welcome message
/diary - View today's nutrition summary
/weekly - View weekly nutrition report
/help - Show help information

Let's get started! Send me a photo of your next meal! 📷
"""
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
📖 **Help - Pregnancy Nutrition Tracker**

**Commands:**
/start - Welcome message and instructions
/diary - View today's nutrition summary
/weekly - View weekly nutrition report
/help - Show this help message

**How it works:**
1. 📸 Take a photo of your meal
2. 🤖 I analyze it using AI
3. 📊 Nutrients are automatically logged
4. 💡 Get personalized recommendations

**Tips:**
• Take clear photos with good lighting
• Include all items in your meal
• Check your diary regularly to track progress

Questions? Just send a message and I'll help!
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
        
        # Check if it's a nutrition question
        text_lower = text.lower()
        is_nutrition_question = any(phrase in text_lower for phrase in [
            'nutrient', 'missing', 'what should i eat', 'what am i missing',
            'what do i need', 'recommendation', 'suggestion', 'what nutrients',
            'deficient', 'low in', 'need more'
        ])
        
        # Check if it's a meal description
        is_meal_description = any(phrase in text_lower for phrase in [
            'ate', 'had', 'eating', 'meal', 'breakfast', 'lunch', 'dinner',
            'snack', 'food', 'chicken', 'rice', 'salad', 'soup'
        ])
        
        if is_nutrition_question:
            # Answer nutrition questions with context
            try:
                response = await update.message.reply_text("💭 Let me check your nutrition status...")
                answer = self.openai_service.answer_nutrition_question(
                    text, user_id, self.meal_diary, self.analyzer
                )
                await response.edit_text(answer)
            except Exception as e:
                logger.error(f"Error answering nutrition question: {e}", exc_info=True)
                await update.message.reply_text(
                    "❌ Sorry, I couldn't analyze your nutrition status. Try asking again or use /diary to see your summary."
                )
        
        elif is_meal_description:
            # Parse meal description and log it
            try:
                processing_msg = await update.message.reply_text(
                    "🍽️ Processing your meal description..."
                )
                
                # Parse time context
                meal_timestamp = self.openai_service.parse_time_context(text)
                
                # Parse meal description
                result = self.openai_service.parse_meal_description(text)
                food_items = result["food_items"]
                
                if not food_items:
                    await processing_msg.edit_text(
                        "❌ I couldn't identify any foods in your description. Could you describe your meal more specifically?"
                    )
                    return
                
                # Calculate nutrients
                nutrients = self.nutrition_db.estimate_nutrients(food_items)
                
                # Save to diary
                meal_id = self.meal_diary.add_meal(user_id, food_items, nutrients, meal_timestamp)
                
                # Format response
                food_list = "\n".join([
                    f"• {item['name']} ({item.get('quantity', 100)}g)"
                    for item in food_items
                ])
                
                time_info = ""
                if meal_timestamp and meal_timestamp.date() != datetime.now().date():
                    time_info = f"\n📅 Logged for: {meal_timestamp.strftime('%B %d, %Y at %I:%M %p')}\n"
                
                response = f"✅ Meal logged successfully!{time_info}\n\n"
                response += f"📝 Foods identified:\n{food_list}\n\n"
                response += f"📊 Key nutrients:\n"
                response += f"• Calories: {nutrients.get('calories', 0):.0f} kcal\n"
                response += f"• Protein: {nutrients.get('protein_g', 0):.1f}g\n"
                response += f"• Iron: {nutrients.get('iron_mg', 0):.1f}mg\n"
                response += f"• Folate: {nutrients.get('folate_mcg', 0):.1f}mcg\n"
                response += f"• Calcium: {nutrients.get('calcium_mg', 0):.1f}mg\n\n"
                response += f"💡 Ask me 'what nutrients am I missing?' to get personalized recommendations!"
                
                await processing_msg.edit_text(response)
                
            except Exception as e:
                logger.error(f"Error processing meal description: {e}", exc_info=True)
                await update.message.reply_text(
                    "❌ Sorry, I couldn't process your meal description. Could you try describing it differently?"
                )
        
        else:
            # General conversation - use AI to respond
            try:
                # Get context about user's nutrition
                try:
                    daily_analysis = self.analyzer.analyze_daily_intake(user_id)
                    context = f"User has logged {daily_analysis['meal_count']} meals today."
                except:
                    context = "User is just getting started."
                
                prompt = f"""You are a friendly, supportive nutritionist helping a pregnant woman track her nutrition. 
                
{context}

User said: "{text}"

Respond naturally and helpfully. If they're asking what you can do, explain you can:
- Analyze meal photos
- Understand meal descriptions (text or voice)
- Answer nutrition questions
- Track nutrients and suggest what's missing

Keep it conversational, encouraging, and supportive. Be brief (2-3 sentences max)."""

                ai_response = self.openai_service.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a friendly, supportive nutritionist specializing in pregnancy nutrition."
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
                    f"Hi {user_name}! 👋\n\nI can help you track your nutrition! Send me:\n"
                    "• 📸 A photo of your meal\n"
                    "• 🗣️ A voice message describing your meal\n"
                    "• 💬 Text describing what you ate\n"
                    "• ❓ Questions like 'what nutrients am I missing?'\n\n"
                    "Try asking me 'what nutrients am I missing?' to get personalized recommendations!"
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
            "🔍 Analyzing your meal... This may take a moment."
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
                # Analyze image
                result = self.openai_service.analyze_meal_image(tmp_path)
                food_items = result["food_items"]
                
                # Calculate nutrients
                nutrients = self.nutrition_db.estimate_nutrients(food_items)
                
                # Save to diary with custom timestamp if provided
                meal_id = self.meal_diary.add_meal(user_id, food_items, nutrients, meal_timestamp)
                
                # Format response
                food_list = "\n".join([
                    f"• {item['name']} ({item.get('quantity', 100)}g)"
                    for item in food_items
                ])
                
                time_info = ""
                if meal_timestamp and meal_timestamp.date() != datetime.now().date():
                    time_info = f"\n📅 Logged for: {meal_timestamp.strftime('%B %d, %Y at %I:%M %p')}\n"
                
                response = f"✅ Meal logged successfully!{time_info}\n\n"
                response += f"📝 Foods identified:\n{food_list}\n\n"
                response += f"📊 Key nutrients:\n"
                response += f"• Calories: {nutrients.get('calories', 0):.0f} kcal\n"
                response += f"• Protein: {nutrients.get('protein_g', 0):.1f}g\n"
                response += f"• Iron: {nutrients.get('iron_mg', 0):.1f}mg\n"
                response += f"• Folate: {nutrients.get('folate_mcg', 0):.1f}mcg\n"
                response += f"• Calcium: {nutrients.get('calcium_mg', 0):.1f}mg\n\n"
                response += f"💡 Ask me 'what nutrients am I missing?' to get personalized recommendations!"
                
                await processing_msg.edit_text(response)
                
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        
        except Exception as e:
            logger.error(f"Error processing photo: {e}", exc_info=True)
            await processing_msg.edit_text(
                "❌ Sorry, I couldn't analyze your meal photo. Please try again with a clearer image."
            )
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages - transcribe and process."""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "there"
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            "🎤 Transcribing your voice message..."
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
                await processing_msg.edit_text(f"📝 You said: \"{transcribed_text}\"\n\nProcessing...")
                
                # Check if it's a question or meal description
                text_lower = transcribed_text.lower()
                is_nutrition_question = any(phrase in text_lower for phrase in [
                    'nutrient', 'missing', 'what should i eat', 'what am i missing',
                    'what do i need', 'recommendation', 'suggestion', 'what nutrients'
                ])
                
                is_meal_description = any(phrase in text_lower for phrase in [
                    'ate', 'had', 'eating', 'meal', 'breakfast', 'lunch', 'dinner',
                    'snack', 'food', 'chicken', 'rice', 'salad', 'soup'
                ])
                
                if is_nutrition_question:
                    # Answer nutrition question
                    answer = self.openai_service.answer_nutrition_question(
                        transcribed_text, user_id, self.meal_diary, self.analyzer
                    )
                    await processing_msg.edit_text(answer)
                
                elif is_meal_description:
                    # Parse meal description and log it
                    meal_timestamp = self.openai_service.parse_time_context(transcribed_text)
                    result = self.openai_service.parse_meal_description(transcribed_text)
                    food_items = result["food_items"]
                    
                    if not food_items:
                        await processing_msg.edit_text(
                            "❌ I couldn't identify any foods in your description. Could you describe your meal more specifically?"
                        )
                        return
                    
                    # Calculate nutrients
                    nutrients = self.nutrition_db.estimate_nutrients(food_items)
                    
                    # Save to diary
                    meal_id = self.meal_diary.add_meal(user_id, food_items, nutrients, meal_timestamp)
                    
                    # Format response
                    food_list = "\n".join([
                        f"• {item['name']} ({item.get('quantity', 100)}g)"
                        for item in food_items
                    ])
                    
                    time_info = ""
                    if meal_timestamp and meal_timestamp.date() != datetime.now().date():
                        time_info = f"\n📅 Logged for: {meal_timestamp.strftime('%B %d, %Y at %I:%M %p')}\n"
                    
                    response = f"✅ Meal logged successfully!{time_info}\n\n"
                    response += f"📝 Foods identified:\n{food_list}\n\n"
                    response += f"📊 Key nutrients:\n"
                    response += f"• Calories: {nutrients.get('calories', 0):.0f} kcal\n"
                    response += f"• Protein: {nutrients.get('protein_g', 0):.1f}g\n"
                    response += f"• Iron: {nutrients.get('iron_mg', 0):.1f}mg\n"
                    response += f"• Folate: {nutrients.get('folate_mcg', 0):.1f}mcg\n"
                    response += f"• Calcium: {nutrients.get('calcium_mg', 0):.1f}mg\n\n"
                    response += f"💡 Ask me 'what nutrients am I missing?' to get personalized recommendations!"
                    
                    await processing_msg.edit_text(response)
                
                else:
                    # General conversation - respond conversationally
                    try:
                        prompt = f"""You are a friendly, supportive nutritionist helping a pregnant woman. She just sent you a voice message saying: "{transcribed_text}"

Respond naturally and helpfully. If it's unclear, ask clarifying questions. Keep it brief (2-3 sentences)."""

                        ai_response = self.openai_service.client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {
                                    "role": "system",
                                    "content": "You are a friendly, supportive nutritionist specializing in pregnancy nutrition."
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
                            "I heard you! Could you tell me more about what you'd like help with? "
                            "You can describe a meal, ask about nutrients, or ask me questions!"
                        )
                
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        
        except Exception as e:
            logger.error(f"Error processing voice: {e}", exc_info=True)
            await processing_msg.edit_text(
                "❌ Sorry, I couldn't process your voice message. Could you try sending it again or type your message?"
            )
    
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

