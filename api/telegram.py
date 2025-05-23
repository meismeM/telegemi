from typing import Dict

import requests
from md2tgmd import escape

from .config import BOT_TOKEN

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(chat_id, text, **kwargs):
    """send text message"""
    payload = {
        "chat_id": chat_id,
        "text": escape(text),
        "parse_mode": "MarkdownV2",
        **kwargs,
    }
    r = requests.post(f"{TELEGRAM_API}/sendMessage", data=payload)
    print(f"Sent message: {text} to {chat_id}")
    return r

def send_imageMessage(chat_id, text, imageID):
    """send image message"""
    payload = {
        "chat_id": chat_id,
        "caption": escape(text),
        "parse_mode": "MarkdownV2",
        "photo": imageID
    }
    r = requests.post(f"{TELEGRAM_API}/sendPhoto", data=payload)
    print(f"Sent imageMessage: {text} to {chat_id}")
    return r

def send_message_with_inline_keyboard(chat_id, text, keyboard, **kwargs):
    """send text message with inline keyboard"""
    payload = {
        "chat_id": chat_id,
        "text": escape(text),
        "parse_mode": "MarkdownV2",
        "reply_markup": {"inline_keyboard": keyboard},
        **kwargs,
    }
    r = requests.post(f"{TELEGRAM_API}/sendMessage", json=payload)
    print(f"Sent message with keyboard: {text} to {chat_id}")
    return r

def forward_message(chat_id, from_chat_id, message_id):
    """forward message to channel"""
    payload = {
        "chat_id": chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
    }
    r = requests.post(f"{TELEGRAM_API}/forwardMessage", json=payload)
    return r

def copy_message(chat_id, from_chat_id, message_id):
    """Copy message to a channel without quoting the original sender"""
    # Get the message details
    get_message_url = f"{TELEGRAM_API}/getChatMessage"
    message_payload = {
        "chat_id": from_chat_id,
        "message_id": message_id
    }
    message_details = requests.post(get_message_url, json=message_payload).json()
    
    if not message_details['ok']:
        print(f"Failed to retrieve message: {message_details['description']}")
        return message_details
    
    # Extract message content
    message_content = message_details['result'].get('text') or message_details['result'].get('caption', '')
    file_id = message_details['result'].get('photo')[-1]['file_id'] if 'photo' in message_details['result'] else None
    
    # Send the message as a new message to the target chat
    if file_id:
        # If the message is a photo
        return send_imageMessage(chat_id, message_content, file_id)
    else:
        # If the message is a text message
        return send_message(chat_id, message_content)

class Update:
    def __init__(self, update: Dict) -> None:
        self.update = update
        self.from_id = update["message"]["from"]["id"]
        self.type = self._type()
        self.text = self._text()
        self.photo_caption = self._photo_caption()
        self.file_id = self._file_id()
        self.user_name = update["message"]["from"].get("username", f" [UnnamedUser](tg://openmessage?user_id={self.from_id})")
        self.message_id: int = update["message"]["message_id"]

    def _type(self):
        if "text" in self.update["message"]:
            text = self.update["message"]["text"]
            if text.startswith("/") and not text.startswith("/new"):
                return "command"
            return "text"
        elif "photo" in self.update["message"]:
            return "photo"
        else:
            return ""

    def _photo_caption(self):
        if self.type == "photo":
            return self.update["message"].get("caption", "describe the photo and answer all questions if it has")
        return ""

    def _text(self):
        if self.type == "text":
            return self.update["message"]["text"]
        elif self.type == "command":
            text = self.update["message"]["text"]
            command = text[1:]
            return command
        return ""

    def _file_id(self):
        if self.type == "photo":
            return self.update["message"]["photo"][-1]["file_id"]
        return ""
