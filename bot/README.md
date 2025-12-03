# Telegram Echo Bot

A simple Telegram bot that echoes back any message you send to it.

## Setup

1. **Get a Bot Token:**
   - Open Telegram and search for [@BotFather](https://t.me/BotFather)
   - Send `/newbot` and follow the instructions
   - Copy the token you receive

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Environment Variable:**
   
   On Windows (PowerShell):
   ```powershell
   $env:TELEGRAM_BOT_TOKEN="your_bot_token_here"
   ```
   
   On Windows (Command Prompt):
   ```cmd
   set TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```
   
   On Linux/Mac:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   ```

4. **Run the Bot:**
   ```bash
   python main.py
   ```

## Usage

- Send `/start` to begin
- Send `/help` for help
- Send any text message and the bot will echo it back

## Features

- Echoes text messages
- Responds to `/start` and `/help` commands
- Logging for debugging

