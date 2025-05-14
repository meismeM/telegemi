# api/command.py
from time import sleep
import time # Import time module for sleep
import google.generativeai as genai
# import re # No longer needed as answer_exercise is removed

from .auth import is_admin
from .config import ALLOWED_USERS,IS_DEBUG_MODE,GOOGLE_API_KEY
from .printLog import send_log
from .telegram import send_message
from .textbook_processor import get_textbook_content, search_concept_pages, get_text_from_pages # Keep for other commands
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
        # "/answer [exercise_query] [textbook_id] - Answer an exercise (textbook_id is required for this one, e.g. /answer Question 3.2 economics9)\n" # REMOVED
        "/create_questions [concept] [optional_textbook_id] - Generate review questions (e.g. /create_questions cells biology9 or /create_questions cells)"
    )
    result = f"{help_text}\n\n{command_list}"
    return result

def _parse_args_concept_topic_textbook(args_str: str, command_name: str, item_name: str = "concept/topic"):
    """Helper to parse arguments for commands like explain, note, create_questions."""
    if not args_str.strip():
        return None, None, ( 
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
        last_part = args_parts[-1]
        if (last_part.isalnum() and any(c.isalpha() for c in last_part)) or \
           last_part.lower() in ["eco9", "hist9", "bio9", "chem9", "phy9", "economics9", "history9", "biology9", "physics9", "chemistry9", "general"]:
            textbook_id = last_part
            item_phrase = " ".join(args_parts[:-1])
        else:
            item_phrase = " ".join(args_parts) 

    if not item_phrase: 
        return None, None, f"The {item_name} cannot be empty. Please try again."

    return item_phrase.strip(), textbook_id.lower(), None


def list_models():
    models_info = []
    if genai: 
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    models_info.append(m.name)
        except Exception as e:
            send_log(f"Error listing models: {e}")
            # No direct user message, error logged
    
    if models_info:
        send_log("Available Models:\n" + "\n".join(models_info))
    else:
        send_log("No models found with 'generateContent' method or Gemini not fully initialized.")
    return "" 

def get_allowed_users():
    send_log(f"ALLOWED_USERS:\n```json\n{ALLOWED_USERS}```")
    return ""


def get_API_key():
    send_log(f"GOOGLE_API_KEY (first key displayed):\n```\n{GOOGLE_API_KEY[0] if GOOGLE_API_KEY else 'Not Set'}```")
    return ""

def speed_test(chat_id): 
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
    elif not is_general_request: 
        prompt = (
            f"You are a helpful AI Tutor for Grade 9 students. "
            f"Explain the concept of '{concept}' in detail and comprehensively, suitable for a Grade 9 student. "
            f"The textbook '{textbook_id}' was specified, but I couldn't find relevant content for '{concept}' in it. "
            f"Please provide a general explanation. Use simple language and clear structure."
        )
        page_refs_text = f"(Could not find specific pages for '{concept}' in textbook '{textbook_id}'. General explanation provided.)"
    else: 
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
        return STREAMING_OUTPUT_SENT 

    if buffered_message.strip():
        send_message(from_id, buffered_message)
    
    if page_refs_text: 
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


# def answer_exercise(...) has been REMOVED


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
        return send_message_test(from_id, command_full_text) 
    
    elif command_name in ["get_allowed_users", "get_api_key", "list_models"]:
        if not is_admin(from_id):
            return admin_auch_info
        if IS_DEBUG_MODE == "0" and command_name != "list_models": 
            return debug_mode_info
        
        if command_name == "get_allowed_users":
            return get_allowed_users() 
        elif command_name == "get_api_key":
            return get_API_key() 
        elif command_name == "list_models":
            return list_models() 

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

    # The /answer command logic has been REMOVED from here
        
    else:
        return "Invalid command. Use /help to see available commands."