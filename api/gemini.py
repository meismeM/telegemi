'''from io import BytesIO

import google.generativeai as genai
import PIL.Image

from .config import GOOGLE_API_KEY, generation_config, safety_settings

genai.configure(api_key=GOOGLE_API_KEY[0])

model_usual = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    safety_settings=safety_settings)

model_vision = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    safety_settings=safety_settings)


def list_models() -> None:
    """list all models"""
    for m in genai.list_models():
        print(m)
        if "generateContent" in m.supported_generation_methods:
            print(m.name)

""" This function is deprecated """
def generate_content(prompt: str) -> str:
    """generate text from prompt"""
    try:
        response = model_usual.generate_content(prompt)
        result = response.text
    except Exception as e:
        result = f"Something went wrong!\n{repr(e)}\n\nThe content you entered may be inappropriate, please modify it and try again"
    return result


def generate_text_with_image(prompt: str, image_bytes: BytesIO) -> str:
    """generate text from prompt and image"""
    img = PIL.Image.open(image_bytes)
    try:
        response = model_vision.generate_content([prompt, img])
        result = response.text
    except Exception as e:
        result = f"Something went wrong!\n{repr(e)}\n\nThe content you entered may be inappropriate, please modify it and try again"
    return result


class ChatConversation:
    """
    Kicks off an ongoing chat. If the input is /new,
    it triggers the start of a fresh conversation.
    """

    def __init__(self) -> None:
        self.chat = model_usual.start_chat(history=[])

    def send_message(self, prompt: str) -> str:
        """send message"""
        if prompt.startswith("/new"):
            self.__init__()
            result = "We're having a fresh chat."
        else:
            try:
                response = self.chat.send_message(prompt)
                result = response.text
            except Exception as e:
                result = f"Something went wrong!\n{repr(e)}\n\nThe content you entered may be inappropriate, please modify it and try again"
        return result

    @property
    def history(self):
        return self.chat.history

    @property
    def history_length(self):
        return len(self.chat.history)


if __name__ == "__main__":
    print(list_models())'''
'''# api/gemini.py
from io import BytesIO
from typing import Dict

import google.generativeai as genai
import PIL.Image

from .config import GOOGLE_API_KEY, generation_config, safety_settings

genai.configure(api_key=GOOGLE_API_KEY[0])

model_usual = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    safety_settings=safety_settings)

model_vision = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    safety_settings=safety_settings)


def list_models() -> None:
    """list all models"""
    for m in genai.list_models():
        print(m)
        if "generateContent" in m.supported_generation_methods:
            print(m.name)

""" This function is deprecated """
def generate_content(prompt: str) -> str: # Keep the original generate_content for non-streaming cases
    """generate text from prompt"""
    try:
        response = model_usual.generate_content(prompt)
        result = response.text
    except Exception as e:
        result = f"Something went wrong!\n{repr(e)}\n\nThe content you entered may be inappropriate, please modify it and try again"
    return result


def generate_text_with_image(prompt: str, image_bytes: BytesIO) -> str:
    """generate text from prompt and image"""
    img = PIL.Image.open(image_bytes)
    try:
        response = model_vision.generate_content([prompt, img])
        result = response.text
    except Exception as e:
        result = f"Something went wrong!\n{repr(e)}\n\nThe content you entered may be inappropriate, please modify it and try again"
    return result

# [!HIGHLIGHT!] New streaming function
def generate_content_stream(prompt: str):
    """Generates content in streaming mode, yielding chunks of the response."""
    try:
        response_stream = model_usual.generate_content(prompt, stream=True) # stream=True enables streaming
        for chunk in response_stream: # Iterate through response chunks
            yield chunk.text # Yield text content of each chunk
    except Exception as e:
        error_message = f"Something went wrong!\n{repr(e)}\n\nThe content you entered may be inappropriate, please modify it and try again"
        yield error_message # Yield error message as a single chunk


class ChatConversation:
    """
    Kicks off an ongoing chat. If the input is /new,
    it triggers the start of a fresh conversation.
    """

    def __init__(self) -> None:
        self.chat = model_usual.start_chat(history=[])

    def send_message(self, prompt: str) -> str:
        """send message"""
        if prompt.startswith("/new"):
            self.__init__()
            result = "We're having a fresh chat."
        else:
            try:
                response = self.chat.send_message(prompt)
                result = response.text
            except Exception as e:
                result = f"Something went wrong!\n{repr(e)}\n\nThe content you entered may be inappropriate, please modify it and try again"
        return result

    @property
    def history(self):
        return self.chat.history

    @property
    def history_length(self):
        return len(self.chat.history)


if __name__ == "__main__":
    print(list_models())'''

# api/gemini.py
from io import BytesIO
from typing import Dict, Iterator # Import Iterator

import google.generativeai as genai
import PIL.Image

from .config import GOOGLE_API_KEY, generation_config, safety_settings

# --- Model setup remains the same ---
genai.configure(api_key=GOOGLE_API_KEY[0])

model_usual = genai.GenerativeModel(
    model_name="gemini-2.0-flash", # Using 1.5 flash as per original
    generation_config=generation_config,
    safety_settings=safety_settings)

model_vision = genai.GenerativeModel(
    model_name="gemini-2.0-flash", # Using 1.5 flash as per original
    generation_config=generation_config,
    safety_settings=safety_settings)


# --- list_models, generate_content (non-streaming), generate_text_with_image remain the same ---
def list_models() -> None:
    """list all models"""
    for m in genai.list_models():
        print(m)
        if "generateContent" in m.supported_generation_methods:
            print(m.name)

def generate_content(prompt: str) -> str:
    """generate text from prompt (non-streaming)"""
    try:
        response = model_usual.generate_content(prompt)
        result = response.text
    except Exception as e:
        result = f"Something went wrong!\n{repr(e)}\n\nThe content you entered may be inappropriate, please modify it and try again"
    return result

def generate_text_with_image(prompt: str, image_bytes: BytesIO) -> str:
    """generate text from prompt and image"""
    img = PIL.Image.open(image_bytes)
    try:
        response = model_vision.generate_content([prompt, img])
        result = response.text
    except Exception as e:
        result = f"Something went wrong!\n{repr(e)}\n\nThe content you entered may be inappropriate, please modify it and try again"
    return result

# --- generate_content_stream (standalone streaming) can remain for textbook commands if needed ---
# Or you could potentially remove it if ChatConversation handles all streaming needs
def generate_content_stream(prompt: str):
    """Generates content in streaming mode, yielding chunks of the response."""
    try:
        response_stream = model_usual.generate_content(prompt, stream=True)
        for chunk in response_stream:
            # Add safety check for empty chunks or parts
            if chunk.parts:
                 yield chunk.text
            else:
                 # Handle potential empty safety-related chunks if necessary
                 print("Received empty chunk part, possibly due to safety settings.")
                 yield "" # Yield empty string or handle differently
    except Exception as e:
        error_message = f"Something went wrong!\n{repr(e)}\n\nThe content you entered may be inappropriate, please modify it and try again"
        yield error_message


# --- ChatConversation Class Modification ---
class ChatConversation:
    """
    Manages an ongoing chat session with history, supporting streaming responses.
    """
    def __init__(self) -> None:
        print("Initializing new ChatConversation") # Log init
        # Make sure model_usual is accessible here
        self.chat = model_usual.start_chat(history=[])

    def send_message(self, prompt: str) -> str:
        """Sends a message and returns the *full* response text (non-streaming)."""
        print(f"ChatConversation.send_message called (History Length: {self.history_length})")
        if prompt.lower().strip() == "/new": # Make check case-insensitive and trim whitespace
            self.__init__() # Re-initialize chat history
            result = " নতুন চ্যাট শুরু করা হয়েছে (New chat started)." # Changed response text
        else:
            try:
                # Use the existing chat instance to send the message
                response = self.chat.send_message(prompt)
                result = response.text
            except Exception as e:
                print(f"Error in ChatConversation.send_message: {e}") # Log error
                result = f"Something went wrong!\n{repr(e)}\n\nPlease try again or use /new to start a fresh chat." # Modified error
        # print(f"ChatConversation.send_message response (first 100): {result[:100]}")
        return result

    # --- NEW STREAMING METHOD ---
    def send_message_stream(self, prompt: str) -> Iterator[str]:
        """Sends a message and yields response chunks (streaming)."""
        print(f"ChatConversation.send_message_stream called (History Length: {self.history_length})")
        if prompt.lower().strip() == "/new": # Handle /new here too for consistency
            self.__init__()
            yield " নতুন চ্যাট শুরু করা হয়েছে (New chat started)." # Yield the response for /new
            return # Stop iteration after yielding

        try:
            # Use stream=True with the existing chat instance
            response_stream = self.chat.send_message(prompt, stream=True)
            for chunk in response_stream:
                 # Add safety check for empty chunks or parts
                if chunk.parts:
                     yield chunk.text
                else:
                    print("Received empty chunk part in chat stream, possibly due to safety settings.")
                    yield "" # Yield empty string or handle differently
        except Exception as e:
            print(f"Error in ChatConversation.send_message_stream: {e}") # Log error
            yield f"Something went wrong during streaming!\n{repr(e)}\n\nPlease try again or use /new." # Yield error message

    @property
    def history(self):
        return self.chat.history

    @property
    def history_length(self):
        # The history object stores pairs (user, model), so length is pairs * 2
        return len(self.chat.history)

# --- if __name__ == "__main__": remains the same ---
if __name__ == "__main__":
    list_models()
