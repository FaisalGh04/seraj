function sendMessage() {
    const userInput = document.getElementById("user-input");
    const message = userInput.value.trim();
    if (message === "") return;

    const chatMessages = document.getElementById("chat-messages");

    // Add user message
    const userMessage = document.createElement("div");
    userMessage.className = "message sent";
    userMessage.innerHTML = `<p>${message}</p>`;
    chatMessages.appendChild(userMessage);

    userInput.value = "";

    // Create a new message element for the AI's response
    const botMessage = document.createElement("div");
    botMessage.className = "message received";
    botMessage.innerHTML = `<p>AI: </p>`;
    chatMessages.appendChild(botMessage);

    // Detect the language of the user's input
    let lang = "en"; // Default to English
    try {
        lang = detectLanguage(message); // Detect language using a library or API
    } catch (error) {
        console.error("Language detection failed:", error);
    }

    // Add Arabic class if the language is Arabic
    if (lang === "ar") {
        botMessage.classList.add("arabic");
    }

    // Create an EventSource to listen for the response
    const eventSource = new EventSource(`/chat?message=${encodeURIComponent(message)}&lang=${encodeURIComponent(lang)}`);

    eventSource.onmessage = (event) => {
        if (event.data === "[END]") {
            // Close the EventSource when the response ends
            eventSource.close();
        } else {
            // Display the AI's response
            const textSpan = botMessage.querySelector("p");
            textSpan.textContent += event.data;
            chatMessages.scrollTop = chatMessages.scrollHeight; // Auto-scroll
        }
    };

    eventSource.onerror = (error) => {
        console.error("EventSource failed:", error);
        eventSource.close();
    };
}

function detectLanguage(text) {
    // Use a language detection library or API here
    // Example: Use langdetect library (https://github.com/Mimino666/langdetect)
    // You can also use an external API like Google Cloud Translation API
    return "en"; // Placeholder, replace with actual detection logic
}

function startVoiceRecognition() {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US'; // Default to English, but you can make this dynamic
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.start();

    recognition.onresult = (event) => {
        const speechResult = event.results[0][0].transcript;
        document.getElementById("user-input").value = speechResult;
        sendMessage();
    };

    recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
    };

    recognition.onspeechend = () => {
        recognition.stop();
    };
}

document.getElementById("user-input").addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});