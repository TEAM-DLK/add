from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext
from telegram.ext import filters

import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to keep track of users and the number of members they have added
user_member_counts = {}

# Dictionary to keep track of users who have been restricted
restricted_users = {}

# Admin user IDs (you can add more admins as needed)
ADMINS = [5917900136]  # Replace with actual admin user IDs

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Welcome to the group! To send messages, please add 3 new members.')

async def track_new_members(update: Update, context: CallbackContext) -> None:
    for new_member in update.message.new_chat_members:
        # Get the user who added the new member
        added_by = update.message.from_user.id

        # Increment the count of members added by this user
        if added_by in user_member_counts:
            user_member_counts[added_by] += 1
        else:
            user_member_counts[added_by] = 1

        # Check if the user has added 3 members
        if user_member_counts[added_by] >= 3 and added_by in restricted_users:
            # Remove restrictions
            await context.bot.restrict_chat_member(
                chat_id=update.message.chat_id,
                user_id=added_by,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_invite_users=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True
                )
            )
            del restricted_users[added_by]
            await update.message.reply_text(f'@{update.message.from_user.username} can now send messages!')

async def enforce_restrictions(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # Admins are exempt from restrictions
    if user_id in ADMINS:
        return

    # Check if the user has added 3 members
    if user_member_counts.get(user_id, 0) < 3:
        # Restrict the user from sending messages
        await context.bot.restrict_chat_member(
            chat_id=update.message.chat_id,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_invite_users=True,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            )
        )
        restricted_users[user_id] = True
        await update.message.reply_text('You need to add 3 new members to send messages.')

async def check_status(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    count = user_member_counts.get(user_id, 0)
    await update.message.reply_text(f'You have added {count} members. You need to add {3 - count} more to send messages.')

def main() -> None:
    # Replace 'YOUR_TOKEN' with your bot's token
    application = Application.builder().token("7952572583:AAGnjCaw4yGAxnZzNaBZo715uYIFkbNdkCA").build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", check_status))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_new_members))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, enforce_restrictions))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()