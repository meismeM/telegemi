# api/command.py
from time import sleep
import time # Import time module for sleep
import google.generativeai as genai
import re # Import re for answer_exercise

# from .command import excute_command, STREAMING_OUTPUT_SENT # <<< REMOVE THIS LINE

from .auth import is_admin
from .config import ALLOWED_USERS,IS_DEBUG_MODE,GOOGLE_API_KEY
from .printLog import send_log
from .telegram import send_message
from .textbook_processor import get_textbook_content, search_concept_pages, get_text_from_pages
from .gemini import generate_content, generate_content_stream

admin_auch_info = "You are not the administrator or your administrator ID is set incorrectly!!!"
debug_mode_info = "Debug mode is not enabled!"
STREAMING_OUTPUT_SENT = "STREAMING_OUTPUT_SENT" # Marker for streaming functions

chat_manager = ChatManager()
pending_approvals = {} # message_id -> approval_data

def handle_message(update_data):
    update = Update(update_data)
    authorized = is_authorized(update.from_id, update.user_name)

    # Determine content for initial log before any processing
    log_initial_content = update.text or update.photo_caption or ("Photo" if update.type == "photo" else "Unknown content type")
    send_log(f"Event received from @{update.user_name} (ID:`{update.from_id}`)\nContent: {log_initial_content}\nRaw: ```json\n{update_data}```")
    
    if not authorized:
        send_message(update.from_id, "You are not authorized to use this bot.")
        send_log(f"Unauthorized access attempt by @{update.user_name} (ID:`{update.from_id}`). Content: {log_initial_content}")
        return

    if update.type == "command":
        command_full_text = update.text # Original command text from update (e.g. "explain ..." or "approve ...")
        
        # Approval/Denial commands are special cases handled directly here
        if command_full_text.startswith("approve") and is_admin(update.from_id):
            try:
                parts = command_full_text.split(" ", 1)
                if len(parts) < 2:
                    send_message(update.from_id, "Invalid approve command. Use: /approve <message_id_to_approve>")
                    return
                target_message_id_str = parts[1]
                target_message_id = int(target_message_id_str) 
            except (IndexError, ValueError):
                send_message(update.from_id, "Invalid command format for approve. Use: /approve <message_id_to_approve>")
                return

            if target_message_id not in pending_approvals:
                send_message(update.from_id, f"Message ID {target_message_id} not found in pending approvals or already processed.")
                return

            approved_item_data = pending_approvals.pop(target_message_id) # Remove from pending
            original_user_id = approved_item_data["from_id"]
            original_user_name = approved_item_data.get("user_name", "UnknownUser") # Get username if stored

            try:
                if "photo_url" in approved_item_data: 
                    send_log(f"Admin @{update.user_name} (ID:{update.from_id}) approved IMAGE message (OriginalMsgID:{target_message_id}) from user @{original_user_name} (ID:{original_user_id})")
                    
                    channel_caption = f"Image from @{original_user_name}:\n{approved_item_data.get('photo_caption', '')}"
                    send_imageMessage(CHANNEL_ID, channel_caption, approved_item_data["imageID"])
                    if approved_item_data.get("response_text"): 
                         send_message(CHANNEL_ID, f"Bot's response to image:\n{approved_item_data['response_text']}")
                    send_message(original_user_id, "Your image submission and the bot's response have been approved and posted to the channel!")
                    send_message(update.from_id, f"Image message {target_message_id} from @{original_user_name} approved and posted.")

                else: # Text message approval
                    send_log(f"Admin @{update.user_name} (ID:{update.from_id}) approved TEXT message (OriginalMsgID:{target_message_id}) from user @{original_user_name} (ID:{original_user_id})")
                    
                    channel_message = f"Query from @{original_user_name}:\n{approved_item_data['text']}\n\nBot Response:\n{approved_item_data['response_text']}"
                    send_message(CHANNEL_ID, channel_message)
                    send_message(original_user_id, "Your message and the bot's response have been approved and posted to the channel!")
                    send_message(update.from_id, f"Text message {target_message_id} from @{original_user_name} approved and posted.")
            except Exception as e:
                send_log(f"Error during approval posting for message {target_message_id} (User: {original_user_id}): {e}")
                send_message(update.from_id, f"An error occurred while posting approved message {target_message_id}: {e}")
            return 

        elif command_full_text.startswith("deny") and is_admin(update.from_id):
            try:
                parts = command_full_text.split(" ", 1)
                if len(parts) < 2:
                    send_message(update.from_id, "Invalid deny command. Use: /deny <message_id_to_deny>")
                    return
                target_message_id_str = parts[1]
                target_message_id = int(target_message_id_str)
            except (IndexError, ValueError):
                send_message(update.from_id, "Invalid command format for deny. Use: /deny <message_id_to_deny>")
                return

            if target_message_id not in pending_approvals:
                send_message(update.from_id, f"Message ID {target_message_id} not found for denial or already processed.")
                return

            denied_item_data = pending_approvals.pop(target_message_id) # Remove from pending
            original_user_id = denied_item_data["from_id"]
            original_user_name = denied_item_data.get("user_name", "UnknownUser")
            send_log(f"Admin @{update.user_name} (ID:{update.from_id}) DENIED message (OriginalMsgID:{target_message_id}) from user @{original_user_name} (ID:{original_user_id})")
            send_message(original_user_id, "Your recent submission has been reviewed and was not approved for posting at this time.")
            send_message(update.from_id, f"Message {target_message_id} from @{original_user_name} denied. User notified.")
            return 

        # For other commands (not approve/deny)
        response_from_command_logic = excute_command(update.from_id, command_full_text)
        
        if response_from_command_logic == STREAMING_OUTPUT_SENT:
            send_log(f"Command '{command_full_text}' by @{update.user_name} executed, output streamed directly.")
        elif response_from_command_logic and response_from_command_logic.strip() != "": 
            send_message(update.from_id, response_from_command_logic)
            send_log(f"Command: /{command_full_text} by @{update.user_name}\nReply: {response_from_command_logic}")
        else: 
            send_log(f"Command '/{command_full_text}' by @{update.user_name} executed, no direct reply to user or reply was empty/handled by log.")
    
    elif update.type == "text":
        chat_instance = chat_manager.get_chat(update.from_id) 
        if not chat_instance.chat: # Check if the underlying Gemini chat session is valid
            send_message(update.from_id, "Sorry, the chat service is currently unavailable. Please try again later.")
            send_log(f"Chat service unavailable for user @{update.user_name} (ID:{update.from_id}). Gemini chat session is None.")
            return

        response_stream_generator = chat_instance.send_message(update.text) 

        buffered_stream_message = ""  
        last_chunk_send_time = time.time() 
        accumulated_full_response = "" 
        # Use the original user's message ID for approval tracking and potential reply_to_message_id
        original_user_message_id = update.message_id 

        try:
            for text_chunk in response_stream_generator:
                if text_chunk:
                    buffered_stream_message += text_chunk
                    accumulated_full_response += text_chunk 
    
                current_processing_time = time.time()
                time_since_last_chunk_sent = current_processing_time - last_chunk_send_time
    
                if len(buffered_stream_message) >= 3500 or \
                   (buffered_stream_message.strip() and time_since_last_chunk_sent >= 3): 
                    if buffered_stream_message.strip():
                        send_message(update.from_id, buffered_stream_message) #, reply_to_message_id=original_user_message_id if first_chunk else None) - Complicates things
                    buffered_stream_message = "" 
                    last_chunk_send_time = current_processing_time
                    time.sleep(0.2) 

        except Exception as e:
            error_msg_for_user = f"An error occurred while processing your message: {e}"
            send_log(f"Streaming error for user @{update.user_name} (ID:{update.from_id}) on text '{update.text}': {e}")
            send_message(update.from_id, error_msg_for_user)
            return 
        
        if buffered_stream_message.strip(): 
            send_message(update.from_id, buffered_stream_message)
        
        # Footer message construction
        footer_msg_parts = []
        if chat_instance.history_length > 6 : # Reduced from 10 for more frequent reminder
            footer_msg_parts.append("Type /new to start a fresh chat.")
        footer_msg_parts.append("Visit http://studysmart-nu.vercel.app for more tools!")
        
        final_footer_message = "\n\n" + " ".join(footer_msg_parts)
        if final_footer_message.strip(): # Only send if there's actual footer content
            send_message(update.from_id, final_footer_message)
            accumulated_full_response += final_footer_message # Add footer to the logged full response

        send_log(f"User @{update.user_name}: {update.text}\nFull Bot Response (streamed): {accumulated_full_response}")
        
        pending_approvals[original_user_message_id] = {
            "from_id": update.from_id,
            "user_name": update.user_name, # Store username for better admin messages
            "text": update.text, 
            "response_text": accumulated_full_response, 
            "timestamp": time.time()
        }
        admin_notify_msg = (
            f"Approval Needed: TEXT from @{update.user_name} (User ID: {update.from_id})\n"
            f"Original Message ID: {original_user_message_id}\n\n"
            f"User Query: {update.text}\n\n"
            f"Bot Reply (first 300 chars): {accumulated_full_response[:300].strip()}...\n\n"
            f"Reply to THIS admin message with:\n"
            f"  `/approve {original_user_message_id}`\n"
            f"  `/deny {original_user_message_id}`"
        )
        send_message(ADMIN_ID, admin_notify_msg)

    elif update.type == "photo":
        image_chat_proc = ImageChatManger(update.photo_caption, update.file_id)
        bot_response_to_image = image_chat_proc.send_image()
        
        send_message(update.from_id, bot_response_to_image, reply_to_message_id=update.message_id)

        user_photo_file_id = update.file_id 
        
        log_msg_text_part = f"User @{update.user_name} (ID:`{update.from_id}`) sent a photo.\nCaption: {update.photo_caption}\nBot Reply: {bot_response_to_image}"
        # send_image_log can take the caption for the admin log image
        send_image_log(f"Photo from @{update.user_name}. Caption: {update.photo_caption or '(No caption)'}. Bot reply: {bot_response_to_image[:100]}...", user_photo_file_id)
        send_log(log_msg_text_part) 

        original_user_message_id = update.message_id
        pending_approvals[original_user_message_id] = {
            "from_id": update.from_id,
            "user_name": update.user_name,
            "photo_caption": update.photo_caption,
            "response_text": bot_response_to_image,
            "photo_url": image_chat_proc.tel_photo_url(), # For potential direct use
            "imageID": user_photo_file_id, 
            "timestamp": time.time()
        }

        admin_notify_caption = (
            f"Approval Needed: PHOTO from @{update.user_name} (User ID: {update.from_id})\n"
            f"Original Message ID: {original_user_message_id}\n\n"
            f"User Caption: {update.photo_caption or '(No caption)'}\n"
            f"Bot Reply: {bot_response_to_image.strip()}\n\n"
            f"Reply to THIS admin message with:\n"
            f"  `/approve {original_user_message_id}`\n"
            f"  `/deny {original_user_message_id}`"
        )
        send_imageMessage(ADMIN_ID, admin_notify_caption, user_photo_file_id) # Send image to admin with approval instructions
