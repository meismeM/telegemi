# api/telegram.py
from typing import Dict, List
import requests
from md2tgmd import escape
import json # Import json for keyboard serialization

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
    # Limit text length for Telegram API
    max_length = 4096
    if len(payload["text"]) > max_length:
        print(f"Warning: Message text truncated for chat_id {chat_id}. Original length: {len(payload['text'])}")
        payload["text"] = payload["text"][:max_length]

    try:
        r = requests.post(f"{TELEGRAM_API}/sendMessage", data=payload)
        r.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        print(f"Sent message: {text[:50]}... to {chat_id}")
        return r
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to {chat_id}: {e}")
        # Optionally, try sending a plain text version if Markdown fails
        try:
            plain_payload = {
                "chat_id": chat_id,
                "text": text[:max_length], # Use original, unescaped text, truncated
                **kwargs,
            }
            r = requests.post(f"{TELEGRAM_API}/sendMessage", data=plain_payload)
            r.raise_for_status()
            print(f"Sent plain text fallback message to {chat_id}")
            return r
        except requests.exceptions.RequestException as e_plain:
            print(f"Error sending plain text fallback message to {chat_id}: {e_plain}")
            return None # Indicate failure


def send_imageMessage(chat_id, text, imageID):
    """send image message"""
    payload = {
        "chat_id": chat_id,
        "caption": escape(text),
        "parse_mode": "MarkdownV2",
        "photo": imageID
    }
    # Limit caption length
    max_length = 1024
    if len(payload["caption"]) > max_length:
         print(f"Warning: Image caption truncated for chat_id {chat_id}. Original length: {len(payload['caption'])}")
         payload["caption"] = payload["caption"][:max_length]

    try:
        r = requests.post(f"{TELEGRAM_API}/sendPhoto", data=payload)
        r.raise_for_status()
        print(f"Sent imageMessage: {text[:50]}... to {chat_id}")
        return r
    except requests.exceptions.RequestException as e:
        print(f"Error sending imageMessage to {chat_id}: {e}")
        return None

# --- NEW FUNCTION ---
def send_message_with_inline_keyboard(chat_id, text, keyboard: List[List[Dict]], **kwargs):
    """send text message with inline keyboard"""
    payload = {
        "chat_id": chat_id,
        "text": escape(text), # Still escape the main text for Markdown
        "parse_mode": "MarkdownV2",
        "reply_markup": json.dumps({"inline_keyboard": keyboard}), # Use json.dumps for nested structure
        **kwargs,
    }
    max_length = 4096
    if len(payload["text"]) > max_length:
        print(f"Warning: Message text truncated for chat_id {chat_id}. Original length: {len(payload['text'])}")
        payload["text"] = payload["text"][:max_length]

    try:
        # Send using json parameter for nested reply_markup
        r = requests.post(f"{TELEGRAM_API}/sendMessage", json=payload)
        r.raise_for_status()
        print(f"Sent message with keyboard: {text[:50]}... to {chat_id}")
        return r
    except requests.exceptions.RequestException as e:
         print(f"Error sending message with keyboard to {chat_id}: {e}")
         # Optionally, try sending a plain text version if Markdown fails
         try:
             plain_payload = {
                 "chat_id": chat_id,
                 "text": text[:max_length], # Use original, unescaped text
                 "reply_markup": json.dumps({"inline_keyboard": keyboard}),
                 **kwargs,
             }
             r = requests.post(f"{TELEGRAM_API}/sendMessage", json=plain_payload)
             r.raise_for_status()
             print(f"Sent plain text fallback message with keyboard to {chat_id}")
             return r
         except requests.exceptions.RequestException as e_plain:
             print(f"Error sending plain text fallback message with keyboard to {chat_id}: {e_plain}")
             return None # Indicate failure


# --- (Keep existing forward_message and copy_message functions) ---

def forward_message(chat_id, from_chat_id, message_id):
    """forward message to channel"""
    payload = {
        "chat_id": chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
    }
    try:
        r = requests.post(f"{TELEGRAM_API}/forwardMessage", json=payload)
        r.raise_for_status()
        return r
    except requests.exceptions.RequestException as e:
        print(f"Error forwarding message: {e}")
        return None

def copy_message(chat_id, from_chat_id, message_id):
    """Copy message to a channel without quoting the original sender"""
    # Get the message details - Note: getChatMessage doesn't exist, need to use copyMessage directly?
    # Let's assume the goal is just to copy, Telegram API has /copyMessage
    payload = {
        "chat_id": chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
    }
    try:
        r = requests.post(f"{TELEGRAM_API}/copyMessage", json=payload)
        r.raise_for_status()
        return r
    except requests.exceptions.RequestException as e:
        print(f"Error copying message: {e}")
        return None


class Update:
    # Keep the Update class as it is, focusing on message data.
    # Callback query data will be accessed directly in handle_message.
    def __init__(self, update: Dict) -> None:
        self.update = update
        # Check if it's a message update before accessing message-specific fields
        if "message" in update:
            self.message = update["message"]
            self.from_id = self.message["from"]["id"]
            self.type = self._type()
            self.text = self._text()
            self.photo_caption = self._photo_caption()
            self.file_id = self._file_id()
            self.user_name = self.message["from"].get("username", f"id:{self.from_id}") # Avoid Markdown in username log
            self.message_id: int = self.message["message_id"]
            self.chat_id = self.message["chat"]["id"] # Store chat_id
        else:
            # Handle other update types like callback_query if needed, or set defaults
            self.message = None
            self.from_id = None
            self.type = None
            self.text = None
            self.photo_caption = None
            self.file_id = None
            self.user_name = None
            self.message_id = None
            self.chat_id = None
             # Check specifically for callback_query
            if 'callback_query' in update:
                 self.type = 'callback_query'
                 callback_query = update['callback_query']
                 self.from_id = callback_query['from']['id']
                 self.user_name = callback_query['from'].get('username', f"id:{self.from_id}")
                 self.chat_id = callback_query['message']['chat']['id']
                 self.message_id = callback_query['message']['message_id']
                 # Add callback specific data if needed, e.g., self.callback_data = callback_query['data']


    def _type(self):
        if not self.message:
             return None # Or specific type if handling other updates here
        if "text" in self.message:
            text = self.message["text"]
            if text.startswith("/"):
                 # Consider /new as a command too now, handled separately
                 return "command"
            return "text"
        elif "photo" in self.message:
            return "photo"
        else:
            return "unknown_message_type" # Return a specific type

    def _photo_caption(self):
        if self.type == "photo":
            return self.message.get("caption", "describe the photo and answer all questions if it has")
        return ""

    def _text(self):
        if self.type == "text":
            return self.message["text"]
        elif self.type == "command":
            text = self.message["text"]
            # Return the full command including the slash for easier handling
            return text # e.g., returns "/help", "/study"
        return ""

    def _file_id(self):
        if self.type == "photo":
            # Ensure 'photo' list is not empty before accessing
            if self.message.get("photo"):
                 return self.message["photo"][-1]["file_id"]
        return ""
