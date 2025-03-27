# api/command.py
from time import sleep
import time # Import time module for sleep
import google.generativeai as genai
import re # Import re for answer_exercise

from .auth import is_admin
from .config import ALLOWED_USERS,IS_DEBUG_MODE,GOOGLE_API_KEY
from .printLog import send_log
# Make sure to import send_message for potential streaming within functions
from .telegram import send_message
from .textbook_processor import get_textbook_content, search_concept_pages, get_text_from_pages
# Import generate_content_stream if you intend to use it directly here
# Or rely on handle.py to manage streaming based on function calls
from .gemini import generate_content, generate_content_stream

admin_auch_info = "You are not the administrator or your administrator ID is set incorrectly!!!"
debug_mode_info = "Debug mode is not enabled!"

# --- UPDATED HELP FUNCTION ---
def help():
    help_text = (
        "Welcome to Gemini 2.0 flash AI! Interact through text or images and experience insightful answers.\n\n"
        "**How to Use:**\n"
        "1.  Start a regular chat by sending any text or image.\n"
        "2.  Use `/study` to get help with specific textbooks.\n"
        "3.  Use `/new` to clear the chat history and start a fresh conversation.\n"
        "4.  Use `/get_my_info` to see your Telegram ID.\n\n"
        "**Textbook Helper (`/study`):**\n"
        "   - Start with `/study`.\n"
        "   - Choose your subject (e.g., Economics, History).\n"
        "   - Choose an action (Explain, Note, Questions).\n"
        "   - Enter the concept, topic, or question when prompted.\n\n"
        "**Admin Commands (if applicable):**\n"
        "   - `/get_allowed_users`, `/get_api_key`, `/list_models` (Requires admin rights & debug mode).\n\n"
        "*Join our channels for more updates:*\n"
        "[Channel 1](https://t.me/+gOUK4JnBcCtkYWQ8)\n"
        "[Channel 2](https://t.me/telegemin)"
    )
    # You can keep the Amharic text if desired
    amharic_help = (
        "\n\nወደ ጀሚኒ 1.5 ፕሮ አርቴፊሻል ኢንተለጀንስ እንኳን ደህና መጡ! ... (rest of your Amharic text) ..."
    )
    command_list = "\n\n**Available Commands:**\n/study - Get help with textbooks (step-by-step guide)\n/new - Start a new chat\n/help - Show this help message\n/get_my_info - Get your Telegram ID"

    # Combine parts
    result = f"{help_text}{command_list}"
    return result
# --- KEEP EXISTING FUNCTIONS (list_models, get_allowed_users, get_API_key, speed_test, send_message_test) ---
def list_models():
    # ... (existing code) ...
    models_info = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                models_info.append(f"- {m.name}")
        if not models_info:
             return "No generative models found."
        return "Available Generative Models:\n" + "\n".join(models_info)
    except Exception as e:
         send_log(f"Error listing models: {e}")
         return "Could not retrieve model list."


def get_allowed_users():
    # ... (existing code) ...
    # Ensure ALLOWED_USERS is treated as a list/set for proper formatting
    allowed_list = ", ".join(filter(None, ALLOWED_USERS)) # Filter out empty strings if split creates them
    return f"Allowed Users/IDs:\n```\n{allowed_list or 'None (Auth likely disabled)'}\n```"

def get_API_key():
    # ... (existing code) ...
    # Consider masking part of the key for security in logs
    masked_keys = [key[:4] + '...' + key[-4:] if key and len(key) > 8 else 'Invalid Key Format' for key in GOOGLE_API_KEY]
    return f"Configured Google API Keys (Masked):\n```\n{', '.join(masked_keys)}\n```"

def speed_test(id):
    # ... (existing code) ...
    send_message(id, "⏳ Starting speed test...")
    sleep(3) # Reduced sleep time
    return "✅ Speed test complete!\nYour network speed: **114514 B/s** (Simulated)"

def send_message_test(id, command_text):
    # ... (existing code, ensure proper parsing) ...
    if not is_admin(id):
        return admin_auch_info
    parts = command_text.split(" ", 2) # Split into 3 parts: /send_message, to_id, text
    if len(parts) != 3:
        return "Command format error. Use: /send_message <user_id> <message_text>"
    to_id_str = parts[1]
    text_to_send = parts[2]
    try:
        # Ensure to_id is a valid integer or chat_id format
        to_id = int(to_id_str)
        send_message(to_id, text_to_send)
        send_log(f"Admin message sent successfully to {to_id}.")
        return "Message sent." # Confirmation back to admin
    except ValueError:
        return f"Invalid user_id: {to_id_str}. Must be an integer."
    except Exception as e:
        send_log(f"Error in send_message_test to {to_id_str}: {e}")
        return f"Failed to send message: {e}"

# --- KEEP TEXTBOOK HELPER FUNCTIONS (explain_concept, prepare_short_note, create_questions) ---
# These functions already handle streaming internally by calling send_message repeatedly.

def explain_concept(from_id, concept, textbook_id):
    """Explains concept with streaming, using time-based chunk buffering and robust error handling."""
    send_message(from_id, f"⏳ Thinking about '{concept}' from {textbook_id}...") # Initial feedback
    concept_pages = search_concept_pages(textbook_id, concept)
    context_text = ""
    page_refs = ""
    prompt = ""
    full_response = ""

    if concept_pages:
        context_text = get_text_from_pages(textbook_id, concept_pages)
        page_refs = f"(Based on pages: {', '.join(map(str, concept_pages))})"
        prompt = f"Explain the concept of '{concept}' based on the following excerpt from pages {page_refs} of the Grade 9 textbook '{textbook_id}':\n\n---\n{context_text}\n---\n\nProvide a detailed and comprehensive explanation suitable for a Grade 9 student, using Markdown for formatting."
    else:
        prompt = f"Explain the concept of '{concept}' in detail and comprehensively, suitable for a Grade 9 student, using Markdown for formatting."
        page_refs = "(Textbook context not found)"

    response_stream = generate_content_stream(prompt)

    buffered_message = ""
    last_chunk_time = time.time()
    message_sent = False # Flag to check if any message was sent

    try:
        for chunk_text in response_stream:
            if chunk_text:
                buffered_message += chunk_text
                full_response += chunk_text

            current_time = time.time()
            time_since_last_chunk = current_time - last_chunk_time

            # Send buffered message if it's large enough or if time has passed
            # Use a reasonable buffer size for Telegram (max 4096 chars per message)
            if len(buffered_message) > 3500 or (buffered_message and time_since_last_chunk >= 3):
                send_message(from_id, buffered_message)
                buffered_message = ""
                last_chunk_time = current_time
                message_sent = True
                time.sleep(0.1) # Small delay to avoid hitting rate limits

    except Exception as e:
        error_message = f"⚠️ Error explaining '{concept}': {e}"
        send_message(from_id, error_message)
        return error_message # Return error to indicate failure

    # Send any remaining buffered text
    if buffered_message:
        send_message(from_id, buffered_message)
        message_sent = True

    # Send page reference only if some content was sent
    if message_sent:
         send_message(from_id, page_refs) # Send page refs as a separate message
         return "Explanation complete." # Signal completion (optional)
    elif not full_response: # Handle cases where Gemini returns empty response
         send_message(from_id, f"🤔 Could not generate an explanation for '{concept}'. {page_refs}")
         return "Could not generate explanation."
    else:
         # This case should ideally not happen if buffered_message was sent
         # but as a fallback, send the full response if it wasn't too long
         if len(full_response) <= 4096:
              send_message(from_id, full_response)
              send_message(from_id, page_refs)
              return "Explanation complete."
         else:
              # If somehow message_sent is False but full_response is long, log error
              send_log(f"Error: Long response for {concept} was not streamed correctly.")
              send_message(from_id, "An issue occurred while sending the explanation.")
              return "Streaming issue."


def prepare_short_note(from_id, topic, textbook_id):
    """Prepares a short note on a topic, using textbook context with page numbers if available, otherwise general AI."""
    send_message(from_id, f"📝 Preparing notes on '{topic}' from {textbook_id}...")
    topic_pages = search_concept_pages(textbook_id, topic)
    context_text = ""
    page_refs = ""

    if topic_pages:
        context_text = get_text_from_pages(textbook_id, topic_pages)
        page_refs = f"(Based on pages: {', '.join(map(str, topic_pages))})"
        prompt = f"Prepare a short, concise but comprehensive study note on the topic of '{topic}' based on the Grade 9 textbook '{textbook_id}', drawing from pages {page_refs}. Focus on 3-5 key bullet points and make it easy to understand for a Grade 9 student. Use Markdown for formatting (like bullet points)."
        if context_text: # Add context only if found
             prompt += f"\n\n---\n{context_text}\n---"
    else:
        prompt = f"Prepare a short, concise study note on the topic of '{topic}'. Focus on 3-5 key bullet points and make it easy to understand for a Grade 9 student. Use Markdown for formatting (like bullet points)."
        page_refs = "(Textbook context not found)"

    # This function doesn't stream in the original code, so call generate_content
    response = generate_content(prompt)
    if response and "Something went wrong" not in response:
         # Send the generated note and then the page reference
         send_message(from_id, response)
         send_message(from_id, page_refs)
         return "Notes prepared." # Signal completion
    else:
         # Send error message or a 'not found' message
         error_msg = response or f"Could not prepare notes for '{topic}'."
         send_message(from_id, f"⚠️ {error_msg} {page_refs}")
         return "Failed to prepare notes."


def create_questions(from_id, concept, textbook_id):
    """Generates questions based on a concept from a textbook, using streaming."""
    send_message(from_id, f"❓ Generating questions about '{concept}' from {textbook_id}...")
    concept_pages = search_concept_pages(textbook_id, concept)
    context_text = ""
    page_refs = ""
    prompt = ""
    full_response = ""

    if concept_pages:
        context_text = get_text_from_pages(textbook_id, concept_pages)
        page_refs = f"(Based on pages: {', '.join(map(str, concept_pages))})"
        prompt = (
            f"Generate 5-7 review questions about the concept of '{concept}' based on the Grade 9 textbook '{textbook_id}' {page_refs}. "
            "Include a mix of question types (e.g., multiple choice, true/false, short answer) suitable for Grade 9 students. "
            "Provide the answer immediately after each question. Use Markdown for formatting (like bolding questions, numbering, etc.)."
        )
        if context_text:
             prompt += f"\n\n---\n{context_text}\n---"
    else:
        prompt = (
            f"Generate 5-7 review questions about the concept of '{concept}'. "
            "Include a mix of question types (e.g., multiple choice, true/false, short answer) suitable for Grade 9 students. "
             "Provide the answer immediately after each question. Use Markdown for formatting."
        )
        page_refs = "(Textbook context not found)"

    response_stream = generate_content_stream(prompt)
    buffered_message = ""
    last_chunk_time = time.time()
    message_sent = False

    try:
        for chunk_text in response_stream:
            if chunk_text:
                buffered_message += chunk_text
                full_response += chunk_text

            current_time = time.time()
            time_since_last_chunk = current_time - last_chunk_time

            if len(buffered_message) > 3500 or (buffered_message and time_since_last_chunk >= 3):
                send_message(from_id, buffered_message)
                buffered_message = ""
                last_chunk_time = current_time
                message_sent = True
                time.sleep(0.1)

    except Exception as e:
        error_message = f"⚠️ Error generating questions for '{concept}': {e}"
        send_message(from_id, error_message)
        return error_message

    if buffered_message:
        send_message(from_id, buffered_message)
        message_sent = True

    if message_sent:
         send_message(from_id, page_refs)
         return "Questions generated."
    elif not full_response:
         send_message(from_id, f"🤔 Could not generate questions for '{concept}'. {page_refs}")
         return "Could not generate questions."
    else:
          # Fallback for non-streamed or short responses
          if len(full_response) <= 4096:
               send_message(from_id, full_response)
               send_message(from_id, page_refs)
               return "Questions generated."
          else:
               send_log(f"Error: Long response for {concept} questions was not streamed.")
               send_message(from_id, "An issue occurred while sending the questions.")
               return "Streaming issue."


# --- UPDATED EXECUTE COMMAND ---
def excute_command(from_id, command_text):
    # Command text now includes the leading '/'
    command_parts = command_text.split(" ", 1)
    command_name = command_parts[0].lower() # Get command name like /start, /help

    # --- Existing commands ---
    if command_name == "/start" or command_name == "/help":
        return help()

    elif command_name == "/get_my_info":
        return f"Your Telegram ID is: `{from_id}`"

    # '/new' is handled by ChatManager in handle.py, no need here unless specific logic needed

    # --- Admin commands ---
    elif command_name in ["/get_allowed_users", "/get_api_key", "/list_models"]:
        if not is_admin(from_id):
            return admin_auch_info
        # Debug mode check might not be needed for listing users/key? Decide based on security needs.
        # if IS_DEBUG_MODE == "0":
        #     return debug_mode_info

        if command_name == "/get_allowed_users":
            return get_allowed_users()
        elif command_name == "/get_api_key":
            return get_API_key()
        elif command_name == "/list_models":
            return list_models() # This already sends logs, maybe return text instead?

    elif command_name == "/send_message":
         # Ensure the full command text is passed
         return send_message_test(from_id, command_text)

    # --- Remove old textbook command parsing ---
    # The logic for /explain, /note, /create_questions is now initiated by /study
    # and handled via callbacks and context in handle.py.
    # Keep the functions themselves (explain_concept, etc.) as they are called by handle.py.

    # --- Deprecated/Fun commands ---
    elif command_name == "/5g_test": # Keep if desired
        return speed_test(from_id)

    # --- Fallback for unknown commands ---
    else:
        # Check if it starts with /approve or /deny (handled in handle.py)
        if command_name.startswith("/approve") or command_name.startswith("/deny"):
             # Let handle.py deal with these specifically
             return "" # Return empty or a specific signal if needed
        # Check if it starts with /study (handled in handle.py)
        elif command_name == "/study":
             return "" # Handled by handle.py

        # Otherwise, it's an invalid command
        return "🤔 Invalid command. Use /help to see available commands."
