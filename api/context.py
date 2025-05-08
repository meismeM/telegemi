"""
The class ChatManager manages all users and their conversations in the
form of a dictionary.

Each user has a ChatConversation instance, which may include multiple
previous conversations of the user (provided by the Google Gemini API).

The class ImageChatManager is rather simple, as the images in Gemini Pro
do not have a contextual environment. This class performs some tasks
such as obtaining photos to addresses and so on.
"""
from io import BytesIO
from typing import Dict, Iterator

import requests

from .config import BOT_TOKEN
from .gemini import ChatConversation, generate_text_with_image # ChatConversation might be used if we want history for images too


class ChatManager:
    """setting up a basic conversation storage manager"""

    def __init__(self):
        self.chats: Dict[int, ChatConversation] = {}

    def _new_chat(self, from_id: int) -> ChatConversation:
        chat = ChatConversation()
        self.chats[from_id] = chat
        return chat

    def get_chat(self, from_id: int) -> ChatConversation:
        chat = self.chats.get(from_id)
        if chat is None:
            chat = self._new_chat(from_id)
        return chat


class ImageChatManger: # Renamed to ImageChatManager for consistency
    def __init__(self, prompt: str, file_id: str) -> None:
        self.prompt = prompt if prompt else "Describe this image in detail and answer any questions."
        self.file_id = file_id

    def _get_file_path(self) -> str | None:
        """Gets the file_path for a given file_id from Telegram."""
        if not BOT_TOKEN or not self.file_id:
            print("Error: BOT_TOKEN or file_id missing for _get_file_path.")
            return None
        try:
            response = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={self.file_id}"
            )
            response.raise_for_status()
            data = response.json()
            if data.get("ok") and data.get("result") and data["result"].get("file_path"):
                return data["result"]["file_path"]
            else:
                print(f"Error getting file path from Telegram: {data.get('description', 'Unknown error')}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"RequestException in _get_file_path: {e}")
            return None


    def tel_photo_url(self) -> str | None:
        """Constructs the direct download URL for a Telegram photo."""
        file_path = self._get_file_path()
        if file_path:
            return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        return None

    def photo_bytes(self) -> BytesIO | None:
        """Downloads photo from Telegram and returns its BytesIO representation."""
        photo_url = self.tel_photo_url()
        if not photo_url:
            return None
        try:
            response = requests.get(photo_url)
            response.raise_for_status()
            return BytesIO(response.content)
        except requests.exceptions.RequestException as e:
            print(f"RequestException in photo_bytes downloading from {photo_url}: {e}")
            return None

    def send_image(self) -> str:
        """Generates text from an image using Gemini."""
        image_bytes_io = self.photo_bytes()
        if not image_bytes_io:
            return "Error: Could not download or process the image from Telegram."
        
        response_text = generate_text_with_image(self.prompt, image_bytes_io)
        return response_text