"""Main Telegram bot for pregnancy nutrition tracking."""
import logging
import tempfile
import os
from pathlib import Path
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
        """Handle text messages - provide helpful responses."""
        text = update.message.text.lower()
        user_name = update.effective_user.first_name or "there"
        
        # Respond to common questions
        if any(word in text for word in ['what can you do', 'what do you do', 'help', 'how']):
            response = f"""Hi {user_name}! 👋

I'm your Pregnancy Nutrition Tracker! Here's what I can do:

📸 **Analyze Meal Photos**
• Send me a photo of your meal
• I'll identify the foods and log the nutrients

📊 **Track Your Nutrition**
• Use /diary to see today's summary
• Use /weekly to see your weekly report

💡 **Get Recommendations**
• I'll suggest foods based on missing nutrients

**Commands:**
/start - Welcome message
/diary - Today's nutrition summary
/weekly - Weekly nutrition report
/help - Show help

Just send me a photo of your meal to get started! 📷"""
        else:
            response = f"""Hi {user_name}! 👋

I help track nutrition during pregnancy by analyzing meal photos.

**To get started:**
• Send me a photo of your meal 📸
• Or use /help to see all commands
• Or use /start for a full introduction

What would you like to do?"""
        
        await update.message.reply_text(response)
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages - analyze meal images."""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "there"
        
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
                
                # Save to diary
                meal_id = self.meal_diary.add_meal(user_id, food_items, nutrients)
                
                # Format response
                food_list = "\n".join([
                    f"• {item['name']} ({item.get('quantity', 100)}g)"
                    for item in food_items
                ])
                
                response = f"✅ Meal logged successfully!\n\n"
                response += f"📝 Foods identified:\n{food_list}\n\n"
                response += f"📊 Key nutrients:\n"
                response += f"• Calories: {nutrients.get('calories', 0):.0f} kcal\n"
                response += f"• Protein: {nutrients.get('protein_g', 0):.1f}g\n"
                response += f"• Iron: {nutrients.get('iron_mg', 0):.1f}mg\n"
                response += f"• Folate: {nutrients.get('folate_mcg', 0):.1f}mcg\n"
                response += f"• Calcium: {nutrients.get('calcium_mg', 0):.1f}mg\n\n"
                response += f"💡 Use /diary to see your daily summary!"
                
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

