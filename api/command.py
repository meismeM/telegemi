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

# [!HIGHLIGHT!] New command functions for textbook processing
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

def answer_exercise(from_id, exercise_number, chapter_section, textbook_id):
    """Answers an exercise from a textbook."""
    textbook_content = get_textbook_content(textbook_id)
    if not textbook_content:
        return f"Textbook with ID '{textbook_id}' not found."

    # --- You'll need a way to identify exercises in the textbook text ---
    exercise_marker = f"Exercise {exercise_number}"
    start_index = textbook_content.lower().find(exercise_marker.lower())
    if start_index == -1:
        return f"Exercise '{exercise_number}' not found in textbook '{textbook_id}'."

    context_start = max(0, start_index - 200) # Context around the exercise
    context_end = min(len(textbook_content), start_index + 800)
    exercise_text = textbook_content[context_start:context_end]

    prompt = f"Answer exercise number '{exercise_number}' from chapter/section '{chapter_section}' based on the following textbook excerpt:\n\n---\n{exercise_text}\n---\n\nProvide a detailed and step-by-step answer if applicable, suitable for a Grade 9 student."
    response = generate_content(prompt)
    return response


# [!HIGHLIGHT!] Modified excute_command to handle new textbook commands
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

    elif command.startswith("explain"): # /explain concept textbook_id
        parts = command.split(" ", 3) # Corrected split count to 3
        if len(parts) == 3: # Corrected check to 3
            command_name, concept, textbook_id = parts # Unpack parts
            return explain_concept(from_id, concept, textbook_id)
        else:
            return "Invalid command format. Use: /explain [concept] [textbook_id]"

    elif command.startswith("note"): # /note topic textbook_id
        parts = command.split(" ", 3) # Corrected split count to 3
        if len(parts) == 3: # Corrected check to 3
            command_name, topic, textbook_id = parts # Unpack parts
            return prepare_short_note(from_id, topic, textbook_id)
        else:
            return "Invalid command format. Use: /note [topic] [textbook_id]"

    elif command.startswith("answer"): # /answer exercise_number chapter_section textbook_id
        parts = command.split(" ", 4) # Corrected split count to 4
        if len(parts) == 4: # Corrected check to 4
            command_name, exercise_number, chapter_section, textbook_id = parts # Unpack parts
            return answer_exercise(from_id, exercise_number, chapter_section, textbook_id)
        else:
            return "Invalid command format. Use: /answer [exercise_number] [chapter_section] [textbook_id]"

    else:
        result = "Invalid command, use /help for help"
        return result
