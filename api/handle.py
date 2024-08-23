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

from .auth import is_authorized, is_admin
from .command import excute_command
from .context import ChatManager, ImageChatManger
from .telegram import Update, send_message, send_imageMessage, send_message_with_inline_keyboard, forward_message
from .printLog import send_log, send_image_log
from .config import CHANNEL_ID, ADMIN_ID

CHANNEL_ID = "-1002238005293"  # Replace with your actual channel ID
ADMIN_CHAT_ID = "@methyops"     # Replace with your admin's chat ID
MESSAGE_ID_TO_FORWARD = 123      # Replace with the message ID you got

forward_message(CHANNEL_ID, ADMIN_CHAT_ID, MESSAGE_ID_TO_FORWARD)  

chat_manager = ChatManager()

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

    elif not authorized:
        send_message(update.from_id, f"You are not allowed to use this bot.\nID:`{update.from_id}`")
        log = f"@{update.user_name} id:`{update.from_id}`No rights to use, The content sent is:\n{update.text}"
        send_log(log)
        return

    elif update.type == "text":
        chat = chat_manager.get_chat(update.from_id)
        answer = chat.send_message(update.text)
        extra_text = (
            "\n\nType /new to kick off a new chat." if chat.history_length > 5 else ""
        )
        response_text = f"{answer}{extra_text}"
        send_message(update.from_id, response_text)

        dialogueLogarithm = int(chat.history_length / 2)
        log = f"@{update.user_name} id:`{update.from_id}`The content sent is:\n{update.text}\nThe reply content is:\n{response_text}\nThe logarithm of historical conversations is:{dialogueLogarithm}"
        send_log(log)

        # Send to admin with inline keyboard for forwarding
        if not is_admin(update.from_id):  # Only send to admin if the sender is NOT the admin
            keyboard = [[{"text": "Forward to Channel", "callback_data": f"forward_{update.message_id}"}]]
            admin_message = f"Text from @{update.user_name}:\n{update.text}\nReply:\n{response_text}"
            send_message_with_inline_keyboard(ADMIN_ID, admin_message, keyboard)

    elif update.type == "photo":
        chat = ImageChatManger(update.photo_caption, update.file_id)
        response_text = chat.send_image()
        send_message(
            update.from_id, response_text, reply_to_message_id=update.message_id
        )

        photo_url = chat.tel_photo_url()
        imageID = update.file_id
        log = f"@{update.user_name} id:`{update.from_id}`[photo]({photo_url}),The accompanying message is:\n{update.photo_caption}\nThe reply content is:\n{response_text}"
        send_image_log("", imageID)
        send_log(log)

        # Send to admin with inline keyboard for forwarding
        if not is_admin(update.from_id):  # Only send to admin if the sender is NOT the admin
            keyboard = [[{"text": "Forward to Channel", "callback_data": f"forward_{update.message_id}"}]]
            admin_message = f"Photo from @{update.user_name}:\nCaption: {update.photo_caption}\nReply:\n{response_text}"
            send_message_with_inline_keyboard(ADMIN_ID, admin_message, keyboard)

    elif "callback_query" in update_data:
        callback_data = update_data["callback_query"]["data"]
        if callback_data.startswith("forward_"):
            message_id = int(callback_data.split("_")[1])
            from_chat_id = update_data["callback_query"]["message"]["chat"]["id"]
            forward_message(CHANNEL_ID, from_chat_id, message_id)

    else:
        send_message(update.from_id, "The content you sent is not recognized\n\n/help")
        log = f"@{update.user_name} id:`{update.from_id}`Sent unrecognized content"
        send_log(log)