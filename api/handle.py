from .auth import is_authorized, is_admin
from .command import excute_command
from .context import ChatManager, ImageChatManger
from .telegram import Update, send_message, forward_message, copy_message, send_imageMessage
from .printLog import send_log, send_image_log
from .config import CHANNEL_ID, ADMIN_ID
import time
chat_manager = ChatManager()
pending_approvals = {}

def handle_message(update_data):
    update = Update(update_data)
    authorized = is_authorized(update.from_id, update.user_name)

    # Log the event (without username and ID)
    #send_log(f"event received\nThe content sent is:\n{update.text}\n```json\n{update_data}```")
    send_log(f"event received\n@{update.user_name} id:`{update.from_id}`\nThe content sent is:\n{update.text}\n```json\n{update_data}```")
    
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
                    send_message_to_channel(approved_message["text"], approved_message["response_text"])
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
                log = f"The command sent is:\n{update.text}\nThe reply content is:\n{response_text}"
                send_log(log)
    
    elif update.type == "text":
        chat = chat_manager.get_chat(update.from_id)
        response_stream = chat.send_message(update.text) 

        buffered_message = ""  
        last_chunk_time = time.time() 
        full_response = "" 
        # [!HIGHLIGHT!] Define message_id here for text messages
        message_id = update.message_id # Get message_id from the update object
    
        try:
            for chunk_text in response_stream:
                if chunk_text:
                    buffered_message += chunk_text
                    full_response += chunk_text
    
                current_time = time.time()
                time_since_last_chunk = current_time - last_chunk_time
    
                # [!HIGHLIGHT!] More explicit buffer flush logic and logging
                if len(buffered_message) > 2000 or time_since_last_chunk >= 4: 
                    message_to_send = buffered_message # Store buffer content in a separate variable
                    buffered_message = "" # Clear buffer IMMEDIATELY before sending
                    send_message(update.from_id,message_to_send) # Send the buffered message
                    #send_message(
            ADMIN_ID,
            f"New message:\n\nMessage: {update.text}\nReply: {message_to_send}\n\nTo approve, reply with /approve {message_id}\nTo deny, reply with /deny {message_id}"
        )
                    print(f"send_message() called - chunk (first 50 chars): {message_to_send[:50]}...") # [!LOGGING!] Log when a chunk is sent
                    last_chunk_time = current_time
                    time.sleep(0.1) # Optional throttling delay

        except Exception as e:
            error_message = f"Error during streaming response for general chat: {e}"
            send_message(update.from_id, error_message)
            send_message(
            ADMIN_ID,
            f"New message:\n\nMessage: {update.text}\nReply: {error_message}")
            return # Exit handler on error
    # Send any remaining buffered text after the stream is finished
        if buffered_message:
            send_message(update.from_id, f"{buffered_message}\n\nUse 'http://studysmart-nu.vercel.app' to generate Notes and Questions")
            send_message(
            ADMIN_ID,
            f"New message:\n\nMessage: {update.text}\nReply: {buffered_message}\n\nTo approve, reply with /approve {message_id}\nTo deny, reply with /deny {message_id}"
        )
            print("send_message() called - remaining buffer (last chunk)") # [!LOGGING!] Log for remaining buffer send
        if buffered_message: 
            #send_message(update.from_id, full_response)
            send_message(ADMIN_ID,f"New message:\n\nMessage: {update.text}\nReply: {full_response}\n\nTo approve, reply with /approve {message_id}\nTo deny, reply with /deny {message_id}")

        extra_text = "\n\nType /new to kick off a new chat." if chat.history_length > 10 else ""
        response_text = f"{full_response}{extra_text}"  # Reassemble for logging and admin approval
        
        pending_approvals[message_id] = { # [!FIXED! - message_id is now defined]
            "from_id": update.from_id,
            "text": update.text,
            "response_text": response_text
        }
        # Notify the admin (with formatted message and without username)
        #send_message(ADMIN_ID,f"New message:\n\nMessage: {update.text}\nReply: {response_text}\n\nTo approve, reply with /approve {message_id}\nTo deny, reply with /deny {message_id}")
    elif update.type == "photo":
        chat = ImageChatManger(update.photo_caption, update.file_id)
        response_text = chat.send_image()
        send_message(update.from_id, response_text, reply_to_message_id=update.message_id)

        photo_url = chat.tel_photo_url()
        imageID = update.file_id
        log = f"[photo]({photo_url}), The accompanying message is:\n{update.photo_caption}\nThe reply content is:\n{response_text}"
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
