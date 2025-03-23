from flask import Flask, render_template, request, jsonify, Response
from openai import OpenAI
import os
import logging
import secrets
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
    
    # Set the secret key (generate one if not provided in environment variables)
    app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(16))
    logger.debug(f"Secret Key: {app.config['SECRET_KEY']}")

    logger.debug(f"Template folder path: {app.template_folder}")

    # Initialize the OpenAI client using the API key from environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    client = OpenAI(api_key=api_key)

    # Debug: Print the API key to verify it's loaded correctly
    print("API Key loaded successfully.")

    # Store conversation history in a dictionary (keyed by session ID)
    conversation_histories = {}

    # Function to truncate conversation history (based on message count)
    def truncate_conversation(conversation_history, max_messages=10):
        while len(conversation_history) > max_messages:
            conversation_history.pop(1)  # Remove the oldest user-assistant pair (keep system message)
        return conversation_history

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
        session_id = request.args.get("session_id", "default")  # Use a session ID to track conversations
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
            # Initialize conversation history for the session if it doesn't exist
            if session_id not in conversation_histories:
                conversation_histories[session_id] = [
                    {"role": "system", "content": "You are a helpful assistant that responds in the same language as the user's input."}
                ]

            # Add user message to conversation history
            conversation_histories[session_id].append({"role": "user", "content": user_input})

            # Truncate conversation history if it exceeds the message limit
            conversation_histories[session_id] = truncate_conversation(conversation_histories[session_id], max_messages=10)

            logger.debug("Sending request to GPT-4 API...")
            response = client.chat.completions.create(
                model="gpt-4",  # Use "gpt-4" or "gpt-4-1106-preview"
                messages=conversation_histories[session_id],
                stream=True  # Enable streaming
            )

            # Stream the response back to the client
            def generate():
                full_response = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        chunk_content = chunk.choices[0].delta.content
                        full_response += chunk_content
                        yield f"data: {chunk_content}\n\n".encode('utf-8')  # Send each chunk individually
                yield "data: [END]\n\n".encode('utf-8')  # Signal the end of the response

                # Add assistant's response to conversation history
                conversation_histories[session_id].append({"role": "assistant", "content": full_response})

            return Response(generate(), mimetype="text/event-stream; charset=utf-8")
        except Exception as e:
            logger.error(f"Error during chat: {e}")
            return jsonify({"response": "An error occurred while processing your request."}), 500

    return app

# Create the Flask app
app = create_app()

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)