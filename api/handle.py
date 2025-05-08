# api/handle.py
from .auth import is_authorized, is_admin
from .command import excute_command, help_command, \
                     explain_concept_logic, prepare_short_note_logic, \
                     create_questions_logic, answer_exercise_logic # Import specific logic functions
from .context import ChatManager, ImageChatManger
from .telegram import Update, send_message, send_imageMessage, \
                      send_message_with_inline_keyboard, answer_callback_query, edit_message_text
from .printLog import send_log # send_image_log can be used if needed
from .config import CHANNEL_ID, ADMIN_ID, AVAILABLE_TEXTBOOKS_FOR_KEYBOARD, IS_DEBUG_MODE
import time
from typing import Dict, Any

chat_manager = ChatManager() # Global instance for user chat histories
pending_approvals: Dict[int, Dict[str, Any]] = {} # message_id -> approval_data
user_interaction_state: Dict[int, Dict[str, Any]] = {} # chat_id -> {stage: str, action: str, data: {}, message_id: int}

# --- Keyboard Definitions ---
def get_main_actions_keyboard():
    keyboard = [
        [
            {"text": "📚 Explain Concept", "callback_data": "action_explain"},
            {"text": "📝 Prepare Note", "callback_data": "action_note"}
        ],
        [
            {"text": "❓ Create Questions", "callback_data": "action_create_q"}, # Shorter callback
            {"text": "💡 Answer Exercise", "callback_data": "action_answer_ex"}
        ],
        [{"text": "❌ Cancel", "callback_data": "action_cancel"}]
    ]
    return keyboard

def get_textbooks_keyboard(current_action: str):
    keyboard = []
    row = []
    if not AVAILABLE_TEXTBOOKS_FOR_KEYBOARD:
        # Fallback if no textbooks are configured
        keyboard.append([{"text": "⚠️ No textbooks configured.", "callback_data": "action_cancel"}])
    else:
        for tb_id, tb_name in AVAILABLE_TEXTBOOKS_FOR_KEYBOARD.items():
            row.append({"text": tb_name, "callback_data": f"tb_{current_action}_{tb_id}"}) # e.g., tb_explain_econ9
            if len(row) >= 2: # Max 2 textbook buttons per row (adjust as needed)
                keyboard.append(row)
                row = []
        if row: # Add any remaining buttons
            keyboard.append(row)
    
    keyboard.append([
        {"text": "⬅️ Back to Actions", "callback_data": "action_back"},
        {"text": "❌ Cancel", "callback_data": "action_cancel"}
    ])
    return keyboard

# --- Main Handler ---
def handle_message(raw_update_data: Dict):
    update = Update(raw_update_data) # Parse the incoming update

    # Centralized authorization check
    if not is_authorized(update.from_id, update.user_name):
        if update.type == "callback_query" and update.callback_query_id:
            answer_callback_query(update.callback_query_id, text="⛔️ You are not authorized.", show_alert=True)
        elif update.chat_id != 0: # Avoid sending if chat_id is 0 (should not happen for user messages)
             send_message(update.chat_id, "⛔️ You are not authorized to use this bot.")
        send_log(f"Unauthorized access: Type: {update.type}, User: @{update.user_name} (ID:`{update.from_id}`)")
        return

    # Log all authorized interactions
    log_detail = "Unknown interaction"
    if update.type in ["text", "command", "edited_text"]:
        log_detail = f"Text/Cmd: '{update.text}'"
    elif update.type == "photo":
        log_detail = f"Photo (caption: '{update.photo_caption or '[None]'}', ID: {update.file_id})"
    elif update.type == "callback_query":
        log_detail = f"Callback: '{update.callback_data}' on msg_id {update.message_id}"
    
    send_log(f"Event: Type: {update.type}, User: @{update.user_name} (ID:`{update.from_id}`), ChatID: {update.chat_id}, Detail: {log_detail}")


    # --- Callback Query Handling ---
    if update.type == "callback_query":
        handle_callback_query(update)
        return

    # --- Message Handling (Text, Command, Photo) ---
    current_chat_id = update.chat_id # This is the user's private chat with the bot

    # Check if user is in an interactive state (expecting text input for /study flow)
    if current_chat_id in user_interaction_state and \
       user_interaction_state[current_chat_id].get("stage") == "awaiting_input" and \
       update.type == "text":
        handle_interactive_text_input(update)
        return

    # --- Standard Command Handling ---
    if update.type == "command":
        command_name = update.command_name
        args_str = update.command_args_str

        if command_name == "study":
            # Clear any previous state for this user when they explicitly start /study
            if current_chat_id in user_interaction_state:
                try: # Attempt to edit the previous message if it exists to remove keyboard
                    prev_msg_id = user_interaction_state[current_chat_id].get("message_id")
                    if prev_msg_id: edit_message_text(current_chat_id, prev_msg_id, "Starting new study session...")
                except Exception: pass # Ignore if edit fails
                del user_interaction_state[current_chat_id]

            msg_sent = send_message_with_inline_keyboard(
                current_chat_id,
                "Hello! I'm your AI Study Assistant. How can I help you with your textbooks today?",
                get_main_actions_keyboard()
            )
            if msg_sent and msg_sent.get("ok") and msg_sent.get("result"):
                user_interaction_state[current_chat_id] = {
                    "stage": "action_selection", 
                    "message_id": msg_sent["result"]["message_id"]
                }
            else:
                send_message(current_chat_id, "⚠️ Oops! Couldn't display study options. Please try `/study` again.")
            return

        elif command_name == "new":
            chat = chat_manager.get_chat(update.from_id)
            chat.send_message("/new") # Resets history in ChatConversation
            send_message(current_chat_id, "🧹 Fresh chat started! Your previous conversation history with me has been cleared.")
            # Clear interactive state if user starts /new
            if current_chat_id in user_interaction_state:
                del user_interaction_state[current_chat_id]
            return
        
        elif command_name == "help" or command_name == "start": # Let excute_command handle help/start
            response_text = help_command(update.from_id) # Pass from_id for admin check in help
            if response_text: send_message(current_chat_id, response_text)
            return

        # Admin approval commands (kept simple for now)
        elif command_name in ["approve", "deny"] and is_admin(update.from_id):
            handle_admin_approval_command(update)
            return

        # For other commands, use excute_command (which calls specific _logic functions or returns text)
        # `update.text` contains the full command string like "/cmd args"
        response_text = excute_command(update.from_id, update.text)
        if response_text is not None: # excute_command might return None for handled streaming or invalid
            send_message(current_chat_id, response_text)
        # If response_text is None, it means the command handled its own output or was invalid by excute_command.
        # No further "invalid command" message needed here for that path.
        return

    # --- General Text Message (not a command, not part of /study flow) ---
    elif update.type == "text":
        chat = chat_manager.get_chat(update.from_id)
        # For general chat, use streaming
        response_stream = chat.send_message(update.text, stream=True) 

        buffered_message = ""  
        last_chunk_time = time.time() 
        full_response_from_ai = "" 
        message_id_for_approval = update.message_id # Original user message ID
    
        try:
            for chunk_text in response_stream:
                if chunk_text:
                    buffered_message += chunk_text
                    full_response_from_ai += chunk_text
    
                current_time = time.time()
                # Send if buffer is large or if some time passed with content in buffer
                if len(buffered_message) >= 3500 or \
                   (buffered_message.strip() and (current_time - last_chunk_time >= 2.5)):
                    if buffered_message.strip():
                        send_message(current_chat_id, buffered_message)
                    buffered_message = "" # Clear buffer
                    last_chunk_time = current_time
                    time.sleep(0.05) # Small delay for message ordering
            
            if buffered_message.strip(): # Send any remaining text in buffer
                send_message(current_chat_id, buffered_message)

        except Exception as e:
            error_message = f"⚠️ Oops! An error occurred while generating a response: {type(e).__name__}."
            send_message(current_chat_id, error_message)
            send_log(f"Streaming error for User ID:`{update.from_id}` on text '{update.text[:100]}...': {e}")
            return 
    
        # Admin approval for general text messages
        if full_response_from_ai.strip() and not ("Error:" in full_response_from_ai or "Oops!" in full_response_from_ai) :
            # Add context for channel message if approved
            extra_text_for_channel = "\n\nℹ️ _Type /new with the bot to start a fresh chat._" if chat.history_length > 8 else ""
            response_text_for_channel_approval = f"{full_response_from_ai}{extra_text_for_channel}"
            
            pending_approvals[message_id_for_approval] = {
                "type": "text",
                "from_id": update.from_id,
                "user_name": update.user_name,
                "original_text": update.text, 
                "ai_response_for_channel": response_text_for_channel_approval # Full response with extras for channel
            }
            
            admin_notification_text = (
                f"📝 **New Text for Approval** (Msg ID: `{message_id_for_approval}`)\n\n"
                f"**From:** @{update.user_name} (ID: `{update.from_id}`)\n"
                f"**Message:** {update.text[:1000]}\n" # Truncate long messages for admin
                f"**AI Reply (raw):** {full_response_from_ai[:1000]}\n\n" # Truncate long AI replies
                f"To approve: `/approve {message_id_for_approval}`\n"
                f"To deny: `/deny {message_id_for_approval}`"
            )
            if ADMIN_ID: send_message(int(ADMIN_ID), admin_notification_text)
            send_message(current_chat_id, "✅ Your message was processed. It's now pending review by an administrator before being published.")
        elif not full_response_from_ai.strip() and not ("Error:" in full_response_from_ai or "Oops!" in full_response_from_ai):
             send_message(current_chat_id, "I received your message, but I don't have a specific response for that right now.")
        # If AI returned an error, it was already sent to the user. No approval needed.
        return

    # --- Photo Message Handling ---
    elif update.type == "photo":
        img_manager = ImageChatManger(update.photo_caption, update.file_id)
        ai_response_for_photo = img_manager.send_image()
        
        # Send AI response directly to the user
        send_message(current_chat_id, ai_response_for_photo, reply_to_message_id=update.message_id)

        # Admin approval for photo messages
        if ai_response_for_photo and not ("Error:" in ai_response_for_photo or "Oops!" in ai_response_for_photo):
            message_id_for_approval = update.message_id
            pending_approvals[message_id_for_approval] = {
                "type": "photo",
                "from_id": update.from_id,
                "user_name": update.user_name,
                "photo_caption": update.photo_caption,
                "ai_response": ai_response_for_photo,
                "file_id": update.file_id # Telegram file_id of the photo
            }

            admin_notification_text = (
                f"🖼️ **New Photo for Approval** (Msg ID: `{message_id_for_approval}`)\n\n"
                f"**From:** @{update.user_name} (ID: `{update.from_id}`)\n"
                f"**Caption:** {update.photo_caption or '[No caption]'}\n"
                f"**AI Reply:** {ai_response_for_photo[:1000]}\n\n" # Truncate long AI replies
                f"To approve: `/approve {message_id_for_approval}`\n"
                f"To deny: `/deny {message_id_for_approval}`"
            )
            if ADMIN_ID:
                admin_id_int = int(ADMIN_ID)
                send_message(admin_id_int, admin_notification_text)
                # Optionally send the photo itself to admin for review
                send_imageMessage(admin_id_int, f"Photo for approval (Msg ID: {message_id_for_approval}). Details in text above/below.", update.file_id)
            send_message(current_chat_id, "✅ Your photo was processed. It's now pending review by an administrator before being published.")
        return
    
    # Fallback for unhandled message types or commands not caught earlier
    if update.type not in ["callback_query", "text", "photo"] and update.type != "command": # if it was a command, it should have been handled
        send_log(f"Unhandled update type: {update.type} from User ID:`{update.from_id}`. Raw: {raw_update_data}")
        # send_message(current_chat_id, "I'm not sure how to handle that type of message yet.")


def handle_callback_query(update: Update):
    """Handles all callback queries from inline keyboards."""
    chat_id = update.chat_id # chat_id from the message with the keyboard
    user_id = update.from_id # user_id of the person who clicked
    message_id = update.message_id # message_id of the message with the keyboard
    callback_data = update.callback_data
    callback_query_id = update.callback_query_id

    # Always answer callback query first to remove loading indicator on the button
    answer_callback_query(callback_query_id)

    state_data = user_interaction_state.get(chat_id, {})
    current_stage = state_data.get("stage")

    if callback_data == "action_cancel":
        edit_message_text(chat_id, message_id, "👍 Study session cancelled.")
        if chat_id in user_interaction_state:
            del user_interaction_state[chat_id]
        return

    if callback_data == "action_back": # Go back to main action selection
        new_text = "Alright, let's go back. What would you like to do?"
        edit_message_text(chat_id, message_id, new_text, keyboard=get_main_actions_keyboard())
        user_interaction_state[chat_id] = {"stage": "action_selection", "message_id": message_id}
        return

    # Stage 1: Action selection (e.g., "action_explain")
    if current_stage == "action_selection" and callback_data.startswith("action_"):
        selected_action = callback_data.split("_", 1)[1] # e.g., "explain", "note", "create_q"
        
        action_map = {
            "explain": "Explain Concept", "note": "Prepare Note",
            "create_q": "Create Questions", "answer_ex": "Answer Exercise"
        }
        action_display_name = action_map.get(selected_action, "Selected Action")

        if selected_action in ["explain", "note", "create_q", "answer_ex"]:
            user_interaction_state[chat_id] = {
                "stage": "textbook_selection",
                "action": selected_action, # Store short action code
                "message_id": message_id
            }
            new_text = f"Great choice: **{action_display_name}**!\nNow, please select a textbook from the list below:"
            edit_message_text(chat_id, message_id, new_text, keyboard=get_textbooks_keyboard(selected_action))
        else:
            edit_message_text(chat_id, message_id, "⚠️ Invalid action. Please try again or /study.")
            if chat_id in user_interaction_state: del user_interaction_state[chat_id]
        return

    # Stage 2: Textbook selection (e.g., "tb_explain_economics9")
    if current_stage == "textbook_selection" and callback_data.startswith("tb_"):
        parts = callback_data.split("_") # tb_ACTION_TEXTBOOKID
        if len(parts) == 3:
            action_from_cb = parts[1] # Action code from callback
            selected_textbook_id = parts[2]
            
            # Verify action in state matches action from callback for consistency
            if state_data.get("action") != action_from_cb:
                edit_message_text(chat_id, message_id, "⚠️ Action mismatch. Please restart with /study.")
                if chat_id in user_interaction_state: del user_interaction_state[chat_id]
                return

            user_interaction_state[chat_id]["stage"] = "awaiting_input"
            user_interaction_state[chat_id]["textbook_id"] = selected_textbook_id
            # message_id in state remains the one we are editing

            prompt_text_map = {
                "explain": "➡️ Please send the **concept or phrase** you want explained:",
                "note": "➡️ Please send the **topic** for which you need a study note:",
                "create_q": "➡️ Please send the **concept or topic** for question generation:",
                "answer_ex": "➡️ Please send the **exact exercise query or number** (e.g., 'Question 3.1a' or a unique phrase from it):"
            }
            prompt_text_display = prompt_text_map.get(action_from_cb, "➡️ Please send your input:")
            
            textbook_display_name = AVAILABLE_TEXTBOOKS_FOR_KEYBOARD.get(selected_textbook_id, selected_textbook_id)
            full_prompt_message = (f"**Textbook:** {textbook_display_name}\n"
                                   f"**Action:** {action_map.get(action_from_cb, action_from_cb.replace('_', ' ').title())}\n\n"
                                   f"{prompt_text_display}")
            edit_message_text(chat_id, message_id, full_prompt_message, keyboard=[[{"text":"❌ Cancel Input","callback_data":"action_cancel"}]]) # Remove textbook keyboard
        else:
            edit_message_text(chat_id, message_id, "⚠️ Invalid textbook selection. Please try again or /study.")
            if chat_id in user_interaction_state: del user_interaction_state[chat_id]
        return
    
    # If callback not handled by above stages, it might be an old one or an error
    send_log(f"Unhandled callback query data: '{callback_data}' for user {user_id} in stage '{current_stage}'")
    # Optionally edit message to indicate an issue or do nothing
    # edit_message_text(chat_id, message_id, "⚠️ An unexpected error occurred with that button. Please try /study again.")


def handle_interactive_text_input(update: Update):
    """Handles text input when the user is in an interactive (/study) state."""
    chat_id = update.chat_id
    user_input_text = update.text.strip()
    
    state = user_interaction_state.get(chat_id) # Should exist if this function is called

    if not state or state.get("stage") != "awaiting_input":
        send_message(chat_id, "⚠️ It seems I wasn't expecting that input. Please try starting over with /study.")
        if chat_id in user_interaction_state: del user_interaction_state[chat_id]
        return

    action_code = state.get("action") # e.g., "explain", "note"
    textbook_id = state.get("textbook_id")
    original_prompt_message_id = state.get("message_id") # The bot's message that prompted for input

    # Clear state immediately to prevent re-entry with same state if user sends multiple messages quickly
    if chat_id in user_interaction_state:
        del user_interaction_state[chat_id]

    # Update the bot's prompt message to "Processing..."
    action_display_map = {
        "explain": "explanation", "note": "note", "create_q": "questions", "answer_ex": "answer"
    }
    processing_action_display = action_display_map.get(action_code, "your request")

    if original_prompt_message_id:
        edit_message_text(chat_id, original_prompt_message_id, 
                          f"⏳ Processing your request for a {processing_action_display} on "
                          f"'{user_input_text[:50]}{'...' if len(user_input_text)>50 else ''}' "
                          f"from '{AVAILABLE_TEXTBOOKS_FOR_KEYBOARD.get(textbook_id, textbook_id)}'...")
    else: # Fallback if original message ID wasn't stored or editing failed
        send_message(chat_id, f"⏳ Processing your request for '{user_input_text[:30]}...'")

    # Call the appropriate logic function from command.py
    # These functions will send messages directly to the user (update.from_id, which is chat_id here)
    
    if action_code == "explain":
        explain_concept_logic(chat_id, user_input_text, textbook_id)
    elif action_code == "note":
        response = prepare_short_note_logic(chat_id, user_input_text, textbook_id)
        if response: send_message(chat_id, response) # Send the returned note
    elif action_code == "create_q":
        create_questions_logic(chat_id, user_input_text, textbook_id)
    elif action_code == "answer_ex":
        response = answer_exercise_logic(chat_id, user_input_text, textbook_id)
        if response: send_message(chat_id, response)
    else:
        send_message(chat_id, "⚠️ Unknown action in interactive flow. Please restart with /study.")
        send_log(f"Error: Unknown action_code '{action_code}' in handle_interactive_text_input for user {chat_id}")

    # Interactive commands currently do NOT go through the pending_approvals queue for channel posting.
    # This can be added if desired by capturing their full output.


def handle_admin_approval_command(update: Update):
    """Handles /approve and /deny commands from an admin."""
    admin_id = update.from_id
    command_name = update.command_name
    args_str = update.command_args_str

    if not args_str or not args_str.isdigit():
        send_message(admin_id, f"Usage: `/{command_name} <message_id>` (message_id must be a number).")
        return

    message_id_to_process = int(args_str)

    if message_id_to_process not in pending_approvals:
        send_message(admin_id, f"⚠️ Message ID `{message_id_to_process}` not found in pending approvals or already processed.")
        return

    item_to_process = pending_approvals.pop(message_id_to_process) # Remove from queue
    original_user_id = item_to_process["from_id"]
    original_user_name = item_to_process["user_name"]
    item_type = item_to_process["type"] # "text" or "photo"

    if command_name == "approve":
        if not CHANNEL_ID:
            send_message(admin_id, "⚠️ CHANNEL_ID is not configured. Cannot send approved message to channel.")
            # Optionally re-add to queue or just notify admin/user
            # pending_approvals[message_id_to_process] = item_to_process 
            return
        
        channel_id_int = int(CHANNEL_ID)
        success_on_channel = False

        try:
            if item_type == "text":
                original_text = item_to_process["original_text"]
                ai_response_for_channel = item_to_process["ai_response_for_channel"]
                channel_message = (f"👤 **User Query** (from @{original_user_name}):\n{original_text}\n\n"
                                   f"🤖 **AI Response:**\n{ai_response_for_channel}")
                send_message(channel_id_int, channel_message)
                success_on_channel = True
            elif item_type == "photo":
                photo_caption = item_to_process["photo_caption"]
                ai_response = item_to_process["ai_response"]
                file_id = item_to_process["file_id"]
                # Send photo with its original caption (if any) + user info
                channel_caption = f"🖼️ Photo from @{original_user_name}"
                if photo_caption: channel_caption += f": \"{photo_caption}\""
                send_imageMessage(channel_id_int, channel_caption, file_id)
                # Send AI's response as a separate message (or reply if API supports replying to media group easily)
                send_message(channel_id_int, f"🤖 **AI Analysis/Response to Photo:**\n{ai_response}")
                success_on_channel = True
            
            if success_on_channel:
                send_message(admin_id, f"✅ Approved and sent to channel: Item from @{original_user_name} (Original Msg ID: `{message_id_to_process}`).")
                send_message(original_user_id, f"🎉 Your {item_type} submission (regarding '{item_to_process.get('original_text', 'your photo')[:30]}...') has been approved and published!")
            else: # Should not happen if try block completes
                 send_message(admin_id, f"⚠️ Approval processed but failed to send to channel for unknown reason (item type: {item_type}).")


        except Exception as e:
            send_message(admin_id, f"🆘 Error sending approved item (Msg ID: `{message_id_to_process}`) to channel: {type(e).__name__} - {e}. Please check logs.")
            send_log(f"CRITICAL: Failed to send approved item {message_id_to_process} to channel {CHANNEL_ID}: {e}")
            # Consider re-adding to queue or other recovery:
            # pending_approvals[message_id_to_process] = item_to_process 
            send_message(original_user_id, f"⚠️ There was an issue publishing your approved {item_type}. Admin has been notified.")

    elif command_name == "deny":
        send_message(admin_id, f"🚫 Denied: Item from @{original_user_name} (Original Msg ID: `{message_id_to_process}`). User will be notified.")
        send_message(original_user_id, f"ℹ️ Your recent {item_type} submission (regarding '{item_to_process.get('original_text', 'your photo')[:30]}...') was not approved for publication at this time.")

    else: # Should not happen if command_name is validated before calling
        send_message(admin_id, f"⚠️ Unknown approval command: {command_name}")