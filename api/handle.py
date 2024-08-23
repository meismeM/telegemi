"""
All the chat that comes through the Telegram bot gets passed to the
handle_message function. This function checks out if the user has the
green light to chat with the bot. Once that's sorted, it figures out if
the user sent words or an image and deals with it accordingly.

For text messages, it fires up the ChatManager class that keeps track of
the back-and-forth with that user.

As for images, in Gemini pro, they're context-free, so you can handle
them pretty straight-up without much fuss.
"""

from .auth import is_authorized
from .command import excute_command
from .context import ChatManager, ImageChatManger
from .telegram import Update, send_message, send_inline_keyboard
from .printLog import send_log, send_image_log
from .admin import is_admin  # Assumes you have an admin-checking function

chat_manager = ChatManager()

def send_message_to_channel(message, from_id, message_id):
    if is_admin(from_id):  # Check if the user is an admin
        keyboard = [
            [
                {"text": "Forward", "callback_data": f"forward:{message_id}"},
                {"text": "Don't Forward", "callback_data": f"cancel:{message_id}"}
            ]
        ]
        send_inline_keyboard(from_id, "Do you want to forward this message to the channel?", keyboard)
    else:
        channel_id = "@telegemin"  # Replace with your channel ID or username
        send_message(channel_id, message)

def handle_message(update_data):
    update = Update(update_data)
    authorized = is_authorized(update.from_id, update.user_name)

    # Log the event
    send_log(f"event received\n@{update.user_name} id:`{update.from_id}`\nThe content sent is:\n{update.text}\n```json\n{update_data}```")

    if update.type == "command":
        response_text = excute_command(update.from_id, update.text)
        if response_text != "":
            send_message(update.from_id, response_text)
            log = f"@{update.user_name} id:`{update.from_id}`The command sent is:\n{update.text}\nThe reply content is:\n{response_text}"
            send_log(log)

            # Send to the channel with admin approval
            channel_message = f"A command was sent:\n{update.text}\nThe reply content is:\n{response_text}"
            send_message_to_channel(channel_message, update.from_id, update.message_id)

    elif not authorized:
        send_message(update.from_id, f"You are not allowed to use this bot.\nID:`{update.from_id}`")
        log = f"@{update.user_name} id:`{update.from_id}`No rights to use, The content sent is:\n{update.text}"
        send_log(log)
        return

    elif update.type == "text":
        chat = chat_manager.get_chat(update.from_id)
        anwser = chat.send_message(update.text)
        extra_text = (
            "\n\nType /new to kick off a new chat." if chat.history_length > 5 else ""
        )
        response_text = f"{anwser}{extra_text}"
        send_message(update.from_id, response_text)

        dialogueLogarithm = int(chat.history_length / 2)
        log = f"@{update.user_name} id:`{update.from_id}`The content sent is:\n{update.text}\nThe reply content is:\n{response_text}\nThe logarithm of historical conversations is:{dialogueLogarithm}"
        send_log(log)

        # Send to the channel with admin approval
        channel_message = f"Text received: {update.text}\nReply: {response_text}"
        send_message_to_channel(channel_message, update.from_id, update.message_id)

    elif update.type == "photo":
        chat = ImageChatManger(update.photo_caption, update.file_id)
        response_text = chat.send_image()
        print(f"update.message_id {update.message_id}")
        send_message(
            update.from_id, response_text, reply_to_message_id=update.message_id
        )

        photo_url = chat.tel_photo_url()
        imageID = update.file_id
        log = f"@{update.user_name} id:`{update.from_id}`[photo]({photo_url}),The accompanying message is:\n{update.photo_caption}\nThe reply content is:\n{response_text}"
        send_image_log("", imageID)
        send_log(log)

        # Send to the channel with admin approval
        channel_message = f"Photo received:\nCaption: {update.photo_caption}\nReply: {response_text}"
        send_message_to_channel(channel_message, update.from_id, update.message_id)

    else:
        send_message(update.from_id, "The content you sent is not recognized\n\n/help")
        log = f"@{update.user_name} id:`{update.from_id}`Sent unrecognized content"
        send_log(log)

        # Send to the channel with admin approval
        channel_message = "Unrecognized content was sent."
        send_message_to_channel(channel_message, update.from_id, update.message_id)

def handle_callback_query(callback_query):
    data = callback_query.data.split(":")
    action = data[0]
    message_id = data[1]

    if action == "forward":
        original_message = get_message_by_id(message_id)  # Retrieve the original message
        channel_id = "@telegemin"
        send_message(channel_id, original_message)
        send_message(callback_query.from_id, "Message forwarded to the channel.")
    
    elif action == "cancel":
        send_message(callback_query.from_id, "Message forwarding canceled.")
