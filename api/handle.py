from .auth import is_authorized, is_admin
from .command import excute_command
from .context import ChatManager, ImageChatManger
from .telegram import Update, send_message, forward_message, copy_message, send_imageMessage
from .printLog import send_log, send_image_log
from .config import CHANNEL_ID, ADMIN_ID

chat_manager = ChatManager()
pending_approvals = {}

def handle_message(update_data):
    update = Update(update_data)
    authorized = is_authorized(update.from_id, update.user_name)

    # Log the event (without username and ID)
    send_log(f"event received\nThe content sent is:\n{update.text}\n```json\n{update_data}```")

    if not authorized:
        send_message(update.from_id, "You are not allowed to use this bot.")  # No ID in message
        log = f"No rights to use, The content sent is:\n{update.text}"
        send_log(log)
        return

    if update.type == "command":
        if update.text.startswith("approve") and is_admin(update.from_id):
            try:
                message_id = int(update.text.split(" ")[1])
            except (IndexError, ValueError):
                send_message(update.from_id, "Invalid command format. Please use /approve <message_id>")
                return

            if message_id not in pending_approvals:
                send_message(update.from_id, "Message ID not found.")
                return

            approved_message = pending_approvals.pop(message_id)

            try:
                if "photo_url" in approved_message:  # It's an image message

caption = approved_message.get("photo_caption", "")  
                    send_imageMessage(CHANNEL_ID, caption, approved_message["imageID"])
                    
                    send_message(CHANNEL_ID, approved_message["response_text"])
                    send_message(approved_message["from_id"], "GREAT!")
                else:  # It's a text message
                    send_message_to_channel(approved_message["text"], approved_message["response_text"]) # Use the new function
                    send_message(approved_message["from_id"], "GREAT!")
            except Exception as e:
                send_message(update.from_id, f"An error occurred while approving: {e}")

        elif update.text.startswith("deny") and is_admin(update.from_id):
            try:
                message_id = int(update.text.split(" ")[1])
            except (IndexError, ValueError):
                send_message(update.from_id, "Invalid command format. Please use /deny <message_id>")
                return

            if message_id not in pending_approvals:
                send_message(update.from_id, "Message ID not found.")
                return

            denied_message = pending_approvals.pop(message_id)
            send_message(denied_message["from_id"], "Your message has been denied.")

        else:  # Handle other commands
            response_text = excute_command(update.from_id, update.text)
            if response_text != "":
                send_message(update.from_id, response_text)
                log = f"The command sent is:\n{update.text}\nThe reply content is:\n{response_text}"  # No username/ID
                send_log(log)

    elif update.type == "text":
        chat = chat_manager.get_chat(update.from_id)
        answer = chat.send_message(update.text)
        extra_text = "\n\nType /new to kick off a new chat." if chat.history_length > 5 else ""
        response_text = f"{answer}{extra_text}"
        send_message(update.from_id, response_text)

        # Log (without username and ID)
        log = f"The content sent is:\n{update.text}\nThe reply content is:\n{response_text}"
        send_log(log)

        # Queue the message for admin approval
        message_id = update.message_id
        pending_approvals[message_id] = {
            "from_id": update.from_id,
            "text": update.text,
            "response_text": response_text
        }

        # Notify the admin (with formatted message and without username)
        send_message(
            ADMIN_ID,
            f"New message:\n\nMessage: {update.text}\nReply: {response_text}\n\nTo approve, reply with /approve {message_id}\nTo deny, reply with /deny {message_id}"
        )

    elif update.type == "photo":
        chat = ImageChatManger(update.photo_caption, update.file_id)
        response_text = chat.send_image()
        send_message(update.from_id, response_text, reply_to_message_id=update.message_id)

        photo_url = chat.tel_photo_url()
        imageID = update.file_id
        log = f"[photo]({photo_url}), The accompanying message is:\n{update.photo_caption}\nThe reply content is:\n{response_text}"  # No username/ID
        send_image_log("", imageID)
        send_log(log)

        # Queue the image for admin approval
        message_id = update.message_id
        pending_approvals[message_id] = {
            "from_id": update.from_id,
            "photo_caption": update.photo_caption,
            "response_text": response_text,
            "photo_url": photo_url,
            "imageID": imageID
        }

        # Notify the admin (without username)
        send_message(
            ADMIN_ID,
            f"New photo:\n\nCaption: {update.photo_caption}\nReply: {response_text}\n\nTo approve, reply with /approve {message_id}\nTo deny, reply with /deny {message_id}"
        )


def send_message_to_channel(message, response):
    try:
        send_message(CHANNEL_ID, f"Message: {message}\nReply: {response}")  # Formatted message
        print(f"Message successfully sent to the channel: {CHANNEL_ID}")
    except Exception as e:
        print(f"Error sending message to channel: {e}")