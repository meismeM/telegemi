# api/index.py
from flask import Flask, render_template, request
from .handle import handle_message
import logging
from .textbook_processor import get_textbook_content # Import get_textbook_content - Corrected import

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Textbook loading is now lazy-loaded on demand via textbook_processor.py
# No pre-loading needed here.

@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        try:
            update = request.json
            logging.info("Received update: %s", update)
            if not update or ("message" not in update and "callback_query" not in update): # Check for message or callback_query
                logging.warning("Invalid or incomplete update (missing message or callback_query): %s", update)
                return "Invalid request data", 400
            handle_message(update)
            return "ok", 200
        except Exception as e:
            logging.error("Error handling request: %s", e, exc_info=True) # Added exc_info for full traceback
            logging.error(f"Exception details: Type: {type(e)}, Args: {e.args}")
            return "Internal server error", 500
    return render_template("status.html")

@app.route("/health", methods=["GET"])
def health_check():
    return {"status": "ok"}, 200

    