# api/telegram.py
from typing import Dict, List, Any, Optional

import requests
from md2tgmd import escape # Ensure this library is installed and handles MarkdownV2 correctly

from .config import BOT_TOKEN

TELEGRAM_API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

def _make_request(endpoint: str, method: str = "POST", data: Dict = None, json_payload: Dict = None, **kwargs) -> Optional[Dict]:
    """Helper function to make requests to Telegram API."""
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN is not configured.")
        return None
    
    url = f"{TELEGRAM_API_BASE}/{endpoint}"
    try:
        if method.upper() == "POST":
            if json_payload:
                response = requests.post(url, json=json_payload, **kwargs)
            else:
                response = requests.post(url, data=data, **kwargs)
        elif method.upper() == "GET":
            response = requests.get(url, params=data, **kwargs)
        else:
            print(f"Unsupported HTTP method: {method}")
            return None
        
        response.raise_for_status()  # Raise an HTTPError for bad responses (4XX or 5XX)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Telegram API request error to {url}: {e}")
        if 'response' in locals() and response is not None:
            print(f"Response status: {response.status_code}, Response content: {response.text}")
        return None
    except ValueError as e: # Includes JSONDecodeError
        print(f"Telegram API JSON decode error for {url}: {e}")
        if 'response' in locals() and response is not None:
            print(f"Response content: {response.text}")
        return None


def send_message(chat_id: int, text: str, parse_mode: str = "MarkdownV2", **kwargs) -> Optional[Dict]:
    """Sends a text message."""
    payload = {
        "chat_id": chat_id,
        "text": escape(text) if parse_mode == "MarkdownV2" else text,
        "parse_mode": parse_mode,
        **kwargs,
    }
    # print(f"Attempting to send message to {chat_id}: {text[:70]}...") # Debug
    return _make_request("sendMessage", data=payload)

def send_imageMessage(chat_id: int, caption: str, imageID: str, parse_mode: str = "MarkdownV2", **kwargs) -> Optional[Dict]:
    """Sends an image message with a caption."""
    payload = {
        "chat_id": chat_id,
        "caption": escape(caption) if parse_mode == "MarkdownV2" else caption,
        "parse_mode": parse_mode,
        "photo": imageID,
        **kwargs,
    }
    return _make_request("sendPhoto", data=payload)

def send_message_with_inline_keyboard(chat_id: int, text: str, keyboard: List[List[Dict[str, str]]], parse_mode: str = "MarkdownV2", **kwargs) -> Optional[Dict]:
    """Sends a message with an inline keyboard."""
    payload = {
        "chat_id": chat_id,
        "text": escape(text) if parse_mode == "MarkdownV2" else text,
        "parse_mode": parse_mode,
        "reply_markup": {"inline_keyboard": keyboard},
        **kwargs,
    }
    return _make_request("sendMessage", json_payload=payload) # Use json_payload for nested structures

def edit_message_text(chat_id: int, message_id: int, text: str, keyboard: Optional[List[List[Dict[str, str]]]] = None, parse_mode: str = "MarkdownV2", **kwargs) -> Optional[Dict]:
    """Edits the text of an existing message. Optionally updates the keyboard."""
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": escape(text) if parse_mode == "MarkdownV2" else text,
        "parse_mode": parse_mode,
        **kwargs,
    }
    if keyboard is not None:
        payload["reply_markup"] = {"inline_keyboard": keyboard}
    
    return _make_request("editMessageText", json_payload=payload)

def answer_callback_query(callback_query_id: str, text: Optional[str] = None, show_alert: bool = False, **kwargs) -> Optional[Dict]:
    """Answers a callback query (e.g., from an inline button press)."""
    payload: Dict[str, Any] = {"callback_query_id": callback_query_id, "show_alert": show_alert, **kwargs}
    if text:
        payload["text"] = text # Max 200 chars
    
    return _make_request("answerCallbackQuery", json_payload=payload)

def forward_message(chat_id: int, from_chat_id: int, message_id: int, **kwargs) -> Optional[Dict]:
    """Forwards a message."""
    payload = {
        "chat_id": chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
        **kwargs,
    }
    return _make_request("forwardMessage", json_payload=payload)

def copy_message(chat_id: int, from_chat_id: int, message_id: int, **kwargs) -> Optional[Dict]:
    """Copies a message."""
    payload = {
        "chat_id": chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
        **kwargs,
    }
    return _make_request("copyMessage", json_payload=payload)


class Update:
    def __init__(self, update_data: Dict) -> None:
        self.raw_update: Dict = update_data
        self.update_type: str = self._determine_update_type() # "message", "edited_message", "callback_query", "unknown"
        
        # Common fields (initialized to sane defaults)
        self.from_id: int = 0
        self.user_name: str = "UnknownUser"
        self.chat_id: int = 0
        self.message_id: int = 0 # For messages, this is the ID of the current message. For callbacks, it's the ID of the message WITH the keyboard.

        # Message-specific fields
        self.text: Optional[str] = None # For text messages or commands (full text)
        self.command_name: Optional[str] = None # e.g., "help" from "/help args"
        self.command_args_str: Optional[str] = None # e.g., "args" from "/help args"
        self.photo_caption: Optional[str] = None
        self.file_id: Optional[str] = None # For photos

        # Callback-specific fields
        self.callback_query_id: Optional[str] = None
        self.callback_data: Optional[str] = None
        # self.callback_message_id: int = 0 # Redundant, use self.message_id
        # self.callback_chat_id: int = 0 # Redundant, use self.chat_id

        self.type: str = "unknown" # More specific type: "text", "command", "photo", "callback_query", etc.

        self._parse()

    def _determine_update_type(self) -> str:
        if "message" in self.raw_update:
            return "message"
        elif "edited_message" in self.raw_update:
            return "edited_message"
        elif "callback_query" in self.raw_update:
            return "callback_query"
        return "unknown"

    def _parse(self) -> None:
        if self.update_type == "message":
            message_data = self.raw_update.get("message", {})
            self._parse_common_message_fields(message_data)
            self._parse_message_content(message_data)
        elif self.update_type == "edited_message":
            # For simplicity, treat edited messages like new ones for parsing, but identify them.
            message_data = self.raw_update.get("edited_message", {})
            self._parse_common_message_fields(message_data)
            # Edited messages might not have all content types, or might need special handling
            # We'll primarily care if an edited message becomes a command.
            if "text" in message_data:
                self.text = message_data["text"]
                if self.text.startswith("/"):
                    self.type = "command" # Treat edited command as a new command
                    self._parse_command_from_text()
                else:
                    self.type = "edited_text" # Just an edited text
            else:
                self.type = "edited_other"
        elif self.update_type == "callback_query":
            callback_data_dict = self.raw_update.get("callback_query", {})
            self.type = "callback_query"
            self.callback_query_id = callback_data_dict.get("id")
            
            from_user = callback_data_dict.get("from", {})
            self.from_id = from_user.get("id", 0)
            self.user_name = from_user.get("username", f"User_{self.from_id}")
            
            self.callback_data = callback_data_dict.get("data")
            
            message_with_keyboard = callback_data_dict.get("message", {})
            if message_with_keyboard:
                self.chat_id = message_with_keyboard.get("chat", {}).get("id", 0)
                self.message_id = message_with_keyboard.get("message_id", 0)
        else:
            self.type = "unknown_update_type"

    def _parse_common_message_fields(self, message_data: Dict) -> None:
        from_user = message_data.get("from", {})
        self.from_id = from_user.get("id", 0)
        self.user_name = from_user.get("username", f"User_{self.from_id}")
        
        chat_data = message_data.get("chat", {})
        self.chat_id = chat_data.get("id", 0)
        self.message_id = message_data.get("message_id", 0)

    def _parse_message_content(self, message_data: Dict) -> None:
        if "text" in message_data:
            self.text = message_data["text"]
            if self.text.startswith("/"):
                self.type = "command"
                self._parse_command_from_text()
            else:
                self.type = "text"
        elif "photo" in message_data:
            self.type = "photo"
            self.photo_caption = message_data.get("caption")
            photo_array = message_data.get("photo", [])
            if photo_array: # Get the largest available photo
                self.file_id = photo_array[-1].get("file_id")
        else:
            self.type = "other_message_type" # e.g., sticker, document, audio

    def _parse_command_from_text(self) -> None:
        if self.text and self.text.startswith("/"):
            parts = self.text[1:].split(" ", 1)
            self.command_name = parts[0].lower()
            if len(parts) > 1:
                self.command_args_str = parts[1]
            else:
                self.command_args_str = "" # Ensure it's an empty string if no args