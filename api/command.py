from time import sleep

import google.generativeai as genai

from .auth import is_admin
from .config import ALLOWED_USERS, IS_DEBUG_MODE, GOOGLE_API_KEY
from .printLog import send_log
from .telegram import send_message
from .handle import pending_approvals, send_message_to_channel

admin_auch_info = "You are not the administrator or your administrator ID is set incorrectly!!!"
debug_mode_info = "Debug mode is not enabled!"

def help():
    help_text = "Welcome to Gemini 1.5 Pro AI! Interact through text or images and experience insightful answers. Unlock the power of AI-driven communication – every message is a chance for a smarter exchange. Send text or image! And most importantly join the channels:  \n [Channel 1](https://t.me/+gOUK4JnBcCtkYWQ8) \n [Channel 2](https://t.me/telegemin). \n በጀሚኒ 1.5 ፕሮ ኤአይ እንኳን ደህና መጡ! በጽሑፍ ወይም በምስሎች ይገናኙ እና ጠቃሚ መልሶችን ያግኙ። የኤአይ የተነደፈ ግንኙነትን ኃይል ይክፈቱ - እያንዳንዱ መልእክት ለበለጠ ብልህ ልውውጥ እድል ነው። ጽሑፍ ወይም ምስል ይላኩ! እና ከሁሉም በላይ በቻናሎች ይቀላቀሉ።"
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

def approve_message(from_id, command):
    if not is_admin(from_id):
        return admin_auch_info

    command_parts = command.strip().split()

    if len(command_parts) != 2:
        return "Invalid command format. Use /approve [message_id]."

    try:
        message_id = int(command_parts[1])
    except ValueError:
        return "Invalid message ID. Please provide a valid number."

    if message_id not in pending_approvals:
        return f"Message ID `{message_id}` not found."

    approval_info = pending_approvals.pop(message_id)

    if "photo_url" in approval_info:
        send_message_to_channel(f"[Photo]({approval_info['photo_url']}) by @{approval_info['user_name']}:\n\nCaption: {approval_info['photo_caption']}\n\n(Approved by Admin)")
    else:
        send_message_to_channel(f"Message by @{approval_info['user_name']}:\n\n{approval_info['text']}\n\n(Approved by Admin)")

    send_message(from_id, f"Message ID `{message_id}` has been approved and posted to the channel.")
    send_message(approval_info["from_id"], "Your message has been approved and posted to the channel.")
    return ""

def deny_message(from_id, command):
    if not is_admin(from_id):
        return admin_auch_info

    command_parts = command.strip().split()

    if len(command_parts) != 2:
        return "Invalid command format. Use /deny [message_id]."

    try:
        message_id = int(command_parts[1])
    except ValueError:
        return "Invalid message ID. Please provide a valid number."

    if message_id not in pending_approvals:
        return f"Message ID `{message_id}` not found."

    approval_info = pending_approvals.pop(message_id)

    send_message(from_id, f"Message ID `{message_id}` has been denied.")
    send_message(approval_info["from_id"], "Your message has been denied and was not posted to the channel.")
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

    elif command.startswith("approve"):
        return approve_message(from_id, command)

    elif command.startswith("deny"):
        return deny_message(from_id, command)

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