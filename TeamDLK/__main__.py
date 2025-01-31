import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests

# Configure logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
DEEPSEEK_API_KEY = "YOUR_DEEPSEEK_API_KEY"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # Verify actual API endpoint

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text("Hello! I'm a DeepSeek-powered bot. Send me a message!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process user messages."""
    user_message = update.message.text
    
    try:
        # Call DeepSeek API
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",  # Confirm model name
            "messages": [{"role": "user", "content": user_message}],
            "temperature": 0.7
        }
        
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise HTTP errors
        
        result = response.json()
        bot_reply = result["choices"][0]["message"]["content"]  # Adjust based on actual response
        
    except Exception as e:
        logger.error(f"Error: {e}")
        bot_reply = "⚠️ Sorry, I encountered an error."
    
    await update.message.reply_text(bot_reply)

def main():
    """Run the bot."""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling
    app.run_polling()

if __name__ == "__main__":
    main()