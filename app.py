from flask import Flask, render_template, request, jsonify, Response, g
from openai import OpenAI
import time
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

    # Template for the prompt
    template = """
    Answer the question below.

    Here is the conversation history: {context}

    Question: {question}

    Answer:
    """

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
        logger.debug(f"Received user input: {user_input}")

        # Handle exit command
        if user_input.lower() == "exit":
            logger.debug("Exit command received.")
            return jsonify({"response": "Goodbye!"})

        # Limit the context size to avoid excessive memory usage
        if len(g.context) > g.MAX_CONTEXT_LENGTH:
            g.context = g.context[-g.MAX_CONTEXT_LENGTH:]
            logger.debug(f"Context trimmed to: {g.context}")

        try:
            logger.debug("Sending request to GPT-4 API...")
            response = client.chat.completions.create(
                model="gpt-4",  # Use "gpt-4" or "gpt-4-1106-preview" depending on your access
                messages=[
                    {"role": "system", "content": template.format(context=g.context, question=user_input)},
                    {"role": "user", "content": user_input}
                ],
                stream=True  # Enable streaming
            )

            # Stream the response back to the client
            def generate():
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield f"data: {chunk.choices[0].delta.content}\n\n"
                        time.sleep(0.1)  # Simulate a delay between words
                yield "data: [END]\n\n"  # Signal the end of the response

            return Response(generate(), mimetype="text/event-stream")
        except Exception as e:
            logger.error(f"Error during chat: {e}")
            return jsonify({"response": "An error occurred while processing your request."}), 500

    return app

# Create the Flask app
app = create_app()