
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

// Update chat messages in the UI
function updateChat(history) {
    let chatBox = document.getElementById("chatBox");

    // Save current scroll position
    let isAtBottom = chatBox.scrollHeight - chatBox.scrollTop === chatBox.clientHeight;

    // Update chat without clearing the existing history
    let newChatHTML = "";
    history.forEach(entry => {
        let role = entry.role === "user" ? "You" : "DeepSeek";
        let content = entry.message.replace(/\n/g, "<br>"); // Default formatting

        if (role == "DeepSeek") {
            content = marked.parse(entry.message); // Convert Markdown to HTML
        }

    //     newChatHTML += `
    //         <p class="${role === 'You' ? 'role_user' : 'role_deepseek'}">
    //             <u><strong>${role}:</strong></u>
    //         </p>
    //         <div class="${role === 'You' ? 'userText' : 'deepseekText'}">${content}</div>
    //     `;
    // });

        if (role=="You") {
            newChatHTML += `<p id="role_user"><u><strong>${role}:</strong></u></p><p id="userText"> ${content}</p>`;
        } else{
            newChatHTML += `<p id="role_deepseek"><u><strong>${role}:</strong></u></p><p id="deepseekText"> ${content}</p>`;
        }
    });

    // Only update if the chat content actually changed (avoids unnecessary re-renders)
    if (chatBox.innerHTML !== newChatHTML) {
        chatBox.innerHTML = newChatHTML;
    }

    // Restore scroll position: Stay at the same place unless at the bottom
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
