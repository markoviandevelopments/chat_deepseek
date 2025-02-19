
let autoRefresh = true;  // Default state: Auto-refresh is ON
let refreshInterval = setInterval(fetchChatHistory, 500); // Start interval

// Fetch chat history every 3 seconds
async function fetchChatHistory() {
    let response = await fetch('/history');
    let data = await response.json();
    updateChat(data.history);
}

// Configure Marked.js and Highlight.js for better rendering
marked.setOptions({
    highlight: function (code, lang) {
        return lang && hljs.getLanguage(lang)
            ? hljs.highlight(code, { language: lang }).value
            : hljs.highlightAuto(code).value;
    },
    breaks: true
});

// Modify Marked's `code` renderer to add a copy button
const renderer = new marked.Renderer();

renderer.code = function (code, language) {
    const validLang = hljs.getLanguage(language) ? language : "plaintext";
    return `
        <div class="code-container">
            <button class="copy-button" onclick="copyCode(this)">Copy</button>
            <pre><code class="language-${validLang}">${hljs.highlight(code, { language: validLang }).value}</code></pre>
        </div>
    `;
};

// Apply the new renderer to Marked
marked.setOptions({ renderer });

// Function to Copy Code Blocks
function copyCode(button) {
    let codeBlock = button.nextElementSibling.querySelector("code");

    if (!codeBlock) {
        console.error("Code block not found!");
        return;
    }

    let text = codeBlock.innerText;

    navigator.clipboard.writeText(text).then(() => {
        button.textContent = "Copied!";
        setTimeout(() => (button.textContent = "Copy"), 1500);
    }).catch(err => {
        console.error("Error copying text: ", err);
    });
}

// Function to Update Chat with Messages
function updateChat(history) {
    let chatBox = document.getElementById("chatBox");

    // Save current scroll position
    let isAtBottom = chatBox.scrollHeight - chatBox.scrollTop === chatBox.clientHeight;

    let newChatHTML = "";
    history.forEach(entry => {
        let role = entry.role === "user" ? "You" : "DeepSeek";
        let content = entry.message;

        // Only parse Markdown if the message is from DeepSeek
        if (role === "DeepSeek") {
            content = marked.parse(content);
        } else {
            // Ensure user text doesn't get converted
            content = content.replace(/\n/g, "<br>");
        }

        newChatHTML += `
            <p class="${role === "You" ? "role_user" : "role_deepseek"}"><u><strong>${role}:</strong></u></p>
            <div class="${role === "You" ? "userText" : "deepseekText"}">${content}</div>
        `;
    });

    // Only update the chatbox if the content actually changed
    if (chatBox.innerHTML !== newChatHTML) {
        chatBox.innerHTML = newChatHTML;

        // Apply syntax highlighting to all new code blocks
        document.querySelectorAll("pre code").forEach((block) => {
            hljs.highlightElement(block);
        });
    }

    // Restore scroll position
    if (isAtBottom) {
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

// Fetch chat history
async function fetchChatHistory() {
    let response = await fetch('/history');
    let data = await response.json();
    updateChat(data.history);
}

// Send User Message
async function sendMessage() {
    let userInput = document.getElementById("userInput").value.trim();
    if (!userInput) return;

    let chatBox = document.getElementById("chatBox");

    // Show the user's message immediately
    chatBox.innerHTML += `<p class="role_user"><strong>You:</strong></p><p class="userText">${userInput.replace(/\n/g, "<br>")}</p>`;
    chatBox.scrollTop = chatBox.scrollHeight;
    document.getElementById("userInput").value = ""; // Clear input field

    // Send request to the server
    let response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userInput })
    });

    let data = await response.json();
    updateChat(data.history);
}

// Function to Toggle Auto-Refresh
async function toggleAutoRefresh() {
    autoRefresh = !autoRefresh;

    let button = document.getElementById("toggleRefresh");

    if (autoRefresh) {
        refreshInterval = setInterval(fetchChatHistory, 500);
        button.textContent = "Auto-Refresh: ON";
    } else {
        clearInterval(refreshInterval);
        button.textContent = "Auto-Refresh: OFF";
    }
}

// Clear Chat History
async function clearChat() {
    await fetch('/clear', { method: 'POST' });
    document.getElementById("chatBox").innerHTML = "";
}

// Load chat history on page load
window.onload = fetchChatHistory;
