
let autoRefresh = true;  // Default state: Auto-refresh is ON
let refreshInterval = setInterval(fetchChatHistory, 500); // Start interval


async function sendMessage() {
    let userInput = document.getElementById("userInput").value.trim();
    if (!userInput) return;

    let chatBox = document.getElementById("chatBox");

    // Immediately show the user's message
    chatBox.innerHTML += `<p id="role_user"><strong>You:</strong></p><p id="userText> ${userInput.replace(/\n/g, "<br>")}</p>`;
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

// Configure marked.js to use Highlight.js for code blocks
marked.setOptions({
    highlight: function (code, lang) {
        return lang && hljs.getLanguage(lang)
            ? hljs.highlight(code, { language: lang }).value
            : hljs.highlightAuto(code).value;
    },
    breaks: true  // Ensures line breaks are preserved
});


function updateChat(history) {
    let chatBox = document.getElementById("chatBox");

    // Save current scroll position
    let isAtBottom = chatBox.scrollHeight - chatBox.scrollTop === chatBox.clientHeight;

    let newChatHTML = "";
    history.forEach(entry => {
        let role = entry.role === "user" ? "You" : "DeepSeek";
        let content = marked.parse(entry.message); // Convert Markdown to HTML

        if (role === "DeepSeek") {
            newChatHTML += `
                <p class="role_deepseek"><u><strong>${role}:</strong></u></p>
                <div class="deepseekText">${content}</div>
            `;
        } else {
            newChatHTML += `
                <p class="role_user"><u><strong>${role}:</strong></u></p>
                <div class="userText">${content}</div>
            `;
        }
    });

    // Update chatBox content only if there's a change (prevents unnecessary redraws)
    if (chatBox.innerHTML !== newChatHTML) {
        chatBox.innerHTML = newChatHTML;

        // Ensure highlight.js is applied to new code blocks
        document.querySelectorAll("pre code").forEach((block) => {
            hljs.highlightElement(block);
        });
    }

    // Restore scroll position
    if (isAtBottom) {
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}



// Function to toggle auto-refresh
async function toggleAutoRefresh() {
    autoRefresh = !autoRefresh; // Toggle state

    let button = document.getElementById("toggleRefresh");

    if (autoRefresh) {
        refreshInterval = setInterval(fetchChatHistory, 500); // Resume refreshing
        button.textContent = "Auto-Refresh: ON";
    } else {
        clearInterval(refreshInterval); // Stop refreshing
        button.textContent = "Auto-Refresh: OFF";
    }
}


// Clear chat history
async function clearChat() {
    await fetch('/clear', { method: 'POST' });
    document.getElementById("chatBox").innerHTML = "";
}

// Load chat history on page load
window.onload = fetchChatHistory;
