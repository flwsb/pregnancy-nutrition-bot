# Pregnancy Nutrition Tracker Bot

A Telegram bot that helps pregnant women track their nutrition by analyzing meal photos and providing personalized dietary recommendations based on pregnancy-specific nutritional requirements.

## Features

- 📸 **Photo Analysis**: Upload meal photos and get automatic food identification
- 📊 **Nutrition Tracking**: Automatically log nutrients from identified foods
- 📅 **Daily Summary**: View your daily nutrition intake and progress
- 📈 **Weekly Reports**: Get comprehensive weekly nutrition analysis
- 💡 **Smart Recommendations**: AI-powered suggestions based on missing nutrients
- 🤖 **Easy to Use**: Simple Telegram interface - just send photos!

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Telegram account
- OpenAI API key

### Step 1: Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the instructions to name your bot
4. Copy the bot token you receive (you'll need it later)

### Step 2: Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (you'll need it later)

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

Replace the placeholder values with your actual tokens.

### Step 5: Run the Bot

**Important**: The bot must be running continuously to receive messages from Telegram.

#### Option 1: Run in Terminal (for testing)
```bash
python3 bot.py
```
The bot will run in the foreground. Press `Ctrl+C` to stop.

#### Option 2: Run in Background (recommended for daily use)
```bash
./run_bot.sh
```
This starts the bot in the background. Logs are saved to `bot.log`.

To stop the background bot:
```bash
./stop_bot.sh
```

#### Option 3: Run as a Service (for always-on)
On macOS, you can use `launchd` to keep it running. On Linux, use `systemd`.

**Note**: When the bot stops, it won't receive messages until you start it again.

### Step 6: Start Using the Bot

1. Open Telegram and search for your bot (the name you gave it)
2. Send `/start` to begin
3. Start sending meal photos!

## Usage

### Commands

- `/start` - Welcome message and instructions
- `/diary` - View today's nutrition summary
- `/weekly` - View weekly nutrition report
- `/help` - Show help information

### How to Use

1. **Log a Meal**: Simply send a photo of your meal to the bot
2. **View Daily Summary**: Use `/diary` to see how you're doing today
3. **Check Weekly Progress**: Use `/weekly` to see your week's nutrition overview
4. **Get Recommendations**: The bot automatically suggests foods to address nutrient gaps

### Tips for Best Results

- Take clear photos with good lighting
- Include all items in your meal in the photo
- Try to get the full meal in frame
- Check your diary regularly to track progress

## Project Structure

```
pregnancy/
├── bot.py                 # Main Telegram bot entry point
├── openai_service.py      # OpenAI API integration
├── nutrition_db.py        # Nutrition knowledge base & calculations
├── meal_diary.py          # SQLite database operations
├── analyzer.py            # Analysis & recommendation logic
├── config.py             # Configuration management
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── data/
    ├── nutrition_base.json  # Pregnancy nutrition requirements
    └── meals.db            # SQLite database (created automatically)
```

## How It Works

1. **Image Analysis**: When you send a photo, the bot uses OpenAI's Vision API to identify foods
2. **Nutrient Calculation**: Identified foods are matched against a nutrition knowledge base
3. **Meal Logging**: Nutrients are stored in a SQLite database
4. **Analysis**: The bot compares your intake against pregnancy-specific requirements
5. **Recommendations**: AI generates personalized suggestions based on nutrient gaps

## Nutritional Requirements

The bot tracks key nutrients important during pregnancy:

- Calories
- Protein
- Iron
- Folate (Folic Acid)
- Calcium
- Vitamin C, D, A, B12
- Zinc
- Omega-3 fatty acids
- Fiber

Requirements are based on standard pregnancy nutritional guidelines.

## Troubleshooting

### Bot doesn't respond
- Check that your `.env` file has the correct tokens
- Verify the bot is running (check console for errors)
- Make sure you've started a conversation with `/start`

### Photo analysis fails
- Try a clearer, better-lit photo
- Ensure all food items are visible
- Check your OpenAI API key is valid and has credits

### Database errors
- The database is created automatically in the `data/` folder
- Make sure the `data/` directory exists and is writable

## Notes

- The bot uses OpenAI's API which incurs costs per request
- Photo analysis uses GPT-4 Vision API
- Recommendations use GPT-4o-mini for cost efficiency
- All data is stored locally in SQLite database
- Each user's data is tracked separately by Telegram user ID

## License

This project is provided as-is for personal use.

