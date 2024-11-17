from flask import Flask, render_template, request
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
    return {"status": "ok"}, 200