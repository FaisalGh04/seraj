function sendMessage() {
    const userInput = document.getElementById("user-input");
    const message = userInput.value.trim();
    if (message === "") return;

    const chatMessages = document.getElementById("chat-messages");

    // Add user message
    const userMessage = document.createElement("div");
    userMessage.className = "message user";
    userMessage.innerHTML = `<span class="text">You: ${message}</span>`;
    chatMessages.appendChild(userMessage);

    userInput.value = "";

    // Create a new message element for the AI's response
    const botMessage = document.createElement("div");
    botMessage.className = "message bot";
    botMessage.innerHTML = `<span class="text">AI: </span>`;
    chatMessages.appendChild(botMessage);

    // Create an EventSource to listen for the response
    const eventSource = new EventSource(`/chat?message=${encodeURIComponent(message)}`);

    eventSource.onmessage = (event) => {
        if (event.data === "[END]") {
            // Close the EventSource when the response ends
            eventSource.close();
        } else {
            // Append the new word to the AI's message
            const textSpan = botMessage.querySelector(".text");
            textSpan.textContent += event.data + " ";
            chatMessages.scrollTop = chatMessages.scrollHeight; // Auto-scroll
        }
    };

    eventSource.onerror = (error) => {
        console.error("EventSource failed:", error);
        eventSource.close();
    };
}

function clearChat() {
    const chatMessages = document.getElementById("chat-messages");
    chatMessages.innerHTML = "";
}

function startVoiceRecognition() {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
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