let mediaRecorder;
let audioChunks = [];

// Function to show/hide the scroll-to-bottom button
function toggleScrollButton() {
    const chatMessages = document.getElementById("chat-messages");
    const scrollButton = document.getElementById("scroll-to-bottom");

    // Show the button if the user is not at the bottom
    if (chatMessages.scrollTop + chatMessages.clientHeight < chatMessages.scrollHeight - 50) {
        scrollButton.style.display = "block";
    } else {
        scrollButton.style.display = "none";
    }
}

// Function to scroll to the bottom of the chat
function scrollToBottom() {
    const chatMessages = document.getElementById("chat-messages");
    chatMessages.scrollTop = chatMessages.scrollHeight;
    toggleScrollButton(); // Hide the button after scrolling
}

// Add event listener for scrolling to toggle the button
document.getElementById("chat-messages").addEventListener("scroll", toggleScrollButton);

function startVoiceRecognition() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then((stream) => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();

            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
                sendAudioToServer(audioBlob);
                audioChunks = [];
            };

            // Stop recording after 5 seconds (or adjust as needed)
            setTimeout(() => {
                mediaRecorder.stop();
            }, 5000);
        })
        .catch((error) => {
            console.error("Error accessing microphone:", error);
        });
}

function sendAudioToServer(audioBlob) {
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.wav");

    fetch("/upload-audio", {
        method: "POST",
        body: formData,
    })
    .then((response) => response.json())
    .then((data) => {
        if (data.transcript) {
            document.getElementById("user-input").value = data.transcript;
            sendMessage();  // Automatically send the transcribed text to the chatbot
        } else {
            console.error("Error transcribing audio:", data.error);
        }
    })
    .catch((error) => {
        console.error("Error uploading audio:", error);
    });
}

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

    // Show the scroll-to-bottom button
    toggleScrollButton();

    userInput.value = "";

    // Create a new message element for the AI's response
    const botMessage = document.createElement("div");
    botMessage.className = "message received";
    botMessage.innerHTML = `<p>AI: </p>`;
    chatMessages.appendChild(botMessage);

    // Scroll to bottom
    scrollToBottom();

    // Create an EventSource to listen for the response
    const eventSource = new EventSource(`/chat?message=${encodeURIComponent(message)}`);

    eventSource.onmessage = (event) => {
        if (event.data === "[END]") {
            // Close the EventSource when the response ends
            eventSource.close();
        } else {
            // Append the chunk to the AI's response
            const textSpan = botMessage.querySelector("p");
            textSpan.textContent += event.data;

            // Show the scroll-to-bottom button
            toggleScrollButton();
        }
    };

    eventSource.onerror = (error) => {
        console.error("EventSource failed:", error);
        eventSource.close();
    };
}

document.getElementById("user-input").addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = (this.scrollHeight) + "px";
});

document.getElementById("user-input").addEventListener("keypress", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

// Initial call to hide the scroll button
toggleScrollButton();