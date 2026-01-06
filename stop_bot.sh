#!/bin/bash
# Script to stop the pregnancy nutrition bot

pkill -f 'python3 bot.py'
if [ $? -eq 0 ]; then
    echo "✅ Bot stopped successfully"
else
    echo "⚠️  Bot process not found (may already be stopped)"
fi

