# api/telegram.py
from typing import Dict, List
import requests
from md2tgmd import escape
import json # Import json for keyboard serialization
import logging # Use logging module

from .config import BOT_TOKEN

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
logger = logging.getLogger(__name__) # Get a logger instance

def send_message(chat_id, text, **kwargs):
    """send text message with robust error handling and Markdown fallback"""
    payload = {
        "chat_id": chat_id,
        "text": escape(text),
        "parse_mode": "MarkdownV2",
        **kwargs,
    }
    max_length = 4096
    original_length = len(payload["text"])
    if original_length > max_length:
        logger.warning(f"Message text truncated for chat_id {chat_id}. Original length: {original_length}")
        payload["text"] = payload["text"][:max_length]

    try:
        r = requests.post(f"{TELEGRAM_API}/sendMessage", data=payload, timeout=10) # Add timeout
        r.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        # logger.info(f"Sent message (MD): {text[:50]}... to {chat_id}")
        return r
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending Markdown message to {chat_id}: {e}. Response: {e.response.text if e.response else 'No Response'}")
        # Fallback to plain text
        try:
            plain_payload = {
                "chat_id": chat_id,
                "text": text, # Use original, unescaped text
                **kwargs,
            }
            # Truncate plain text if necessary
            if len(plain_payload["text"]) > max_length:
                 logger.warning(f"Plain fallback message truncated for chat_id {chat_id}. Original length: {len(plain_payload['text'])}")
                 plain_payload["text"] = plain_payload["text"][:max_length]

            r = requests.post(f"{TELEGRAM_API}/sendMessage", data=plain_payload, timeout=10)
            r.raise_for_status()
            logger.info(f"Sent plain text fallback message to {chat_id}")
            return r
        except requests.exceptions.RequestException as e_plain:
            logger.error(f"Error sending plain text fallback message to {chat_id}: {e_plain}. Response: {e_plain.response.text if e_plain.response else 'No Response'}")
            return None # Indicate failure


def send_imageMessage(chat_id, text, imageID):
    """send image message"""
    payload = {
        "chat_id": chat_id,
        "caption": escape(text),
        "parse_mode": "MarkdownV2",
        "photo": imageID
    }
    max_length = 1024
    if len(payload["caption"]) > max_length:
         logger.warning(f"Image caption truncated for chat_id {chat_id}. Original length: {len(payload['caption'])}")
         payload["caption"] = payload["caption"][:max_length]

    try:
        r = requests.post(f"{TELEGRAM_API}/sendPhoto", data=payload, timeout=10)
        r.raise_for_status()
        logger.info(f"Sent imageMessage: {text[:50]}... to {chat_id}")
        return r
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending imageMessage to {chat_id}: {e}")
        return None

# --- send_message_with_inline_keyboard --- Verify using json=payload
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
        logger.warning(f"Message text truncated for chat_id {chat_id}. Original length: {len(payload['text'])}")
        payload["text"] = payload["text"][:max_length]

    try:
        # *** IMPORTANT: Use json=payload for nested reply_markup ***
        r = requests.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=10)
        r.raise_for_status()
        logger.info(f"Sent message with keyboard: {text[:50]}... to {chat_id}")
        return r
    except requests.exceptions.RequestException as e:
         logger.error(f"Error sending message with keyboard (Markdown) to {chat_id}: {e}. Response: {e.response.text if e.response else 'No Response'}")
         # Fallback to plain text
         try:
             plain_payload = {
                 "chat_id": chat_id,
                 "text": text, # Use original, unescaped text
                 "reply_markup": json.dumps({"inline_keyboard": keyboard}),
                 **kwargs,
             }
             if len(plain_payload["text"]) > max_length:
                  logger.warning(f"Plain fallback message truncated for chat_id {chat_id}. Original length: {len(plain_payload['text'])}")
                  plain_payload["text"] = plain_payload["text"][:max_length]

             r = requests.post(f"{TELEGRAM_API}/sendMessage", json=plain_payload, timeout=10)
             r.raise_for_status()
             logger.info(f"Sent plain text fallback message with keyboard to {chat_id}")
             return r
         except requests.exceptions.RequestException as e_plain:
             logger.error(f"Error sending plain text fallback message with keyboard to {chat_id}: {e_plain}. Response: {e_plain.response.text if e_plain.response else 'No Response'}")
             return None # Indicate failure


# --- (Keep existing forward_message and copy_message functions, add basic error handling) ---

def forward_message(chat_id, from_chat_id, message_id):
    """forward message to channel"""
    payload = {
        "chat_id": chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
    }
    try:
        r = requests.post(f"{TELEGRAM_API}/forwardMessage", json=payload, timeout=10)
        r.raise_for_status()
        return r
    except requests.exceptions.RequestException as e:
        logger.error(f"Error forwarding message: {e}")
        return None

def copy_message(chat_id, from_chat_id, message_id):
    """Copy message to a channel without quoting the original sender"""
    payload = {
        "chat_id": chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
    }
    try:
        r = requests.post(f"{TELEGRAM_API}/copyMessage", json=payload, timeout=10)
        r.raise_for_status()
        return r
    except requests.exceptions.RequestException as e:
        logger.error(f"Error copying message: {e}")
        return None

# --- Update Class (No major changes needed here for these issues) ---
class Update:
    def __init__(self, update: Dict) -> None:
        self.update = update
        if "message" in update:
            self.message = update["message"]
            self.from_id = self.message["from"]["id"]
            self.type = self._type()
            self.text = self._text()
            self.photo_caption = self._photo_caption()
            self.file_id = self._file_id()
            self.user_name = self.message["from"].get("username", f"id:{self.from_id}")
            self.message_id: int = self.message["message_id"]
            self.chat_id = self.message["chat"]["id"]
        else:
            self.message = None
            self.from_id = None
            self.type = None
            self.text = None
            self.photo_caption = None
            self.file_id = None
            self.user_name = None
            self.message_id = None
            self.chat_id = None
            if 'callback_query' in update:
                 self.type = 'callback_query'
                 callback_query = update['callback_query']
                 self.from_id = callback_query['from']['id']
                 self.user_name = callback_query['from'].get('username', f"id:{self.from_id}")
                 self.chat_id = callback_query['message']['chat']['id']
                 self.message_id = callback_query['message']['message_id']
                 # self.callback_data = callback_query['data'] # Can add if needed

    def _type(self):
        if not self.message: return None
        if "text" in self.message:
            text = self.message["text"]
            if text.startswith("/"): return "command"
            return "text"
        elif "photo" in self.message: return "photo"
        else: return "unknown_message_type"

    def _photo_caption(self):
        if self.type == "photo": return self.message.get("caption", "describe the photo") # Simplified default
        return ""

    def _text(self):
        if self.type == "text": return self.message["text"]
        elif self.type == "command": return self.message["text"]
        return ""

    def _file_id(self):
        if self.type == "photo":
            if self.message.get("photo"): return self.message["photo"][-1]["file_id"]
        return ""
