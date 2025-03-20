"""from flask import Flask, render_template, request
from .handle import handle_message
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        try:
            update = request.json
            logging.info("Received update: %s", update)
            if not update or "update_id" not in update:
                logging.warning("Invalid or incomplete update: %s", update)
                return "Invalid request data", 400
            handle_message(update)
            return "ok", 200
        except Exception as e:
            logging.error("Error handling request: %s", e)
            return "Internal server error", 500
    return render_template("status.html")

@app.route("/health", methods=["GET"])
def health_check():
    return {"status": "ok"}, 200"""

# api/index.py
from flask import Flask, render_template, request
from .handle import handle_message
import logging
from .textbook_processor import load_textbook # Import load_textbook

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# [!HIGHLIGHT!] Textbook loading section in app initialization
with app.app_context():
    print("Starting textbook loading during app initialization...") # Added start log
    try:
        load_textbook("economics9", "economics9.pdf")
        load_textbook("history9", "history9.pdf")
        print("Textbooks loaded successfully during app initialization.") # Success log
    except Exception as e:
        print(f"ERROR: Textbook loading failed during app initialization: {e}") # Error log with exception
    print("Textbook loading process completed (see messages above for status).") # Completion log

@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        try:
            update = request.json
            logging.info("Received update: %s", update)
            if not update or "update_id" not in update:
                logging.warning("Invalid or incomplete update: %s", update)
                return "Invalid request data", 400
            handle_message(update)
            return "ok", 200
        except Exception as e:
            logging.error("Error handling request: %s", e)
            # [!HIGHLIGHT!] Log the exception type and arguments (for more details)
            logging.error(f"Exception details: Type: {type(e)}, Args: {e.args}") # ADD THIS LINE
            return "Internal server error", 500
    return render_template("status.html") # Corrected indentation here

@app.route("/health", methods=["GET"])
def health_check():
    return {"status": "ok"}, 200

""" # api/index.py
from flask import Flask, render_template, request
from .handle import handle_message
import logging
from .textbook_processor import load_textbook # Import load_textbook (though not directly used here anymore)

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# [!HIGHLIGHT!] REMOVED textbook loading from here - now lazy loaded

@app.route("/", methods=["POST", "GET"])
def home():
    # ... (rest of your home function - no changes needed here) ...
    if request.method == "POST":
        try:
            update = request.json
            logging.info("Received update: %s", update)
            if not update or "update_id" not in update:
                logging.warning("Invalid or incomplete update: %s", update)
                return "Invalid request data", 400
            handle_message(update)
            return "ok", 200
        except Exception as e:
            logging.error("Error handling request: %s", e)
            logging.error(f"Exception details: Type: {type(e)}, Args: {e.args}")
            return "Internal server error", 500
    return render_template("status.html")

@app.route("/health", methods=["GET"])
def health_check():
    return {"status": "ok"}, 200"""
