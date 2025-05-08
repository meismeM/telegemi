# api/command.py
from time import sleep
import time 
import google.generativeai as genai # Keep for list_models, though actual generation is via gemini.py
import re # For answer_exercise regex

from .auth import is_admin
from .config import ALLOWED_USERS, IS_DEBUG_MODE, GOOGLE_API_KEY, AVAILABLE_TEXTBOOKS_FOR_KEYBOARD
from .printLog import send_log
from .telegram import send_message # For direct messaging from commands if needed (e.g., status updates)
from .textbook_processor import get_textbook_data, search_concept_pages, get_text_from_pages
from .gemini import generate_content, generate_content_stream

admin_auch_info = "⛔️ You are not authorized to use this command."
debug_mode_info = "ℹ️ This command is only available in debug mode."

# --- Helper for argument parsing ---
def _parse_args(args_str: str, num_expected_parts: int = 2) -> list[str] | None:
    """
    Parses arguments string. Expects last part to be textbook_id or similar single token.
    The rest is joined as the first argument (concept/topic/query).
    Returns a list of [multi_word_arg, last_arg] or None if parsing fails.
    """
    if not args_str:
        return None
    
    parts = args_str.strip().rsplit(" ", 1) # Split from right, once
    if len(parts) == num_expected_parts:
        # Ensure textbook_id is valid if it's one of the known ones
        # if num_expected_parts == 2 and parts[1] not in AVAILABLE_TEXTBOOKS_FOR_KEYBOARD:
            # This check might be too strict if we allow arbitrary textbook IDs not in the keyboard list
            # For now, we assume it's a valid ID passed by the keyboard flow or a knowledgeable user.
            # pass
        return parts
    elif num_expected_parts == 1 and len(parts) <= 1 : # For commands expecting only one (possibly multi-word) arg
        return [args_str.strip()]
    return None


# --- Command Functions ---
def help_command(from_id: int):
    help_text_main = (
        "Welcome to your AI Study Assistant! 🤖\n\n"
        "I can help you with your Grade 9 textbooks. You can interact with me by typing messages, "
        "sending photos, or using the interactive study tools.\n\n"
        "**Key Features:**\n"
        "💬 **General Chat:** Ask me anything! I'll try my best to answer.\n"
        "🖼️ **Image Understanding:** Send a photo, and I can describe it or answer questions about it.\n"
        "📚 **Interactive Study Tools:** Use the `/study` command for guided help with your textbooks."
    )
    
    commands_list = (
        "\n\n**Available Commands:**\n"
        "`/study` - Access interactive tools (explain, notes, questions).\n"
        "`/new` - Start a fresh chat conversation with me.\n"
        "`/help` - Show this help message.\n"
        "`/get_my_info` - Display your Telegram ID."
    )
    
    admin_commands_header = "\n\n**Admin Commands (requires authorization & debug mode):**"
    admin_commands_list = (
        "`/get_allowed_users` - List users authorized to use the bot.\n"
        "`/get_api_key` - Show partial Google API Key status.\n"
        "`/list_models` - List available AI models.\n"
        "`/send_message <user_id> <text>` - Send a message to a user."
    )

    full_help = help_text_main + commands_list
    if is_admin(from_id) and IS_DEBUG_MODE == '1':
        full_help += admin_commands_header + admin_commands_list
        
    # Adding Amharic text (ensure your terminal/editor supports UTF-8)
    amharic_intro = (
        "\n\n---\n"
        "ወደ ጀሚኒ 1.5 ፕሮ አርቴፊሻል ኢንተለጀንስ እንኳን ደህና መጡ! "
        "እኔ በተለያዩ መንገዶች ልረዳችሁ የምችል የአርቴፊሻል ኢንተለጀንስ ቻት ቦት ነኝ። "
        "በአስተዋይ መልሶች፣ በጽሑፍ ወይም በምስሎች የአርቴፊሻል ኢንተለጀንስ የተጎላበተ ግንኙነት ይለማመዱ።\n\n"
        "⏩ ማንኛውንም ጥያቄ ይመልሱ።\n"
        "⏩ የፈጠራ ጽሑፎችን ይፍጠሩ።\n"
        "⏩ ቋንቋዎችን በቀላሉ ይተርጉሙ።\n"
        "⏩ ውስብስብ ፅንሰ ሀሳቦችን ያብራሩ።"
    )
    # full_help += amharic_intro # Uncomment if Amharic text is desired

    # Channel links - ensure these are valid
    channel_links = (
        "\n\n**Join our channels for updates:**\n"
        "[Channel 1](https://t.me/+gOUK4JnBcCtkYWQ8)\n" # Example link
        "[Channel 2](https://t.me/telegemin)" # Example link
    )
    # full_help += channel_links # Uncomment if channel links are desired

    return full_help

def list_models_command():
    if not genai.api_key:
        return "Gemini API key not configured. Cannot list models."
    models_info = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                models_info.append(f"- `{m.name}`")
        if models_info:
            return "Available Gemini models (supporting `generateContent`):\n" + "\n".join(models_info)
        return "No Gemini models found with `generateContent` support."
    except Exception as e:
        return f"Error listing models: {e}"

def get_allowed_users_command():
    if ALLOWED_USERS:
        return f"Authorized users/IDs:\n`{', '.join(ALLOWED_USERS)}`"
    return "No specific users are whitelisted (AUCH_ENABLE might be '0')."

def get_api_key_command():
    if GOOGLE_API_KEY and GOOGLE_API_KEY[0]: # Check first key in the list
        key_preview = GOOGLE_API_KEY[0][:4] + "..." + GOOGLE_API_KEY[0][-4:]
        return f"Google API Key is set. Preview: `{key_preview}`"
    return "Google API Key is not set or is empty."

def speed_test_command(chat_id: int):
    send_message(chat_id, "⏱️ Starting speed test...")
    sleep(1.5) # Reduced sleep
    # This is a mock speed, not a real test
    return "✅ Speed test complete!\nYour simulated connection speed: **114514 B/s** (mock value)"

def send_message_admin_command(admin_id: int, args_str: str):
    parts = args_str.split(" ", 1)
    if len(parts) < 2:
        return "Usage: /send_message `<user_id>` `<text_to_send>`"
    
    try:
        target_user_id = int(parts[0])
    except ValueError:
        return "Invalid `user_id`. It must be a number."
    
    message_text_to_send = parts[1]
    
    try:
        send_message(target_user_id, f"ℹ️ Message from Administrator:\n\n{message_text_to_send}")
        send_log(f"Admin (ID:`{admin_id}`) sent message to User ID:`{target_user_id}`: '{message_text_to_send[:50]}...'")
        return f"Message sent to User ID:`{target_user_id}`."
    except Exception as e:
        send_log(f"Error sending admin message from ID:`{admin_id}` to User ID:`{target_user_id}`: {e}")
        return f"Failed to send message: {type(e).__name__}"


# --- Textbook Interaction Functions (called by interactive flow or direct commands) ---

def explain_concept_logic(user_id: int, concept: str, textbook_id: str):
    """Logic for explaining a concept. Sends messages directly for streaming."""
    send_message(user_id, f"⏳ Looking up '{concept}' in '{AVAILABLE_TEXTBOOKS_FOR_KEYBOARD.get(textbook_id, textbook_id)}'...")
    
    concept_pages = search_concept_pages(textbook_id, concept, max_pages=3) # Limit pages for context
    context_text = ""
    page_refs_str = f"(Textbook: {AVAILABLE_TEXTBOOKS_FOR_KEYBOARD.get(textbook_id, textbook_id)})" # Default page ref

    if concept_pages:
        context_text = get_text_from_pages(textbook_id, concept_pages)
        page_numbers_display = ", ".join(map(str, sorted(list(set(concept_pages)))))
        page_refs_str = f"(Source: {AVAILABLE_TEXTBOOKS_FOR_KEYBOARD.get(textbook_id, textbook_id)}, pages {page_numbers_display})"
        prompt = (f"Explain the concept of '{concept}' in a clear and detailed way suitable for a Grade 9 student. "
                  f"Base your explanation on the following excerpt from pages {page_numbers_display} of the textbook '{textbook_id}':\n\n"
                  f"---\n{context_text}\n---\n\n"
                  f"Explanation for '{concept}':")
    else:
        page_refs_str = f"(Concept '{concept}' not found in {AVAILABLE_TEXTBOOKS_FOR_KEYBOARD.get(textbook_id, textbook_id)}. General explanation provided.)"
        prompt = (f"Explain the concept of '{concept}' in a clear and detailed way suitable for a Grade 9 student. "
                  f"The concept was not found in the specified textbook, so provide a general explanation.")

    # Streaming response
    response_stream = generate_content_stream(prompt)
    buffered_message = ""
    last_chunk_time = time.time()
    full_response_for_log = ""

    try:
        for chunk_text in response_stream:
            if chunk_text:
                buffered_message += chunk_text
                full_response_for_log += chunk_text

            current_time = time.time()
            # Send if buffer is large or if some time passed with content in buffer
            if len(buffered_message) >= 3500 or \
               (buffered_message.strip() and (current_time - last_chunk_time >= 2.5)):
                if buffered_message.strip():
                    send_message(user_id, buffered_message)
                buffered_message = ""
                last_chunk_time = current_time
                time.sleep(0.05) # Small delay to allow messages to arrive in order

    except Exception as e:
        error_msg = f"⚠️ Error streaming explanation: {type(e).__name__}"
        send_message(user_id, error_msg)
        send_log(f"Streaming error for /explain '{concept}' ({textbook_id}): {e}\nPartial response: {full_response_for_log[:200]}")
        send_message(user_id, page_refs_str) # Send page refs even on error
        return # Function handles its own output

    if buffered_message.strip(): # Send any remaining text
        send_message(user_id, buffered_message)
    
    send_message(user_id, page_refs_str) # Send page references at the end
    send_log(f"Streamed /explain '{concept}' ({textbook_id}) to User ID:`{user_id}`. Response length: {len(full_response_for_log)}")
    # This function returns None as it handles its own output via send_message.


def prepare_short_note_logic(user_id: int, topic: str, textbook_id: str) -> Optional[str]:
    """Logic for preparing a short note. Returns the note as a string or None on error."""
    send_message(user_id, f"📝 Preparing a short note on '{topic}' from '{AVAILABLE_TEXTBOOKS_FOR_KEYBOARD.get(textbook_id, textbook_id)}'...")

    topic_pages = search_concept_pages(textbook_id, topic, max_pages=4)
    context_text = ""
    page_refs_str = f"(Textbook: {AVAILABLE_TEXTBOOKS_FOR_KEYBOARD.get(textbook_id, textbook_id)})"

    if topic_pages:
        context_text = get_text_from_pages(textbook_id, topic_pages)
        page_numbers_display = ", ".join(map(str, sorted(list(set(topic_pages)))))
        page_refs_str = f"(Source: {AVAILABLE_TEXTBOOKS_FOR_KEYBOARD.get(textbook_id, textbook_id)}, pages {page_numbers_display})"
        prompt = (f"Prepare a concise but comprehensive study note on the topic of '{topic}' for a Grade 9 student. "
                  f"Base this note on the following excerpt from pages {page_numbers_display} of the textbook '{textbook_id}'. "
                  f"Focus on 5-6 key bullet points or short paragraphs. Make it easy to understand and memorize.\n\n"
                  f"---\n{context_text}\n---\n\n"
                  f"Study note for '{topic}':")
    else:
        page_refs_str = f"(Topic '{topic}' not found in {AVAILABLE_TEXTBOOKS_FOR_KEYBOARD.get(textbook_id, textbook_id)}. General note provided.)"
        prompt = (f"Prepare a concise study note on the topic of '{topic}' for a Grade 9 student. "
                  f"Focus on 5-6 key bullet points or short paragraphs. Make it easy to understand and memorize. "
                  f"The topic was not found in the specified textbook, so provide a general note.")

    response = generate_content(prompt) # Non-streaming for notes
    if "Error:" in response or "Oops!" in response : # Check if Gemini returned an error
        final_response = f"⚠️ Could not generate note for '{topic}'. AI Error: {response}"
    else:
        final_response = f"**Study Note: {topic}**\n\n{response}\n\n{page_refs_str}"
    
    send_log(f"Generated note for /note '{topic}' ({textbook_id}) for User ID:`{user_id}`. Response length: {len(response)}")
    return final_response


def create_questions_logic(user_id: int, concept: str, textbook_id: str):
    """Logic for creating questions. Sends messages directly for streaming."""
    send_message(user_id, f"❓ Generating questions for '{concept}' from '{AVAILABLE_TEXTBOOKS_FOR_KEYBOARD.get(textbook_id, textbook_id)}'...")

    concept_pages = search_concept_pages(textbook_id, concept, max_pages=3)
    context_text = ""
    page_refs_str = f"(Textbook: {AVAILABLE_TEXTBOOKS_FOR_KEYBOARD.get(textbook_id, textbook_id)})"

    if concept_pages:
        context_text = get_text_from_pages(textbook_id, concept_pages)
        page_numbers_display = ", ".join(map(str, sorted(list(set(concept_pages)))))
        page_refs_str = f"(Questions based on {AVAILABLE_TEXTBOOKS_FOR_KEYBOARD.get(textbook_id, textbook_id)}, pages {page_numbers_display})"
        prompt = (f"Generate 10-15 review questions about the concept of '{concept}' for a Grade 9 student. "
                  f"Base these questions on the excerpt from pages {page_numbers_display} of the textbook '{textbook_id}'. "
                  f"Include a mix of question types (e.g., 5 multiple choice with A,B,C,D options, 5 true/false, 3 short answer). "
                  f"Provide the correct answer immediately after each question (e.g., 'Answer: B' or 'Answer: True' or 'Answer: [short answer]').\n\n"
                  f"---\n{context_text}\n---\n\n"
                  f"Review questions for '{concept}':")
    else:
        page_refs_str = (f"(Concept '{concept}' not found in {AVAILABLE_TEXTBOOKS_FOR_KEYBOARD.get(textbook_id, textbook_id)}. "
                         f"General questions provided.)")
        prompt = (f"Generate 10-15 review questions about the concept of '{concept}' for a Grade 9 student. "
                  f"Include a mix of question types (e.g., multiple choice, true/false, short answer). "
                  f"Provide the correct answer immediately after each question. "
                  f"The concept was not found in the specified textbook, so generate general questions.")

    # Streaming response
    response_stream = generate_content_stream(prompt)
    # (Similar streaming logic as explain_concept_logic)
    buffered_message = ""
    last_chunk_time = time.time()
    full_response_for_log = ""
    try:
        for chunk_text in response_stream:
            if chunk_text:
                buffered_message += chunk_text
                full_response_for_log += chunk_text
            current_time = time.time()
            if len(buffered_message) >= 3500 or \
               (buffered_message.strip() and (current_time - last_chunk_time >= 2.5)):
                if buffered_message.strip(): send_message(user_id, buffered_message)
                buffered_message = ""
                last_chunk_time = current_time
                time.sleep(0.05)
    except Exception as e:
        error_msg = f"⚠️ Error streaming questions: {type(e).__name__}"
        send_message(user_id, error_msg)
        send_log(f"Streaming error for /create_questions '{concept}' ({textbook_id}): {e}\nPartial: {full_response_for_log[:200]}")
        send_message(user_id, page_refs_str)
        return
    if buffered_message.strip(): send_message(user_id, buffered_message)
    send_message(user_id, page_refs_str)
    send_log(f"Streamed /create_questions '{concept}' ({textbook_id}) to User ID:`{user_id}`. Resp len: {len(full_response_for_log)}")
    # Returns None, handles own output


def answer_exercise_logic(user_id: int, exercise_query: str, textbook_id: str) -> Optional[str]:
    """Logic for answering an exercise. Returns the answer as a string or None on error."""
    send_message(user_id, f"🔍 Searching for exercise '{exercise_query}' in '{AVAILABLE_TEXTBOOKS_FOR_KEYBOARD.get(textbook_id, textbook_id)}'...")

    textbook_data = get_textbook_data(textbook_id)
    if not textbook_data or "chunks" not in textbook_data:
        return f"⚠️ Textbook '{textbook_id}' not found or has no content. Please ensure it's preprocessed."

    # Simple approach: combine all text for searching. Could be optimized.
    full_textbook_content = "\n\n".join([chunk.get("text", "") for chunk in textbook_data["chunks"]])
    if not full_textbook_content.strip():
        return f"⚠️ Textbook '{textbook_id}' seems to have empty content."

    # Regex to find exercise numbers/ids - this is highly dependent on PDF text quality
    # Example: "Question 1.2", "Exercise 3a", "Review Question 5"
    # This regex is a starting point and might need significant tuning.
    exercise_regex_str = rf"((?:Review\s+Questions?|Exercises?|Problems?|Tasks?)\s*(?:[:.]|\n))?\s*(?:Question|Exercise|Problem|Task|No\.|#)?\s*({re.escape(exercise_query)}[\w\.\-]*)(\s|\n|$)"
    # A simpler regex might be better if the query itself is fairly unique, e.g., "Question 3.1".
    # We are looking for the query string itself.
    
    context_text = ""
    match_found_flag = False
    
    # Try to find the exact query phrase first.
    query_lower = exercise_query.lower()
    query_start_index = full_textbook_content.lower().find(query_lower)

    if query_start_index != -1:
        match_found_flag = True
        # Extract a window around the found query
        context_start = max(0, query_start_index - 500) # Characters before
        context_end = min(len(full_textbook_content), query_start_index + len(exercise_query) + 1500) # Characters after
        context_text = full_textbook_content[context_start:context_end]
        send_log(f"Found direct mention of '{exercise_query}' in {textbook_id}. Using surrounding context.")
    else:
        # Fallback: If direct query not found, try a broader search or inform user.
        # For now, we'll say not found if the exact query isn't there as regex is too unreliable alone.
        send_log(f"Direct mention of '{exercise_query}' not found in {textbook_id}.")
        # We could try regex here as a fallback, but it's often noisy.
        # For now, let's proceed with empty context if direct search fails, Gemini might still answer generally.

    if not match_found_flag: # Or if context_text is still empty after fallback
         return (f"⚠️ Exercise query '{exercise_query}' was not clearly found in "
                 f"'{AVAILABLE_TEXTBOOKS_FOR_KEYBOARD.get(textbook_id, textbook_id)}'. "
                 f"Please try a more specific or different phrasing (e.g., 'Question 2.1b' or a unique phrase from the question).")

    prompt = (f"Based on the following excerpt from the textbook '{textbook_id}', "
              f"please provide a detailed answer to the exercise: '{exercise_query}'. "
              f"If it's a calculation, show steps. If it's a conceptual question, explain thoroughly.\n\n"
              f"---\nTEXTBOOK EXCERPT (may or may not contain the exact question, provide best effort based on this context):\n{context_text}\n---\n\n"
              f"Question to answer: '{exercise_query}'\n\nDetailed Answer:")
    
    response = generate_content(prompt)
    if "Error:" in response or "Oops!" in response:
        final_response = f"⚠️ Could not generate answer for '{exercise_query}'. AI Error: {response}"
    else:
        final_response = (f"**Answer for Exercise: {exercise_query}** "
                          f"_(from {AVAILABLE_TEXTBOOKS_FOR_KEYBOARD.get(textbook_id, textbook_id)})_\n\n{response}")

    send_log(f"Generated answer for /answer '{exercise_query}' ({textbook_id}) for User ID:`{user_id}`. Response length: {len(response)}")
    return final_response


# --- Main Command Executor (for direct text commands) ---
def excute_command(from_id: int, full_command_text: str) -> Optional[str]:
    """
    Executes direct text commands.
    Returns a string to be sent back to the user, or None if command handles its own output or is invalid.
    """
    parts = full_command_text.strip().split(" ", 1)
    command_name = parts[0].lower()
    args_str = parts[1] if len(parts) > 1 else ""

    if command_name == "help" or command_name == "start":
        return help_command(from_id)
    elif command_name == "get_my_info":
        return f"Your Telegram ID is: `{from_id}`"
    
    # --- Admin & Debug Commands ---
    if command_name == "list_models":
        if not is_admin(from_id): return admin_auch_info
        if IS_DEBUG_MODE != '1': return debug_mode_info
        return list_models_command()
    elif command_name == "get_allowed_users":
        if not is_admin(from_id): return admin_auch_info
        if IS_DEBUG_MODE != '1': return debug_mode_info
        return get_allowed_users_command()
    elif command_name == "get_api_key":
        if not is_admin(from_id): return admin_auch_info
        if IS_DEBUG_MODE != '1': return debug_mode_info
        return get_api_key_command()
    elif command_name == "send_message": # Admin sending message to a user
        if not is_admin(from_id): return admin_auch_info
        # if IS_DEBUG_MODE != '1': return debug_mode_info # Might allow admin to use this even if not debug
        return send_message_admin_command(from_id, args_str)

    # --- Deprecated or less used commands ---
    elif command_name == "5g_test": # Example of a simple command
        return speed_test_command(from_id) # Pass chat_id (which is from_id for direct commands)

    # --- Commands that are now primarily handled by interactive flow ---
    # These can still be invoked via text but might be less user-friendly.
    # The interactive flow in handle.py calls the `_logic` functions directly.
    
    # Example: /explain demand curve economics9
    parsed_args_explain = _parse_args(args_str, 2)
    if command_name == "explain" and parsed_args_explain:
        concept, textbook_id = parsed_args_explain
        explain_concept_logic(from_id, concept, textbook_id)
        return None # Output handled by the logic function
    elif command_name == "explain": # Incorrect usage
        return "Usage: `/explain <concept_phrase> <textbook_id>` (e.g., `/explain demand curve economics9`)"

    parsed_args_note = _parse_args(args_str, 2)
    if command_name == "note" and parsed_args_note:
        topic, textbook_id = parsed_args_note
        return prepare_short_note_logic(from_id, topic, textbook_id)
    elif command_name == "note":
        return "Usage: `/note <topic_phrase> <textbook_id>`"

    parsed_args_cq = _parse_args(args_str, 2)
    if command_name == "create_questions" and parsed_args_cq:
        concept, textbook_id = parsed_args_cq
        create_questions_logic(from_id, concept, textbook_id)
        return None # Output handled
    elif command_name == "create_questions":
        return "Usage: `/create_questions <concept_phrase> <textbook_id>`"

    parsed_args_ans = _parse_args(args_str, 2)
    if command_name == "answer" and parsed_args_ans:
        query, textbook_id = parsed_args_ans
        return answer_exercise_logic(from_id, query, textbook_id)
    elif command_name == "answer":
        return "Usage: `/answer <exercise_query> <textbook_id>`"

    # If command is not recognized by this point (and not /study or /new handled in handle.py)
    # It could be a general text message if it wasn't prefixed with /.
    # If it was prefixed with / and not caught, then it's an invalid command.
    # `handle.py` will make this distinction. For `excute_command`, if it's called,
    # it means it was a command.
    
    # Do not return "Invalid command" here, as /study and /new are handled in handle.py
    # This function is for commands *other* than those.
    # If a command reaches here and is not matched, it's effectively unhandled by this specific router.
    # `handle.py` should provide the "Invalid command" message if appropriate.
    return None # Signal that this command was not processed here