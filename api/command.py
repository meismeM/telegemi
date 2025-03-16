"""from time import sleep

import google.generativeai as genai

from .auth import is_admin
from .config import ALLOWED_USERS,IS_DEBUG_MODE,GOOGLE_API_KEY
from .printLog import send_log
from .telegram import send_message

admin_auch_info = "You are not the administrator or your administrator ID is set incorrectly!!!"
debug_mode_info = "Debug mode is not enabled!"

def help():
    help_text = "Welcome to Gemini 2.0 flash AI! Interact through text or images and experience insightful answers. Unlock the power of AI-driven communication – every message is a chance for a smarter exchange. Send text or image!\n Experience the power of AI-driven communication through insightful answers, text, or images. \n👾 Features \n Answer any question, even challenging or strange ones. \n ⏩ Generate creative text formats like poems, scripts, code, emails, and more. \n ⏩ Translate languages effortlessly. \n ⏩ Simplify complex concepts with clear explanations. \n ⏩  Perform math and calculations. \n ⏩ Assist with research and creative content generation. \n ⏩ Provide fun with word games, quizzes, and much more!\n ⏩ Send a text or image and unlock smarter exchanges. Don’t forget to join the channels below for more: And most importantly join the channels:  \n [Channel 1](https://t.me/+gOUK4JnBcCtkYWQ8) \n [Channel 2](https://t.me/telegemin). \n ወደ ጀሚኒ 1.5 ፕሮ አርቴፊሻል ኢንተለጀንስ እንኳን ደህና መጡ! ድንቅ 3 ከፍተኛ ተጠቃሚዎች ያሉት ጎግል AI ፣ እኔ እዚህ ስፍር ቁጥር በሌላቸው መንገዶች ልረዳችሁ የምችል የአርቴፊሻል ኢንተለጀንስ ቻት ቦት ነኝ። በአስተዋይ መልሶች፣ በጽሑፍ ወይም በምስሎች የአርቴፊሻል ኢንተለጀንስ የተጎላበተ የግንኙነት ይለማመዱ። \n \n ⏩ ማንኛውንም ጥያቄ፣ ፈታኝ ወይም እንግዳ የሆኑትንም እንኳ መልስ ያግኙ። \n ⏩ እንደ ግጥም፣ ስክሪፕት፣ ኮድ፣ ኢሜይሎች እና ሌሎችም ያሉ የፈጠራ ጽሑፎችን ይፍጠሩ። \n ⏩ ቋንቋዎችን በቀላሉ መተርጎም። \n ⏩ ውስብስብ ጽንሰ-ሐሳቦችን በግልጽ ማብራራት። \n ⏩ የሂሳብ ስሌቶችን መስራት። \n ⏩ በምርምር እና በፈጠራ ይዘት ያላቸው ፅሁፎች። \n ⏩ በቃላት ጨዋታዎች፣ ጥያቄዎች እና በብዙ ተጨማሪ ነገሮች ይዝናኑ!\n ⏩ ጽሑፍ ወይም ምስል ይላኩ እና መልስ ያግኙ። ለተጨማሪ መረጃ ከታች ባሉት ቻናሎች መቀላቀልዎን አይርሱ።"
    command_list = "/new - Start a new chat" #\n/get_my_info - Get personal information\n/get_allowed_users - Get the list of users allowed to use robots (available only to admin)\n/list_models - List available models (available only to admin)\n/get_api_key - Get API key (available only to admin)"
    result = f"{help_text}\n\n{command_list}"
    return result

def list_models():
    for m in genai.list_models():
        send_log(str(m))
        if 'generateContent' in m.supported_generation_methods:
            send_log(str(m.name))
    return ""

def get_allowed_users():
    send_log(f"```json\n{ALLOWED_USERS}```")
    return ""


def get_API_key():
    send_log(f"```json\n{GOOGLE_API_KEY}```")
    return ""

def speed_test(id):
    send_message(id, "开始测速")
    sleep(5)
    return "测试完成，您的5G速度为：\n**114514B/s**"

def send_message_test(id, command):
    if not is_admin(id):
        return admin_auch_info
    a = command.find(" ")
    b = command.find(" ", a + 1)
    if a == -1 or b == -1:
        return "Command format error"
    to_id = command[a+1:b]
    text = command[b+1:]
    try:
        send_message(to_id, text)
    except Exception as e:
        send_log(f"err:\n{e}")
        return
    send_log("success")
    return ""

def excute_command(from_id, command):
    if command == "start" or command == "help":
        return help()

    elif command == "get_my_info":
        result = f"your telegram id is: `{from_id}`"
        return result

    elif command == "5g_test":
        return speed_test(from_id)

    elif command.startswith("send_message"):
        return send_message_test(from_id, command)

    elif command in ["get_allowed_users", "get_api_key", "list_models"]:
        if not is_admin(from_id):
            return admin_auch_info
        if IS_DEBUG_MODE == "0":
            return debug_mode_info

        if command == "get_allowed_users":
            return get_allowed_users()
        elif command == "get_api_key":
            return get_API_key()
        elif command == "list_models":
            return list_models()

    else:
        result = "Invalid command, use /help for help"
        return result """

from time import sleep

import google.generativeai as genai

from .auth import is_admin
from .config import ALLOWED_USERS,IS_DEBUG_MODE,GOOGLE_API_KEY
from .printLog import send_log
from .telegram import send_message
from .textbook_processor import get_textbook_content # Import textbook loader
from .gemini import generate_content # Ensure this is imported or defined

admin_auch_info = "You are not the administrator or your administrator ID is set incorrectly!!!"
debug_mode_info = "Debug mode is not enabled!"

def help():
    help_text = "Welcome to Gemini 2.0 flash AI! Interact through text or images and experience insightful answers. Unlock the power of AI-driven communication – every message is a chance for a smarter exchange. Send text or image!\n Experience the power of AI-driven communication through insightful answers, text, or images. \n👾 Features \n Answer any question, even challenging or strange ones. \n ⏩ Generate creative text formats like poems, scripts, code, emails, and more. \n ⏩ Translate languages effortlessly. \n ⏩ Simplify complex concepts with clear explanations. \n ⏩  Perform math and calculations. \n ⏩ Assist with research and creative content generation. \n ⏩ Provide fun with word games, quizzes, and much more!\n ⏩ Send a text or image and unlock smarter exchanges. Don’t forget to join the channels below for more: And most importantly join the channels:  \n [Channel 1](https://t.me/+gOUK4JnBcCtkYWQ8) \n [Channel 2](https://t.me/telegemin). \n ወደ ጀሚኒ 1.5 ፕሮ አርቴፊሻል ኢንተለጀንስ እንኳን ደህና መጡ! ድንቅ 3 ከፍተኛ ተጠቃሚዎች ያሉት ጎግል AI ፣ እኔ እዚህ ስፍር ቁጥር በሌላቸው መንገዶች ልረዳችሁ የምችል የአርቴፊሻል ኢንተለጀንስ ቻት ቦት ነኝ። በአስተዋይ መልሶች፣ በጽሑፍ ወይም በምስሎች የአርቴፊሻል ኢንተለጀንስ የተጎላበተ የግንኙነት ይለማመዱ። \n \n ⏩ ማንኛውንም ጥያቄ፣ ፈታኝ ወይም እንግዳ የሆኑትንም እንኳ መልስ ያግኙ። \n ⏩ እንደ ግጥም፣ ስክሪፕት፣ ኮድ፣ ኢሜይሎች እና ሌሎችም ያሉ የፈጠራ ጽሑፎችን ይፍጠሩ። \n ⏩ ቋንቋዎችን በቀላሉ መተርጎም። \n ⏩ ውስብስብ ጽንሰ-ሐሳቦችን በግልጽ ማብራራት። \n ⏩ የሂሳብ ስሌቶችን መስራት። \n ⏩ በምርምር እና በፈጠራ ይዘት ያላቸው ፅሁፎች። \n ⏩ በቃላት ጨዋታዎች፣ ጥያቄዎች እና በብዙ ተጨማሪ ነገሮች ይዝናኑ!\n ⏩ ጽሑፍ ወይም ምስል ይላኩ እና መልስ ያግኙ። ለተጨማሪ መረጃ ከታች ባሉት ቻናሎች መቀላቀልዎን አይርሱ።"
    command_list = "/new - Start a new chat" #\n/get_my_info - Get personal information\n/get_allowed_users - Get the list of users allowed to use robots (available only to admin)\n/list_models - List available models (available only to admin)\n/get_api_key - Get API key (available only to admin)"
    result = f"{help_text}\n\n{command_list}"
    return result

def list_models():
    for m in genai.list_models():
        send_log(str(m))
        if 'generateContent' in m.supported_generation_methods:
            send_log(str(m.name))
    return ""

def get_allowed_users():
    send_log(f"```json\n{ALLOWED_USERS}```")
    return ""


def get_API_key():
    send_log(f"```json\n{GOOGLE_API_KEY}```")
    return ""

def speed_test(id):
    send_message(id, "开始测速")
    sleep(5)
    return "测试完成，您的5G速度为：\n**114514B/s**"

def send_message_test(id, command):
    if not is_admin(id):
        return admin_auch_info
    a = command.find(" ")
    b = command.find(" ", a + 1)
    if a == -1 or b == -1:
        return "Command format error"
    to_id = command[a+1:b]
    text = command[b+1:]
    try:
        send_message(to_id, text)
    except Exception as e:
        send_log(f"err:\n{e}")
        return
    send_log("success")
    return ""

def explain_concept(from_id, concept, textbook_id):
    """Explains a concept from a textbook."""
    textbook_content = get_textbook_content(textbook_id)
    if not textbook_content:
        return f"Textbook with ID '{textbook_id}' not found or could not be loaded."

    # --- Simple approach: Search for concept in textbook (very basic) ---
    search_term = concept
    start_index = textbook_content.lower().find(search_term.lower())
    if start_index == -1:
        return f"Concept '{concept}' not found in textbook '{textbook_id}'."

    context_start = max(0, start_index - 500) # Get some context before and after
    context_end = min(len(textbook_content), start_index + 1000)
    context_text = textbook_content[context_start:context_end]

    prompt = f"Explain the concept of '{concept}' based on the following excerpt from the Grade 9 textbook '{textbook_id}':\n\n---\n{context_text}\n---\n\nProvide a clear and concise explanation suitable for a Grade 9 student."
    response = generate_content(prompt) # Use your existing Gemini function (ensure it's defined or imported)
    return response

def prepare_short_note(from_id, topic, textbook_id):
    """Prepares a short note on a topic from a textbook."""
    textbook_content = get_textbook_content(textbook_id)
    if not textbook_content:
        return f"Textbook with ID '{textbook_id}' not found."

    prompt = f"Prepare a short, concise study note on the topic of '{topic}' based on the Grade 9 textbook '{textbook_id}'. Focus on the key points and make it easy to understand for a Grade 9 student. Limit the note to around 3-4 key points."
    response = generate_content(prompt)
    return response

"""def answer_exercise(from_id, exercise_query, textbook_id): # Renamed exercise_number to exercise_query - more flexible
    #Answers an exercise from a textbook.
    textbook_content = get_textbook_content(textbook_id)
    if not textbook_content:
        return f"Textbook with ID '{textbook_id}' not found."

    # [!HIGHLIGHT!] More flexible exercise marker search using regex (basic)
    import re
    # Example query: "Part I Question 2", "Part II Question 4", "Review Questions Part I 5", etc.
    exercise_regex = re.compile(rf"(Review Questions)?\s*(Part [IVX]+:)?\s*(Question|exercise)\s*([\d.]+)", re.IGNORECASE)

    best_match_start = -1
    best_match_end = -1
    context_text = "Exercise not found." # Default message

    for match in exercise_regex.finditer(textbook_content):
        full_match = match.group(0) # Full matched string (e.g., "Review Questions Part I: 1")
        part = match.group(2) # "Part I:", "Part II:", etc. or None
        question_type = match.group(3) # "Question" or "exercise"
        question_number = match.group(4) # "1", "2", "3", etc.

        # [!HIGHLIGHT!]  Simple query matching - improve this for better matching if needed
        query_lower = exercise_query.lower()
        match_text_lower = full_match.lower()

        if query_lower in match_text_lower: # Basic substring match - could be improved
            best_match_start = match.start()
            best_match_end = match.end()
            break # For now, take the first match.  Could refine to find "best" match later

    if best_match_start != -1:
        context_start = max(0, best_match_start - 500) # Context before and after
        context_end = min(len(textbook_content), best_match_end + 1000)
        context_text = textbook_content[context_start:context_end]
    else:
        return f"Exercise '{exercise_query}' not found in textbook '{textbook_id}'."


    prompt = f"Based on the following excerpt from a Grade 9 economics textbook, answer the review question:\n\n---\n{context_text}\n---\n\nSpecifically, answer exercise/question: '{exercise_query}'. Provide a detailed answer suitable for a Grade 9 student. If it's a True/False question, state True or False and briefly explain why. If it's multiple choice, indicate the correct option (A, B, C, or D) and explain your reasoning."
    response = generate_content(prompt)
    return response"""


def excute_command(from_id, command):
    if command == "start" or command == "help":
        return help()
    elif command == "get_my_info":
        result = f"your telegram id is: `{from_id}`"
        return result
    elif command == "5g_test":
        return speed_test(from_id)
    elif command.startswith("send_message"):
        return send_message_test(from_id, command)
    elif command in ["get_allowed_users", "get_api_key", "list_models"]:
        if not is_admin(from_id):
            return admin_auch_info
        if IS_DEBUG_MODE == "0":
            return debug_mode_info
        if command == "get_allowed_users":
            return get_allowed_users()
        elif command == "get_api_key":
            return get_API_key()
        elif command == "list_models":
            return list_models()

    # [!HIGHLIGHT!] Modified command handling for explain, note, answer
    elif command.startswith("explain"):
        parts = command.split(" ", 1) # Split only once at the first space
        if len(parts) == 2: # Now we expect 2 parts: command and the rest
            command_name, concept_and_textbook_id = parts # The rest is concept + textbook_id
            concept_parts = concept_and_textbook_id.split() # Split the rest by spaces again
            if concept_parts: # Check if there's anything after 'explain'
                textbook_id = concept_parts[-1] # Assume textbook_id is the last word
                concept = " ".join(concept_parts[:-1]) # Join the rest as concept phrase
                return explain_concept(from_id, concept, textbook_id)
            else:
                return "Invalid command format. Use: /explain [concept] [textbook_id]"
        else:
            return "Invalid command format. Use: /explain [concept] [textbook_id]"

    elif command.startswith("note"):
        parts = command.split(" ", 1) # Split only once at the first space
        if len(parts) == 2:
            command_name, topic_and_textbook_id = parts
            topic_parts = topic_and_textbook_id.split()
            if topic_parts:
                textbook_id = topic_parts[-1]
                topic = " ".join(topic_parts[:-1])
                return prepare_short_note(from_id, topic, textbook_id)
            else:
                return "Invalid command format. Use: /note [topic] [textbook_id]"
        else:
            return "Invalid command format. Use: /note [topic] [textbook_id]"

    elif command.startswith("answer"):
        parts = command.split(" ", 1) # Split only once at the first space
        if len(parts) == 2:
            command_name, exercise_and_textbook_id = parts
            exercise_parts = exercise_and_textbook_id.split()
            if exercise_parts and len(exercise_parts) >= 2: # Expect at least exercise_number and textbook_id
                textbook_id = exercise_parts[-1]
                chapter_section = exercise_parts[-2] # Assuming chapter_section is before textbook_id
                exercise_number_parts = exercise_parts[:-2] # Everything before chapter_section is exercise number parts
                exercise_number = " ".join(exercise_number_parts) # In case exercise number is also a phrase
                return answer_exercise(from_id, exercise_number, chapter_section, textbook_id)
            else:
                return "Invalid command format. Use: /answer [exercise_number] [chapter_section] [textbook_id]"
        else:
            return "Invalid command format. Use: /answer [exercise_number] [chapter_section] [textbook_id]"

    else:
        result = "Invalid command, use /help for help"
        return result
