import os
from re import split

""" Required """

BOT_TOKEN = os.environ.get("BOT_TOKEN")
# Ensure GOOGLE_API_KEY is correctly parsed; handle if it's a single key not needing split
google_api_key_env = os.getenv("GOOGLE_API_KEY", '')
GOOGLE_API_KEY = split(r'[ ,;，；]+', google_api_key_env) if google_api_key_env else []


""" Optional """

ALLOWED_USERS_ENV = os.getenv("ALLOWED_USERS", '')
ALLOWED_USERS = [u.strip() for u in split(r'[ ,;，；]+', ALLOWED_USERS_ENV.replace("@", "").lower()) if u.strip()]

#Whether to push logs and enable some admin commands
IS_DEBUG_MODE = os.getenv("IS_DEBUG_MODE", '1') # '0' or '1'
#The target account that can execute administrator instructions and log push can use /get_my_info to obtain the ID.
ADMIN_ID = os.getenv("ADMIN_ID", "1470186445") # Ensure this is a string

CHANNEL_ID = os.getenv("CHANNEL_ID","-1002238005293") # Ensure this is a string

#Determines whether to verify identity. If 0, anyone can use the bot. It is enabled by default.
AUCH_ENABLE = os.getenv("AUCH_ENABLE", "0") # '0' or '1'

""" read https://ai.google.dev/api/rest/v1/GenerationConfig """
generation_config = {
    "max_output_tokens": 8192,
    "temperature": 0.7, # Added a common default
}

""" read https://ai.google.dev/api/rest/v1/HarmCategory """
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE"
    },
]

""" Interactive Keyboard Settings """
AVAILABLE_TEXTBOOKS_FOR_KEYBOARD = {
    "economics9": "Economics G9",  # id: Display Name
    "history9": "History G9",
    # Add more textbooks here as they become available and indexed
    # "math9": "Mathematics G9" # Example
}
