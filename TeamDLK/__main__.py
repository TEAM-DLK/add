from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    CommandHandler,
    CallbackContext,
    ChatMemberHandler,
)
from telegram.constants import ChatMemberStatus

user_data = {}  # Tracks users added by each member
whitelist = set()  # Users exempt from message deletion

async def track_added_members(update: Update, context: CallbackContext):
    chat_member = update.chat_member
    old_status = chat_member.old_chat_member.status
    new_status = chat_member.new_chat_member.status

    # Check if a user was added to the group
    if (old_status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR] 
        and new_status == ChatMemberStatus.MEMBER):
        inviter_id = chat_member.from_user.id
        added_user_id = chat_member.new_chat_member.user.id

        # Skip if user added themselves (e.g., via link)
        if inviter_id == added_user_id:
            return

        if inviter_id not in user_data:
            user_data[inviter_id] = set()
        if len(user_data[inviter_id]) < 3:
            user_data[inviter_id].add(added_user_id)

async def free_user(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    # Check if the user is an admin
    try:
        chat = await context.bot.get_chat(chat_id)
        admins = await chat.get_administrators()
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
        return

    admin_ids = [admin.user.id for admin in admins]
    if user_id not in admin_ids:
        await update.message.reply_text("Only admins can use this command.")
        return

    # Check for mentioned user
    if not context.args:
        await update.message.reply_text("Usage: /free @username")
        return

    username = context.args[0].lstrip('@')
    try:
        user = await context.bot.get_chat(username)
        whitelist.add(user.id)
        await update.message.reply_text(f"User {username} is now allowed to send messages.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def message_handler(update: Update, context: CallbackContext):
    if update.message is None:
        return
    
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    # Check if user is admin
    try:
        chat = await context.bot.get_chat(chat_id)
        admins = await chat.get_administrators()
    except Exception as e:
        print(f"Error fetching admins: {e}")
        return

    admin_ids = [admin.user.id for admin in admins]
    if user_id in admin_ids:
        return

    # Check if user is whitelisted
    if user_id in whitelist:
        return

    # Check if user has added members (changed from >=3 to >=1)
    if len(user_data.get(user_id, set())) >= 1:
        return

    # Delete the message
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")

def main():
    app = Application.builder().token("7952572583:-O0EYMynuQkRKkGk").build()

    app.add_handler(ChatMemberHandler(track_added_members))
    app.add_handler(CommandHandler("free", free_user))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE,
        message_handler
    ))

    app.run_polling()

if __name__ == "__main__":
    main()
[file content end]