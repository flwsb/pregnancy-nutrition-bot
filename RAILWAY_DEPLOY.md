# Deploying to Railway

Railway is perfect for hosting your bot 24/7 - it's always running, even when your Mac is off!

## Quick Deploy Steps

### Option 1: Deploy via Railway Dashboard (Easiest)

1. **Go to Railway**: https://railway.app
2. **Create New Project**: Click "New Project"
3. **Deploy from GitHub** (recommended):
   - Connect your GitHub account
   - Select this repository
   - Railway will auto-detect it's a Python project
   
   **OR Deploy from Directory**:
   - Click "Deploy from GitHub repo" → "Configure GitHub App"
   - Or use Railway CLI (see below)

4. **Set Environment Variables**:
   - Go to your project → Variables tab
   - Add these variables:
     ```
     TELEGRAM_BOT_TOKEN=your_bot_token_here
     OPENAI_API_KEY=your_openai_key_here
     ```

5. **Deploy**: Railway will automatically build and deploy!

### Option 2: Deploy via Railway CLI

1. **Install Railway CLI**:
   ```bash
   npm i -g @railway/cli
   ```

2. **Login**:
   ```bash
   railway login
   ```

3. **Initialize Project**:
   ```bash
   railway init
   ```

4. **Set Environment Variables**:
   ```bash
   railway variables set TELEGRAM_BOT_TOKEN=your_bot_token_here
   railway variables set OPENAI_API_KEY=your_openai_key_here
   ```

5. **Deploy**:
   ```bash
   railway up
   ```

## What Gets Deployed

- **Telegram Bot**: Runs continuously, accessible via Telegram
- **Streamlit App** (optional): If you want web interface too

## Running Both Bot + Streamlit

If you want both the Telegram bot AND the Streamlit web app:

1. Create two services in Railway:
   - **Service 1**: Telegram Bot (`bot.py`)
   - **Service 2**: Streamlit App (`streamlit run app.py`)

2. Or use the Procfile to run both (modify as needed)

## Cost

- **Railway Free Tier**: $5/month credit (usually enough for a bot)
- **Hobby Plan**: $5/month if you exceed free tier
- Very affordable for always-on hosting!

## Monitoring

- Check logs in Railway dashboard
- Bot will auto-restart if it crashes
- Set up alerts if needed

## Database

The SQLite database (`data/meals.db`) will persist in Railway's filesystem. For production, consider upgrading to Railway's Postgres if you need more reliability.

