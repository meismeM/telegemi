from .config import IS_DEBUG_MODE,ADMIN_ID
from .telegram import send_message,send_imageMessage # Assuming these are correctly defined in telegram.py
import datetime

admin_id_str = ADMIN_ID # Ensure ADMIN_ID from config is treated as string if needed for send_message
is_debug_mode_str = IS_DEBUG_MODE # Ensure IS_DEBUG_MODE from config is '0' or '1'

def send_log(text: str):
    if is_debug_mode_str == "1" and admin_id_str:
        try:
            # Attempt to convert admin_id to int for send_message if it expects int
            admin_id_int = int(admin_id_str)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            send_message(admin_id_int, f"LOG [{timestamp}]:\n{text}")
        except ValueError:
            print(f"ERROR: ADMIN_ID '{admin_id_str}' is not a valid integer for sending logs.")
        except Exception as e:
            print(f"ERROR sending log: {e}")


def send_image_log(text: str, imageID: str):
    if is_debug_mode_str == "1" and admin_id_str:
        try:
            admin_id_int = int(admin_id_str)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            send_imageMessage(admin_id_int, f"LOG [{timestamp}]:\n{text}", imageID)
        except ValueError:
            print(f"ERROR: ADMIN_ID '{admin_id_str}' is not a valid integer for sending image logs.")
        except Exception as e:
            print(f"ERROR sending image log: {e}")