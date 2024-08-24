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
        # Handle admin commands (approve/deny)
        if update.text.startswith("/approve") or update.text.startswith("/deny"):
            handle_admin_commands(update_data)
        else:
            # Handle other commands
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


def handle_admin_commands(update_data):
    update = Update(update_data)
    admin_id = update.from_id
    command_parts = update.text.strip().split()  # Strip extra spaces

    if admin_id != ADMIN_ID:
        send_message(admin_id, "You are not authorized to approve or deny messages.")
        return

    if len(command_parts) < 2 or command_parts[0] not in ["/approve", "/deny"]:
        send_message(admin_id, "Invalid command format. Use /approve [message_id] or /deny [message_id].")
        return

    action = command_parts[0]
    try:
        message_id = int(command_parts[1])
    except ValueError:
        send_message(admin_id, "Invalid message ID. Please provide a valid number.")
        return

    if message_id not in pending_approvals:
        send_message(admin_id, f"Message ID `{message_id}` not found.")
        return

    approval_info = pending_approvals.pop(message_id)

    if action == "/approve":
        # Post the message to the channel
        if "photo_url" in approval_info:
            send_message_to_channel(f"[Photo]({approval_info['photo_url']}) by @{approval_info['user_name']}:\n\nCaption: {approval_info['photo_caption']}\n\n(Approved by Admin)")
        else:
            send_message_to_channel(f"Message by @{approval_info['user_name']}:\n\n{approval_info['text']}\n\n(Approved by Admin)")

        send_message(admin_id, f"Message ID `{message_id}` has been approved and posted to the channel.")
        send_message(approval_info["from_id"], "Your message has been approved and posted to the channel.")
    elif action == "/deny":
        send_message(admin_id, f"Message ID `{message_id}` has been denied.")
        send_message(approval_info["from_id"], "Your message has been denied and was not posted to the channel.")