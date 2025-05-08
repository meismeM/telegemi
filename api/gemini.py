# api/gemini.py
from io import BytesIO
from typing import Dict, Iterator, Union # Added Union

import google.generativeai as genai
import PIL.Image

from .config import GOOGLE_API_KEY, generation_config, safety_settings

# Configure Gemini API
if GOOGLE_API_KEY and GOOGLE_API_KEY[0]: # Check if API key list is not empty and first key exists
    genai.configure(api_key=GOOGLE_API_KEY[0])
else:
    print("WARNING: GOOGLE_API_KEY is not configured or empty. Gemini functions will fail.")
    # Optionally, raise an error or set a flag to disable Gemini features
    # raise ValueError("GOOGLE_API_KEY is not configured.")

# Initialize models (consider error handling if API key is missing)
try:
    model_usual = genai.GenerativeModel(
        model_name="gemini-1.5-flash-latest", # Use specific or latest version
        generation_config=generation_config,
        safety_settings=safety_settings)

    model_vision = genai.GenerativeModel(
        model_name="gemini-1.5-flash-latest", # Use specific or latest version for vision too
        generation_config=generation_config,
        safety_settings=safety_settings)
except Exception as e:
    print(f"ERROR configuring Gemini models: {e}. Ensure GOOGLE_API_KEY is valid.")
    # Fallback or mock models if needed for testing without API key
    model_usual = None
    model_vision = None


def list_models() -> None:
    """Lists available Gemini models."""
    if not genai.api_key:
        print("Gemini API key not configured. Cannot list models.")
        return
    print("Available Gemini Models (supporting generateContent):")
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            print(f"- {m.name}")

def generate_content(prompt: str) -> str: 
    """Generates text from a prompt (non-streaming)."""
    if not model_usual:
        return "Error: Gemini text model is not initialized. Check API key and configuration."
    try:
        response = model_usual.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API error in generate_content: {e}")
        return f"Oops! Something went wrong with the AI: {type(e).__name__}. Please try again later or rephrase your request."

def generate_text_with_image(prompt: str, image_bytes: BytesIO) -> str:
    """Generates text from a prompt and an image."""
    if not model_vision:
        return "Error: Gemini vision model is not initialized. Check API key and configuration."
    try:
        img = PIL.Image.open(image_bytes)
        response = model_vision.generate_content([prompt, img])
        return response.text
    except Exception as e:
        print(f"Gemini API error in generate_text_with_image: {e}")
        return f"Oops! Something went wrong with processing the image and text: {type(e).__name__}. Please try again."

def generate_content_stream(prompt: str) -> Iterator[str]:
    """Generates content in streaming mode, yielding chunks of the response."""
    if not model_usual:
        yield "Error: Gemini text model is not initialized. Check API key and configuration."
        return
    try:
        response_stream = model_usual.generate_content(prompt, stream=True) 
        for chunk in response_stream: 
            if chunk.text: # Ensure text exists in the chunk
                yield chunk.text
    except Exception as e:
        print(f"Gemini API streaming error in generate_content_stream: {e}")
        yield f"Oops! A streaming error occurred with the AI: {type(e).__name__}. Please try again."


class ChatConversation:
    """Manages an ongoing chat session with Gemini."""

    def __init__(self) -> None:
        if not model_usual:
            print("WARNING: ChatConversation initialized but Gemini model_usual is not available.")
            self.chat = None # Or a mock chat object
        else:
            self.chat = model_usual.start_chat(history=[])

    def send_message(self, prompt: str, stream: bool = False) -> Union[str, Iterator[str]]:
        """
        Sends a message to the chat.
        Returns a string for non-streaming, or an iterator for streaming.
        """
        if not self.chat:
            no_chat_msg = "Error: Chat session not initialized (Gemini model might be unavailable)."
            return iter([no_chat_msg]) if stream else no_chat_msg

        if prompt.startswith("/new"):
            self.__init__() # Start a fresh chat
            fresh_chat_msg = "We're having a fresh chat now!"
            return iter([fresh_chat_msg]) if stream else fresh_chat_msg
        
        try:
            if stream:
                response_stream = self.chat.send_message(prompt, stream=True)
                def stream_generator():
                    for chunk in response_stream:
                        if chunk.text:
                            yield chunk.text
                return stream_generator()
            else: # Non-streaming
                response = self.chat.send_message(prompt)
                return response.text
        except Exception as e:
            print(f"Gemini API error in ChatConversation.send_message: {e}")
            error_message = f"Oops! AI conversation error: {type(e).__name__}."
            return iter([error_message]) if stream else error_message

    @property
    def history(self):
        return self.chat.history if self.chat else []

    @property
    def history_length(self):
        return len(self.chat.history) if self.chat else 0


if __name__ == "__main__":
    list_models()
    # Example usage (requires GOOGLE_API_KEY to be set in environment)
    # if model_usual:
    #     print("\nTesting generate_content:")
    #     print(generate_content("Tell me a short joke."))
    #     print("\nTesting ChatConversation (non-streaming):")
    #     chat_session = ChatConversation()
    #     print(chat_session.send_message("Hello Gemini!"))
    #     print(chat_session.send_message("What is the capital of France?"))
    #     print("\nTesting ChatConversation (streaming):")
    #     chat_session_stream = ChatConversation()
    #     print(next(chat_session_stream.send_message("/new", stream=True))) # Clear for stream test
    #     stream_response = chat_session_stream.send_message("Explain quantum physics in one sentence.", stream=True)
    #     for chunk in stream_response:
    #         print(chunk, end='', flush=True)
    #     print()