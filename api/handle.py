from .auth import is_authorized, is_admin
from .command import excute_command
from .context import ChatManager, ImageChatManger
from .telegram import Update, send_message, send_imageMessage
from .printLog import send_log, send_image_log
from .config import CHANNEL_ID, ADMIN_ID

chat_manager = ChatManager()
pending_approvals = {}

def send_message_to_channel(message):
    try:
        send_message(CHANNEL_ID, message)
        print(f"Message successfully sent to the channel: {CHANNEL_ID}")
    except Exception as e:
        print(f"Error sending message to channel: {e}")

def handle_message(update_data):
    update = Update(update_data)
    authorized = is_authorized(update.from_id, update.user_name)

    # Log the event
    send_log(f"event received\n@{update.user_name} id:`{update.from_id}`\nThe content sent is:\n{update.text}\n```json\n{update_data}```")

    if not authorized:
        send_message(update.from_id, f"You are not allowed to use this bot.\nID:`{update.from_id}`")
        log = f"@{update.user_name} id:`{update.from_id}`No rights to use, The content sent is:\n{update.text}"
        send_log(log)
        return

    if update.type == "command":
        response_text = excute_command(update.from_id, update.text)
        if response_text != "":
            send_message(update.from_id, response_text)
            log = f"@{update.user_name} id:`{update.from_id}`The command sent is:\n{update.text}\nThe reply content is:\n{response_text}"
            send_log(log)

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

        # Queue the message for admin approval
        message_id = update.message_id
        pending_approvals[message_id] = {
            "from_id": update.from_id,
            "user_name": update.user_name,
            "text": update.text,
            "response_text": response_text
        }
        
        # Notify the admin
        send_message(
            ADMIN_ID, 
            f"New message from @{update.user_name} (ID: `{update.from_id}`):\n\nMessage: {update.text}\nReply: {response_text}\n\nTo approve, reply with /approve {message_id}\nTo deny, reply with /deny {message_id}"
        )

    elif update.type == "photo":
        chat = ImageChatManger(update.photo_caption, update.file_id)
        response_text = chat.send_image()
        send_message(update.from_id, response_text, reply_to_message_id=update.message_id)

        photo_url = chat.tel_photo_url()
        imageID = update.file_id
        log = f"@{update.user_name} id:`{update.from_id}`[photo]({photo_url}), The accompanying message is:\n{update.photo_caption}\nThe reply content is:\n{response_text}"
        send_image_log("", imageID)
        send_log(log)

        # Queue the image for admin approval
        message_id = update.message_id
        pending_approvals[message_id] = {
            "from_id": update.from_id,
            "user_name": update.user_name,
            "photo_caption": update.photo_caption,
            "response_text": response_text,
            "photo_url": photo_url,
            "imageID": imageID
        }

        # Notify the admin
        send_message(
            ADMIN_ID, 
            f"New photo from @{update.user_name} (ID: `{update.from_id}`):\n\nCaption: {update.photo_caption}\nReply: {response_text}\n\nTo approve, reply with /approve {message_id}\nTo deny, reply with /deny {message_id}"
        )