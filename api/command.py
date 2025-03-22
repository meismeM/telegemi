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
        return result 

from time import sleep

import google.generativeai as genai

from .auth import is_admin
from .config import ALLOWED_USERS,IS_DEBUG_MODE,GOOGLE_API_KEY
from .printLog import send_log
from .telegram import send_message
from .textbook_processor import get_textbook_content
from .gemini import generate_content

admin_auch_info = "You are not the administrator or your administrator ID is set incorrectly!!!"
debug_mode_info = "Debug mode is not enabled!"

def help():
    help_text = "Welcome to Gemini 2.0 flash AI! Interact through text or images and experience insightful answers. ... (rest of your help text) ..." # Keep your existing help text
    command_list = "/new - Start new chat\n/explain [concept] [textbook_id] - Explain a concept from textbook\n/note [topic] [textbook_id] - Prepare short note on a topic\n/answer [exercise_query] [textbook_id] - Answer exercise (WIP)" # Added explain, note, answer to command list
    result = f"{help_text}\n\n{command_list}"
    return result

# ... (list_models, get_allowed_users, get_API_key, speed_test, send_message_test - no changes needed) ...

def explain_concept(from_id, concept, textbook_id):
    #Explains a concept, using textbook context if available, otherwise general AI.
    textbook_content = get_textbook_content(textbook_id)
    context_text = None # Initialize context_text to None

    if textbook_content: # Check if textbook content is loaded
        search_term = concept
        start_index = textbook_content.lower().find(search_term.lower())
        if start_index != -1: # Concept found in textbook
            context_start = max(0, start_index - 500)
            context_end = min(len(textbook_content), start_index + 1000)
            context_text = textbook_content[context_start:context_end]

    if context_text: # If textbook context was found, use it in prompt
        prompt = f"Explain the concept of '{concept}' based on the following excerpt from the Grade 9 textbook '{textbook_id}':\n\n---\n{context_text}\n---\n\nProvide a clear and concise explanation suitable for a Grade 9 student."
    else: # If no textbook context found, use general prompt
        prompt = f"Explain the concept of '{concept}' in a clear and concise way, suitable for a Grade 9 student."

    response = generate_content(prompt)
    return response

def prepare_short_note(from_id, topic, textbook_id):
    #Prepares a short note on a topic, using textbook context if available, otherwise general AI.
    textbook_content = get_textbook_content(textbook_id)
    context_text = None # Initialize context_text to None

    if textbook_content: # Check if textbook content is loaded
        search_term = topic
        start_index = textbook_content.lower().find(search_term.lower())
        if start_index != -1: # Topic found in textbook
            context_start = max(0, start_index - 500)
            context_end = min(len(textbook_content), start_index + 1000)
            context_text = textbook_content[context_start:context_end]

    if context_text: # If textbook context was found, use it in prompt
        prompt = f"Prepare a short, concise study note on the topic of '{topic}' based on the following excerpt from the Grade 9 textbook '{textbook_id}'. Focus on the key points and make it easy to understand for a Grade 9 student. Limit the note to around 3-4 key points.\n\n---\n{context_text}\n---"
    else: # If no textbook context found, use general prompt
        prompt = f"Prepare a short, concise study note on the topic of '{topic}'. Focus on the key points and make it easy to understand for a Grade 9 student. Limit the note to around 3-4 key points."

    response = generate_content(prompt)
    return response


def answer_exercise(from_id, exercise_query, textbook_id):
    #Answers an exercise from a textbook.
    textbook_content = get_textbook_content(textbook_id)
    if not textbook_content:
        return f"Textbook with ID '{textbook_id}' not found."

    import re
    exercise_regex = re.compile(rf"(Review Questions)?\s*(Part [IVX]+:)?\s*(Question|exercise)\s*([\d.]+)", re.IGNORECASE)

    best_match_start = -1
    best_match_end = -1
    context_text = "Exercise not found."

    query_parts = exercise_query.lower().split()

    print(f"--- Searching for exercise: '{exercise_query}' ---")

    found_matches = []

    for match in exercise_regex.finditer(textbook_content.lower()):
        full_match = match.group(0)
        part = match.group(2)
        question_type = match.group(3)
        question_number = match.group(4)

        match_score = 0
        for query_part in query_parts:
            if query_part in full_match.lower():
                match_score += 1

        found_matches.append({
            "full_match": full_match,
            "part": part,
            "question_type": question_type,
            "question_number": question_number,
            "score": match_score
        })

        if best_match_start == -1 or match_score > best_match_score:
            best_match_start = match.start()
            best_match_end = match.end()
            best_match_score = match_score

    print("--- All Regex Matches Found (with scores): ---")
    for match_info in found_matches:
        print(f"  Match: '{match_info['full_match']}', Score: {match_info['score']}, Part: '{match_info['part']}', Type: '{match_info['question_type']}', Number: '{match_info['question_number']}'")

    if best_match_start != -1 and best_match_score > 0 :
        context_start = max(0, best_match_start - 500)
        context_end = min(len(textbook_content), best_match_end + 1000)
        context_text = textbook_content[context_start:context_text]
        print(f"--- Best Match Found: '{context_text[:100]}...' (score: {best_match_score}) ---")
    else:
        print("--- No Suitable Exercise Match Found ---")
        return f"Exercise '{exercise_query}' not found in textbook '{textbook_id}'."

    prompt = f"Based on the following excerpt from a Grade 9 economics textbook, answer the review question:\n\n---\n{context_text}\n---\n\nSpecifically, answer exercise/question: '{exercise_query}'."
    response = generate_content(prompt)
    return response


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
        parts = command.split(" ", 1)
        if len(parts) == 2:
            command_name, concept_and_textbook_id = parts
            concept_parts = concept_and_textbook_id.split()
            if concept_parts:
                textbook_id = concept_parts[-1]
                concept = " ".join(concept_parts[:-1])
                return explain_concept(from_id, concept, textbook_id)
            else:
                return "Invalid command format. Use: /explain [concept] [textbook_id]"
        else:
            return "Invalid command format. Use: /explain [concept] [textbook_id]"

    elif command.startswith("note"): # /note topic textbook_id
        parts = command.split(" ", 1)
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

    elif command.startswith("answer"): # /answer exercise_query textbook_id (exercise_query can now include chapter_section)
        parts = command.split(" ", 1)
        if len(parts) == 2:
            command_name, exercise_and_textbook_id = parts
            exercise_parts = exercise_and_textbook_id.split()
            if exercise_parts and len(exercise_parts) >= 1: # Expect at least exercise_query and textbook_id
                textbook_id = exercise_parts[-1]
                exercise_query_parts = exercise_parts[:-1] # Everything before textbook_id is exercise query
                exercise_query = " ".join(exercise_query_parts)
                return answer_exercise(from_id, exercise_query, textbook_id)
            else:
                return "Invalid command format. Use: /answer [exercise_query] [textbook_id]"
        else:
            return "Invalid command format. Use: /answer [exercise_query] [textbook_id]"

    else:
        result = "Invalid command, use /help for help"
        return result


        
Let advance other commands and there output to have good result but general request 
"""'''
from time import sleep

import google.generativeai as genai

from .auth import is_admin
from .config import ALLOWED_USERS,IS_DEBUG_MODE,GOOGLE_API_KEY
from .printLog import send_log
from .telegram import send_message
from .textbook_processor import get_textbook_content, search_concept_pages, get_text_from_pages
from .gemini import generate_content

admin_auch_info = "You are not the administrator or your administrator ID is set incorrectly!!!"
debug_mode_info = "Debug mode is not enabled!"

def help():
    help_text = "Welcome to Gemini 2.0 flash AI! Interact through text or images and experience insightful answers. Unlock the power of AI-driven communication – every message is a chance for a smarter exchange. Send text or image!\n Experience the power of AI-driven communication through insightful answers, text, or images. \n👾 Features \n Answer any question, even challenging or strange ones. \n ⏩ Generate creative text formats like poems, scripts, code, emails, and more. \n ⏩ Translate languages effortlessly. \n ⏩ Simplify complex concepts with clear explanations. \n ⏩  Perform math and calculations. \n ⏩ Assist with research and creative content generation. \n ⏩ Provide fun with word games, quizzes, and much more!\n ⏩ Send a text or image and unlock smarter exchanges. Don’t forget to join the channels below for more: And most importantly join the channels:  \n [Channel 1](https://t.me/+gOUK4JnBcCtkYWQ8) \n [Channel 2](https://t.me/telegemin). \n ወደ ጀሚኒ 1.5 ፕሮ አርቴፊሻል ኢንተለጀንስ እንኳን ደህና መጡ! ድንቅ 3 ከፍተኛ ተጠቃሚዎች ያሉት ጎግል AI ፣ እኔ እዚህ ስፍር ቁጥር በሌላቸው መንገዶች ልረዳችሁ የምችል የአርቴፊሻል ኢንተለጀንስ ቻት ቦት ነኝ። በአስተዋይ መልሶች፣ በጽሑፍ ወይም በምስሎች የአርቴፊሻል ኢንተለጀንስ የተጎላበተ የግንኙነት ይለማመዱ። \n \n ⏩ ማንኛውንም ጥያቄ፣ ፈታኝ ወይም እንግዳ የሆኑትንም እንኳ መልስ ያግኙ። \n ⏩ እንደ ግጥም፣ ስክሪፕት፣ ኮድ፣ ኢሜይሎች እና ሌሎችም ያሉ የፈጠራ ጽሑፎችን ይፍጠሩ። \n ⏩ ቋንቋዎችን በቀላሉ መተርጎም። \n ⏩ ውስብስብ ጽንሰ-ሐሳቦችን በግልጽ ማብራራት። \n ⏩ የሂሳብ ስሌቶችን መስራት። \n ⏩ በምርምር እና በፈጠራ ይዘት ያላቸው ፅሁፎች። \n ⏩ በቃላት ጨዋታዎች፣ ጥያቄዎች እና በብዙ ተጨማሪ ነገሮች ይዝናኑ!\n ⏩ ጽሑፍ ወይም ምስል ይላኩ እና መልስ ያግኙ። ለተጨማሪ መረጃ ከታች ባሉት ቻናሎች መቀላቀልዎን አይርሱ።"
    command_list = "/new - Start new chat\n/explain [concept] [textbook_id] - Explain a concept from textbook\n/note [topic] [textbook_id] - Prepare short note on a topic"
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
    """Explains a concept, using textbook context with page numbers if available, otherwise general AI."""
    concept_pages = search_concept_pages(textbook_id, concept) # Use helper function to find relevant pages
    context_text = ""
    page_refs = ""

    if concept_pages: # If concept found in textbook
        context_text = get_text_from_pages(textbook_id, concept_pages) # Get text from relevant pages
        page_refs = f"(Pages: {', '.join(map(str, concept_pages))})" # Create page number reference string
        prompt = f"Explain the concept of '{concept}' based on the following excerpt from pages {page_refs} of the Grade 9 textbook '{textbook_id}':\n\n---\n{context_text}\n---\n\nProvide a detail and comprehensive explanation suitable for a Grade 9 student." # More detailed prompt
    else: # If not found, use general prompt
        prompt = f"Explain the concept of '{concept}' in detail and comprehensively, suitable for a Grade 9 student." # More detailed general prompt
        page_refs = "(Textbook page not found)"

    response = generate_content(prompt)
    return f"{response}\n\n{page_refs}" # Append page reference to response


def prepare_short_note(from_id, topic, textbook_id):
    """Prepares a short note on a topic, using textbook context with page numbers if available, otherwise general AI."""
    topic_pages = search_concept_pages(textbook_id, topic) # Use helper function to find relevant pages
    context_text = ""
    page_refs = ""

    if topic_pages: # If topic found in textbook
        context_text = get_text_from_pages(textbook_id, topic_pages) # Get text from relevant pages
        page_refs = f"(Pages: {', '.join(map(str, topic_pages))})" # Create page number reference string
        prompt = f"Prepare a short, concise but comprehensive study note on the topic of '{topic}' based on the Grade 9 textbook '{textbook_id}', drawing from pages {page_refs}. Focus on key points and make it easy to understand for a Grade 9 student. Limit the note to around 5-6 key points if possible.\n\n---\n{context_text}\n---" # More detailed prompt
    else: # If not found, use general prompt
        prompt = f"Prepare a short, concise but comprehensive study note on the topic of '{topic}'. Focus on key points and make it easy to understand for a Grade 9 student. Limit the note to around 5-6 key points if possible." # More detailed general prompt
        page_refs = "(Textbook page not found)"

    response = generate_content(prompt)
    return f"{response}\n\n{page_refs}" # Append page reference to response

def answer_exercise(from_id, exercise_query, textbook_id):
    """Answers an exercise from a textbook."""
    textbook_content = get_textbook_content(textbook_id)
    if not textbook_content:
        return f"Textbook with ID '{textbook_id}' not found."

    import re
    exercise_regex = re.compile(rf"(Review Questions)?\s*(Part [IVX]+:)?\s*(Question|exercise)\s*([\d.]+)", re.IGNORECASE)

    best_match_start = -1
    best_match_end = -1
    context_text = "Exercise not found."

    query_parts = exercise_query.lower().split()

    print(f"--- Searching for exercise: '{exercise_query}' ---") # Log the query

    found_matches = [] # List to store all matches for logging

    for match in exercise_regex.finditer(textbook_content.lower()):
        full_match = match.group(0)
        part = match.group(2)
        question_type = match.group(3)
        question_number = match.group(4)

        match_score = 0
        for query_part in query_parts:
            if query_part in full_match.lower():
                match_score += 1

        found_matches.append({ # Store match details for logging
            "full_match": full_match,
            "part": part,
            "question_type": question_type,
            "question_number": question_number,
            "score": match_score
        })

        if best_match_start == -1 or match_score > best_match_score:
            best_match_start = match.start()
            best_match_end = match.end()
            best_match_score = match_score

    # [!HIGHLIGHT!] Log all found matches (even if no "best match" is good enough)
    print("--- All Regex Matches Found (with scores): ---")
    for match_info in found_matches:
        print(f"  Match: '{match_info['full_match']}', Score: {match_info['score']}, Part: '{match_info['part']}', Type: '{match_info['question_type']}', Number: '{match_info['question_number']}'")

    if best_match_start != -1 and best_match_score > 0 : # Added score check to ensure at least some word matched
        context_start = max(0, best_match_start - 500)
        context_end = min(len(textbook_content), best_match_end + 1000)
        context_text = textbook_content[context_start:context_end]
        print(f"--- Best Match Found: '{context_text[:100]}...' (score: {best_match_score}) ---") # Log best match
    else:
        print("--- No Suitable Exercise Match Found ---") # Log if no good match
        return f"Exercise '{exercise_query}' not found in textbook '{textbook_id}'."

    prompt = f"Based on the following excerpt from a Grade 9 economics textbook, answer the review question:\n\n---\n{context_text}\n---\n\nSpecifically, answer exercise/question: '{exercise_query}'."
    response = generate_content(prompt)
    return response

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
    else:
        result = "Invalid command, use /help for help"
        return result
        

    elif command.startswith("answer"):
        parts = command.split(" ", 1) # Split only once at the first space
        if len(parts) == 2:
            command_name, exercise_and_textbook_id = parts
            exercise_parts = exercise_and_textbook_id.split()
            if exercise_parts and len(exercise_parts) >= 2: # Expect at least exercise_number and textbook_id
                textbook_id = exercise_parts[-1]
                # [!HIGHLIGHT!] Combine exercise_number and chapter_section into exercise_query
                exercise_query_parts = exercise_parts[:-1] # Everything before textbook_id is exercise query
                exercise_query = " ".join(exercise_query_parts) # Join as exercise_query phrase

                # [!CORRECTED CALL!] Pass only 3 arguments: from_id, exercise_query, textbook_id
                return answer_exercise(from_id, exercise_query, textbook_id)
            else:
                return "Invalid command format. Use: /answer [exercise_query] [textbook_id]"
        else:
            return "Invalid command format. Use: /answer [exercise_query] [textbook_id]"'''

  # api/command.py
from time import sleep
import time # Import time module for sleep
import google.generativeai as genai

from .auth import is_admin
from .config import ALLOWED_USERS,IS_DEBUG_MODE,GOOGLE_API_KEY
from .printLog import send_log
from .telegram import send_message
from .textbook_processor import get_textbook_content, search_concept_pages, get_text_from_pages
from .gemini import generate_content, generate_content_stream # Add generate_content_stream to import

admin_auch_info = "You are not the administrator or your administrator ID is set incorrectly!!!"
debug_mode_info = "Debug mode is not enabled!"

def help():
    help_text = "Welcome to Gemini 2.0 flash AI! Interact through text or images and experience insightful answers. Unlock the power of AI-driven communication – every message is a chance for a smarter exchange. Send text or image!\n Experience the power of AI-driven communication through insightful answers, text, or images. \n👾 Features \n Answer any question, even challenging or strange ones. \n ⏩ Generate creative text formats like poems, scripts, code, emails, and more. \n ⏩ Translate languages effortlessly. \n ⏩ Simplify complex concepts with clear explanations. \n ⏩  Perform math and calculations. \n ⏩ Assist with research and creative content generation. \n ⏩ Provide fun with word games, quizzes, and much more!\n ⏩ Send a text or image and unlock smarter exchanges. Don’t forget to join the channels below for more: And most importantly join the channels:  \n [Channel 1](https://t.me/+gOUK4JnBcCtkYWQ8) \n [Channel 2](https://t.me/telegemin). \n ወደ ጀሚኒ 1.5 ፕሮ አርቴፊሻል ኢንተለጀንስ እንኳን ደህና መጡ! ድንቅ 3 ከፍተኛ ተጠቃሚዎች ያሉት ጎግል AI ፣ እኔ እዚህ ስፍር ቁጥር በሌላቸው መንገዶች ልረዳችሁ የምችል የአርቴፊሻል ኢንተለጀንስ ቻት ቦት ነኝ። በአስተዋይ መልሶች፣ በጽሑፍ ወይም በምስሎች የአርቴፊሻል ኢንተለጀንስ የተጎላበተ የግንኙነት ይለማመዱ። \n \n ⏩ ማንኛውንም ጥያቄ፣ ፈታኝ ወይም እንግዳ የሆኑትንም እንኳ መልስ ያግኙ። \n ⏩ እንደ ግጥም፣ ስክሪፕት፣ ኮድ፣ ኢሜይሎች እና ሌሎችም ያሉ የፈጠራ ጽሑፎችን ይፍጠሩ። \n ⏩ ቋንቋዎችን በቀላሉ መተርጎም። \n ⏩ ውስብስብ ጽንሰ-ሐሳቦችን በግልጽ ማብራራት። \n ⏩ የሂሳብ ስሌቶችን መስራት። \n ⏩ በምርምር እና በፈጠራ ይዘት ያላቸው ፅሁፎች። \n ⏩ በቃላት ጨዋታዎች፣ ጥያቄዎች እና በብዙ ተጨማሪ ነገሮች ይዝናኑ!\n ⏩ ጽሑፍ ወይም ምስል ይላኩ እና መልስ ያግኙ። ለተጨማሪ መረጃ ከታች ባሉት ቻናሎች መቀላቀልዎን አይርሱ።"
    command_list = "/new - Start new chat\n/explain [concept] [textbook_id] - Explain a concept from textbook\n/note [topic] [textbook_id] - Prepare short note on a topic\n/answer [exercise_query] [textbook_id] - Answer exercise (WIP)"
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

'''def explain_concept(from_id, concept, textbook_id):
    """Explains a concept, using textbook context with page numbers if available, otherwise general AI."""
    concept_pages = search_concept_pages(textbook_id, concept) # Use helper function to find relevant pages
    context_text = ""
    page_refs = ""

    if concept_pages: # If concept found in textbook
        context_text = get_text_from_pages(textbook_id, concept_pages) # Get text from relevant pages
        page_refs = f"(Pages: {', '.join(map(str, concept_pages))})" # Create page number reference string
        prompt = f"Explain the concept of '{concept}' based on the following excerpt from pages {page_refs} of the Grade 9 textbook '{textbook_id}':\n\n---\n{context_text}\n---\n\nProvide a detailed and comprehensive explanation suitable for a Grade 9 student." # More detailed prompt
    else: # If not found, use general prompt
        prompt = f"Explain the concept of '{concept}' in detail and comprehensively, suitable for a Grade 9 student." # More detailed general prompt
        page_refs = "(Textbook page not found)"

    response = generate_content(prompt)
    return f"{response}\n\n{page_refs}" # Append page reference to response
def explain_concept(from_id, concept, textbook_id):
    """Explains a concept, using textbook context with page numbers and streaming response."""
    concept_pages = search_concept_pages(textbook_id, concept)
    context_text = ""
    page_refs = ""

    if concept_pages:
        context_text = get_text_from_pages(textbook_id, concept_pages)
        page_refs = f"(Pages: {', '.join(map(str, concept_pages))})"
        prompt = f"Explain the concept of '{concept}' based on the following excerpt from pages {page_refs} of the Grade 9 textbook '{textbook_id}':\n\n---\n{context_text}\n---\n\nProvide a detailed and comprehensive explanation suitable for a Grade 9 student."
    else:
        prompt = f"Explain the concept of '{concept}' in detail and comprehensively, suitable for a Grade 9 student."
        page_refs = "(Textbook page not found)"

    # [!HIGHLIGHT!] Use generate_content_stream instead of generate_content
    response_stream = generate_content_stream(prompt) # Get a stream of response chunks

    full_response = "" # Accumulate full response text for page refs and return
    for chunk_text in response_stream: # Iterate through response chunks
        if chunk_text: # Check if chunk is not empty (error message might be empty)
            send_message(from_id, chunk_text) # Send each chunk as a Telegram message
            full_response += chunk_text # Accumulate for final response

    return f"{full_response}\n\n{page_refs}" # Append page reference to the accumulated response'''



def explain_concept(from_id, concept, textbook_id):
    """Explains concept with streaming, using time-based chunk buffering and robust error handling."""
    concept_pages = search_concept_pages(textbook_id, concept)
    context_text = ""
    page_refs = ""
    prompt = ""
    full_response = ""  # Initialize full_response

    if concept_pages:
        context_text = get_text_from_pages(textbook_id, concept_pages)
        page_refs = f"(Pages: {', '.join(map(str, concept_pages))})"
        prompt = f"Explain the concept of '{concept}' based on the following excerpt from pages {page_refs} of the Grade 9 textbook '{textbook_id}':\n\n---\n{context_text}\n---\n\nProvide a detailed and comprehensive explanation suitable for a Grade 9 student."
    else:
        prompt = f"Explain the concept of '{concept}' in detail and comprehensively, suitable for a Grade 9 student."
        page_refs = "(Textbook page not found)"

    response_stream = generate_content_stream(prompt)

    buffered_message = ""
    last_chunk_time = time.time()

    try:
        for chunk_text in response_stream:
            if chunk_text:
                buffered_message += chunk_text
                full_response += chunk_text # [!HIGHLIGHT!] Accumulate full_response here!

            current_time = time.time()
            time_since_last_chunk = current_time - last_chunk_time

            if len(buffered_message) > 5000 or time_since_last_chunk >= 5:
                send_message(from_id, buffered_message)
                buffered_message = ""
                last_chunk_time = current_time

    except Exception as e:
        error_message = f"Error during streaming response from Gemini: {e}"
        send_message(from_id, error_message)
        return error_message

    # Send any remaining buffered text
    if buffered_message:
        send_message(from_id, buffered_message)

    return f"{full_response}\n\n{page_refs}" # Append page reference to the accumulated response

def create_questions(from_id, concept, textbook_id):
    """Generates questions based on a concept from a textbook, using streaming."""
    concept_pages = search_concept_pages(textbook_id, concept)
    context_text = ""
    page_refs = ""
    prompt = ""  # Initialize prompt

    if concept_pages: # If concept found in textbook
        context_text = get_text_from_pages(textbook_id, concept_pages)
        page_refs = f"(Pages: {', '.join(map(str, concept_pages))})"
        prompt = f"Generate 5-10 review questions about the concept of '{concept}' based on the following excerpt from pages {page_refs} of the Grade 9 textbook '{textbook_id}':\n\n---\n{context_text}\n---\n\nThese questions should be suitable for Grade 9 students to test their understanding of the concept. Include a variety of question types (e.g., multiple choice, true/false, short answer) if appropriate for the concept." # Modified prompt to generate questions
    else: # If not found, use general prompt (less textbook-specific questions)
        prompt = f"Generate 5-7 review questions about the concept of '{concept}'. These questions should be suitable for Grade 9 students and cover the key aspects of this concept. Include a variety of question types (e.g., multiple choice, true/false, short answer) if appropriate." # Modified prompt for general questions
        page_refs = "(Textbook page not found)"

    response_stream = generate_content_stream(prompt)

    buffered_message = ""
    last_chunk_time = time.time()
    full_response = ""  # Initialize full_response

    try:
        for chunk_text in response_stream:
            if chunk_text:
                buffered_message += chunk_text
                full_response += chunk_text

            current_time = time.time()
            time_since_last_chunk = current_time - last_chunk_time

            if len(buffered_message) > 2000 or time_since_last_chunk >= 3:
                send_message(from_id, buffered_message)
                buffered_message = ""
                last_chunk_time = current_time
                time.sleep(0.1)

    except Exception as e:
        error_message = f"Error during streaming response for create_questions: {e}" # Updated error message
        send_message(from_id, error_message)
        return error_message

    # Send any remaining buffered text
    if buffered_message:
        send_message(from_id, buffered_message)

    return f"{full_response}\n\n{page_refs}" # Append page reference

def prepare_short_note(from_id, topic, textbook_id):
    """Prepares a short note on a topic, using textbook context with page numbers if available, otherwise general AI."""
    topic_pages = search_concept_pages(textbook_id, topic) # Use helper function to find relevant pages
    context_text = ""
    page_refs = ""

    if topic_pages: # If topic found in textbook
        context_text = get_text_from_pages(textbook_id, topic_pages) # Get text from relevant pages
        page_refs = f"(Pages: {', '.join(map(str, topic_pages))})" # Create page number reference string
        prompt = f"Prepare a short, concise but comprehensive study note on the topic of '{topic}' based on the Grade 9 textbook '{textbook_id}', drawing from pages {page_refs}. Focus on key points and make it easy to understand for a Grade 9 student. Limit the note to around 5-6 key points if possible.\n\n---\n{context_text}\n---" # More detailed prompt
    else: # If not found, use general prompt
        prompt = f"Prepare a short, concise but comprehensive study note on the topic of '{topic}'. Focus on key points and make it easy to understand for a Grade 9 student. Limit the note to around 3-4 key points if possible." # More detailed general prompt
        page_refs = "(Textbook page not found)"

    response = generate_content(prompt)
    return f"{response}\n\n{page_refs}" # Append page reference to response

def answer_exercise(from_id, exercise_query, textbook_id):
    """Answers an exercise from a textbook."""
    textbook_content = get_textbook_content(textbook_id)
    if not textbook_content:
        return f"Textbook with ID '{textbook_id}' not found."

    import re
    exercise_regex = re.compile(rf"(Review Questions)?\s*(Part [IVX]+:)?\s*(Question|exercise)\s*([\d.]+)", re.IGNORECASE)

    best_match_start = -1
    best_match_end = -1
    context_text = "Exercise not found."

    query_parts = exercise_query.lower().split()

    print(f"--- Searching for exercise: '{exercise_query}' ---") # Log the query

    found_matches = [] # List to store all matches for logging

    for match in exercise_regex.finditer(textbook_content.lower()):
        full_match = match.group(0)
        part = match.group(2)
        question_type = match.group(3)
        question_number = match.group(4)

        match_score = 0
        for query_part in query_parts:
            if query_part in full_match.lower():
                match_score += 1

        found_matches.append({ # Store match details for logging
            "full_match": full_match,
            "part": part,
            "question_type": question_type,
            "question_number": question_number,
            "score": match_score
        })

        if best_match_start == -1 or match_score > best_match_score:
            best_match_start = match.start()
            best_match_end = match.end()
            best_match_score = match_score

    # [!HIGHLIGHT!] Log all found matches (even if no "best match" is good enough)
    print("--- All Regex Matches Found (with scores): ---")
    for match_info in found_matches:
        print(f"  Match: '{match_info['full_match']}', Score: {match_info['score']}, Part: '{match_info['part']}', Type: '{match_info['question_type']}', Number: '{match_info['question_number']}'")

    if best_match_start != -1 and best_match_score > 0 : # Added score check to ensure at least some word matched
        context_start = max(0, best_match_start - 500)
        context_end = min(len(textbook_content), best_match_end + 1000)
        context_text = textbook_content[context_start:context_end]
        print(f"--- Best Match Found: '{context_text[:100]}...' (score: {best_match_score}) ---") # Log best match
    else:
        print("--- No Suitable Exercise Match Found ---") # Log if no good match
        return f"Exercise '{exercise_query}' not found in textbook '{textbook_id}'."

    prompt = f"Based on the following excerpt from a Grade 9 economics textbook, answer the review question:\n\n---\n{context_text}\n---\n\nSpecifically, answer exercise/question: '{exercise_query}'."
    response = generate_content(prompt)
    return response

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

          
    elif command.startswith("create_questions"): # /create_questions concept textbook_id
        parts = command.split(" ", 1) # Split only once at the first space
        if len(parts) == 2: # Now we expect 2 parts: command and the rest
            command_name, concept_and_textbook_id = parts # The rest is concept + textbook_id
            concept_parts = concept_and_textbook_id.split() # Split the rest by spaces again
            if concept_parts: # Check if there's anything after 'explain'
                textbook_id = concept_parts[-1] # Assume textbook_id is the last word
                concept = " ".join(concept_parts[:-1]) # Join the rest as concept phrase
                return "Invalid command format. Use: /create_questions [concept] [textbook_id]"
            else:
                return "Invalid command format. Use: /create_questions [concept] [textbook_id]"
        else:
            return "Invalid command format. Use: /create_questions [concept] [textbook_id]"

    
    else:
        result = "Invalid command, use /help for help"
        return result 
