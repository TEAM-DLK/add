import telegram
from telegram.ext import Updater, MessageHandler, ApplicationBuilder, filters

# Replace with your bot's token
BOT_TOKEN = "7952572583:AAEGu0QYuQ-0umRn3Ade4VnFnVzsd3kbKo4"

# Dictionary to store user's "added" contacts.  Key is the user ID, value is a set of user IDs they've added.
added_contacts = {}

def start(update, context):
    update.message.reply_text("Welcome! This bot limits direct messages to 3 contacts until they are added.")

def handle_message(update, context):
    user_id = update.message.from_user.id
    message_text = update.message.text
    chat_id = update.message.chat_id

    # Check if it's a direct message (private chat)
    if update.message.chat.type == telegram.Chat.PRIVATE:
        target_user_id = None  # We'll determine this

        # Extract target user ID (this part needs improvement - see below)
        if update.message.reply_to_message:
            target_user_id = update.message.reply_to_message.from_user.id
        #elif  # Add logic here to extract user ID from a mention
            # Example (requires parsing the message text):
            # if "@username" in message_text:
            #    target_username = message_text.split("@")[1].split(" ")[0] # Extract username
            #    # Use Telegram API to get user ID from username (complex, rate-limited)
        
        if target_user_id: # If we were able to identify a target user
            if user_id not in added_contacts:
                added_contacts[user_id] = set()
            
            if target_user_id in added_contacts[user_id]:
                # Check the limit
                if len(added_contacts[user_id]) > 3:
                    update.message.delete() # Delete the message
                    update.message.reply_text("You've reached your direct message limit.  Add more contacts!")
                    return
            else:
                update.message.delete()
                update.message.reply_text("You can only message people you have added!")
                return
    # else: Group message. Do nothing. Mentions are allowed here.


def add_contact(update, context): # Example command to "add" a contact
    user_id = update.message.from_user.id
    # Get target user ID (similar logic as above)
    target_user_id = None
    if update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id

    if target_user_id:
      if user_id not in added_contacts:
          added_contacts[user_id] = set()
      added_contacts[user_id].add(target_user_id)
      update.message.reply_text(f"You've added {update.message.reply_to_message.from_user.first_name} to your contacts.")


def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build() # New way to initialize
    updater = application.updater
    dispatcher = updater.dispatcher

    start_handler = telegram.ext.CommandHandler("start", start)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)  # Corrected filter usage
    add_handler = telegram.ext.CommandHandler("add", add_contact)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(message_handler)
    dispatcher.add_handler(add_handler)

    application.run_polling() # New way to start polling
    application.idle()


if __name__ == '__main__':
    main()
