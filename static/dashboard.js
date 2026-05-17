const socket = io();
const queueList = document.getElementById('queue-list');
const activeChatHeader = document.getElementById('active-chat-header');
const chatBody = document.getElementById('chat-body');
const chatFooter = document.getElementById('chat-footer');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');

let currentActiveChat = null;

// Join as agent
socket.on('connect', () => {
    socket.emit('join_agent');
});

// Global Image Fallback Handler
window.addEventListener('error', (e) => {
    if (e.target.tagName === 'IMG' && !e.target.dataset.triedFallback) {
        const alt = e.target.alt || 'placeholder';
        const keywords = alt.replace(/\s+/g, '_');
        e.target.src = `https://image.pollinations.ai/prompt/${keywords}?width=800&height=600&nologo=true`;
        e.target.dataset.triedFallback = 'true';
    }
}, true);

// Listen for queue updates
socket.on('queue_update', (data) => {
    const queue = data.queue;
    queueList.innerHTML = '';
    
    if (queue.length === 0) {
        queueList.innerHTML = '<li><p class="text-muted">No users waiting.</p></li>';
        return;
    }
    
    queue.forEach(convId => {
        const li = document.createElement('li');
        li.className = 'queue-item';
        
        const p = document.createElement('p');
        p.textContent = `User: ${convId.substring(0, 10)}...`;
        
        const btn = document.createElement('button');
        btn.textContent = 'Takeover Chat';
        btn.onclick = () => takeoverChat(convId);
        
        li.appendChild(p);
        li.appendChild(btn);
        queueList.appendChild(li);
    });
});

function takeoverChat(convId) {
    currentActiveChat = convId;
    
    // Notify server we are taking over
    socket.emit('agent_takeover', { conversation_id: convId });
    
    // Update UI
    activeChatHeader.innerHTML = `<h2>Chatting with ${convId.substring(0, 10)}...</h2><p class="online">Connected</p>`;
    chatBody.style.display = 'flex';
    chatFooter.style.display = 'flex';
    chatBody.innerHTML = '<div class="message bot"><div class="msg-content">You have taken over the chat.</div></div>';
}

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

function sendMessage() {
    if (!currentActiveChat) return;
    
    const text = chatInput.value.trim();
    if (!text) return;
    
    // Add to own UI (agent is 'customer' class here to show on the right side)
    addMessage(text, 'customer');
    chatInput.value = '';
    
    // Send to server
    socket.emit('agent_message', {
        conversation_id: currentActiveChat,
        message: text
    });
}

sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

const aiAssistBtn = document.getElementById('ai-assist-btn');
if (aiAssistBtn) {
    aiAssistBtn.addEventListener('click', async () => {
        if (!currentActiveChat) return;
        
        const originalText = aiAssistBtn.textContent;
        aiAssistBtn.textContent = '⏳';
        aiAssistBtn.disabled = true;
        
        try {
            const res = await fetch('/api/agent_assist', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ conversation_id: currentActiveChat })
            });
            const data = await res.json();
            if (data.suggestion) {
                chatInput.value = data.suggestion;
            }
        } catch (e) {
            console.error("AI Assist error:", e);
        } finally {
            aiAssistBtn.textContent = originalText;
            aiAssistBtn.disabled = false;
        }
    });
}


// Listen for messages from the user we are chatting with
socket.on('new_message', (data) => {
    if (data.sender === 'customer' && currentActiveChat) {
        addMessage(data.text, 'bot'); // user messages appear on the left (bot style for agent dashboard)
    }
});

// Analytics Dashboard Logic
const navChat = document.getElementById('nav-chat');
const navAnalytics = document.getElementById('nav-analytics');
const chatView = document.getElementById('chat-view');
const analyticsView = document.getElementById('analytics-view');
const queueSection = document.getElementById('queue-section');

if (navChat && navAnalytics) {
    navChat.addEventListener('click', () => {
        navChat.classList.add('active');
        navAnalytics.classList.remove('active');
        chatView.style.display = 'block';
        analyticsView.style.display = 'none';
        queueSection.style.display = 'block';
    });

    navAnalytics.addEventListener('click', () => {
        navAnalytics.classList.add('active');
        navChat.classList.remove('active');
        chatView.style.display = 'none';
        analyticsView.style.display = 'block';
        queueSection.style.display = 'none';
        fetchAnalytics();
    });
}

function fetchAnalytics() {
    fetch('/api/analytics')
        .then(res => res.json())
        .then(data => {
            document.getElementById('metric-deflection').textContent = data.deflection_rate + '%';
            document.getElementById('metric-response').textContent = data.avg_response_time_ms + ' ms';
            document.getElementById('metric-escalations').textContent = data.escalations;
            
            const tbody = document.getElementById('query-logs-body');
            if (!tbody) return;
            
            tbody.innerHTML = '';
            
            if (data.unresolved_queries.length === 0) {
                tbody.innerHTML = '<tr><td colspan="2" class="text-center text-muted">No unresolved queries yet.</td></tr>';
            } else {
                // reverse to show newest first
                data.unresolved_queries.slice().reverse().forEach(q => {
                    const tr = document.createElement('tr');
                    
                    const tdTime = document.createElement('td');
                    tdTime.textContent = q.timestamp;
                    
                    const tdQuery = document.createElement('td');
                    tdQuery.textContent = q.query;
                    
                    tr.appendChild(tdTime);
                    tr.appendChild(tdQuery);
                    tbody.appendChild(tr);
                });
            }
        })
        .catch(err => console.error("Error fetching analytics:", err));
}
