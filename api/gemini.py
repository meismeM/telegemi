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
# api/gemini.py
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
    print(list_models())
