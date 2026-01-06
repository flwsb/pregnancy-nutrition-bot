#!/bin/bash
# Script to run the pregnancy nutrition bot in the background

cd "$(dirname "$0")"
nohup python3 bot.py > bot.log 2>&1 &
echo "Bot started in background. PID: $!"
echo "Logs are being written to bot.log"
echo "To stop the bot, run: pkill -f 'python3 bot.py'"

