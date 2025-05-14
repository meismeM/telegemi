# api/command.py
from time import sleep
import time # Import time module for sleep
import google.generativeai as genai
import re # Import re for answer_exercise

# MAKE SURE THE LINE "from .command import excute_command, STREAMING_OUTPUT_SENT" IS NOT HERE

from .auth import is_admin
from .config import ALLOWED_USERS,IS_DEBUG_MODE,GOOGLE_API_KEY
from .printLog import send_log
from .telegram import send_message
from .textbook_processor import get_textbook_content, search_concept_pages, get_text_from_pages
from .gemini import generate_content, generate_content_stream

admin_auch_info = "You are not the administrator or your administrator ID is set incorrectly!!!"
debug_mode_info = "Debug mode is not enabled!"
STREAMING_OUTPUT_SENT = "STREAMING_OUTPUT_SENT" # Marker for streaming functions

def help():
    help_text = "Welcome to Gemini 2.0 flash AI! Interact through text or images and experience insightful answers. Unlock the power of AI-driven communication – every message is a chance for a smarter exchange. Send text or image!\n Experience the power of AI-driven communication through insightful answers, text, or images. \n👾 Features \n Answer any question, even challenging or strange ones. \n ⏩ Generate creative text formats like poems, scripts, code, emails, and more. \n ⏩ Translate languages effortlessly. \n ⏩ Simplify complex concepts with clear explanations. \n ⏩  Perform math and calculations. \n ⏩ Assist with research and creative content generation. \n ⏩ Provide fun with word games, quizzes, and much more!\n ⏩ Send a text or image and unlock smarter exchanges. Don’t forget to join the channels below for more: And most importantly join the channels:  \n [Channel 1](https://t.me/+gOUK4JnBcCtkYWQ8) \n [Channel 2](https://t.me/telegemin). \n ወደ ጀሚኒ 1.5 ፕሮ አርቴፊሻል ኢንተለጀንስ እንኳን ደህና መጡ! ድንቅ 3 ከፍተኛ ተጠቃሚዎች ያሉት ጎግል AI ፣ እኔ እዚህ ስፍር ቁጥር በሌላቸው መንገዶች ልረዳችሁ የምችል የአርቴፊሻል ኢንተለጀንስ ቻት ቦት ነኝ። በአስተዋይ መልሶች፣ በጽሑፍ ወይም በምስሎች የአርቴፊሻል ኢንተለጀንስ የተጎላበተ የግንኙነት ይለማመዱ። \n \n ⏩ ማንኛውንም ጥያቄ፣ ፈታኝ ወይም እንግዳ የሆኑትንም እንኳ መልስ ያግኙ። \n ⏩ እንደ ግጥም፣ ስክሪፕት፣ ኮድ፣ ኢሜይሎች እና ሌሎችም ያሉ የፈጠራ ጽሑፎችን ይፍጠሩ። \n ⏩ ቋንቋዎችን በቀላሉ መተርጎም። \n ⏩ ውስብስብ ጽንሰ-ሐሳቦችን በግልጽ ማብራራት። \n ⏩ የሂሳብ ስሌቶችን መስራት። \n ⏩ በምርምር እና በፈጠራ ይዘት ያላቸው ፅሁፎች። \n ⏩ በቃላት ጨዋታዎች、 ጥያቄዎች እና በብዙ ተጨማሪ ነገሮች ይዝናኑ!\n ⏩ ጽሑፍ ወይም ምስል ይላኩ እና መልስ ያግኙ። ለተጨማሪ መረጃ ከታች ባሉት ቻናሎች መቀላቀልዎን አይርሱ።"
    command_list = (
        "/new - Start new chat\n"
        "/explain [concept] [textbook_id] - Explain a concept from textbook\n"
        "/note [topic] [textbook_id] - Prepare short note on a topic\n"
        "/answer [exercise_query] [textbook_id] - Answer an exercise from a textbook\n"
        "/create_questions [concept] [textbook_id] - Generate review questions"
    )
    result = f"{help_text}\n\n{command_list}"
    return result

def list_models():
    models_info = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            models_info.append(m.name)
    if models_info:
        send_log("Available Models:\n" + "\n".join(models_info))
    else:
        send_log("No models found with 'generateContent' method.")
    return ""

def get_allowed_users():
    send_log(f"ALLOWED_USERS:\n```json\n{ALLOWED_USERS}```")
    return ""


def get_API_key():
    send_log(f"GOOGLE_API_KEY (first key displayed):\n```\n{GOOGLE_API_KEY[0] if GOOGLE_API_KEY else 'Not Set'}```")
    return ""

def speed_test(id):
    send_message(id, "开始测速...")
    # Simulate some work
    time.sleep(2)
    # Simulate varying speeds for fun
    simulated_speed = int(time.time() * 1000) % 50000 + 10000 # Random-ish speed
    return f"测试完成，您的5G速度大约为：\n**{simulated_speed} B/s**"


def send_message_test(id, command): # 'command' here is the full command string like "send_message <to_id> <text>"
    if not is_admin(id):
        return admin_auch_info

    parts = command.split(" ", 2) # split into "send_message", "to_id", "text"
    if len(parts) < 3:
        return "Command format error. Use: /send_message <target_user_id> <message_text>"

    to_id_str = parts[1]
    text_to_send = parts[2]

    if not to_id_str.isdigit():
        return f"Invalid target user ID: '{to_id_str}'. ID must be a number."

    try:
        send_message(to_id_str, text_to_send)
        send_log(f"Admin {id} sent message to {to_id_str}: '{text_to_send}'")
        return f"Message sent to {to_id_str}." # Confirmation to admin
    except Exception as e:
        send_log(f"Error sending message from admin {id} to {to_id_str}: {e}")
        return f"Failed to send message to {to_id_str}. Error: {e}"


def explain_concept(from_id, concept, textbook_id):
    """Explains concept with streaming, using time-based chunk buffering and robust error handling."""
    concept_pages = search_concept_pages(textbook_id, concept)
    context_text = ""
    page_refs_text = ""
    prompt = ""
    full_response_for_log = ""

    if concept_pages:
        context_text = get_text_from_pages(textbook_id, concept_pages)
        page_refs_text = f"(Relevant pages from '{textbook_id}': {', '.join(map(str, concept_pages))})"
        prompt = f"Explain the concept of '{concept}' based on the following excerpt from pages {', '.join(map(str, concept_pages))} of the Grade 9 textbook '{textbook_id}':\n\n---\n{context_text}\n---\n\nProvide a detailed and comprehensive explanation suitable for a Grade 9 student. Structure your explanation clearly, using bullet points or numbered lists for key aspects if appropriate."
    else:
        prompt = f"Explain the concept of '{concept}' in detail and comprehensively, suitable for a Grade 9 student. Structure your explanation clearly, using bullet points or numbered lists for key aspects if appropriate."
        page_refs_text = f"(Could not find specific pages for '{concept}' in textbook '{textbook_id}'. General explanation provided.)"

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
        return error_message

    if buffered_message.strip():
        send_message(from_id, buffered_message)
        # full_response_for_log already includes this due to += logic

    if page_refs_text:
         send_message(from_id, page_refs_text)

    send_log(f"Full explanation for '{concept}' ({textbook_id}):\n{full_response_for_log}\n{page_refs_text}")
    return STREAMING_OUTPUT_SENT

def create_questions(from_id, concept, textbook_id):
    """Generates questions based on a concept from a textbook, using streaming."""
    concept_pages = search_concept_pages(textbook_id, concept)
    context_text = ""
    page_refs_text = ""
    prompt = ""
    full_response_for_log = ""

    if concept_pages:
        context_text = get_text_from_pages(textbook_id, concept_pages)
        page_refs_text = f"(Questions based on pages from '{textbook_id}': {', '.join(map(str, concept_pages))})"
        prompt = f"Generate 15-20 review questions about the concept of '{concept}' based on the following excerpt from pages {', '.join(map(str, concept_pages))} of the Grade 9 textbook '{textbook_id}':\n\n---\n{context_text}\n---\n\nThese questions should be suitable for Grade 9 students to test their understanding. Include a variety of question types (e.g., 7-10 multiple choice with options A, B, C, D; 3-5 true/false; 3-5 short answer). Clearly label each question (e.g., Q1, Q2). Provide the correct answer immediately after each question, labeled (e.g., Answer: A, Answer: True, Answer: ...)."
    else:
        prompt = f"Generate 15-20 review questions about the concept of '{concept}'. These questions should be suitable for Grade 9 students and cover key aspects. Include a variety of question types (e.g., multiple choice, true/false, short answer). Clearly label each question and provide the correct answer immediately after each."
        page_refs_text = f"(Could not find specific pages for '{concept}' in textbook '{textbook_id}'. General questions provided.)"

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
        return error_message

    if buffered_message.strip():
        send_message(from_id, buffered_message)

    if page_refs_text:
        send_message(from_id, page_refs_text)

    send_log(f"Full questions for '{concept}' ({textbook_id}):\n{full_response_for_log}\n{page_refs_text}")
    return STREAMING_OUTPUT_SENT

def prepare_short_note(from_id, topic, textbook_id):
    """Prepares a short note on a topic, using textbook context with page numbers if available, otherwise general AI."""
    topic_pages = search_concept_pages(textbook_id, topic)
    context_text = ""
    page_refs_text = ""

    if topic_pages:
        context_text = get_text_from_pages(textbook_id, topic_pages)
        page_refs_text = f"(Note based on pages from '{textbook_id}': {', '.join(map(str, topic_pages))})"
        prompt = f"Prepare a concise but comprehensive study note on the topic of '{topic}', drawing from the provided text from pages {', '.join(map(str, topic_pages))} of the Grade 9 textbook '{textbook_id}'. Focus on 5-7 key points, definitions, and important concepts. Make it easy to understand for a Grade 9 student. Use bullet points for clarity.\n\n---\n{context_text}\n---"
    else:
        prompt = f"Prepare a concise but comprehensive study note on the topic of '{topic}'. Focus on 5-7 key points, definitions, and important concepts. Make it easy to understand for a Grade 9 student. Use bullet points for clarity."
        page_refs_text = f"(Could not find specific pages for '{topic}' in textbook '{textbook_id}'. General note provided.)"

    response = generate_content(prompt)
    return f"{response}\n\n{page_refs_text}"

def answer_exercise(from_id, exercise_query, textbook_id):
    """Answers an exercise from a textbook."""
    textbook_index_data = get_textbook_content(textbook_id)
    if not textbook_index_data or "chunks" not in textbook_index_data:
        return f"Textbook with ID '{textbook_id}' not found or is empty. Ensure it has been preprocessed."

    full_textbook_content = ""
    for chunk_data in textbook_index_data["chunks"]:
        full_textbook_content += chunk_data.get("text", "") + "\n\n" # Ensure 'text' key exists

    if not full_textbook_content.strip():
        return f"Textbook '{textbook_id}' appears to have no text content after loading."

    exercise_regex = re.compile(rf"(Review Questions?|Exercises?)?\s*(Part\s*[IVXLCDM]+(?:[\s\-.]\w+)?:?)?\s*(Question|Exercise|Problem)\s*([\d.]+[a-z]?)", re.IGNORECASE)

    best_match_start = -1
    best_match_end = -1
    best_match_score = 0
    context_to_use = "Exercise not found."

    query_parts = exercise_query.lower().split()
    send_log(f"--- Searching for exercise: '{exercise_query}' in '{textbook_id}' ---")

    # Debug: Log first 500 chars of textbook content being searched
    # send_log(f"Searching within content (first 500 chars): {full_textbook_content[:500]}...")

    for match in exercise_regex.finditer(full_textbook_content.lower()):
        match_text_group0 = match.group(0) # Full matched text e.g., "Question 1.1" or "Part I: Exercise 2a"

        current_match_score = 0
        # Score based on how many parts of the user's query are in the regex match
        for q_part in query_parts:
            if q_part in match_text_group0:
                current_match_score += 1

        # Prioritize more specific matches (e.g., "Question 1.1" vs just "Question")
        if match.group(4): # If a number (group 4) is part of the match
            current_match_score += 2 # Higher weight for numbered questions
        if match.group(2): # If a "Part" is specified
            current_match_score +=1

        if current_match_score > best_match_score:
            best_match_score = current_match_score
            best_match_start = match.start()
            best_match_end = match.end()

    if best_match_start != -1 and best_match_score > 0:
        context_start_index = max(0, best_match_start - 600) # Increase context before
        context_end_index = min(len(full_textbook_content), best_match_end + 1200) # Increase context after
        context_to_use = full_textbook_content[context_start_index:context_end_index]
        send_log(f"--- Best Match Found for '{exercise_query}' (score: {best_match_score}). Context (first 200 chars): {context_to_use[:200]}... ---")
    else:
        send_log(f"--- No Suitable Exercise Match Found for '{exercise_query}' in '{textbook_id}' using regex. Trying broad search... ---")
        # Fallback: if regex fails, try a simpler text search for the query itself if it's specific enough
        if len(exercise_query) > 5: # Avoid very short queries
            try:
                query_start_index = full_textbook_content.lower().find(exercise_query.lower())
                if query_start_index != -1:
                    context_start_index = max(0, query_start_index - 600)
                    context_end_index = min(len(full_textbook_content), query_start_index + len(exercise_query) + 1200)
                    context_to_use = full_textbook_content[context_start_index:context_end_index]
                    send_log(f"--- Fallback broad search found '{exercise_query}'. Context (first 200 chars): {context_to_use[:200]}... ---")
                else:
                     return f"Exercise '{exercise_query}' not found in textbook '{textbook_id}'. Please try rephrasing or check the exercise number/wording."
            except Exception: # Should not happen with string find
                 return f"Exercise '{exercise_query}' not found in textbook '{textbook_id}'. Please try rephrasing."
        else:
            return f"Exercise '{exercise_query}' not found in textbook '{textbook_id}'. Please be more specific or check the exercise number/wording."


    prompt = f"You are an expert teaching assistant for Grade 9 students. Based SOLELY on the following excerpt from the textbook '{textbook_id}', please answer the specific exercise or question: '{exercise_query}'.\n\nTextbook Excerpt:\n---\n{context_to_use}\n---\n\nYour Answer for '{exercise_query}':\n(Provide a clear, step-by-step answer if it's a problem, or a direct answer if it's a question. Ensure your answer is suitable for a Grade 9 student and directly addresses all parts of the specified exercise/question. If the excerpt does not contain the answer, state that explicitly.)"
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
        return send_message_test(from_id, command_full_text)

    elif command_name in ["get_allowed_users", "get_api_key", "list_models"]:
        if not is_admin(from_id):
            return admin_auch_info
        if IS_DEBUG_MODE == "0":
            return debug_mode_info

        if command_name == "get_allowed_users":
            return get_allowed_users()
        elif command_name == "get_api_key":
            return get_API_key()
        elif command_name == "list_models":
            return list_models()

    elif command_name == "explain":
        if not args_str:
            return "Usage: /explain [concept phrase] [textbook_id]"
        args_parts = args_str.strip().split()
        if len(args_parts) < 2:
            return "Usage: /explain [concept phrase] [textbook_id]\n(e.g., /explain supply and demand economics9)"
        textbook_id = args_parts[-1]
        concept = " ".join(args_parts[:-1])
        if not concept.strip():
             return "Concept cannot be empty. Usage: /explain [concept phrase] [textbook_id]"
        return explain_concept(from_id, concept, textbook_id)

    elif command_name == "note":
        if not args_str:
            return "Usage: /note [topic phrase] [textbook_id]"
        args_parts = args_str.strip().split()
        if len(args_parts) < 2:
            return "Usage: /note [topic phrase] [textbook_id]\n(e.g., /note causes of world war 1 history9)"
        textbook_id = args_parts[-1]
        topic = " ".join(args_parts[:-1])
        if not topic.strip():
            return "Topic cannot be empty. Usage: /note [topic phrase] [textbook_id]"
        return prepare_short_note(from_id, topic, textbook_id)

    elif command_name == "create_questions":
        if not args_str:
            return "Usage: /create_questions [concept phrase] [textbook_id]"
        args_parts = args_str.strip().split()
        if len(args_parts) < 2:
            return "Usage: /create_questions [concept phrase] [textbook_id]\n(e.g., /create_questions market equilibrium economics9)"
        textbook_id = args_parts[-1]
        concept = " ".join(args_parts[:-1])
        if not concept.strip():
            return "Concept cannot be empty. Usage: /create_questions [concept phrase] [textbook_id]"
        return create_questions(from_id, concept, textbook_id)

    elif command_name == "answer":
        if not args_str:
            return "Usage: /answer [exercise query phrase] [textbook_id]"
        args_parts = args_str.strip().split()
        if len(args_parts) < 2:
            return "Usage: /answer [exercise query phrase] [textbook_id]\n(e.g., /answer Question 3.2 economics9)"
        textbook_id = args_parts[-1]
        exercise_query = " ".join(args_parts[:-1])
        if not exercise_query.strip():
            return "Exercise query cannot be empty. Usage: /answer [exercise query phrase] [textbook_id]"
        return answer_exercise(from_id, exercise_query, textbook_id)

    else:
        return "Invalid command. Use /help to see available commands."
