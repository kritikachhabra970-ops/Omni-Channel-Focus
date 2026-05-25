const socket = io({ transports: ['polling'] });
const chatBody = document.getElementById('chat-body');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const chatStatus = document.getElementById('chat-status');

// Generate a random user ID for this session
const conversationId = localStorage.getItem('conversationId') || 'user_' + Math.random().toString(36).substr(2, 9);
localStorage.setItem('conversationId', conversationId);

let isAgentHandling = false;

// Join the chat room for this user
socket.on('connect', () => {
    socket.emit('join_chat', { conversation_id: conversationId });
});

// Global Image Fallback Handler
window.addEventListener('error', (e) => {
    if (e.target.tagName === 'IMG' && !e.target.dataset.triedFallback) {
        const alt = e.target.alt || 'placeholder';
        const keywords = alt.replace(/\s+/g, '_');
        e.target.src = `https://image.pollinations.ai/prompt/${keywords}?width=800&height=600&nologo=true`;
        e.target.dataset.triedFallback = 'true';
        console.log(`Image failed, falling back to Pollinations for: ${keywords}`);
    }
}, true);

function addMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender);
    
    const contentDiv = document.createElement('div');
    contentDiv.classList.add('msg-content');
    
    if (typeof marked !== 'undefined') {
        contentDiv.innerHTML = marked.parse(text);
    } else {
        contentDiv.textContent = text;
    }
    
    msgDiv.appendChild(contentDiv);
    chatBody.appendChild(msgDiv);
    
    // Scroll to bottom
    chatBody.scrollTop = chatBody.scrollHeight;
}

async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    
    // 1. Add user message to UI
    addMessage(text, 'customer');
    chatInput.value = '';
    
    // 2. If agent is handling, emit via socket
    if (isAgentHandling) {
        socket.emit('customer_message', {
            conversation_id: conversationId,
            message: text
        });
        return;
    }
    
    // 3. Otherwise, send to AI backend
    try {
        const response = await fetch('/api/bot_reply', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: text,
                conversation_id: conversationId
            })
        });
        
        const data = await response.json();
        
        // Mock typing delay
        setTimeout(() => {
            addMessage(data.reply, 'bot');
            if (data.escalate) {
                chatStatus.textContent = 'Waiting for Agent...';
                chatStatus.className = 'waiting';
            }
        }, 600);
        
    } catch (error) {
        console.error('Error sending message to bot:', error);
    }
}

sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Listen for agent joining
socket.on('agent_joined', (data) => {
    isAgentHandling = true;
    chatStatus.textContent = 'Agent Connected';
    chatStatus.className = 'online';
    addMessage(data.message, 'bot'); // Display system message as bot
});

// Listen for new messages from agent
socket.on('new_message', (data) => {
    if (data.sender === 'agent') {
        addMessage(data.text, 'bot'); // Agent messages appear as bot/receiver style
    }
});

// Check server/API key status on page load
fetch('/api/status')
    .then(response => response.json())
    .then(data => {
        if (!data.api_key_valid) {
            const warningBanner = document.getElementById('api-warning-banner');
            if (warningBanner) {
                warningBanner.style.display = 'block';
            }
        }
    })
    .catch(error => console.error('Error verifying API status:', error));
