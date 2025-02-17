async function sendMessage() {
    let userInput = document.getElementById("userInput").value.trim();
    if (!userInput) return;

    let chatBox = document.getElementById("chatBox");

    // Immediately show the user's message
    chatBox.innerHTML += `<p><strong>You:</strong> ${userInput.replace(/\n/g, "<br>")}</p>`;
    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to bottom
    document.getElementById("userInput").value = ""; // Clear input

    // Send request to the server
    let response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userInput })
    });

    let data = await response.json();
    updateChat(data.history);
}

// Fetch chat history every 3 seconds
async function fetchChatHistory() {
    let response = await fetch('/history');
    let data = await response.json();
    updateChat(data.history);
}

// Update chat messages in the UI
function updateChat(history) {
    let chatBox = document.getElementById("chatBox");
    chatBox.innerHTML = "";
    history.forEach(entry => {
        let role = entry.role === "user" ? "You" : "DeepSeek";
        chatBox.innerHTML += `<p><strong>${role}:</strong> ${entry.message.replace(/\n/g, "<br>")}</p>`;
    });
    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll
}

// Clear chat history
async function clearChat() {
    await fetch('/clear', { method: 'POST' });
    document.getElementById("chatBox").innerHTML = "";
}

// Auto-refresh chat every 500 ms
setInterval(fetchChatHistory, 500);

// Load chat history on page load
window.onload = fetchChatHistory;
