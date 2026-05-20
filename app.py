from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room
import uuid
import re
import time
from datetime import datetime
import os
from dotenv import load_dotenv
import google.generativeai as genai
import requests

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY and GEMINI_API_KEY != "your_api_key_here":
    genai.configure(api_key=GEMINI_API_KEY)
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 512,
    }
    
    gemini_model = genai.GenerativeModel(
        model_name='gemini-flash-lite-latest',
        system_instruction="You are a helpful AI assistant. Be concise. If the user asks for an image, output the exact tag [IMAGE_SEARCH: subject] replacing subject with what they asked for. Do not use Markdown image syntax. Otherwise, use text.",
        generation_config=generation_config
    )
    fallback_model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction="Professional assistant. If the user asks for an image, output [IMAGE_SEARCH: subject].",
        generation_config=generation_config
    )
else:
    gemini_model = None
    fallback_model = None
    fallback_model = None

# Final fallback responses if AI is completely unavailable
MOCK_SUGGESTIONS = [
    "I'm looking into this for you. Could you please provide a few more details?",
    "Thank you for your patience. I'm checking the details and will get back to you in just a moment.",
    "I understand your request. Let me verify that information and I'll be right with you.",
    "I'm happy to help with this. Could you please clarify your request so I can provide the most accurate response?",
    "I'm processing your request. One moment please while I gather the necessary information."
]
import random

def get_real_image(query):
    try:
        import urllib.parse
        import re
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.bing.com/images/search?q={encoded_query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        res = requests.get(url, headers=headers)
        # Bing stores image URLs in the 'm' attribute of 'a' tags with class 'iusc'
        matches = re.finditer(r'murl&quot;:&quot;(.*?)&quot;', res.text)
        for match in matches:
            url_match = match.group(1)
            # Filter out common stock photo watermarked images
            if url_match.startswith("http") and "shutterstock" not in url_match and "istock" not in url_match:
                return url_match
    except Exception as e:
        print(f"Image search error: {e}")
    # Fallback dynamically generates an image if Web search fails
    return f"https://image.pollinations.ai/prompt/{query.replace(' ', '_')}?width=800&height=600&nologo=true"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory storage for simplicity (instead of SQLite for a quick prototype)
conversations = {}
agents = {} # session_id -> status
queue = [] # list of conversation_ids waiting for an agent

# Analytics Data
analytics_data = {
    'total_queries': 0,
    'escalations': 0,
    'unresolved_queries': [], # list of dicts: {'query': '...', 'timestamp': '...'}
    'bot_response_times': [], # list of floats (seconds)
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/bot_reply', methods=['POST'])
def bot_reply():
    start_time = time.time()
    data = request.json
    message = data.get('message', '')
    conversation_id = data.get('conversation_id')
    
    if not conversation_id:
        return jsonify({'error': 'No conversation ID'}), 400
        
    analytics_data['total_queries'] += 1
        
    # Initialize conversation if it doesn't exist
    if conversation_id not in conversations:
        chat_session = gemini_model.start_chat(history=[]) if gemini_model else None
        conversations[conversation_id] = {'status': 'bot', 'messages': [], 'gemini_chat': chat_session}

    # Basic intent detection and AI response
    msg_lower = message.lower()
    escalate = False
    bot_response = "I'm sorry, I don't quite understand. Could you rephrase?"
    
    if any(word in msg_lower for word in ['human', 'agent', 'help', 'operator', 'representative', 'real person']):
        bot_response = "I understand you want to speak with a human agent. Let me connect you..."
        escalate = True
        analytics_data['escalations'] += 1
    else:
        chat_session = conversations[conversation_id].get('gemini_chat')
        if chat_session:
            try:
                # Keep history short for maximum speed (last 10 messages)
                if hasattr(chat_session, 'history') and len(chat_session.history) > 10:
                    chat_session.history = chat_session.history[-10:]
                    
                response = chat_session.send_message(message)
                bot_response = response.text
            except Exception as e:
                print(f"Gemini API Error: {e}")
                # Mock NLP Fallback due to API error
                if any(word in msg_lower for word in ['hello', 'hi', 'hey']):
                    bot_response = "Hello! How can I help you today?"
                elif 'price' in msg_lower or 'cost' in msg_lower:
                    bot_response = "Our pricing starts at $9.99/month. Would you like more details on our plans?"
                elif 'refund' in msg_lower:
                    bot_response = "I can help with that. Please provide your order number."
                else:
                    bot_response = "I am an AI assistant. I can answer questions about pricing, refunds, or connect you to an agent. How can I assist you further?"
                    analytics_data['unresolved_queries'].append({
                        'query': message,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
        else:
            # Mock NLP Fallback
            if any(word in msg_lower for word in ['hello', 'hi', 'hey']):
                bot_response = "Hello! How can I help you today?"
            elif 'price' in msg_lower or 'cost' in msg_lower:
                bot_response = "Our pricing starts at $9.99/month. Would you like more details on our plans?"
            elif 'refund' in msg_lower:
                bot_response = "I can help with that. Please provide your order number."
            else:
                bot_response = "I am an AI assistant. I can answer questions about pricing, refunds, or connect you to an agent. How can I assist you further?"
                analytics_data['unresolved_queries'].append({
                    'query': message,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
        # Post-process image search tags
        matches = re.finditer(r'\[IMAGE_SEARCH:\s*(.*?)\]', bot_response)
        for match in matches:
            subject = match.group(1)
            img_url = get_real_image(subject)
            if img_url:
                bot_response = bot_response.replace(match.group(0), f'![{subject}]({img_url})')
            else:
                bot_response = bot_response.replace(match.group(0), f'*(Sorry, I could not find an image for "{subject}")*')
        
    if escalate:
        # Mark conversation as waiting for agent
        conversations[conversation_id]['status'] = 'waiting'
            
        if conversation_id not in queue:
            queue.append(conversation_id)
            
        # Notify dashboard about new queue item
        socketio.emit('queue_update', {'queue': queue}, to='agents')

    response_time = time.time() - start_time
    analytics_data['bot_response_times'].append(response_time)

    return jsonify({
        'reply': bot_response,
        'escalate': escalate
    })

@app.route('/api/agent_assist', methods=['POST'])
def agent_assist():
    data = request.json
    conversation_id = data.get('conversation_id')
    
    if not conversation_id or conversation_id not in conversations:
        return jsonify({'error': 'Invalid conversation'}), 400
        
    chat_session = conversations[conversation_id].get('gemini_chat')
    if not chat_session:
        return jsonify({'suggestion': 'No AI context available for this chat.'})
        
    instruction = "Draft the exact response for the agent to send to the customer based on the conversation above. Use Google Search to verify facts if needed. Provide ONLY the final text of the response. No introductory text like 'Here is a suggestion' or 'Certainly'. No filler. If the user asked for an image, output the exact tag [IMAGE_SEARCH: subject]."

    try:
        # 1. Primary Attempt: gemini-flash-lite
        history = list(chat_session.history)
        response = gemini_model.generate_content(history + [instruction])
        sugg = response.text.strip()
        for match in re.finditer(r'\[IMAGE_SEARCH:\s*(.*?)\]', sugg):
            url = get_real_image(match.group(1))
            sugg = sugg.replace(match.group(0), f'![{match.group(1)}]({url})' if url else f'*(Image not found)*')
        return jsonify({'suggestion': sugg})
    except Exception as e:
        print(f"Primary AI Assist Error (Attempting Fallback): {e}")
        try:
            # 2. Secondary Attempt: gemini-1.5-flash
            if fallback_model:
                response = fallback_model.generate_content(list(chat_session.history) + [instruction])
                sugg = response.text.strip()
                for match in re.finditer(r'\[IMAGE_SEARCH:\s*(.*?)\]', sugg):
                    url = get_real_image(match.group(1))
                    sugg = sugg.replace(match.group(0), f'![{match.group(1)}]({url})' if url else f'*(Image not found)*')
                return jsonify({'suggestion': sugg})
        except Exception as e2:
            print(f"Secondary AI Assist Error (Using Mock): {e2}")
            
    # 3. Tertiary Attempt: Mock Suggesion (Guarantees no "API limits" error)
    return jsonify({'suggestion': random.choice(MOCK_SUGGESTIONS)})

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    total = analytics_data['total_queries']
    escalations = analytics_data['escalations']
    deflection_rate = 0
    if total > 0:
        deflection_rate = ((total - escalations) / total) * 100
        
    times = analytics_data['bot_response_times']
    avg_response_time = sum(times) / len(times) if times else 0
    
    return jsonify({
        'deflection_rate': round(deflection_rate, 2),
        'avg_response_time_ms': round(avg_response_time * 1000, 2),
        'total_queries': total,
        'escalations': escalations,
        'unresolved_queries': analytics_data['unresolved_queries'][-50:] # latest 50
    })

# Socket.IO Event Handlers

@socketio.on('connect')
def test_connect():
    pass

@socketio.on('join_agent')
def on_join_agent():
    join_room('agents')
    emit('queue_update', {'queue': queue})
    print("Agent joined")

@socketio.on('join_chat')
def on_join_chat(data):
    room = data.get('conversation_id')
    join_room(room)
    print(f"User joined chat: {room}")

@socketio.on('agent_takeover')
def on_agent_takeover(data):
    conversation_id = data.get('conversation_id')
    agent_id = request.sid
    
    if conversation_id in queue:
        queue.remove(conversation_id)
        if conversation_id in conversations:
            conversations[conversation_id]['status'] = 'agent_handling'
            conversations[conversation_id]['agent_id'] = agent_id
            
        join_room(conversation_id)
        
        # Notify user that agent has joined
        emit('agent_joined', {'message': 'An agent has joined the chat.'}, room=conversation_id)
        # Update dashboards
        emit('queue_update', {'queue': queue}, to='agents')
        
@socketio.on('agent_message')
def on_agent_message(data):
    conversation_id = data.get('conversation_id')
    message = data.get('message')
    
    # Broadcast to the room (customer will see it)
    emit('new_message', {'sender': 'agent', 'text': message}, room=conversation_id)

@socketio.on('customer_message')
def on_customer_message(data):
    conversation_id = data.get('conversation_id')
    message = data.get('message')
    
    # If agent is handling, just broadcast it in the room
    if conversation_id in conversations and conversations[conversation_id].get('status') == 'agent_handling':
        emit('new_message', {'sender': 'customer', 'text': message}, room=conversation_id)

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
