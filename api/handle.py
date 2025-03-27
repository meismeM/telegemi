import time
from .auth import is_authorized, is_admin
# Import the specific execution functions needed
from .command import excute_command, explain_concept, prepare_short_note, create_questions
from .context import ChatManager, ImageChatManger
# Import send_message_with_inline_keyboard if needed elsewhere, though likely not
from .telegram import Update, send_message, forward_message, copy_message, send_imageMessage, send_message_with_inline_keyboard
from .printLog import send_log, send_image_log
from .config import CHANNEL_ID, ADMIN_ID
import requests

chat_manager = ChatManager()
pending_approvals = {}
# This dictionary stores the state: {user_id: {"command_type": "explain", "textbook_id": "econ9"}}
waiting_for_topic = {}


def handle_callback_query(update_data):
    """Handles Telegram callback queries (button clicks)."""
    send_log(f"--- handle_callback_query START ---") # Log entry
    update = Update(update_data)
    callback_data = update.callback_data
    from_id = update.callback_from_id
    callback_query_id = None # Initialize

    if "callback_query" in update_data:
        callback_query_id = update_data["callback_query"]["id"]
        send_log(f"Callback Query ID: {callback_query_id}") # Log ID
    else:
         send_log("WARNING: 'callback_query' not found in update_data for callback handler.")

    # Answer the callback query ASAP
    if callback_query_id:
        try:
            answer_payload = {"callback_query_id": callback_query_id}
            # Use the imported TELEGRAM_API
            r = requests.post(f"{TELEGRAM_API}/answerCallbackQuery", json=answer_payload)
            send_log(f"Answered callback query {callback_query_id}. Status: {r.status_code}")
            if r.status_code != 200:
                 send_log(f"Error answering callback query: {r.text}")
        except Exception as e:
            send_log(f"CRITICAL Error during answerCallbackQuery for {callback_query_id}: {e}")
            # Decide if you should proceed or return? For now, log and continue.

    if not from_id:
        send_log("ERROR: Callback query received without a valid 'from_id'. Aborting.")
        send_log(f"--- handle_callback_query END (Error: No from_id) ---")
        return

    send_log(f"Callback query details: from_id=`{from_id}`, data=`{callback_data}`")

    if callback_data:
        try:
            send_log("Splitting callback_data...") # Log before split
            command_type, textbook_id = callback_data.split("_", 1)
            send_log(f"Split OK: command_type='{command_type}', textbook_id='{textbook_id}'")

            # Basic validation
            if command_type not in ["explain", "note", "create_questions"]:
                 raise ValueError(f"Invalid command_type '{command_type}' received")
            # Add textbook_id validation if needed

            send_log(f"Updating waiting_for_topic for user {from_id}") # Log before state update
            waiting_for_topic[from_id] = {"command_type": command_type, "textbook_id": textbook_id}
            send_log(f"State updated: waiting_for_topic = {waiting_for_topic}") # Log after state update

            subject_name = textbook_id.replace("9", " Grade 9").capitalize()

            if command_type == "explain":
                prompt_message = f"OK. Please enter the *concept* you want explained from {subject_name}:"
            elif command_type == "note":
                 prompt_message = f"OK. Please enter the *topic* you want a note on from {subject_name}:"
            elif command_type == "create_questions":
                 prompt_message = f"OK. Please enter the *concept* you want review questions for from {subject_name}:"
            else: # Should not happen due to validation above, but fallback
                 prompt_message = f"Please enter the topic/concept for {subject_name}:"

            send_log(f"Sending prompt message to {from_id}: '{prompt_message}'") # Log before send
            send_message(from_id, prompt_message) # Send prompt to user
            send_log(f"Prompt message sent successfully to {from_id}.") # Log after send

        except ValueError as e:
            send_log(f"ERROR handling callback_data '{callback_data}': {e}")
            try: # Try sending error message to user
                send_message(from_id, "Sorry, there was an error processing your selection. Please try the command again.")
            except Exception as send_e:
                 send_log(f"Failed to send error message to user {from_id}: {send_e}")
            # Clean up potentially invalid state
            if from_id in waiting_for_topic:
                send_log(f"Cleaning up state for {from_id} due to error.")
                del waiting_for_topic[from_id]
        except Exception as e:
             send_log(f"UNEXPECTED error in handle_callback_query: {e}")
             try:
                send_message(from_id, "An unexpected error occurred. Please try again later.")
             except Exception as send_e:
                 send_log(f"Failed to send unexpected error message to user {from_id}: {send_e}")
             if from_id in waiting_for_topic:
                send_log(f"Cleaning up state for {from_id} due to unexpected error.")
                del waiting_for_topic[from_id]
    else:
        send_log(f"ERROR: Invalid or empty callback_data received from {from_id}.")
        try:
            send_message(from_id, "Invalid selection data received.") # Error message
        except Exception as send_e:
             send_log(f"Failed to send invalid callback data message to user {from_id}: {send_e}")

    send_log(f"--- handle_callback_query END ---") # Log exit
def handle_message(update_data):
    update = Update(update_data)
    authorized = is_authorized(update.from_id, update.user_name)

    # Basic check for message structure
    if not update.from_id or ("message" not in update.update and "channel_post" not in update.update) :
         send_log(f"Received update without message or from_id: {update_data}")
         return # Ignore malformed updates

    # Log the event
    log_text = update.text or update.photo_caption or "[No Text/Caption]"
    send_log(f"Event received from @{update.user_name} id:`{update.from_id}` Type: {update.type}\nContent: {log_text}\n```json\n{update_data}```")

    if not authorized:
        try:
            send_message(update.from_id, "Sorry, you are not authorized to use this bot.")
            log = f"Unauthorized access attempt by @{update.user_name} id:`{update.from_id}`. Content: {log_text}"
            send_log(log)
        except Exception as e:
             send_log(f"Error sending unauthorized message to {update.from_id}: {e}")
        return

    # --- STATE CHECK: Is the bot waiting for a topic from this user? ---
    if update.from_id in waiting_for_topic and update.type == "text" and not update.text.startswith('/'):
        state = waiting_for_topic[update.from_id]
        command_type = state["command_type"]
        textbook_id = state["textbook_id"]
        topic_or_concept = update.text # This message is the topic/concept

        send_log(f"Processing '{topic_or_concept}' for command '{command_type}' with textbook '{textbook_id}' from user {update.from_id}")

        # --- Remove state BEFORE processing to prevent race conditions/errors ---
        del waiting_for_topic[update.from_id]

        try:
            # Call the appropriate function from command.py
            # These functions now handle sending messages directly (including streaming)
            if command_type == "explain":
                explain_concept(update.from_id, topic_or_concept, textbook_id)
            elif command_type == "note":
                prepare_short_note(update.from_id, topic_or_concept, textbook_id)
            elif command_type == "create_questions":
                create_questions(update.from_id, topic_or_concept, textbook_id)
            # Add elif for other commands if needed

            # Since functions handle sending, no need to send response here
            send_log(f"Successfully processed topic '{topic_or_concept}' for user {update.from_id}")

        except Exception as e:
            error_msg = f"An error occurred while processing your request for '{topic_or_concept}': {e}"
            send_log(error_msg)
            send_message(update.from_id, error_msg)
            # State already removed, just notify user

        # --- IMPORTANT: Return after handling the topic ---
        return

    # --- If not waiting for a topic, proceed with normal message handling ---

    elif update.type == "command":
        # Admin approval/denial commands
        if update.text.startswith("approve ") and is_admin(update.from_id):
            try:
                message_id_str = update.text.split(" ", 1)[1]
                 # Check if message_id_str is numeric before converting
                if not message_id_str.isdigit():
                     send_message(update.from_id, "Invalid Message ID format. It should be a number.")
                     return
                message_id = int(message_id_str)

                if message_id not in pending_approvals:
                    send_message(update.from_id, f"Message ID {message_id} not found in pending approvals.")
                    return

                approved_message = pending_approvals.pop(message_id) # Remove from pending

                try:
                    send_message(update.from_id, f"Approving message {message_id}...") # Feedback to admin
                    if "imageID" in approved_message: # Check using a key more likely to exist for images
                        caption = approved_message.get("photo_caption", "")
                        # Send image first, then the AI response text
                        send_imageMessage(CHANNEL_ID, caption, approved_message["imageID"])
                        if approved_message.get("response_text"): # Send AI response if exists
                             send_message(CHANNEL_ID, f"AI Response:\n{approved_message['response_text']}")
                        send_message(approved_message["from_id"], "Your image and caption have been approved and posted!")
                        send_log(f"Admin approved and posted image message {message_id} to channel {CHANNEL_ID}")
                    else: # It's a text message
                         # Combine original message and response for the channel post
                        channel_post = f"**User Question:**\n{approved_message['text']}\n\n**AI Response:**\n{approved_message['response_text']}"
                        send_message(CHANNEL_ID, channel_post)
                        send_message(approved_message["from_id"], "Your message has been approved and posted!")
                        send_log(f"Admin approved and posted text message {message_id} to channel {CHANNEL_ID}")

                except Exception as e:
                    send_log(f"Error occurred during approval of {message_id}: {e}")
                    send_message(update.from_id, f"An error occurred while posting approved message {message_id}: {e}")
                     # Optionally put back in pending? Depends on desired retry logic.
                    # pending_approvals[message_id] = approved_message

            except IndexError:
                send_message(update.from_id, "Invalid command format. Use: /approve <message_id>")
            except ValueError: # Handles if split[1] is not convertible to int
                 send_message(update.from_id, "Invalid Message ID format. It should be a number.")
            except Exception as e: # Catch other unexpected errors during approval command processing
                 send_log(f"Unexpected error processing /approve command: {e}")
                 send_message(update.from_id, f"An unexpected error occurred: {e}")


        elif update.text.startswith("deny ") and is_admin(update.from_id):
            try:
                message_id_str = update.text.split(" ", 1)[1]
                if not message_id_str.isdigit():
                     send_message(update.from_id, "Invalid Message ID format. It should be a number.")
                     return
                message_id = int(message_id_str)

                if message_id not in pending_approvals:
                    send_message(update.from_id, f"Message ID {message_id} not found in pending approvals.")
                    return

                denied_message = pending_approvals.pop(message_id) # Remove from pending
                send_message(update.from_id, f"Denying message {message_id}...") # Feedback to admin
                send_message(denied_message["from_id"], "Sorry, your message was not approved for posting.")
                send_log(f"Admin denied message {message_id}.")

            except IndexError:
                send_message(update.from_id, "Invalid command format. Use: /deny <message_id>")
            except ValueError:
                 send_message(update.from_id, "Invalid Message ID format. It should be a number.")
            except Exception as e:
                 send_log(f"Unexpected error processing /deny command: {e}")
                 send_message(update.from_id, f"An unexpected error occurred: {e}")


        # Handle other commands (/new, /help, /get_my_info, admin debug cmds)
        else:
            # excute_command might return text to send, None if it sent messages itself, or an error string
            response_text = excute_command(update.from_id, update.text)
            if response_text: # Only send if there's text to send back
                send_message(update.from_id, response_text)
                log = f"Command: {update.text}\nReply: {response_text}"
                send_log(log)
            # else: response handled by excute_command itself (like keyboards or admin logs)


    elif update.type == "text": # General text message (NOT a topic response)
        chat = chat_manager.get_chat(update.from_id)
        # Use the streaming function from gemini directly if ChatManager doesn't support it
        # response_stream = chat.send_message(update.text) # Assumes ChatManager.send_message returns a stream
        # OR directly call gemini's streaming function if ChatManager doesn't handle it:
        response_stream = generate_content_stream(update.text) # Using gemini.py's streaming

        buffered_message = ""
        last_send_time = time.time()
        full_response = ""
        message_id = update.message_id # For admin approval context
        initial_chunk_sent_to_user = False

        try:
            for chunk_text in response_stream:
                if chunk_text:
                    buffered_message += chunk_text
                    full_response += chunk_text # Accumulate full response for logging/approval

                current_time = time.time()
                # Send based on buffer size or time elapsed
                if len(buffered_message) > 1500 or (current_time - last_send_time >= 4 and buffered_message):
                    try:
                        send_message(update.from_id, buffered_message)
                        initial_chunk_sent_to_user = True
                        buffered_message = "" # Clear buffer AFTER sending
                        last_send_time = current_time
                        sleep(0.1) # Throttle
                    except Exception as send_err:
                         print(f"Error sending chat chunk to user {update.from_id}: {send_err}")
                         # Decide if to break or continue

            # Send any remaining buffer
            if buffered_message:
                try:
                    send_message(update.from_id, buffered_message)
                    initial_chunk_sent_to_user = True
                except Exception as send_err:
                    print(f"Error sending final chat buffer to user {update.from_id}: {send_err}")


            # Add the '/new' suggestion if history is long and response was successful
            if initial_chunk_sent_to_user and chat.history_length > 10 : # Only if chat history applies and message was sent
                 try:
                    send_message(update.from_id, "\n\n_Type /new to start a fresh chat._")
                 except Exception as send_err:
                    print(f"Error sending '/new' suggestion to user {update.from_id}: {send_err}")

            # --- Admin Approval Logic for Text ---
            if full_response and message_id: # Only queue if a response was generated
                 pending_approvals[message_id] = {
                    "from_id": update.from_id,
                    "text": update.text, # Original user message
                    "response_text": full_response # Full AI response
                }
                 # Notify admin
                 admin_notify_text = (f"📝 New Text Message Pending Approval:\n\n"
                                     f"User: @{update.user_name} (`{update.from_id}`)\n"
                                     f"Message ID: `{message_id}`\n\n"
                                     f"**Question:**\n{update.text}\n\n"
                                     f"**AI Response:**\n{full_response[:1000]}...\n\n" # Truncate long responses for notification
                                     f"Reply with `/approve {message_id}` or `/deny {message_id}`")
                 try:
                    send_message(ADMIN_ID, admin_notify_text)
                 except Exception as admin_err:
                     send_log(f"CRITICAL Error sending text approval notification to ADMIN: {admin_err}")


        except Exception as e:
            error_message = f"Error during streaming chat response: {e}"
            send_log(error_message)
            try:
                 # Send error to user
                 send_message(update.from_id, f"Sorry, I encountered an error processing your message: {e}")
                 # Optionally notify admin about the error
                 send_message(ADMIN_ID, f"⚠️ Error processing message for user {update.from_id} (`@{update.user_name}`):\nMessage: {update.text}\nError: {e}")
            except Exception as report_err:
                 send_log(f"Error reporting chat stream error: {report_err}")
            return # Exit handler on error


    elif update.type == "photo":
        chat_img = ImageChatManger(update.photo_caption, update.file_id)
        message_id = update.message_id # For admin approval context

        try:
            # Generate response (non-streaming for images usually)
            response_text = chat_img.send_image()

            # Send response to user first
            send_message(update.from_id, response_text, reply_to_message_id=update.message_id)

            # Log with photo URL
            try:
                photo_url = chat_img.tel_photo_url()
                log_caption = f"Caption: {update.photo_caption}\nReply: {response_text}"
                # send_image_log(log_caption, update.file_id) # Send image+caption log
                # Send separate text log with URL for context
                send_log(f"📸 Photo received from @{update.user_name} id:`{update.from_id}`\n[Photo Link]({photo_url})\n{log_caption}")
            except Exception as log_err:
                send_log(f"Error generating photo URL or logging image: {log_err}")
                photo_url = "[Error getting URL]" # Placeholder

            # --- Admin Approval Logic for Photos ---
            if response_text and message_id: # Queue if response generated
                pending_approvals[message_id] = {
                    "from_id": update.from_id,
                    "photo_caption": update.photo_caption,
                    "response_text": response_text,
                    "imageID": update.file_id # Use file_id directly
                }
                # Notify admin
                admin_notify_text = (f"🖼️ New Image Message Pending Approval:\n\n"
                                     f"User: @{update.user_name} (`{update.from_id}`)\n"
                                     f"Message ID: `{message_id}`\n\n"
                                     f"**Caption:**\n{update.photo_caption}\n\n"
                                     f"**AI Response:**\n{response_text[:1000]}...\n\n"
                                     # Maybe add [Photo Link]({photo_url}) here if reliable
                                     f"Reply with `/approve {message_id}` or `/deny {message_id}`")
                try:
                     # Send notification text first
                    send_message(ADMIN_ID, admin_notify_text)
                     # Then attempt to send the image itself to admin for easier review
                    send_imageMessage(ADMIN_ID, f"Image for Approval (ID: {message_id})", update.file_id)
                except Exception as admin_err:
                    send_log(f"CRITICAL Error sending image approval notification to ADMIN: {admin_err}")


        except Exception as e:
            error_message = f"Error processing image: {e}"
            send_log(error_message)
            try:
                 # Send error to user
                 send_message(update.from_id, f"Sorry, I couldn't process the image: {e}", reply_to_message_id=update.message_id)
                 # Notify admin
                 send_message(ADMIN_ID, f"⚠️ Error processing image for user {update.from_id} (`@{update.user_name}`):\nCaption: {update.photo_caption}\nError: {e}")
            except Exception as report_err:
                 send_log(f"Error reporting image processing error: {report_err}")
            return

    # Ignore other types of updates for now
    # else:
    #     send_log(f"Ignoring update of unhandled type '{update.type}' from user {update.from_id}")

# --- send_message_to_channel (Minor change for clarity) ---
# This function seems unused now as approval logic handles posting directly
# def send_message_to_channel(message, response):
#     try:
#         # Consider a more structured format
#         channel_post = f"**User Question:**\n{message}\n\n**AI Response:**\n{response}"
#         send_message(CHANNEL_ID, channel_post)
#         print(f"Message successfully sent to channel {CHANNEL_ID}")
#         send_log(f"Posted to channel {CHANNEL_ID}:\n{channel_post}")
#     except Exception as e:
#         print(f"Error sending message to channel {CHANNEL_ID}: {e}")
#         send_log(f"ERROR sending to channel {CHANNEL_ID}: {e}")
