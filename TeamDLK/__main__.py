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

# Configuration
BOT_USERNAME = "@LisaVipRoBot"  # Replace with your bot's username
OWNER_ID = 5917900136 # Replace with your owner's user ID

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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

async def track_added_members(update: Update, context: CallbackContext):
    try:
        chat_member = update.chat_member
        if not chat_member.old_chat_member:
            logger.warning("old_chat_member is None. Skipping update.")
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
        logger.error(f"Error in track_added_members: {e}", exc_info=True)

async def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Exception while handling update:", exc_info=context.error)

def main():
    app = Application.builder().token("7952572583:AAFenHPWINA136S17Nd-O0EYMynuQkRKkGk").build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(ChatMemberHandler(track_added_members))
    app.add_handler(CommandHandler("free", free_user))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE,
        message_handler
    ))
    
    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == "__main__":
    main()