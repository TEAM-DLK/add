from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    CommandHandler,
    CallbackContext,
    ChatMemberHandler,
)
from telegram.constants import ChatMemberStatus
import logging
import sys
import telegram

# Configuration
BOT_USERNAME = "@LisaVipRoBot"  # Replace with your bot's username
OWNER_ID = 5917900136               # Replace with your owner ID
TOKEN = "7952572583:AAFenHPWINA136S17Nd-O0EYMynuQkRKkGk"  # Your bot token

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variables
user_data = {}
whitelist = set()

async def start(update: Update, context: CallbackContext):
    """Send welcome message with inline button to add bot to group"""
    if update.effective_chat.type != "private":
        return
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "➕ Add me to your group",
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
        )]
    ])
    
    text = (
        "👋 Hello! I'm a group management bot.\n\n"
        "⚠️ To use me properly:\n"
        "1. Add me to your group\n"
        "2. Make me admin\n"
        "3. Let's keep the group clean!"
    )
    
    await update.message.reply_text(text, reply_markup=keyboard)

async def help_command(update: Update, context: CallbackContext):
    """Show help message"""
    help_text = (
        "📚 Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/free @username - Whitelist a user (admin only)\n"
        "/stats - Bot statistics (owner only)"
    )
    await update.message.reply_text(help_text)

async def stats(update: Update, context: CallbackContext):
    """Owner command: Show bot statistics"""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ This command is for the owner only!")
        return
    
    stats_text = (
        f"📊 Bot Statistics:\n"
        f"• Total tracked users: {len(user_data)}\n"
        f"• Whitelisted users: {len(whitelist)}\n"
        f"• Groups monitored: {len(context.bot_data.get('groups', {}))}"
    )
    await update.message.reply_text(stats_text)

async def free_user(update: Update, context: CallbackContext):
    """Admin command: Whitelist a user"""
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    # Admin check
    try:
        chat = await context.bot.get_chat(chat_id)
        admins = await chat.get_administrators()
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
        return

    admin_ids = [admin.user.id for admin in admins]
    if user_id not in admin_ids:
        await update.message.reply_text("❌ Only admins can use this command.")
        return

    # Mention check
    if not update.message.entities or not any(e.type == "mention" for e in update.message.entities):
        await update.message.reply_text("ℹ️ Usage: /free @username")
        return

    try:
        mention = next(e for e in update.message.entities if e.type == "mention")
        username = update.message.text[mention.offset+1:mention.offset+mention.length]
        user = await context.bot.get_chat(username)
        whitelist.add(user.id)
        await update.message.reply_text(f"✅ User @{username} is now whitelisted.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def track_added_members(update: Update, context: CallbackContext):
    try:
        chat_member = update.chat_member
        
        if not chat_member.old_chat_member:
            logger.warning("Skipping update with missing old_chat_member")
            return
            
        old_status = chat_member.old_chat_member.status
        new_status = chat_member.new_chat_member.status

        if (old_status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR] 
            and new_status == ChatMemberStatus.MEMBER):
            inviter_id = chat_member.from_user.id
            added_user_id = chat_member.new_chat_member.user.id

            if inviter_id == added_user_id:
                return

            if inviter_id not in user_data:
                user_data[inviter_id] = set()
            if len(user_data[inviter_id]) < 3:
                user_data[inviter_id].add(added_user_id)
                
    except Exception as e:
        logger.error(f"Track members error: {e}", exc_info=True)

async def message_handler(update: Update, context: CallbackContext):
    if update.message is None:
        return
    
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    try:
        chat = await context.bot.get_chat(chat_id)
        admins = await chat.get_administrators()
    except Exception as e:
        logger.error(f"Admin check error: {e}")
        return

    admin_ids = [admin.user.id for admin in admins]
    if user_id in admin_ids or user_id in whitelist:
        return

    if len(user_data.get(user_id, set())) >= 1:
        return

    try:
        await context.bot.delete_message(chat_id, update.message.message_id)
    except Exception as e:
        logger.error(f"Delete message failed: {e}")

async def error_handler(update: Update, context: CallbackContext):
    logger.error("Exception: %s", context.error, exc_info=context.error)

def main():
    try:
        # Check for existing instances
        app = Application.builder().token(TOKEN).build()
        
        # Clear any existing webhook configuration
        app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook cleared successfully")

        # Register handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("stats", stats))
        app.add_handler(CommandHandler("free", free_user))
        app.add_handler(ChatMemberHandler(track_added_members))
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE,
            message_handler
        ))
        app.add_error_handler(error_handler)

        logger.info("Starting bot in polling mode...")
        app.run_polling()

    except telegram.error.Conflict:
        logger.critical("Another bot instance is already running! Shutting down.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Failed to start bot: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()