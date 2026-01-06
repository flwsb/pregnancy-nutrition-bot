# Deployment Instructions

## ✅ GitHub Repository
**Repository**: https://github.com/flwsb/pregnancy-nutrition-bot
**Status**: Code pushed successfully ✓

## 🚂 Railway Deployment

### Quick Setup (5 minutes)

1. **Go to Railway Dashboard**: https://railway.app/project/567fffa9-eac6-441e-945d-4305d3e6130b

2. **Connect GitHub Repository**:
   - Click "New" → "GitHub Repo"
   - Select `pregnancy-nutrition-bot`
   - Railway will auto-detect Python and deploy

3. **Set Environment Variables**:
   - Go to your service → "Variables" tab
   - Add these two variables:
     ```
     TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
     OPENAI_API_KEY=your_openai_api_key
     ```

4. **Deploy**:
   - Railway will automatically build and deploy
   - Check "Deployments" tab for status
   - View logs in "Logs" tab

### Alternative: Deploy via CLI

If you prefer command line:

```bash
cd /Users/flowiesboeck/Documents/pregnancy
railway link  # Select project when prompted
railway variables set TELEGRAM_BOT_TOKEN=your_token
railway variables set OPENAI_API_KEY=your_key
railway up
```

## 🎯 After Deployment

1. **Check Logs**: Railway dashboard → Your service → Logs
2. **Test Bot**: Open Telegram, find your bot, send `/start`
3. **Monitor**: Bot will auto-restart if it crashes

## 📝 Notes

- The bot will run 24/7 on Railway
- Database (`data/meals.db`) persists in Railway's filesystem
- Free tier: $5/month credit (usually enough)
- Both you and your wife can use the same bot (tracked by Telegram user ID)

