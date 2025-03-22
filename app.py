# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, Response, g
from openai import OpenAI
import time
import os
import logging
from dotenv import load_dotenv
from langdetect import detect, DetectorFactory

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Ensure consistent language detection
DetectorFactory.seed = 0

def create_app():
    app = Flask(__name__, template_folder="templates")
    logger.debug(f"Template folder path: {app.template_folder}")

    # Initialize the OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    client = OpenAI(api_key=api_key)

    # Debug: Print the API key to verify it's loaded correctly
    print("API Key:", api_key)

    # Store conversation context in Flask's g object
    @app.before_request
    def initialize_context():
        if not hasattr(g, 'context'):
            g.context = ""
        if not hasattr(g, 'MAX_CONTEXT_LENGTH'):
            g.MAX_CONTEXT_LENGTH = 500  # Reduce context size
        logger.debug(f"Context initialized: {g.context}")

    # Routes
    @app.route("/")
    def home():
        logger.debug("Rendering home page...")
        return render_template("index.html")

    @app.route("/about")
    def about():
        logger.debug("Rendering about page...")
        return render_template("about.html")

    @app.route("/services")
    def services():
        logger.debug("Rendering services page...")
        return render_template("services.html")

    @app.route("/contact")
    def contact():
        logger.debug("Rendering contact page...")
        return render_template("contact.html")

    @app.route("/chat", methods=["GET"])
    def chat_stream():
        user_input = request.args.get("message", "").strip()
        lang = detect(user_input) if user_input else "en"  # Detect language or default to English
        logger.debug(f"Received user input: {user_input} (Language: {lang})")

        # Handle exit command
        if user_input.lower() == "exit":
            logger.debug("Exit command received.")
            return jsonify({"response": "Goodbye!"})

        # Check if the input contains words similar to other languages
        if lang not in ["ar", "en"]:
            # If the detected language is not Arabic or English, force English
            lang = "en"
            logger.debug(f"Input contains non-Arabic/English words. Forcing response in English.")

        try:
            logger.debug("Sending request to GPT-4 API...")
            response = client.chat.completions.create(
                model="gpt-4",  # Use "gpt-4" or "gpt-4-1106-preview"
                messages=[
                    {"role": "system", "content": f"You are a helpful assistant that responds in the same language as the user's input. The detected language is {lang}. Ensure that punctuation marks are placed at the end of the sentence, not at the beginning."},
                    {"role": "user", "content": user_input}
                ],
                stream=True  # Enable streaming
            )

            # Stream the response back to the client
            def generate():
                full_response = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                yield f"data: {full_response}\n\n".encode('utf-8')  # Send the full response
                yield "data: [END]\n\n".encode('utf-8')  # Signal the end of the response

            return Response(generate(), mimetype="text/event-stream; charset=utf-8")
        except Exception as e:
            logger.error(f"Error during chat: {e}")
            return jsonify({"response": "An error occurred while processing your request."}), 500

    return app

# Create the Flask app
app = create_app()

