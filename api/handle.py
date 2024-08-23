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
from .telegram import Update, send_message, send_message_with_inline_keyboard
from .printLog import send_log, send_image_log
from .config import ADMIN_ID  # Import ADMIN_ID from the config file

chat_manager = ChatManager()

def send_message_to_channel(message):
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
            
            # Send to the admin for approval before posting to the channel
            channel_message = f"A command was sent:\n{update.text}\nThe reply content is:\n{response_text}"
            send_message_with_inline_keyboard(
                ADMIN_ID, 
                f"Command from @{update.user_name} (ID: `{update.from_id}`)\n\n{channel_message}",
                [[{"text": "Post to Channel", "callback_data": f"post_command_{update.message_id}"}]]
            )

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
        
        # Send to the admin for approval before posting to the channel
        send_message_with_inline_keyboard(
            ADMIN_ID, 
            f"Message from @{update.user_name} (ID: `{update.from_id}`)\n\nMessage: {update.text}\nReply: {response_text}",
            [[{"text": "Post to Channel", "callback_data": f"post_text_{update.message_id}"}]]
        )

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
        
        # Send to the admin for approval before posting to the channel
        send_message_with_inline_keyboard(
            ADMIN_ID, 
            f"Photo from @{update.user_name} (ID: `{update.from_id}`)\n\nCaption: {update.photo_caption}\nReply: {response_text}",
            [[{"text": "Post to Channel", "callback_data": f"post_photo_{update.message_id}"}]]
        )

    elif "callback_query" in update_data:
        callback_data = update_data["callback_query"]["data"]
        
        # Check the callback data and extract relevant information
        if callback_data.startswith("post_"):
            action_type, message_id = callback_data.split("_")[1:]
            
            # Log what is happening
            send_log(f"Admin approved a {action_type} with message_id: {message_id}")
            
            # Get the original message text from the admin's message
            original_message = update_data["callback_query"]["message"]["text"]
            
            # Post to the channel
            send_message_to_channel(f"{original_message}\n\n(Approved by Admin)")
            
            # Notify the admin of successful posting
            send_message(ADMIN_ID, "The message has been posted to the channel successfully.")

    else:
        send_message(update.from_id, "The content you sent is not recognized\n\n/help")
        log = f"@{update.user_name} id:`{update.from_id}`Sent unrecognized content"
        send_log(log)
        send_message_to_channel("Unrecognized content was sent.")
