# api/command.py
from time import sleep
import time # Import time module for sleep
import google.generativeai as genai
import re # Import re for answer_exercise

from .auth import is_admin
from .config import ALLOWED_USERS,IS_DEBUG_MODE,GOOGLE_API_KEY
from .printLog import send_log
from .telegram import send_message
from .textbook_processor import get_textbook_content, search_concept_pages, get_text_from_pages
from .gemini import generate_content, generate_content_stream

admin_auch_info = "You are not the administrator or your administrator ID is set incorrectly!!!"
debug_mode_info = "Debug mode is not enabled!"
STREAMING_OUTPUT_SENT = "STREAMING_OUTPUT_SENT" # Marker for streaming functions

DEFAULT_TEXTBOOK_ID = "general" # Used when no textbook is specified

def help():
    help_text = "Welcome to Gemini 2.0 flash AI! Interact through text or images and experience insightful answers. Unlock the power of AI-driven communication – every message is a chance for a smarter exchange. Send text or image!\n Experience the power of AI-driven communication through insightful answers, text, or images. \n👾 Features \n Answer any question, even challenging or strange ones. \n ⏩ Generate creative text formats like poems, scripts, code, emails, and more. \n ⏩ Translate languages effortlessly. \n ⏩ Simplify complex concepts with clear explanations. \n ⏩  Perform math and calculations. \n ⏩ Assist with research and creative content generation. \n ⏩ Provide fun with word games, quizzes, and much more!\n ⏩ Send a text or image and unlock smarter exchanges. Don’t forget to join the channels below for more: And most importantly join the channels:  \n [Channel 1](https://t.me/+gOUK4JnBcCtkYWQ8) \n [Channel 2](https://t.me/telegemin). \n ወደ ጀሚኒ 1.5 ፕሮ አርቴፊሻል ኢንተለጀንስ እንኳን ደህና መጡ! ድንቅ 3 ከፍተኛ ተጠቃሚዎች ያሉት ጎግል AI ፣ እኔ እዚህ ስፍር ቁጥር በሌላቸው መንገዶች ልረዳችሁ የምችል የአርቴፊሻል ኢንተለጀንስ ቻት ቦት ነኝ። በአስተዋይ መልሶች、 በጽሑፍ ወይም በምስሎች የአርቴፊሻል ኢንተለጀንስ የተጎላበተ የግንኙነት ይለማመዱ። \n \n ⏩ ማንኛውንም ጥያቄ、 ፈታኝ ወይም እንግዳ የሆኑትንም እንኳ መልስ ያግኙ። \n ⏩ እንደ ግጥም、 ስክሪፕት、 ኮድ、 ኢሜይሎች እና ሌሎችም ያሉ የፈጠራ ጽሑፎችን ይፍጠሩ። \n ⏩ ቋንቋዎችን በቀላሉ መተርጎም። \n ⏩ ውስብስብ ጽንሰ-ሐሳቦችን በግልጽ ማብራራት። \n ⏩ የሂሳብ ስሌቶችን መስራት። \n ⏩ በምርምር እና በፈጠራ ይዘት ያላቸው ፅሁፎች። \n ⏩ በቃላት ጨዋታዎች、 ጥያቄዎች እና በብዙ ተጨማሪ ነገሮች ይዝናኑ!\n ⏩ ጽሑፍ ወይም ምስል ይላኩ እና መልስ ያግኙ። ለተጨማሪ መረጃ ከታች ባሉት ቻናሎች መቀላቀልዎን አይርሱ።"
    command_list = (
        "/new - Start new chat\n"
        "/explain [concept] [optional_textbook_id] - Explain a concept (e.g., /explain photosynthesis biology9 or /explain photosynthesis)\n"
        "/note [topic] [optional_textbook_id] - Prepare short note (e.g., /note world war 1 history9 or /note world war 1)\n"
        "/answer [exercise_query] [textbook_id] - Answer an exercise (textbook_id is required for this one, e.g. /answer Question 3.2 economics9)\n"
        "/create_questions [concept] [optional_textbook_id] - Generate review questions (e.g. /create_questions cells biology9 or /create_questions cells)"
    )
    result = f"{help_text}\n\n{command_list}"
    return result

def _parse_args_concept_topic_textbook(args_str: str, command_name: str, item_name: str = "concept/topic"):
    """Helper to parse arguments for commands like explain, note, create_questions."""
    if not args_str.strip():
        return None, None, ( # Return tuple: (item, textbook_id, error_message)
            f"I can help with that! Please provide the **{item_name}** you're interested in, "
            f"and optionally a **textbook ID** (e.g., `economics9`).\n\n"
            f"Example: `/{command_name} {item_name}_phrase [textbook_id]`\n"
            f"Or: `/{command_name} {item_name}_phrase` (for a general {item_name})"
        )

    args_parts = args_str.strip().split()
    item_phrase = ""
    textbook_id = DEFAULT_TEXTBOOK_ID

    if len(args_parts) == 1:
        item_phrase = args_parts[0]
    elif len(args_parts) > 1:
        # A simple heuristic: if the last part doesn't contain spaces and has a digit,
        # or is a common short ID, assume it's a textbook_id.
        # More robust would be a list of known textbook_ids or aliases.
        last_part = args_parts[-1]
        # Example check: isalnum and not purely numeric, or common short IDs
        if (last_part.isalnum() and any(c.isalpha() for c in last_part)) or \
           last_part.lower() in ["eco9", "hist9", "bio9", "chem9", "phy9"]: # Add more short aliases
            # Check if last_part is a known textbook ID prefix or full ID
            # For now, a simpler check:
            # A more robust check would involve looking up `last_part` in a predefined list of textbook IDs/aliases
            # if is_valid_textbook_id_format(last_part): # You'd need to define this
            textbook_id = last_part
            item_phrase = " ".join(args_parts[:-1])
            # else:
            # item_phrase = " ".join(args_parts) # Treat all as concept/topic
        else:
            item_phrase = " ".join(args_parts) # Treat all as concept/topic

    if not item_phrase: # Should be caught by the initial check, but as a safeguard
        return None, None, f"The {item_name} cannot be empty. Please try again."

    return item_phrase.strip(), textbook_id.lower(), None


def list_models():
    models_info = []
    if genai: # Check if genai object is available (initialized)
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    models_info.append(m.name)
        except Exception as e:
            send_log(f"Error listing models: {e}")
            return "Could not retrieve model list at this time."

    if models_info:
        send_log("Available Models:\n" + "\n".join(models_info))
    else:
        send_log("No models found with 'generateContent' method or Gemini not fully initialized.")
    return "" # No direct message to user, info sent to log

def get_allowed_users():
    send_log(f"ALLOWED_USERS:\n```json\n{ALLOWED_USERS}```")
    return ""


def get_API_key():
    send_log(f"GOOGLE_API_KEY (first key displayed):\n```\n{GOOGLE_API_KEY[0] if GOOGLE_API_KEY else 'Not Set'}```")
    return ""

def speed_test(chat_id): # Changed id to chat_id for clarity
    send_message(chat_id, "开始测速...")
    time.sleep(2)
    simulated_speed = int(time.time() * 1000) % 50000 + 10000 
    return f"测试完成，您的5G速度大约为：\n**{simulated_speed} B/s**"


def send_message_test(admin_chat_id, command_full_text):
    if not is_admin(admin_chat_id):
        return admin_auch_info
    
    parts = command_full_text.split(" ", 2) 
    if len(parts) < 3:
        return "Command format error. Use: /send_message <target_user_id> <message_text>"
    
    to_id_str = parts[1]
    text_to_send = parts[2]

    if not to_id_str.isdigit():
        return f"Invalid target user ID: '{to_id_str}'. ID must be a number."
        
    try:
        send_message(to_id_str, text_to_send)
        send_log(f"Admin {admin_chat_id} sent message to {to_id_str}: '{text_to_send}'")
        return f"Message sent to {to_id_str}." 
    except Exception as e:
        send_log(f"Error sending message from admin {admin_chat_id} to {to_id_str}: {e}")
        return f"Failed to send message to {to_id_str}. Error: {e}"


def explain_concept(from_id, concept, textbook_id):
    """Explains concept with streaming, using time-based chunk buffering and robust error handling."""
    context_text = ""
    page_refs_text = ""
    prompt = ""
    full_response_for_log = ""
    
    is_general_request = textbook_id.lower() == DEFAULT_TEXTBOOK_ID
    concept_pages = []
    if not is_general_request:
        concept_pages = search_concept_pages(textbook_id, concept)

    if concept_pages:
        context_text = get_text_from_pages(textbook_id, concept_pages)
        page_refs_text = f"(Explanation based on pages from '{textbook_id}': {', '.join(map(str, concept_pages))})"
        prompt = (
            f"You are a helpful AI Tutor for Grade 9 students. "
            f"Explain the concept of '{concept}' based on the following excerpt from pages {', '.join(map(str, concept_pages))} "
            f"of the textbook '{textbook_id}':\n\n---\n{context_text}\n---\n\n"
            f"Provide a detailed and comprehensive explanation suitable for a Grade 9 student. "
            f"Use simple language, analogies if helpful, and structure your explanation clearly, perhaps with bullet points for key aspects."
        )
    elif not is_general_request: # Textbook specified, but no pages found
        prompt = (
            f"You are a helpful AI Tutor for Grade 9 students. "
            f"Explain the concept of '{concept}' in detail and comprehensively, suitable for a Grade 9 student. "
            f"The textbook '{textbook_id}' was specified, but I couldn't find relevant content for '{concept}' in it. "
            f"Please provide a general explanation. Use simple language and clear structure."
        )
        page_refs_text = f"(Could not find specific pages for '{concept}' in textbook '{textbook_id}'. General explanation provided.)"
    else: # General request
        prompt = (
            f"You are a helpful AI Tutor for Grade 9 students. "
            f"Explain the concept of '{concept}' in detail and comprehensively, suitable for a Grade 9 student. "
            f"Use simple language, analogies if helpful, and structure your explanation clearly, perhaps with bullet points for key aspects."
        )
        page_refs_text = "(General explanation provided, no specific textbook context used.)"


    response_stream = generate_content_stream(prompt)
    buffered_message = ""
    last_chunk_time = time.time()

    try:
        for chunk_text in response_stream:
            if chunk_text:
                buffered_message += chunk_text
                full_response_for_log += chunk_text

            current_time = time.time()
            time_since_last_chunk = current_time - last_chunk_time

            if len(buffered_message) >= 3500 or (buffered_message.strip() and time_since_last_chunk >= 3): 
                if buffered_message.strip():
                    send_message(from_id, buffered_message)
                buffered_message = ""
                last_chunk_time = current_time
                time.sleep(0.2) 
    except Exception as e:
        error_message = f"Error during streaming explanation from Gemini: {e}"
        send_log(f"Streaming error for explain_concept ('{concept}', {textbook_id}): {e}")
        send_message(from_id, error_message)
        return STREAMING_OUTPUT_SENT # Indicate streaming happened even if error message was sent

    if buffered_message.strip():
        send_message(from_id, buffered_message)
    
    if page_refs_text: # Send page references as a final, separate message
         send_message(from_id, page_refs_text)
    
    send_log(f"Full explanation for '{concept}' ({textbook_id}) by user {from_id}:\n{full_response_for_log}\n{page_refs_text}")
    return STREAMING_OUTPUT_SENT


def create_questions(from_id, concept, textbook_id):
    """Generates questions based on a concept from a textbook, using streaming."""
    context_text = ""
    page_refs_text = ""
    prompt = ""
    full_response_for_log = ""

    is_general_request = textbook_id.lower() == DEFAULT_TEXTBOOK_ID
    concept_pages = []
    if not is_general_request:
        concept_pages = search_concept_pages(textbook_id, concept)

    if concept_pages:
        context_text = get_text_from_pages(textbook_id, concept_pages)
        page_refs_text = f"(Questions based on pages from '{textbook_id}': {', '.join(map(str, concept_pages))})"
        prompt = (
            f"You are an AI Quiz Generator for Grade 9 students. "
            f"Generate 10-15 review questions about the concept of '{concept}' based on the provided text from pages "
            f"{', '.join(map(str, concept_pages))} of the textbook '{textbook_id}':\n\n---\n{context_text}\n---\n\n"
            f"These questions should test understanding for Grade 9 level. Include a mix of types: "
            f"~5-7 multiple choice (with 4 distinct options A, B, C, D), "
            f"~3-4 true/false, and ~2-3 short answer. "
            f"Clearly label each question (e.g., Q1, Q2). Provide the correct answer immediately after each question, labeled (e.g., Answer: A)."
        )
    elif not is_general_request:
        prompt = (
            f"You are an AI Quiz Generator for Grade 9 students. "
            f"Generate 10-15 review questions about the concept of '{concept}'. "
            f"The textbook '{textbook_id}' was specified, but I couldn't find relevant content for '{concept}' in it. "
            f"Please generate general questions suitable for Grade 9 level. Include a mix of question types and provide answers."
        )
        page_refs_text = f"(Could not find specific pages for '{concept}' in textbook '{textbook_id}'. General questions provided.)"
    else:
        prompt = (
            f"You are an AI Quiz Generator for Grade 9 students. "
            f"Generate 10-15 review questions about the concept of '{concept}'. "
            f"These questions should be suitable for Grade 9 level and cover key aspects. "
            f"Include a mix of types: ~5-7 multiple choice (options A,B,C,D), ~3-4 true/false, ~2-3 short answer. Provide answers clearly."
        )
        page_refs_text = "(General questions provided, no specific textbook context used.)"

    response_stream = generate_content_stream(prompt) # Assuming this function exists and works
    buffered_message = ""
    last_chunk_time = time.time()

    try:
        for chunk_text in response_stream:
            if chunk_text:
                buffered_message += chunk_text
                full_response_for_log += chunk_text

            current_time = time.time()
            time_since_last_chunk = current_time - last_chunk_time

            if len(buffered_message) >= 3500 or (buffered_message.strip() and time_since_last_chunk >= 3):
                if buffered_message.strip():
                    send_message(from_id, buffered_message)
                buffered_message = ""
                last_chunk_time = current_time
                time.sleep(0.2)
    except Exception as e:
        error_message = f"Error during streaming question generation: {e}"
        send_log(f"Streaming error for create_questions ('{concept}', {textbook_id}): {e}")
        send_message(from_id, error_message)
        return STREAMING_OUTPUT_SENT

    if buffered_message.strip():
        send_message(from_id, buffered_message)
        
    if page_refs_text:
        send_message(from_id, page_refs_text)

    send_log(f"Full questions for '{concept}' ({textbook_id}) by user {from_id}:\n{full_response_for_log}\n{page_refs_text}")
    return STREAMING_OUTPUT_SENT


def prepare_short_note(from_id, topic, textbook_id):
    """Prepares a short note on a topic, using textbook context or general AI (non-streaming)."""
    context_text = ""
    page_refs_text = ""
    
    is_general_request = textbook_id.lower() == DEFAULT_TEXTBOOK_ID
    topic_pages = []
    if not is_general_request:
        topic_pages = search_concept_pages(textbook_id, topic)

    if topic_pages:
        context_text = get_text_from_pages(textbook_id, topic_pages)
        page_refs_text = f"(Note based on pages from '{textbook_id}': {', '.join(map(str, topic_pages))})"
        prompt = (
            f"You are an AI Study Assistant for Grade 9 students. "
            f"Prepare a concise but comprehensive study note on the topic of '{topic}', drawing from the provided text "
            f"from pages {', '.join(map(str, topic_pages))} of the textbook '{textbook_id}'. "
            f"Focus on 5-7 key points, definitions, and important concepts. Make it easy to understand. Use bullet points for clarity.\n\n"
            f"---\n{context_text}\n---"
        )
    elif not is_general_request:
        prompt = (
            f"You are an AI Study Assistant for Grade 9 students. "
            f"Prepare a concise study note on the topic of '{topic}'. "
            f"The textbook '{textbook_id}' was specified, but I couldn't find relevant content. "
            f"Please provide a general note focusing on 5-7 key points, suitable for Grade 9."
        )
        page_refs_text = f"(Could not find specific pages for '{topic}' in textbook '{textbook_id}'. General note provided.)"
    else:
        prompt = (
            f"You are an AI Study Assistant for Grade 9 students. "
            f"Prepare a concise study note on the topic of '{topic}'. "
            f"Focus on 5-7 key points, definitions, and important concepts. Make it easy to understand. Use bullet points."
        )
        page_refs_text = "(General note provided, no specific textbook context used.)"

    response = generate_content(prompt) 
    return f"{response}\n\n{page_refs_text}"


def answer_exercise(from_id, exercise_query, textbook_id):
    """Answers an exercise from a textbook. Textbook_id is required here."""
    if textbook_id.lower() == DEFAULT_TEXTBOOK_ID:
        return "To answer a specific exercise, please provide the textbook ID. Example: `/answer Exercise 1.1 economics9`"

    textbook_index_data = get_textbook_content(textbook_id)
    if not textbook_index_data or "chunks" not in textbook_index_data:
        return f"Textbook with ID '{textbook_id}' not found or is empty. Please ensure it has been preprocessed."

    full_textbook_content = "".join(chunk_data.get("text", "") + "\n\n" for chunk_data in textbook_index_data["chunks"])

    if not full_textbook_content.strip():
        return f"Textbook '{textbook_id}' appears to have no text content after loading."

    # Regex improved slightly for flexibility
    exercise_regex = re.compile(
        r"(Review Questions?|Exercises?|Problems?|Activities)?\s*"
        r"(Part\s*[IVXLCDM\d]+(?:[\s\-.:\w]+)?\s*[:;]?)?\s*" # Part I, Part 1, Part A, etc.
        r"(Question|Exercise|Problem|No\.?|Q\.?)\s*([\d.]+[a-zA-Z]?)", # Question 1, Ex 1.a, Prob. 2
        re.IGNORECASE
    )
    
    best_match_start, best_match_end, best_match_score = -1, -1, 0
    context_to_use = "Exercise not found in textbook content."

    query_parts_lower = exercise_query.lower().split()
    send_log(f"--- User {from_id} searching for exercise: '{exercise_query}' in '{textbook_id}' ---")
    
    for match in exercise_regex.finditer(full_textbook_content.lower()):
        match_text_group0 = match.group(0) 
        
        current_match_score = sum(1 for q_part in query_parts_lower if q_part in match_text_group0)
        
        if match.group(5): current_match_score += 2 # Group 5 is the exercise number ([\d.]+[a-zA-Z]?)
        if match.group(3): current_match_score += 1 # Group 3 is (Part ...)
        
        if current_match_score > best_match_score:
            best_match_score = current_match_score
            best_match_start = match.start()
            best_match_end = match.end()
    
    if best_match_start != -1 and best_match_score > 0:
        context_start_index = max(0, best_match_start - 700) 
        context_end_index = min(len(full_textbook_content), best_match_end + 1500)
        context_to_use = full_textbook_content[context_start_index:context_end_index]
        send_log(f"--- Best Regex Match Found for '{exercise_query}' (score: {best_match_score}). Context (first 200 chars): {context_to_use[:200].replace('`', '\\`')}... ---")
    else:
        send_log(f"--- No strong Regex Match for '{exercise_query}' in '{textbook_id}'. Trying broader search... ---")
        if len(exercise_query) > 4:
            try:
                # Simple substring search as a fallback
                # This is less precise but might catch cases the regex misses.
                query_start_idx = full_textbook_content.lower().find(exercise_query.lower())
                if query_start_idx != -1:
                    context_start_idx = max(0, query_start_idx - 700)
                    # Try to find end of question or a reasonable chunk
                    # Look for next question, or paragraph breaks, or fixed length
                    next_question_match = exercise_regex.search(full_textbook_content.lower(), query_start_idx + len(exercise_query))
                    context_end_idx = next_question_match.start() if next_question_match else query_start_idx + len(exercise_query) + 1500
                    context_end_idx = min(len(full_textbook_content), context_end_idx)
                    
                    context_to_use = full_textbook_content[context_start_idx:context_end_idx]
                    send_log(f"--- Fallback broad search found text similar to '{exercise_query}'. Context (first 200 chars): {context_to_use[:200].replace('`', '\\`')}... ---")
                else:
                    return f"Exercise '{exercise_query}' could not be clearly located in textbook '{textbook_id}'. Please try rephrasing, be more specific, or check the exercise wording/number."
            except Exception as e_broad:
                 send_log(f"Error during broad search for '{exercise_query}': {e_broad}")
                 return f"Exercise '{exercise_query}' not found in textbook '{textbook_id}'. Please try rephrasing."
        else:
            return f"Exercise query '{exercise_query}' is too short or could not be found in '{textbook_id}'. Please be more specific."

    prompt = (
        f"You are an expert AI Teaching Assistant for Grade 9. Based SOLELY on the following excerpt from the textbook '{textbook_id}', "
        f"provide a clear and accurate answer to the specific exercise/question: '{exercise_query}'.\n\n"
        f"Textbook Excerpt:\n---\n{context_to_use}\n---\n\n"
        f"Your Answer for '{exercise_query}':\n"
        f"(If it's a problem, show steps if appropriate. Ensure your answer is suitable for a Grade 9 student and directly addresses all parts of the query. "
        f"If the excerpt clearly does not contain enough information to answer, state that explicitly and explain what's missing if possible.)"
    )
    response = generate_content(prompt)
    return response


def excute_command(from_id, command_full_text): 
    command_parts = command_full_text.split(" ", 1)
    command_name = command_parts[0].lower() 
    args_str = command_parts[1] if len(command_parts) > 1 else ""

    if command_name == "start" or command_name == "help":
        return help()
    elif command_name == "get_my_info":
        return f"Your Telegram ID is: `{from_id}`"
    elif command_name == "5g_test":
        return speed_test(from_id)
    elif command_name == "send_message": 
        # This command needs the full text to parse to_id and message
        return send_message_test(from_id, command_full_text) 
    
    # Admin only commands
    elif command_name in ["get_allowed_users", "get_api_key", "list_models"]:
        if not is_admin(from_id):
            return admin_auch_info
        if IS_DEBUG_MODE == "0" and command_name != "list_models": # list_models might be ok for admin even if not debug
            return debug_mode_info
        
        if command_name == "get_allowed_users":
            return get_allowed_users() # Sends to log
        elif command_name == "get_api_key":
            return get_API_key() # Sends to log
        elif command_name == "list_models":
            return list_models() # Sends to log, no direct user reply needed

    # Student-focused commands
    elif command_name == "explain":
        concept, textbook_id, error_msg = _parse_args_concept_topic_textbook(args_str, command_name, "concept")
        if error_msg: return error_msg
        return explain_concept(from_id, concept, textbook_id)

    elif command_name == "note":
        topic, textbook_id, error_msg = _parse_args_concept_topic_textbook(args_str, command_name, "topic")
        if error_msg: return error_msg
        return prepare_short_note(from_id, topic, textbook_id)

    elif command_name == "create_questions":
        concept, textbook_id, error_msg = _parse_args_concept_topic_textbook(args_str, command_name, "concept for questions")
        if error_msg: return error_msg
        return create_questions(from_id, concept, textbook_id)

    elif command_name == "answer":
        if not args_str.strip():
            return (
                "I can try to answer an exercise for you!\n"
                "Please provide the **exercise query** (e.g., 'Question 1.2a' or 'Define inflation') "
                "AND the **textbook ID** (e.g., `economics9`). Textbook ID is required for this command.\n\n"
                "Example: `/answer Define inflation economics9`"
            )
        
        args_parts = args_str.strip().split()
        if len(args_parts) < 2: # Need at least query and textbook_id
            return "Usage: /answer [exercise query phrase] [textbook_id]\n(e.g., /answer Question 3.2 economics9)"
        
        textbook_id = args_parts[-1].lower()
        exercise_query = " ".join(args_parts[:-1]).strip()

        if not exercise_query:
            return "Exercise query cannot be empty. Usage: /answer [exercise query phrase] [textbook_id]"
        if textbook_id == DEFAULT_TEXTBOOK_ID : # Should have been caught by len < 2 but double check
             return "A specific textbook ID is required for the /answer command. Example: `/answer Question 3.2 economics9`"

        return answer_exercise(from_id, exercise_query, textbook_id)
        
    else:
        return "Invalid command. Use /help to see available commands."
