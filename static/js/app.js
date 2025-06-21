function displayMessage(message, sender) {
    const chatMessages = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = 'message ' + (sender === 'ai' ? 'ai-message' : sender === 'user' ? 'user-message' : 'error-message');
    div.innerHTML = `<div class="message-bubble">${message}</div>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function getUserId() {
    return document.getElementById('userId')?.value?.trim() || 'guest';
}

function getSessionId() {
    return document.getElementById('sessionId')?.value?.trim() || '';
}

async function sendQuestion(question, userId) {
    // Show typing indicator
    document.getElementById('typingIndicator').style.display = 'block';
    try {
        const res = await fetch('/api/chat/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, user_id: userId })
        });
        const result = await res.json();
        console.log(result);

        if (result.success && result.data && result.data.answer) {
            displayMessage(result.data.answer, 'ai');
        } else if (result.error) {
            displayMessage(result.error, 'error');
        } else {
            displayMessage('No answer received.', 'error');
        }
    } catch (err) {
        displayMessage('Error contacting server.', 'error');
    }
    // Hide typing indicator
    document.getElementById('typingIndicator').style.display = 'none';
}

// Example: handle chat form submission
document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const userId = 'user_' + Math.random().toString(36).substring(2, 10);

    if (chatForm && chatInput) {
        chatForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const question = chatInput.value.trim();
            if (!question) return;
            displayMessage(question, 'user');
            chatInput.value = '';
            await sendQuestion(question, userId);
        });
    }
});

// Handle form submit for Enter/Send button
document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    if (chatForm && messageInput) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const question = messageInput.value.trim();
            if (!question) return;
            displayMessage(question, 'user');
            sendQuestion(question, getUserId());
            messageInput.value = '';
        });
    }
});

// Handle Ask AI button
function askAI() {
    const messageInput = document.getElementById('messageInput');
    const question = messageInput.value.trim();
    if (!question) return;
    displayMessage(question, 'user');
    sendQuestion(question, getUserId());
    messageInput.value = '';
}