# api/command.py
from time import sleep
import time # Import time module for sleep
import google.generativeai as genai

from .auth import is_admin
from .config import ALLOWED_USERS,IS_DEBUG_MODE,GOOGLE_API_KEY
from .printLog import send_log
# Import send_message_with_inline_keyboard here, keep send_message for other uses
from .telegram import send_message, send_message_with_inline_keyboard
from .textbook_processor import get_textbook_content, search_concept_pages, get_text_from_pages
from .gemini import generate_content, generate_content_stream

admin_auch_info = "You are not the administrator or your administrator ID is set incorrectly!!!"
debug_mode_info = "Debug mode is not enabled!"
# Define available textbook IDs here or import from config if preferred
TEXTBOOK_IDS = ["economics9", "history9", "english9", "physics9", "biology9", "chemistry9", "citizenship9", "geography9"]

def help():
    help_text = "Welcome to Gemini 2.0 flash AI! Interact through text or images and experience insightful answers. Unlock the power of AI-driven communication – every message is a chance for a smarter exchange. Send text or image!\n Experience the power of AI-driven communication through insightful answers, text, or images. \n👾 Features \n Answer any question, even challenging or strange ones. \n ⏩ Generate creative text formats like poems, scripts, code, emails, and more. \n ⏩ Translate languages effortlessly. \n ⏩ Simplify complex concepts with clear explanations. \n ⏩  Perform math and calculations. \n ⏩ Assist with research and creative content generation. \n ⏩ Provide fun with word games, quizzes, and much more!\n ⏩ Send a text or image and unlock smarter exchanges. Don’t forget to join the channels below for more: And most importantly join the channels:  \n [Channel 1](https://t.me/+gOUK4JnBcCtkYWQ8) \n [Channel 2](https://t.me/telegemin). \n ወደ ጀሚኒ 1.5 ፕሮ አርቴፊሻል ኢንተለጀንስ እንኳን ደህና መጡ! ድንቅ 3 ከፍተኛ ተጠቃሚዎች ያሉት ጎግል AI ፣ እኔ እዚህ ስፍር ቁጥር በሌላቸው መንገዶች ልረዳችሁ የምችል የአርቴፊሻል ኢንተለጀንስ ቻት ቦት ነኝ። በአስተዋይ መልሶች፣ በጽሑፍ ወይም በምስሎች የአርቴፊሻል ኢንተለጀንስ የተጎላበተ የግንኙነት ይለማመዱ። \n \n ⏩ ማንኛውንም ጥያቄ፣ ፈታኝ ወይም እንግዳ የሆኑትንም እንኳ መልስ ያግኙ። \n ⏩ እንደ ግጥም፣ ስክሪፕት፣ ኮድ፣ ኢሜይሎች እና ሌሎችም ያሉ የፈጠራ ጽሑፎችን ይፍጠሩ። \n ⏩ ቋንቋዎችን በቀላሉ መተርጎም። \n ⏩ ውስብስብ ጽንሰ-ሐሳቦችን በግልጽ ማብራራት። \n ⏩ የሂሳብ ስሌቶችን መስራት። \n ⏩ በምርምር እና በፈጠራ ይዘት ያላቸው ፅሁፎች። \n ⏩ በቃላት ጨዋታዎች፣ ጥያቄዎች እና በብዙ ተጨማሪ ነገሮች ይዝናኑ!\n ⏩ ጽሑፍ ወይም ምስል ይላኩ እና መልስ ያግኙ። ለተጨማሪ መረጃ ከታች ባሉት ቻናሎች መቀላቀልዎን አይርሱ።"
    command_list = ("/new - Start new chat\n"
                    "/explain - Get explanation from textbook\n"
                    "/note - Prepare short note from textbook\n"
                    "/create_questions - Generate review questions from textbook\n"
                    # Keep answer command commented or refine its logic separately
                    # "/answer [exercise_query] [textbook_id] - Answer exercise (WIP)"
                   )
    result = f"{help_text}\n\n{command_list}"
    return result

# --- list_models, get_allowed_users, get_API_key, speed_test, send_message_test remain the same ---
def list_models():
    output = [] # Collect output instead of sending logs directly
    for m in genai.list_models():
        # send_log(str(m)) # Avoid sending logs directly from here
        if 'generateContent' in m.supported_generation_methods:
            output.append(m.name)
            # send_log(str(m.name))
    send_log("Available Models:\n" + "\n".join(output)) # Send collected list once
    return "Model list logged for admin." # Return confirmation to user

def get_allowed_users():
    send_log(f"```json\n{ALLOWED_USERS}```")
    return "Allowed users list logged for admin."

def get_API_key():
    send_log(f"```json\n{GOOGLE_API_KEY}```")
    return "API keys logged for admin."

def speed_test(id):
    # This is a placeholder/joke function, keep as is
    send_message(id, "开始测速")
    sleep(1) # Reduced sleep for faster testing
    return "测试完成，您的5G速度为：\n**114514B/s**"

def send_message_test(id, command):
    if not is_admin(id):
        return admin_auch_info
    parts = command.split(" ", 2) # Split into 3 parts: /send_message, to_id, text
    if len(parts) != 3:
        return "Command format error. Use: /send_message <user_id> <text>"
    to_id = parts[1]
    text = parts[2]
    try:
        # Consider adding validation if to_id is numeric
        send_message(to_id, text)
        send_log(f"Admin sent message to {to_id}") # Log success
        return "Message sent successfully." # Confirmation to admin
    except Exception as e:
        send_log(f"Error sending message from admin to {to_id}: {e}")
        return f"Failed to send message: {e}"
# --- Core Logic Functions (explain_concept, prepare_short_note, create_questions) ---
# These functions now handle their own response sending (including streaming)

def explain_concept(from_id, concept, textbook_id):
    """Explains concept with streaming, using time-based chunk buffering and robust error handling."""
    send_message(from_id, f"Explaining '{concept}' from {textbook_id}...") # Initial feedback
    concept_pages = search_concept_pages(textbook_id, concept)
    context_text = ""
    page_refs = ""
    prompt = ""
    full_response = "" # Initialize full_response

    if concept_pages:
        context_text = get_text_from_pages(textbook_id, concept_pages)
        # Limit context size sent to Gemini if needed (e.g., first/last X chars or pages)
        # context_text = context_text[:8000] # Example limit
        page_refs = f"(Based on Pages: {', '.join(map(str, concept_pages))})"
        prompt = f"Explain the concept of '{concept}' based on the following excerpt from the Grade 9 textbook '{textbook_id}':\n\n---\n{context_text}\n---\n\nProvide a detailed and comprehensive explanation suitable for a Grade 9 student. Use Markdown for formatting."
    else:
        prompt = f"Explain the concept of '{concept}' in detail and comprehensively, suitable for a Grade 9 student. Use Markdown for formatting."
        page_refs = "(Concept not found in specific pages of the textbook index)"

    response_stream = generate_content_stream(prompt)
    buffered_message = ""
    last_send_time = time.time()
    initial_chunk_sent = False

    try:
        for chunk_text in response_stream:
            if chunk_text:
                buffered_message += chunk_text
                full_response += chunk_text

            current_time = time.time()
            # Send if buffer is large OR enough time passed OR it's the very end potentially
            # Adjust buffer size and time interval as needed
            if len(buffered_message) > 1500 or (current_time - last_send_time >= 3 and buffered_message):
                 # Use try-except for send_message
                try:
                    send_message(from_id, buffered_message)
                    buffered_message = ""
                    last_send_time = current_time
                    initial_chunk_sent = True
                    sleep(0.1) # Small delay to avoid hitting rate limits
                except Exception as send_err:
                    print(f"Error sending chunk: {send_err}") # Log send error
                    # Decide whether to continue or stop streaming
                    # For now, we'll log and continue, the user might miss a chunk
        
        # Send any remaining buffered text after the loop
        if buffered_message:
             try:
                send_message(from_id, buffered_message)
                initial_chunk_sent = True
             except Exception as send_err:
                print(f"Error sending final buffer: {send_err}")


        # Send page refs only if some content was generated and sent
        if initial_chunk_sent:
            try:
                send_message(from_id, page_refs)
            except Exception as send_err:
                 print(f"Error sending page refs: {send_err}")

    except Exception as e:
        error_message = f"Sorry, an error occurred while generating the explanation for '{concept}': {e}"
        try:
            send_message(from_id, error_message)
        except Exception as send_err:
            print(f"Error sending error message: {send_err}")
        # Return the error message so handle_message knows something went wrong
        return error_message # Indicate error occurred

    # Return None or a success indicator if needed by handle_message
    return None # Indicates success/completion


def prepare_short_note(from_id, topic, textbook_id):
    """Prepares a short note, using textbook context. Sends result directly."""
    send_message(from_id, f"Preparing note for '{topic}' from {textbook_id}...") # Initial feedback
    topic_pages = search_concept_pages(textbook_id, topic)
    context_text = ""
    page_refs = ""
    prompt = ""

    if topic_pages:
        context_text = get_text_from_pages(textbook_id, topic_pages)
        # context_text = context_text[:8000] # Optional limit
        page_refs = f"(Based on Pages: {', '.join(map(str, topic_pages))})"
        prompt = f"Prepare a concise but comprehensive study note (using bullet points or numbered lists) on the topic of '{topic}' based on the Grade 9 textbook '{textbook_id}', drawing from the provided text. Focus on key points suitable for a Grade 9 student. Use Markdown.\n\n---\n{context_text}\n---"
    else:
        prompt = f"Prepare a concise but comprehensive study note (using bullet points or numbered lists) on the topic of '{topic}'. Focus on key points suitable for a Grade 9 student. Use Markdown."
        page_refs = "(Topic not found in specific pages of the textbook index)"

    try:
        # This command doesn't stream in the original code, so use generate_content
        response = generate_content(prompt)
        # Send the complete response
        send_message(from_id, f"{response}\n\n{page_refs}")
    except Exception as e:
        error_message = f"Sorry, an error occurred while generating the note for '{topic}': {e}"
        send_message(from_id, error_message)
        return error_message # Indicate error

    return None # Indicate success

def create_questions(from_id, concept, textbook_id):
    """Generates questions based on a concept from a textbook, using streaming."""
    send_message(from_id, f"Generating questions for '{concept}' from {textbook_id}...") # Initial feedback
    concept_pages = search_concept_pages(textbook_id, concept)
    context_text = ""
    page_refs = ""
    prompt = ""
    full_response = "" # Initialize full_response

    if concept_pages:
        context_text = get_text_from_pages(textbook_id, concept_pages)
        # context_text = context_text[:8000] # Optional limit
        page_refs = f"(Based on Pages: {', '.join(map(str, concept_pages))})"
        prompt = f"Generate 10-15 review questions (e.g., 5 multiple choice, 5 short answer, 3 true/false) about the concept of '{concept}' based on the provided excerpt from the Grade 9 textbook '{textbook_id}'. Include the correct answer immediately after each question. Format using Markdown.\n\n---\n{context_text}\n---"
    else:
        prompt = f"Generate 10-15 review questions (e.g., 5 multiple choice, 5 short answer, 3 true/false) about the concept of '{concept}'. These should be suitable for Grade 9 students. Include the correct answer immediately after each question. Format using Markdown."
        page_refs = "(Concept not found in specific pages of the textbook index)"

    response_stream = generate_content_stream(prompt)
    buffered_message = ""
    last_send_time = time.time()
    initial_chunk_sent = False

    try:
        for chunk_text in response_stream:
            if chunk_text:
                buffered_message += chunk_text
                full_response += chunk_text

            current_time = time.time()
            if len(buffered_message) > 1500 or (current_time - last_send_time >= 3 and buffered_message):
                try:
                    send_message(from_id, buffered_message)
                    buffered_message = ""
                    last_send_time = current_time
                    initial_chunk_sent = True
                    sleep(0.1)
                except Exception as send_err:
                    print(f"Error sending question chunk: {send_err}")


        if buffered_message:
            try:
                send_message(from_id, buffered_message)
                initial_chunk_sent = True
            except Exception as send_err:
                 print(f"Error sending final question buffer: {send_err}")


        if initial_chunk_sent:
             try:
                send_message(from_id, page_refs)
             except Exception as send_err:
                  print(f"Error sending question page refs: {send_err}")


    except Exception as e:
        error_message = f"Sorry, an error occurred while generating questions for '{concept}': {e}"
        try:
            send_message(from_id, error_message)
        except Exception as send_err:
             print(f"Error sending error message: {send_err}")
        return error_message # Indicate error

    return None # Indicate success

# --- answer_exercise remains complex, keep it commented or refine separately ---
# def answer_exercise(from_id, exercise_query, textbook_id): ...

# --- excute_command ---
def excute_command(from_id, command):
    command_name = command.split(" ", 1)[0] # Get the base command name

    if command_name == "start" or command_name == "help":
        return help() # Return the help text to be sent by handle_message

    elif command_name == "get_my_info":
        return f"your telegram id is: `{from_id}`" # Return info text

    elif command_name == "5g_test":
        # This function sends its own message, so return "" or None
        speed_test(from_id)
        return None # Indicate message already sent

    elif command_name == "send_message":
        # This function sends its own message or returns an error string
        response = send_message_test(from_id, command)
        if response == admin_auch_info: # Check for auth error specifically
             return response
        else:
             return None # Indicate message handled or error message returned


    # --- Admin Debug Commands ---
    elif command_name in ["get_allowed_users", "get_api_key", "list_models"]:
        if not is_admin(from_id):
            return admin_auch_info
        if IS_DEBUG_MODE != "1": # Check against '1' as it's a string from env
            return debug_mode_info

        if command_name == "get_allowed_users":
            return get_allowed_users() # Returns confirmation string
        elif command_name == "get_api_key":
            return get_API_key() # Returns confirmation string
        elif command_name == "list_models":
            return list_models() # Returns confirmation string

    # --- Inline Keyboard Commands ---
    elif command_name in ["explain", "note", "create_questions"]:
        command_type = command_name # e.g., "explain"
        keyboard = []
        row = []
        # Consider making TEXTBOOK_IDS dynamically fetched or configurable
        for textbook_id in TEXTBOOK_IDS:
            # Make button text more readable if needed
            button_text = textbook_id.replace("9", " Gr9").capitalize() # e.g., "Economics Gr9"
            callback_data = f"{command_type}_{textbook_id}" # e.g., "explain_economics9"
            row.append({"text": button_text, "callback_data": callback_data})
            if len(row) >= 2: # Max 2 buttons per row
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        text = f"Please choose a subject for the '{command_type.replace('_', ' ')}' command:"
        try:
            send_message_with_inline_keyboard(from_id, text, keyboard)
            return None # Indicate message sent
        except Exception as e:
            send_log(f"Error sending inline keyboard: {e}")
            return f"Error creating subject selection menu: {e}" # Return error to user

    # --- REMOVED BLOCKS for argument parsing like /explain concept textbook_id ---
    # elif command.startswith("explain"): ... (DELETED)
    # elif command.startswith("note"): ... (DELETED)
    # elif command.startswith("create_questions"): ... (DELETED)
    # elif command.startswith("answer"): ... (DELETED or keep refining)

    # --- Default ---
    else:
        # Only return invalid command if it wasn't handled above
        # Check if it's /new, which is handled by ChatManager
        if command_name != "new":
            return "Invalid command. Use /help to see available commands."
        else:
            # /new is handled implicitly by ChatManager.send_message, no response needed here
            return None
