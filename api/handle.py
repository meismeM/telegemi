# api/handle.py
import time
import traceback
import logging
from .auth import is_authorized, is_admin
from .command import help, get_allowed_users, get_API_key, list_models, speed_test, send_message_test, \
                     explain_concept, prepare_short_note, create_questions
from .context import ChatManager, ImageChatManger
# Import specific sending functions
from .telegram import Update, send_message, send_imageMessage, send_message_with_inline_keyboard
from .printLog import send_log # Use send_log for consistency or switch to logging module
from .config import CHANNEL_ID, ADMIN_ID, IS_DEBUG_MODE
import requests # For answerCallbackQuery
from .config import TELEGRAM_API # Import TELEGRAM_API base URL

logger = logging.getLogger(__name__)

# --- State Management (Simple cache - see Vercel note) ---
user_context = {}
MAX_CONTEXT_AGE_SECONDS = 300

AVAILABLE_TEXTBOOKS = {
    "economics9": "Economics Grade 9", "history9": "History Grade 9", "biology9": "Biology Grade 9",
    "chemistry9": "Chemistry Grade 9", "citizenship": "Citizenship Grade 9", "english9": "English Grade 9",
    "geography9": "Geography Grade 9", "physics9": "Physics Grade 9"
}

pending_approvals = {}

# --- Helper to answer callback ---
def acknowledge_callback(callback_query_id):
     """Sends an empty answerCallbackQuery to Telegram."""
     try:
          requests.post(f"{TELEGRAM_API}/answerCallbackQuery", json={"callback_query_id": callback_query_id}, timeout=5)
          # logger.info(f"Acknowledged callback_query: {callback_query_id}")
     except requests.exceptions.RequestException as ack_err:
          logger.error(f"Error acknowledging callback_query {callback_query_id}: {ack_err}")
          send_log(f"Error acknowledging callback_query: {ack_err}") # Also send to admin log if desired


# --- Main Handler ---
def handle_message(update_data):
    start_time = time.time() # For checking function duration
    try:
        # --- Callback Query Handling ---
        if 'callback_query' in update_data:
            callback_query = update_data['callback_query']
            user_id = callback_query['from']['id']
            chat_id = callback_query['message']['chat']['id']
            callback_query_id = callback_query['id'] # Get ID for acknowledgment
            callback_data = callback_query['data']
            username = callback_query['from'].get('username', f"id:{user_id}")

            send_log(f"Callback received from @{username} (id:`{user_id}`): {callback_data}")

            # Acknowledge callback quickly
            acknowledge_callback(callback_query_id)

            # --- Authorization ---
            if not is_authorized(user_id, username):
                send_message(chat_id, "You are not allowed to use this feature.")
                return "ok", 200

            # --- Process Callback Data ---
            if callback_data.startswith("subject:"):
                textbook_id = callback_data.split(":", 1)[1]
                if textbook_id in AVAILABLE_TEXTBOOKS:
                    textbook_name = AVAILABLE_TEXTBOOKS[textbook_id]
                    keyboard = [
                        [{"text": "Explain Concept", "callback_data": f"action:explain:{textbook_id}"}],
                        [{"text": "Create Notes", "callback_data": f"action:note:{textbook_id}"}],
                        [{"text": "Generate Questions", "callback_data": f"action:questions:{textbook_id}"}]
                    ]
                    send_message_with_inline_keyboard(
                        chat_id,
                        f"Selected: **{textbook_name}**.\nWhat would you like to do?",
                        keyboard
                    )
                else: send_message(chat_id, "Invalid subject selection.")

            elif callback_data.startswith("action:"):
                parts = callback_data.split(":", 2)
                if len(parts) == 3:
                    action = parts[1]
                    textbook_id = parts[2]
                    if textbook_id in AVAILABLE_TEXTBOOKS:
                        textbook_name = AVAILABLE_TEXTBOOKS[textbook_id]
                        user_context[user_id] = {'action': action, 'textbook_id': textbook_id, 'timestamp': time.time()}
                        prompt_keyword = 'concept or question' if action == 'explain' else ('topic' if action == 'note' else 'concept')
                        prompt_text = f"OK. Please send the *{prompt_keyword}* you want to **{action.replace('_', ' ')}** from *{textbook_name}*."
                        send_message(chat_id, prompt_text)
                    else: send_message(chat_id, "Invalid action selection (textbook).")
                else: send_message(chat_id, "Error processing action.")

            return "ok", 200 # Callback handled

        # --- Regular Message Handling ---
        if not "message" in update_data:
             logger.warning(f"Received non-message update type: {update_data.get('update_id')}")
             return "ok", 200

        update = Update(update_data)

        if not update.from_id or not update.type:
             logger.warning(f"Could not parse update or irrelevant type: {update_data.get('update_id')}")
             return "ok", 200

        user_id = update.from_id
        chat_id = update.chat_id
        username = update.user_name

        # --- Authorization ---
        authorized = is_authorized(user_id, username)
        log_entry = f"Event received from @{username} (id:`{user_id}`, chat:`{chat_id}`): Type={update.type}, Text='{str(update.text)[:50]}...'"
        # logger.info(log_entry) # Use logger or send_log
        send_log(log_entry)

        if not authorized:
            send_message(chat_id, "You are not allowed to use this bot.")
            return "ok", 200

        # --- Context Check ---
        current_time = time.time()
        context = user_context.get(user_id)
        if context and (current_time - context['timestamp'] > MAX_CONTEXT_AGE_SECONDS):
            logger.info(f"Context expired for user {user_id}")
            del user_context[user_id]
            context = None

        if context and update.type == "text" and not update.text.startswith('/'):
            action = context['action']
            textbook_id = context['textbook_id']
            user_input_text = update.text

            send_log(f"Processing context for @{username}: Action={action}, Textbook={textbook_id}, Input='{user_input_text[:50]}...'")

            # Call the appropriate function - they handle their own messaging/streaming
            if action == "explain":
                explain_concept(user_id, user_input_text, textbook_id)
            elif action == "note":
                prepare_short_note(user_id, user_input_text, textbook_id)
            elif action == "questions":
                create_questions(user_id, user_input_text, textbook_id)

            if user_id in user_context: del user_context[user_id]
            logger.info(f"Processed context for user {user_id}. Duration: {time.time() - start_time:.2f}s")
            return "ok", 200

        # --- Process Commands ---
        elif update.type == "command":
            command_text = update.text
            command_name = command_text.split(" ", 1)[0].lower()

            if command_name == "/study":
                keyboard = [
                     [{"text": name, "callback_data": f"subject:{id}"}]
                     for id, name in AVAILABLE_TEXTBOOKS.items()
                ]
                # Simple 2-column layout
                if len(keyboard) > 1:
                     keyboard = [keyboard[i] + (keyboard[i+1] if i+1 < len(keyboard) else []) for i in range(0, len(keyboard), 2)]

                send_message_with_inline_keyboard(chat_id, "📚 Which subject would you like help with?", keyboard)

            elif command_name.startswith("/approve") or command_name.startswith("/deny"):
                 # Admin approval logic (simplified from previous version for brevity)
                 is_approve = command_name.startswith("/approve")
                 if not is_admin(user_id):
                      send_message(chat_id, admin_auch_info)
                      return "ok", 200
                 try:
                     parts = command_text.split(" ", 1)
                     if len(parts) < 2:
                          send_message(chat_id, f"Invalid format. Use `/{'approve' if is_approve else 'deny'} <message_id>`")
                          return "ok", 200
                     msg_id = int(parts[1])

                     if msg_id not in pending_approvals:
                          send_message(chat_id, f"Message ID `{msg_id}` not found for {'approval' if is_approve else 'denial'}.")
                          return "ok", 200

                     processed_message = pending_approvals.pop(msg_id)

                     if is_approve:
                          # Send to channel
                          if "photo_url" in processed_message:
                               send_imageMessage(CHANNEL_ID, processed_message.get("photo_caption", ""), processed_message["imageID"])
                               send_message(CHANNEL_ID, f"Reply:\n{processed_message['response_text']}")
                          else:
                               channel_text = f"❓ **Question:**\n{processed_message['text']}\n\n💡 **Reply:**\n{processed_message['response_text']}"
                               send_message(CHANNEL_ID, channel_text)
                          # Notify user & admin
                          send_message(processed_message["from_id"], "✅ Your message has been approved and sent!")
                          send_message(user_id, f"✅ Approved message `{msg_id}`.")
                          send_log(f"Admin @{username} approved message {msg_id}")
                     else: # Deny
                          send_message(processed_message["from_id"], "❌ Your message was not approved.")
                          send_message(user_id, f"❌ Denied message `{msg_id}`.")
                          send_log(f"Admin @{username} denied message {msg_id}")

                 except ValueError: send_message(chat_id, "Invalid message ID.")
                 except Exception as e:
                      send_message(chat_id, f"Error processing {'approval' if is_approve else 'denial'}: {e}")
                      send_log(f"Error {'approving' if is_approve else 'denying'} message {msg_id}: {e}\n{traceback.format_exc()}")

            # --- Other commands ---
            else:
                 response_text = ""
                 if command_name == "/start" or command_name == "/help": response_text = help()
                 elif command_name == "/get_my_info": response_text = f"Your Telegram ID is: `{user_id}`"
                 elif command_name == "/new": response_text = "Starting a new chat..." # ChatManager handles reset below
                 elif command_name in ["/get_allowed_users", "/get_api_key", "/list_models"]:
                     if not is_admin(user_id): response_text = admin_auch_info
                     elif IS_DEBUG_MODE == "0" and command_name != "/get_allowed_users": response_text = debug_mode_info
                     else:
                          if command_name == "/get_allowed_users": response_text = get_allowed_users()
                          elif command_name == "/get_api_key": response_text = get_API_key()
                          elif command_name == "/list_models": response_text = list_models()
                 elif command_name == "/send_message": response_text = send_message_test(user_id, command_text)
                 elif command_name == "/5g_test": response_text = speed_test(user_id)
                 else: response_text = "🤔 Unknown command. Use /help."

                 if response_text: send_message(chat_id, response_text)

            logger.info(f"Processed command {command_name} for user {user_id}. Duration: {time.time() - start_time:.2f}s")
            return "ok", 200

        # --- Process Regular Text (Gemini Chat) ---
        elif update.type == "text":
             if 'chat_manager' not in globals(): globals()['chat_manager'] = ChatManager()

             chat = chat_manager.get_chat(user_id)
             if update.text.lower().strip() == "/new":
                 chat = chat_manager._new_chat(user_id)
                 send_message(chat_id, "✨ Starting a fresh chat!")
                 return "ok", 200

             send_message(chat_id, "🤔 Thinking...")
             try:
                 # *** Crucial part for streaming debug ***
                 response_stream = chat.send_message(update.text) # Assume this returns a stream/iterator

                 full_response = ""
                 buffered_message = ""
                 last_chunk_time = time.time()
                 message_id = update.message_id
                 chunk_count = 0 # Counter for logging

                 for chunk_text in response_stream:
                     chunk_count += 1
                     # logger.info(f"Chat chunk {chunk_count} received for user {user_id}: {chunk_text[:30]}...") # Detailed log
                     send_log(f"Chunk {chunk_count} for @{username}: '{str(chunk_text)[:30]}...'") # Log reception

                     if chunk_text:
                         buffered_message += chunk_text
                         full_response += chunk_text

                     current_time = time.time()
                     time_since_last_chunk = current_time - last_chunk_time

                     if len(buffered_message) > 3500 or (buffered_message and time_since_last_chunk >= 4):
                         message_to_send = buffered_message
                         buffered_message = "" # Clear buffer *before* sending
                         send_log(f"Sending chat buffer (len={len(message_to_send)}) to @{username}")
                         send_message(chat_id, message_to_send) # Send the buffered message
                         last_chunk_time = current_time
                         time.sleep(0.1) # Throttle

                     # Check elapsed time - Vercel timeout check
                     if time.time() - start_time > 55: # Example: Check if nearing 60s limit
                          logger.warning(f"Function timeout likely for user {user_id} during streaming.")
                          send_log(f"⚠️ Function nearing timeout for @{username} during streaming.")
                          send_message(chat_id, "...(Response might be incomplete due to processing time limit)...")
                          break # Exit loop if timeout is likely

                 # Send any remaining buffer *after* the loop finishes or breaks
                 if buffered_message:
                     send_log(f"Sending final chat buffer (len={len(buffered_message)}) to @{username}")
                     send_message(chat_id, buffered_message)

                 if not full_response:
                     send_message(chat_id, "I couldn't generate a response for that.")
                     full_response = "[No response generated]"


                 # Admin approval
                 if ADMIN_ID and CHANNEL_ID:
                     pending_approvals[message_id] = {"from_id": user_id, "text": update.text, "response_text": full_response}
                     approval_request_text = (f"📩 New msg from @{username} (id:`{user_id}`):\n\n"
                                              f"**Msg:**\n{update.text}\n\n"
                                              f"**Reply:**\n{full_response[:1000]}{'...' if len(full_response)>1000 else ''}\n\n"
                                              f"Use `/approve {message_id}` or `/deny {message_id}`.")
                     send_message(ADMIN_ID, approval_request_text)

                 if chat.history_length > 10: send_message(chat_id, "\n💡 Tip: `/new` for fresh chat.")

             except Exception as e:
                 error_message = f"❌ An error occurred with Gemini: {e}"
                 send_message(chat_id, error_message)
                 logger.error(f"Error processing chat for @{username}: {e}\n{traceback.format_exc()}")
                 send_log(f"Error in Gemini chat for @{username}: {e}")

             logger.info(f"Processed text message for user {user_id}. Duration: {time.time() - start_time:.2f}s")
             return "ok", 200

        # --- Process Photos ---
        elif update.type == "photo":
             # (Keep existing photo logic, ensure error handling is present)
            if 'ImageChatManger' not in globals(): pass # Ensure class is available

            chat_img = ImageChatManger(update.photo_caption, update.file_id)
            send_message(chat_id, "🖼️ Analyzing image...")
            try:
                response_text = chat_img.send_image()
                send_message(chat_id, response_text, reply_to_message_id=update.message_id)
                photo_url = chat_img.tel_photo_url()
                log_text = f"[photo]({photo_url}), Cap: {update.photo_caption}, Reply: {response_text[:50]}..."
                send_log(log_text)

                # Admin approval
                if ADMIN_ID and CHANNEL_ID:
                     msg_id_img = update.message_id
                     pending_approvals[msg_id_img] = {"from_id": user_id, "photo_caption": update.photo_caption, "response_text": response_text, "photo_url": photo_url, "imageID": update.file_id}
                     approval_req_img = (f"📸 New photo @{username} (id:`{user_id}`):\n\n"
                                         f"**Cap:** {update.photo_caption}\n**Reply:** {response_text[:1000]}...\n\n"
                                         f"`/approve {msg_id_img}` or `/deny {msg_id_img}`.")
                     try: send_imageMessage(ADMIN_ID, approval_req_img, update.file_id)
                     except: send_message(ADMIN_ID, approval_req_img + "\n(Img preview failed)")

            except Exception as e:
                 send_message(chat_id, f"❌ Error processing image: {e}")
                 logger.error(f"Error processing photo for @{username}: {e}\n{traceback.format_exc()}")
                 send_log(f"Error processing photo for @{username}: {e}")

            logger.info(f"Processed photo for user {user_id}. Duration: {time.time() - start_time:.2f}s")
            return "ok", 200

        # --- Fallback ---
        else:
             logger.warning(f"Unhandled message type '{update.type}' from @{username}")
             return "ok", 200

    # --- General Error Catch ---
    except Exception as e:
        error_details = traceback.format_exc()
        logger.exception(f"🚨 Unhandled error in handle_message: {e}") # Log exception with stack trace
        send_log(f"🚨 Unhandled error: {e}\n{error_details[:1000]}...") # Send truncated error log
        try:
             error_chat_id = update_data.get('message', {}).get('chat', {}).get('id') or \
                             update_data.get('callback_query', {}).get('message', {}).get('chat', {}).get('id')
             if error_chat_id: send_message(error_chat_id, "Sorry, an internal error occurred.")
        except Exception as notify_err:
             logger.error(f"🚨 Failed to notify user about error: {notify_err}")
        return "error", 500


# --- Keep send_message_to_channel ---
def send_message_to_channel(message, response):
     try:
        channel_message = f"❓ **Question:**\n{message}\n\n💡 **Reply:**\n{response}"
        send_message(CHANNEL_ID, channel_message)
        logger.info(f"Message sent to channel: {CHANNEL_ID}")
     except Exception as e:
        logger.error(f"Error sending message to channel {CHANNEL_ID}: {e}")
        send_log(f"Error sending approved message to channel {CHANNEL_ID}: {e}")
