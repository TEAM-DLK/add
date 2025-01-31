import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)
from datetime import datetime, timedelta
import sqlite3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database setup
conn = sqlite3.connect('memberbooster.db', check_same_thread=False)
cursor = conn.cursor()

# Create tables
cursor.executescript('''
    CREATE TABLE IF NOT EXISTS groups (
        group_id INTEGER PRIMARY KEY,
        force_add INTEGER DEFAULT 0,
        max_add INTEGER DEFAULT 0,
        channel_id TEXT,
        channel2_id TEXT,
        btn_enabled INTEGER DEFAULT 0,
        btn_text TEXT DEFAULT "Admin Panel",
        btn_url TEXT DEFAULT "https://example.com",
        custom_text TEXT DEFAULT "⚠️ Hello !name, you need to add !count more members to chat!",
        hard_mode INTEGER DEFAULT 0,
        daily_limit INTEGER DEFAULT 0
    );
    
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER,
        group_id INTEGER,
        added_members INTEGER DEFAULT 0,
        daily_added INTEGER DEFAULT 0,
        last_active DATETIME,
        is_exempt INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, group_id)
    );
    
    CREATE TABLE IF NOT EXISTS channels (
        group_id INTEGER PRIMARY KEY,
        channel1_id TEXT,
        channel2_id TEXT
    );
    
    CREATE TABLE IF NOT EXISTS top_users (
        user_id INTEGER,
        group_id INTEGER,
        total_added INTEGER DEFAULT 0,
        last_updated DATETIME
    );
''')
conn.commit()

# Helper functions
def get_group_settings(group_id):
    cursor.execute('SELECT * FROM groups WHERE group_id = ?', (group_id,))
    return cursor.fetchone()

def get_user_data(user_id, group_id):
    cursor.execute('''
        SELECT * FROM users 
        WHERE user_id = ? AND group_id = ?
    ''', (user_id, group_id))
    return cursor.fetchone()

# Admin check decorator
def restricted(func):
    async def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if update.effective_chat.type == 'private':
            await update.message.reply_text("This command only works in groups!")
            return
        member = await update.effective_chat.get_member(user_id)
        if member.status not in ['administrator', 'creator']:
            await update.message.reply_text("⛔ Command restricted to admins!")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

# Command handlers
@restricted
async def set_max(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id
    args = context.args
    if args and args[0].isdigit():
        max_add = int(args[0])
        cursor.execute('''
            UPDATE groups 
            SET force_add = ?, max_add = ?
            WHERE group_id = ?
        ''', (1 if max_add > 0 else 0, max_add, group_id))
        conn.commit()
        await update.message.reply_text(f"✅ Force add requirement set to {max_add}!")

@restricted
async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id
    args = context.args
    if args:
        channel_id = args[0]
        cursor.execute('''
            INSERT OR REPLACE INTO channels (group_id, channel1_id)
            VALUES (?, ?)
        ''', (group_id, channel_id))
        conn.commit()
        await update.message.reply_text(f"✅ Force join channel set to {channel_id}!")

async def show_remain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    group_id = update.effective_chat.id
    user_data = get_user_data(user_id, group_id)
    
    if user_data:
        await update.message.reply_text(
            f"📊 Your stats:\n"
            f"• Total added: {user_data[2]}\n"
            f"• Daily added: {user_data[3]}\n"
            f"• Last active: {user_data[4]}"
        )

@restricted
async def set_custom_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id
    text = ' '.join(context.args)
    cursor.execute('''
        UPDATE groups 
        SET custom_text = ?
        WHERE group_id = ?
    ''', (text, group_id))
    conn.commit()
    await update.message.reply_text("✅ Custom message updated!")

async def enforce_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    group_id = update.effective_chat.id
    message = update.message

    # Check if user is exempt
    user_data = get_user_data(user.id, group_id)
    if user_data and user_data[5] == 1:
        return

    group_settings = get_group_settings(group_id)
    if not group_settings:
        return

    # Check force add requirements
    if group_settings[1] == 1:  # force_add enabled
        required = group_settings[2]  # max_add
        added = user_data[2] if user_data else 0
        
        if added < required:
            await message.delete()
            warning_text = group_settings[8].replace("!name", user.full_name)
            warning_text = warning_text.replace("!count", str(required - added))
            
            if group_settings[5] == 1:  # Button enabled
                keyboard = [[InlineKeyboardButton(
                    group_settings[6], 
                    url=group_settings[7]
                )]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await message.reply_text(warning_text, reply_markup=reply_markup)
            else:
                await message.reply_text(warning_text)
            return

    # Check channel membership
    channels = cursor.execute('''
        SELECT channel1_id, channel2_id 
        FROM channels 
        WHERE group_id = ?
    ''', (group_id,)).fetchone()
    
    if channels:
        for channel_id in channels:
            if channel_id:
                try:
                    member = await context.bot.get_chat_member(channel_id, user.id)
                    if member.status not in ['member', 'administrator', 'creator']:
                        await message.delete()
                        await message.reply_text("⛔ You must join our channel first!")
                        return
                except Exception as e:
                    logger.error(f"Channel check error: {e}")

# Initialize bot
def main():
    app = Application.builder().token(TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("max", set_max))
    app.add_handler(CommandHandler("channel", set_channel))
    app.add_handler(CommandHandler("remain", show_remain))
    app.add_handler(CommandHandler("text", set_custom_text))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, enforce_rules))

    # Start bot
    app.run_polling()

if __name__ == "__main__":
    main()