
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

marked.setOptions({
    highlight: function (code, lang) {
        return lang && hljs.getLanguage(lang)
            ? hljs.highlight(code, { language: lang }).value
            : hljs.highlightAuto(code).value;
    },
    breaks: true,
    renderer: new marked.Renderer()
});

// Modify marked's `code` renderer to insert the "Copy" button
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

// Apply the new renderer to `marked`
marked.setOptions({ renderer });


function copyCode(button) {
    let codeBlock = button.nextElementSibling.querySelector("code");
    let text = codeBlock.innerText;

    navigator.clipboard.writeText(text).then(() => {
        button.textContent = "Copied!";
        setTimeout(() => (button.textContent = "Copy"), 1500);
    }).catch(err => {
        console.error("Error copying text: ", err);
    });
}

function updateChat(history) {
    let chatBox = document.getElementById("chatBox");

    // Save current scroll position
    let isAtBottom = chatBox.scrollHeight - chatBox.scrollTop === chatBox.clientHeight;

    let newChatHTML = "";
    history.forEach(entry => {
        let role = entry.role === "user" ? "You" : "DeepSeek";
        let content = marked.parse(entry.message); // Convert Markdown to HTML

        if (role === "DeepSeek") {
            // Wrap code blocks with a div for styling and copy button
            content = content.replace(
                /<pre><code([\s\S]*?)>([\s\S]*?)<\/code><\/pre>/g,
                (match, lang, code) => `
                    <div class="code-container">
                        <button class="copy-button" onclick="copyCode(this)">Copy</button>
                        <pre><code${lang}>${code}</code></pre>
                    </div>
                `
            );

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

    // Only update if the chat content actually changed
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
