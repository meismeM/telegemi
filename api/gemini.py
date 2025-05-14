# api/gemini.py
from io import BytesIO
import os # For GOOGLE_API_KEY check if needed, though config.py handles it primarily

import google.generativeai as genai
import PIL.Image

from .config import GOOGLE_API_KEY, generation_config, safety_settings
from .printLog import send_log # For logging critical errors

# Ensure GOOGLE_API_KEY is not empty and select the first key
# config.py already splits it, so GOOGLE_API_KEY should be a list
CONFIGURED_API_KEY = None
if GOOGLE_API_KEY and isinstance(GOOGLE_API_KEY, list) and len(GOOGLE_API_KEY) > 0 and GOOGLE_API_KEY[0]:
    CONFIGURED_API_KEY = GOOGLE_API_KEY[0]
else:
    # Log this critical issue, as the bot won't function
    log_message = "CRITICAL WARNING: GOOGLE_API_KEY is not configured properly or is empty in config.py. Gemini models cannot be initialized."
    print(log_message)
    send_log(log_message) # Also send to Telegram admin log if possible


# Use model names as originally specified by the user
MODEL_NAME_DEFAULT = "gemini-2.0-flash" # User's original model
# MODEL_NAME_DEFAULT = "gemini-1.5-flash-latest" # Alternative modern option

model_usual = None
model_vision = None

if CONFIGURED_API_KEY:
    try:
        genai.configure(api_key=CONFIGURED_API_KEY)
        
        model_usual = genai.GenerativeModel(
            model_name=MODEL_NAME_DEFAULT, 
            generation_config=generation_config,
            safety_settings=safety_settings)

        model_vision = genai.GenerativeModel( # Assuming vision also uses the same base model or a vision-capable variant
            model_name=MODEL_NAME_DEFAULT, # Or "gemini-pro-vision" if that's intended and available
            generation_config=generation_config,
            safety_settings=safety_settings)
        print(f"Gemini models ('{MODEL_NAME_DEFAULT}') initialized successfully.")
        send_log(f"Gemini models ('{MODEL_NAME_DEFAULT}') initialized successfully.")

    except Exception as e:
        error_log_msg = f"CRITICAL ERROR initializing Gemini models with name '{MODEL_NAME_DEFAULT}': {e}. Check API key and model availability."
        print(error_log_msg)
        send_log(error_log_msg)
        # Models will remain None
else:
    # This case is already logged above. Models remain None.
    pass


def _parse_gemini_response(response, context_for_error=""):
    """Helper to consistently parse Gemini responses and handle errors/empty content."""
    try:
        # Check for blocking first
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            block_reason_msg = f"Content generation blocked. Reason: {response.prompt_feedback.block_reason}."
            if response.prompt_feedback.safety_ratings:
                block_reason_msg += f" Safety Ratings: {response.prompt_feedback.safety_ratings}"
            send_log(f"Gemini Safety Block {context_for_error}: {block_reason_msg}")
            return f"I'm sorry, I can't generate a response for that request due to content safety guidelines. [{response.prompt_feedback.block_reason}]"

        # Try to extract text from candidates (common structure)
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                # Concatenate text from all parts
                text_parts = [part.text for part in candidate.content.parts if hasattr(part, 'text')]
                if text_parts:
                    return "".join(text_parts)
            # Check finish reason for safety even if parts are empty
            if candidate.finish_reason and str(candidate.finish_reason).upper() not in ["STOP", "UNSPECIFIED", "MAX_TOKENS", "NULL"]: # FINISH_REASON_STOP = 1
                finish_reason_msg = f"Content generation may have been interrupted or altered. Reason: {candidate.finish_reason}."
                if candidate.safety_ratings:
                    finish_reason_msg += f" Safety Ratings: {candidate.safety_ratings}"
                send_log(f"Gemini Finish Reason {context_for_error}: {finish_reason_msg}")
                # If text was already extracted, append this as a warning. If not, this becomes the error.
                # For now, if text_parts was empty and finish_reason is concerning, return the reason.
                if not text_parts:
                     return f"I encountered an issue: {finish_reason_msg} Please try rephrasing your request."


        # Fallback for older SDKs or different response structures (less common now)
        if hasattr(response, 'text') and response.text:
            return response.text
        if hasattr(response, 'parts') and response.parts: # Direct parts attribute
             return "".join(part.text for part in response.parts if hasattr(part, 'text'))
        
        # If no text found after all checks
        send_log(f"Gemini Warning {context_for_error}: No text content found in response. Full response: {response}")
        return "I received an empty response. Please try rephrasing your request or try again later."

    except Exception as e:
        send_log(f"Error parsing Gemini response {context_for_error}: {e}. Response: {response}")
        return f"An unexpected error occurred while processing the response from the AI. Details: {e}"


def generate_content(prompt: str) -> str:
    """Generate text from prompt (non-streaming)."""
    if not model_usual:
        no_model_msg = "Error: Text generation model is not available. Please check configuration and logs."
        send_log(no_model_msg + f" (Prompt: {prompt[:100]}...)")
        return no_model_msg
    try:
        response = model_usual.generate_content(prompt)
        return _parse_gemini_response(response, context_for_error=f"for non-streaming prompt: {prompt[:100]}...")
    except Exception as e:
        error_msg = f"Something went wrong generating content!\n{repr(e)}"
        send_log(f"Gemini generate_content EXCEPTION for prompt '{prompt[:100]}...': {error_msg}")
        return error_msg


def generate_text_with_image(prompt: str, image_bytes: BytesIO) -> str:
    """Generate text from prompt and image (non-streaming)."""
    if not model_vision:
        no_model_msg = "Error: Vision model is not available. Please check configuration and logs."
        send_log(no_model_msg + f" (Prompt: {prompt[:100]}...)")
        return no_model_msg
    try:
        img = PIL.Image.open(image_bytes)
        # For multimodal, content should be a list: [text_prompt, image_object]
        response = model_vision.generate_content([prompt, img]) 
        return _parse_gemini_response(response, context_for_error=f"for image prompt: {prompt[:100]}...")
    except Exception as e:
        error_msg = f"Something went wrong generating text with image!\n{repr(e)}"
        send_log(f"Gemini generate_text_with_image EXCEPTION for prompt '{prompt[:100]}...': {error_msg}")
        return error_msg


def generate_content_stream(prompt: str):
    """Generates content in streaming mode, yielding chunks of the response."""
    if not model_usual:
        no_model_msg = "Error: Text generation model for streaming is not available. Check logs."
        send_log(no_model_msg + f" (Prompt: {prompt[:100]}...)")
        yield no_model_msg
        return
    
    try:
        response_stream = model_usual.generate_content(prompt, stream=True)
        for chunk in response_stream:
            # Parsing logic adapted from _parse_gemini_response for chunks
            chunk_text = ""
            blocked_by_safety = False

            if chunk.prompt_feedback and chunk.prompt_feedback.block_reason:
                block_reason_msg = f"Streaming blocked. Reason: {chunk.prompt_feedback.block_reason}."
                if chunk.prompt_feedback.safety_ratings:
                    block_reason_msg += f" Safety: {chunk.prompt_feedback.safety_ratings}"
                send_log(f"Gemini Stream Safety Block for prompt '{prompt[:100]}...': {block_reason_msg}")
                yield f"\n\n[I'm sorry, further generation for this request was stopped due to content safety guidelines: {chunk.prompt_feedback.block_reason}]"
                blocked_by_safety = True
                break # Stop streaming if definitively blocked

            if chunk.candidates:
                candidate = chunk.candidates[0]
                if candidate.content and candidate.content.parts:
                    text_parts = [part.text for part in candidate.content.parts if hasattr(part, 'text')]
                    chunk_text = "".join(text_parts)
                
                # Check finish reason in chunks too
                if candidate.finish_reason and str(candidate.finish_reason).upper() not in ["STOP", "UNSPECIFIED", "MAX_TOKENS", "NULL"]:
                    finish_reason_msg = f"Stream interrupted/altered. Reason: {candidate.finish_reason}."
                    send_log(f"Gemini Stream Finish Reason for prompt '{prompt[:100]}...': {finish_reason_msg}")
                    if not chunk_text: # If no text in this chunk but a concerning finish reason
                        yield f"\n\n[Stream may have been affected: {candidate.finish_reason}]"
                    if str(candidate.finish_reason).upper() == "SAFETY": # Explicit safety stop
                         blocked_by_safety = True # Ensure loop breaks

            elif hasattr(chunk, 'text') and chunk.text: # Simpler structure (less likely for streams)
                 chunk_text = chunk.text
            elif hasattr(chunk, 'parts') and chunk.parts:
                 chunk_text = "".join(part.text for part in chunk.parts if hasattr(part, 'text'))

            if chunk_text:
                yield chunk_text
            
            if blocked_by_safety:
                break # Exit outer loop if safety block occurred

    except Exception as e:
        error_message = f"Streaming error!\n{repr(e)}"
        send_log(f"Gemini generate_content_stream EXCEPTION for prompt '{prompt[:100]}...': {error_message}")
        yield error_message


class ChatConversation:
    """Manages an ongoing chat conversation, with streaming responses."""
    def __init__(self) -> None:
        self.chat = None
        self.user_prompt_history = [] # For tracking user turns for /new logic

        if not model_usual:
            log_msg = "Warning: ChatConversation initialized, but 'model_usual' is None. Chat will not function."
            print(log_msg)
            send_log(log_msg)
        else:
            try:
                self.chat = model_usual.start_chat(history=[])
            except Exception as e:
                log_msg = f"Error starting chat session in ChatConversation: {e}"
                print(log_msg)
                send_log(log_msg)
                self.chat = None # Ensure chat is None if start_chat fails

    def send_message(self, prompt: str): 
        """Sends a message to the chat and yields response chunks (streams)."""
        if not self.chat:
            no_chat_msg = "Error: Chat model is not available or session not started. Cannot process message."
            send_log(no_chat_msg + f" (Prompt: {prompt[:100]}...)")
            yield no_chat_msg
            return

        current_prompt_lower = prompt.lower().strip()
        if current_prompt_lower != "/new":
             self.user_prompt_history.append(prompt)

        if current_prompt_lower == "/new":
            if model_usual: # Re-check model_usual before trying to start a new chat
                try:
                    self.chat = model_usual.start_chat(history=[]) 
                    self.user_prompt_history = [] 
                    yield "We're having a fresh chat now." 
                except Exception as e:
                    err_msg = f"Error resetting chat with /new: {e}"
                    send_log(err_msg)
                    yield err_msg
            else: # Should ideally not be reached if self.chat was valid before
                yield "Error: Cannot start a new chat as the underlying model is unavailable."
            return 

        try:
            # Use the same streaming logic as generate_content_stream
            response_stream = self.chat.send_message(prompt, stream=True)
            for chunk in response_stream:
                chunk_text = ""
                blocked_by_safety = False

                # Check for prompt feedback leading to blocking
                if chunk.prompt_feedback and chunk.prompt_feedback.block_reason:
                    block_reason_msg = f"Chat stream blocked. Reason: {chunk.prompt_feedback.block_reason}."
                    send_log(f"Gemini Chat Safety Block for prompt '{prompt[:100]}...': {block_reason_msg}")
                    yield f"\n\n[I'm sorry, my response was stopped due to content safety: {chunk.prompt_feedback.block_reason}]"
                    blocked_by_safety = True
                    break 

                if chunk.candidates:
                    candidate = chunk.candidates[0]
                    if candidate.content and candidate.content.parts:
                        text_parts = [part.text for part in candidate.content.parts if hasattr(part, 'text')]
                        chunk_text = "".join(text_parts)
                    
                    if candidate.finish_reason and str(candidate.finish_reason).upper() not in ["STOP", "UNSPECIFIED", "MAX_TOKENS", "NULL"]:
                        finish_reason_str = str(candidate.finish_reason).upper()
                        #send_log(f"Gemini Chat Stream Finish Reason '{finish_reason_str}' for prompt '{prompt[:100]}...'")
                        if not chunk_text and finish_reason_str != "SAFETY": # If no text and not already a safety message
                            yield f"\n\n[Chat stream affected: {candidate.finish_reason}]"
                        if finish_reason_str == "SAFETY":
                            blocked_by_safety = True # Ensure loop breaks if safety is the explicit finish reason
                
                # Fallbacks for simpler structures (less likely in new SDK streams)
                elif hasattr(chunk, 'text') and chunk.text: chunk_text = chunk.text
                elif hasattr(chunk, 'parts') and chunk.parts: chunk_text = "".join(part.text for part in chunk.parts if hasattr(part, 'text'))


                if chunk_text:
                    yield chunk_text
                
                if blocked_by_safety:
                    # Optionally, reset chat history if severely blocked
                    # self.chat = model_usual.start_chat(history=[])
                    # self.user_prompt_history = []
                    break
        except Exception as e:
            error_message = f"Chat streaming error!\n{repr(e)}"
            send_log(f"Gemini ChatConversation.send_message EXCEPTION for prompt '{prompt[:100]}...': {error_message}")
            yield error_message
            # Optionally reset chat on severe errors to prevent broken state
            # if model_usual: self.chat = model_usual.start_chat(history=[])
            # self.user_prompt_history = []
            # yield "Chat history has been reset due to an error."

    @property
    def history(self):
        return self.chat.history if self.chat else []

    @property
    def history_length(self):
        # Gemini's chat.history includes both user and model turns.
        # Number of user messages can be len(self.user_prompt_history)
        return len(self.chat.history) if self.chat else 0


if __name__ == "__main__":
    print("--- Gemini Module (__main__) ---")
    if CONFIGURED_API_KEY and model_usual: # Check if models were actually initialized
        print("\n--- Listing Models ---")
        # list_models() # This is a function in command.py, not here directly.
        # For local testing of this module, can call genai's list_models
        try:
            print("Available GenAI Models (supporting generateContent):")
            for m in genai.list_models():
                if "generateContent" in m.supported_generation_methods:
                    print(f"- {m.name}")
        except Exception as e_list:
            print(f"Error listing models directly in gemini.py __main__: {e_list}")

        print("\n--- Testing generate_content (non-streaming) ---")
        print(f"Test Joke: {generate_content('Tell me a short, clean joke.')}")
        
        print("\n--- Testing ChatConversation (streaming) ---")
        chat_test = ChatConversation()
        if chat_test.chat: # Proceed only if chat session is valid
            print("User: Hello")
            full_bot_reply = ""
            for chunk_item in chat_test.send_message("Hello, how are you today?"):
                full_bot_reply += chunk_item
                print(f"Bot chunk: '{chunk_item}'")
            print(f"Bot full reply: {full_bot_reply}\n------")
            
            print("User: What is the capital of France?")
            full_bot_reply = ""
            for chunk_item in chat_test.send_message("What is the capital of France?"):
                full_bot_reply += chunk_item
                print(f"Bot chunk: '{chunk_item}'")
            print(f"Bot full reply: {full_bot_reply}\n------")
            print(f"Chat history length: {chat_test.history_length}")
            
            print("User: /new")
            full_bot_reply = ""
            for chunk_item in chat_test.send_message("/new"): 
                 full_bot_reply += chunk_item
                 print(f"Bot chunk: '{chunk_item}'")
            print(f"Bot full reply: {full_bot_reply}\n------")
            print(f"Chat history length after /new: {chat_test.history_length}")
        else:
            print("ChatConversation test skipped as chat session is not available.")
    else:
        print("Skipping __main__ tests as GOOGLE_API_KEY is not configured or models failed to initialize.")
