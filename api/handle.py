# api/handle.py
import time
import traceback # For detailed error logging
from .auth import is_authorized, is_admin
# Import specific functions from command, not the executor
from .command import help, get_allowed_users, get_API_key, list_models, speed_test, send_message_test, \
                     explain_concept, prepare_short_note, create_questions
from .context import ChatManager, ImageChatManger
from .telegram import Update, send_message, send_imageMessage, send_message_with_inline_keyboard
from .printLog import send_log, send_image_log
from .config import CHANNEL_ID, ADMIN_ID, IS_DEBUG_MODE

# --- State Management (Use with caution on Vercel - consider external storage) ---
# Simple dictionary to hold context for the next message after an action prompt
user_context = {}  # Format: {user_id: {'action': 'explain', 'textbook_id': 'economics9', 'timestamp': time.time()}}
MAX_CONTEXT_AGE_SECONDS = 300  # e.g., 5 minutes

# Define available textbooks here or load from config/processor
AVAILABLE_TEXTBOOKS = {
    "economics9": "Economics Grade 9",
    "history9": "History Grade 9",
    "biology9": "Biology Grade 9",
    "chemistry9": "Chemistry Grade 9",
    "citizenship": "Citizenship Grade 9",
    "english9": "English Grade 9",
    "geography9": "Geography Grade 9",
    "physics9": "Physics Grade 9"
}

# Store messages pending admin approval
pending_approvals = {}

# --- Main Handler ---
def handle_message(update_data):
    try:
        # --- Callback Query Handling ---
        if 'callback_query' in update_data:
            callback_query = update_data['callback_query']
            user_id = callback_query['from']['id']
            chat_id = callback_query['message']['chat']['id']
            # message_id = callback_query['message']['message_id'] # For potential message editing
            callback_data = callback_query['data']
            username = callback_query['from'].get('username', f"id:{user_id}") # For logging/auth

            send_log(f"Callback received from @{username} (id:`{user_id}`): {callback_data}")

            # --- Authorization for callbacks ---
            if not is_authorized(user_id, username):
                send_message(chat_id, "You are not allowed to use this feature.")
                send_log(f"Unauthorized callback attempt by @{username} (id:`{user_id}`)")
                return "ok", 200

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
                    # TODO: Optionally edit the original message instead of sending a new one
                else:
                    send_message(chat_id, "Invalid subject selection.")

            elif callback_data.startswith("action:"):
                parts = callback_data.split(":", 2)
                if len(parts) == 3:
                    action = parts[1]
                    textbook_id = parts[2]
                    if textbook_id in AVAILABLE_TEXTBOOKS:
                        textbook_name = AVAILABLE_TEXTBOOKS[textbook_id]
                        # Store context (simple cache example - see Vercel note above)
                        user_context[user_id] = {'action': action, 'textbook_id': textbook_id, 'timestamp': time.time()}
                        prompt_text = f"OK. Please send the *{'concept' if action != 'note' else 'topic'}* you want to **{action.replace('_', ' ')}** from *{textbook_name}*."
                        send_message(chat_id, prompt_text)
                        # TODO: Optionally edit the original message
                    else:
                         send_message(chat_id, "Invalid action selection.")
                else:
                     send_message(chat_id, "Error processing action.")

            # Acknowledge the callback query to remove the "loading" state on the button
            try:
                 requests.post(f"{TELEGRAM_API}/answerCallbackQuery", json={"callback_query_id": callback_query['id']})
            except Exception as ack_err:
                 send_log(f"Error acknowledging callback query: {ack_err}")

            return "ok", 200

        # --- Regular Message Handling ---
        # Ensure it's a message update
        if not "message" in update_data:
             send_log(f"Received non-message update type: {update_data.get('update_id')}")
             return "ok", 200 # Ignore other update types for now

        update = Update(update_data)

        # Basic check if update parsing failed or not a message type we handle
        if not update.from_id or not update.type:
             send_log(f"Could not parse update or irrelevant type: {update_data.get('update_id')}")
             return "ok", 200

        user_id = update.from_id
        chat_id = update.chat_id
        username = update.user_name

        # --- Authorization for messages ---
        authorized = is_authorized(user_id, username)
        send_log(f"Event received from @{username} (id:`{user_id}`, chat:`{chat_id}`): Type={update.type}, Text='{update.text[:50]}...'")

        if not authorized:
            send_message(chat_id, "You are not allowed to use this bot.")
            send_log(f"Unauthorized message from @{username} (id:`{user_id}`)")
            return "ok", 200

        # --- Context Check (Simple Cache - see Vercel note) ---
        context = user_context.get(user_id)
        # Clean up expired contexts
        if user_id in user_context and (time.time() - user_context[user_id]['timestamp'] > MAX_CONTEXT_AGE_SECONDS):
            del user_context[user_id]
            context = None # Clear expired context

        if context and update.type == "text" and not update.text.startswith('/'):
            action = context['action']
            textbook_id = context['textbook_id']
            user_input_text = update.text # This is the concept/topic

            send_log(f"Processing context for @{username}: Action={action}, Textbook={textbook_id}, Input='{user_input_text[:50]}...'")

            # Call the appropriate function from command.py
            # These functions handle sending messages, including streaming
            if action == "explain":
                explain_concept(user_id, user_input_text, textbook_id)
            elif action == "note":
                prepare_short_note(user_id, user_input_text, textbook_id)
            elif action == "questions":
                create_questions(user_id, user_input_text, textbook_id)

            # Clear context after use
            if user_id in user_context:
                del user_context[user_id]

            return "ok", 200 # Context handled

        # --- Process Commands ---
        elif update.type == "command":
            command_text = update.text # Full command like "/help" or "/approve 123"

            # --- /study command ---
            if command_text.lower() == "/study":
                keyboard = [
                     [{"text": name, "callback_data": f"subject:{id}"}]
                     for id, name in AVAILABLE_TEXTBOOKS.items()
                ]
                # Arrange in 2 columns if many textbooks
                if len(keyboard) > 4:
                    keyboard_pairs = []
                    for i in range(0, len(keyboard), 2):
                        pair = keyboard[i]
                        if i + 1 < len(keyboard):
                            pair.extend(keyboard[i+1])
                        keyboard_pairs.append(pair)
                    keyboard = keyboard_pairs

                send_message_with_inline_keyboard(chat_id, "📚 Which subject would you like help with?", keyboard)
                return "ok", 200

            # --- Admin Approval Commands ---
            elif command_text.lower().startswith("/approve") and is_admin(user_id):
                try:
                    parts = command_text.split(" ", 1)
                    if len(parts) < 2:
                         send_message(chat_id, "Invalid format. Use `/approve <message_id>`")
                         return "ok", 200
                    message_id_to_approve = int(parts[1])

                    if message_id_to_approve not in pending_approvals:
                        send_message(chat_id, f"Message ID `{message_id_to_approve}` not found for approval.")
                        return "ok", 200

                    approved_message = pending_approvals.pop(message_id_to_approve)

                    # Send to channel
                    if "photo_url" in approved_message: # Image message
                        caption = approved_message.get("photo_caption", "")
                        response_text_approved = approved_message["response_text"]
                        image_id_approved = approved_message["imageID"]
                        send_imageMessage(CHANNEL_ID, caption, image_id_approved)
                        send_message(CHANNEL_ID, f"Reply:\n{response_text_approved}") # Send response separately
                    else: # Text message
                        text_approved = approved_message["text"]
                        response_text_approved = approved_message["response_text"]
                        send_message(CHANNEL_ID, f"❓ **Question:**\n{text_approved}\n\n💡 **Reply:**\n{response_text_approved}")

                    # Notify original user and admin
                    send_message(approved_message["from_id"], "✅ Your message has been approved and sent to the channel!")
                    send_message(user_id, f"✅ Approved and sent message `{message_id_to_approve}`.")
                    send_log(f"Admin @{username} approved message {message_id_to_approve}")

                except ValueError:
                    send_message(chat_id, "Invalid message ID. Must be a number.")
                except Exception as e:
                    send_message(chat_id, f"An error occurred while approving: {e}")
                    send_log(f"Error approving message {message_id_to_approve}: {e}\n{traceback.format_exc()}")

                return "ok", 200

            elif command_text.lower().startswith("/deny") and is_admin(user_id):
                try:
                    parts = command_text.split(" ", 1)
                    if len(parts) < 2:
                         send_message(chat_id, "Invalid format. Use `/deny <message_id>`")
                         return "ok", 200
                    message_id_to_deny = int(parts[1])

                    if message_id_to_deny not in pending_approvals:
                        send_message(chat_id, f"Message ID `{message_id_to_deny}` not found for denial.")
                        return "ok", 200

                    denied_message = pending_approvals.pop(message_id_to_deny)
                    # Notify original user and admin
                    send_message(denied_message["from_id"], "❌ Your message was not approved for the channel.")
                    send_message(user_id, f"❌ Denied message `{message_id_to_deny}`.")
                    send_log(f"Admin @{username} denied message {message_id_to_deny}")

                except ValueError:
                    send_message(chat_id, "Invalid message ID. Must be a number.")
                except Exception as e:
                    send_message(chat_id, f"An error occurred while denying: {e}")
                    send_log(f"Error denying message {message_id_to_deny}: {e}\n{traceback.format_exc()}")

                return "ok", 200

            # --- Other commands (call functions from command.py) ---
            else:
                 response_text = ""
                 command_name = command_text.split(" ", 1)[0].lower()

                 if command_name == "/start" or command_name == "/help":
                      response_text = help()
                 elif command_name == "/get_my_info":
                      response_text = f"Your Telegram ID is: `{user_id}`" # Use user_id from update
                 elif command_name == "/new":
                      # Handled by ChatManager below, just acknowledge
                      response_text = "Starting a new chat..." # Or let ChatManager handle response
                 # Admin commands
                 elif command_name in ["/get_allowed_users", "/get_api_key", "/list_models"]:
                     if not is_admin(user_id):
                         response_text = admin_auch_info
                     elif IS_DEBUG_MODE == "0" and command_name != "/get_allowed_users": # Allow listing users even if not debug?
                          response_text = debug_mode_info
                     else:
                          if command_name == "/get_allowed_users": response_text = get_allowed_users()
                          elif command_name == "/get_api_key": response_text = get_API_key()
                          elif command_name == "/list_models": response_text = list_models()
                 elif command_name == "/send_message":
                      response_text = send_message_test(user_id, command_text)
                 elif command_name == "/5g_test":
                      response_text = speed_test(user_id)
                 else:
                      response_text = "🤔 Unknown command. Use /help."

                 if response_text:
                      send_message(chat_id, response_text)
                      send_log(f"Command '{command_name}' processed for @{username}. Reply sent.")

            return "ok", 200

        # --- Process Regular Text (Gemini Chat) ---
        elif update.type == "text":
             # Ensure ChatManager exists (instantiate if not, though module-level is typical)
             if 'chat_manager' not in globals():
                  globals()['chat_manager'] = ChatManager()

             chat = chat_manager.get_chat(user_id)
             # Handle /new command specifically for chat reset
             if update.text.lower().strip() == "/new":
                 chat = chat_manager._new_chat(user_id) # Reset chat
                 send_message(chat_id, "✨ Starting a fresh chat! Previous history cleared.")
                 send_log(f"New chat started for @{username} (id:`{user_id}`)")
                 return "ok", 200

             # Send prompt to Gemini (potentially streaming)
             send_message(chat_id, "🤔 Thinking...") # Indicate processing
             try:
                 response_stream = chat.send_message(update.text) # Assume this returns a stream

                 full_response = ""
                 buffered_message = ""
                 last_chunk_time = time.time()
                 message_id = update.message_id # ID of the user's message

                 for chunk_text in response_stream:
                     if chunk_text:
                         buffered_message += chunk_text
                         full_response += chunk_text

                     current_time = time.time()
                     time_since_last_chunk = current_time - last_chunk_time

                     if len(buffered_message) > 3500 or (buffered_message and time_since_last_chunk >= 4):
                         message_to_send = buffered_message
                         buffered_message = ""
                         send_message(chat_id, message_to_send)
                         send_log(f"Sent chat chunk to @{username} (id:`{user_id}`)")
                         last_chunk_time = current_time
                         time.sleep(0.1)

                 # Send any remaining buffer
                 if buffered_message:
                     send_message(chat_id, buffered_message)
                     send_log(f"Sent final chat chunk to @{username} (id:`{user_id}`)")

                 if not full_response:
                      send_message(chat_id, "I couldn't generate a response for that.")
                      full_response = "[No response generated]"


                 # Admin approval logic (only if ADMIN_ID and CHANNEL_ID are set)
                 if ADMIN_ID and CHANNEL_ID:
                     pending_approvals[message_id] = {
                         "from_id": user_id,
                         "text": update.text,
                         "response_text": full_response # Store the complete response
                     }
                     approval_request_text = (
                         f"📩 New message from @{username} (id:`{user_id}`):\n\n"
                         f"**Message:**\n{update.text}\n\n"
                         f"**Reply:**\n{full_response[:1000]}...\n\n" # Show only part of long replies
                         f"Use `/approve {message_id}` or `/deny {message_id}`."
                     )
                     send_message(ADMIN_ID, approval_request_text)
                     send_log(f"Sent message {message_id} from @{username} for admin approval.")

                 # Suggest /new if history is long
                 if chat.history_length > 10:
                     send_message(chat_id, "\n\n💡 Tip: Type `/new` to start a fresh chat.")

             except Exception as e:
                 error_message = f"❌ An error occurred: {e}"
                 send_message(chat_id, error_message)
                 send_log(f"Error processing chat for @{username}: {e}\n{traceback.format_exc()}")

             return "ok", 200

        # --- Process Photos ---
        elif update.type == "photo":
            # Ensure ImageChatManger exists (instantiate if needed)
             if 'ImageChatManger' not in globals():
                  # This might need adjustment based on how ImageChatManger is defined/used
                  pass

             chat_img = ImageChatManger(update.photo_caption, update.file_id)
             send_message(chat_id, "🖼️ Analyzing image...") # Indicate processing
             try:
                 response_text = chat_img.send_image()
                 send_message(chat_id, response_text, reply_to_message_id=update.message_id)

                 photo_url = chat_img.tel_photo_url()
                 imageID = update.file_id
                 log_text = f"[photo]({photo_url}), Caption:\n{update.photo_caption}\nReply:\n{response_text}"
                 # send_image_log("", imageID) # Maybe send log text with image?
                 send_log(log_text)

                 # Admin approval logic for photos
                 if ADMIN_ID and CHANNEL_ID:
                     message_id_img = update.message_id
                     pending_approvals[message_id_img] = {
                         "from_id": user_id,
                         "photo_caption": update.photo_caption,
                         "response_text": response_text,
                         "photo_url": photo_url,
                         "imageID": imageID
                     }
                     approval_request_text_img = (
                         f"📸 New photo from @{username} (id:`{user_id}`):\n\n"
                         f"**Caption:** {update.photo_caption}\n\n"
                         f"**Reply:**\n{response_text[:1000]}...\n\n"
                         f"Use `/approve {message_id_img}` or `/deny {message_id_img}`."
                     )
                     # Send photo preview to admin too if possible? /sendPhoto might work
                     try:
                         send_imageMessage(ADMIN_ID, approval_request_text_img, imageID)
                     except Exception:
                         send_message(ADMIN_ID, approval_request_text_img + f"\n(Could not send image preview)")
                     send_log(f"Sent photo {message_id_img} from @{username} for admin approval.")

             except Exception as e:
                  error_message = f"❌ An error occurred processing the image: {e}"
                  send_message(chat_id, error_message)
                  send_log(f"Error processing photo for @{username}: {e}\n{traceback.format_exc()}")

             return "ok", 200

        # --- Fallback for unknown message types ---
        else:
             send_log(f"Unhandled message type '{update.type}' from @{username} (id:`{user_id}`)")
             # Optionally send a message to the user
             # send_message(chat_id, "Sorry, I can only process text messages and photos right now.")
             return "ok", 200

    # --- General Error Catch ---
    except Exception as e:
        # Log the error details
        error_details = traceback.format_exc()
        send_log(f"🚨 Unhandled error in handle_message: {e}\n{error_details}")
        # Optionally notify admin or user (carefully, avoid loops)
        try:
             # Try to get chat_id if available in the raw data
             error_chat_id = update_data.get('message', {}).get('chat', {}).get('id') or \
                             update_data.get('callback_query', {}).get('message', {}).get('chat', {}).get('id')
             if error_chat_id:
                  send_message(error_chat_id, "Sorry, an internal error occurred. Please try again later.")
        except Exception as notify_err:
             send_log(f"🚨 Additionally, failed to notify user about the error: {notify_err}")

        return "error", 500 # Indicate internal server error

# --- Keep send_message_to_channel function ---
def send_message_to_channel(message, response):
    # This function is called AFTER admin approval
    try:
        # Format the message nicely for the channel
        channel_message = f"❓ **Question:**\n{message}\n\n💡 **Reply:**\n{response}"
        send_message(CHANNEL_ID, channel_message)
        print(f"Message successfully sent to the channel: {CHANNEL_ID}")
    except Exception as e:
        print(f"Error sending message to channel {CHANNEL_ID}: {e}")
        send_log(f"Error sending approved message to channel {CHANNEL_ID}: {e}")
