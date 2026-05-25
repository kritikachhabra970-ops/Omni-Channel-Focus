import pusher
import uuid
import re
import time
from datetime import datetime
import os
from dotenv import load_dotenv
import google.generativeai as genai
import requests
from flask import Flask, render_template, request, jsonify
# Pusher Setup
pusher_client = pusher.Pusher(
  app_id='2158913',
  key='145e79fafd58fc0714e0',
  secret='28ef5a5db30015c38f2e', 
  cluster='ap2',
  ssl=True
)

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_model = None
fallback_model = None
api_key_valid = False

if GEMINI_API_KEY and GEMINI_API_KEY != "your_api_key_here":
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Dry-run validation of the API key
        list(genai.list_models())
        api_key_valid = True
        print("SUCCESS: Gemini API Key verified successfully!")
    except Exception as e:
        print(f"CRITICAL WARNING: Gemini API Key validation failed: {e}")
        print("The server will run in premium MOCK FALLBACK mode. Please configure a valid GEMINI_API_KEY in your .env file to enable real AI.")
        api_key_valid = False

if api_key_valid:
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 512,
    }
    
    BUSINESS_CONTEXT = """You are a helpful Customer Support AI Assistant for OmniChannel. Be concise and friendly.

BUSINESS INFORMATION YOU MUST USE TO ANSWER CUSTOMER QUESTIONS:

💳 PRICING & SUBSCRIPTION PLANS:
1. Starter Plan: $9.99/month - Basic access, standard email support.
2. Pro Plan: $29.99/month - High-speed, priority support, full chatbot capabilities.
3. Enterprise Plan: Custom pricing - Tailored integrations, dedicated account manager.

🔄 REFUND & CANCELLATION POLICY:
- We offer a hassle-free 14-day money-back guarantee on all new plans.
- To cancel: provide your order number or account email and state the reason.
- Refunds are processed within 3-5 business days.

📞 SUPPORT & CONTACT DETAILS:
- Email Support: support@omnichannel.com (Available 24/7)
- Phone Support: +1 (800) 555-0199 (Mon-Fri, 9 AM - 5 PM EST)
- Live Operator: Customers can type 'talk to agent' to connect to a live human agent.

Always use the above information when customers ask about pricing, plans, costs, refunds, cancellations, or contact details.
If the user asks for an image, output the exact tag [IMAGE_SEARCH: subject] replacing subject with what they asked for. Do not use Markdown image syntax."""

    gemini_model = genai.GenerativeModel(
        model_name='gemini-flash-lite-latest',
        system_instruction=BUSINESS_CONTEXT,
        generation_config=generation_config
    )
    fallback_model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=BUSINESS_CONTEXT,
        generation_config=generation_config
    )

# Final fallback responses if AI is completely unavailable
MOCK_SUGGESTIONS = [
    "I'm looking into this for you. Could you please provide a few more details?",
    "Thank you for your patience. I'm checking the details and will get back to you in just a moment.",
    "I understand your request. Let me verify that information and I'll be right with you.",
    "I'm happy to help with this. Could you please clarify your request so I can provide the most accurate response?",
    "I'm processing your request. One moment please while I gather the necessary information."
]

def get_mock_response(message):
    msg_lower = message.lower()
    if any(word in msg_lower for word in ['hello', 'hi', 'hey', 'greetings', 'morning', 'evening']):
        return "Hello! 👋 Welcome to our Customer Support. I'm currently running in demo/mock mode, but I can help you with pricing plans, refunds, support contacts, or connect you to a live human operator. What can I help you with today?"
    
    elif any(word in msg_lower for word in ['price', 'cost', 'pricing', 'plan', 'subscription', 'monthly', 'annual']):
        return "💳 **Our Pricing & Subscription Plans:**\n\n1. **Starter Plan:** $9.99/mo - Basic access, standard email support.\n2. **Pro Plan:** $29.99/mo - High-speed, priority support, full chatbot capabilities.\n3. **Enterprise Plan:** Custom pricing - Tailored integrations, dedicated account manager.\n\nWould you like to upgrade or have specific billing questions?"
        
    elif any(word in msg_lower for word in ['refund', 'cancel', 'return', 'money back', 'charge']):
        return "🔄 **Refund & Cancellation Policy:**\n\nWe offer a hassle-free, **14-day money-back guarantee** on all new plans! If you are unsatisfied or want to cancel your plan:\n1. Please provide your order number or account email.\n2. State the reason for cancellation.\n\nOnce submitted, refunds are usually processed within 3-5 business days."
        
    elif any(word in msg_lower for word in ['contact', 'email', 'phone', 'call', 'support', 'address']):
        return "📞 **Support & Contact Details:**\n\n* **Email Support:** support@omnichannel.com (Available 24/7)\n* **Phone Support:** +1 (800) 555-0199 (Mon-Fri, 9 AM - 5 PM EST)\n* **Live Operator:** Just type 'talk to agent' to connect directly to our agent dashboard!"
        
    elif any(word in msg_lower for word in ['feature', 'capability', 'what can you do', 'how does this work']):
        return "🤖 **What I Can Do:**\n\n* **Automated Support:** Solve basic pricing, refund, and contact inquiries.\n* **Smart Escales:** Connect you instantly to a live human operator when you ask.\n* **Dashboard Analytics:** Admin/Agent tools are available at `/dashboard` to view statistics in real-time."
        
    else:
        return "I am our AI Assistant in Demo Mode. 🤖\n\nI can answer questions about:\n* **Pricing Plans** (Type 'pricing')\n* **Refund Policy** (Type 'refund')\n* **Contact & Support Info** (Type 'contact')\n\nAlternatively, if you'd like to chat with a real human operator, just type **'talk to agent'**!"

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

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        'api_key_configured': GEMINI_API_KEY is not None and GEMINI_API_KEY != "your_api_key_here",
        'api_key_valid': api_key_valid
    })

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
    
    if any(word in msg_lower for word in ['human', 'agent', 'help', 'operator', 'representative', 'real person', 'talk to agent']):
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
                bot_response = get_mock_response(message)
                if bot_response.startswith("I am our AI Assistant"):
                    analytics_data['unresolved_queries'].append({
                        'query': message,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
        else:
            # Mock NLP Fallback
            bot_response = get_mock_response(message)
            if bot_response.startswith("I am our AI Assistant"):
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
        pusher_client.trigger('chat-channel', 'queue-update', {'queue': queue})

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

# Pusher API route for sending messages
@app.route('/api/send_message', methods=['POST'])
def send_message():
    data = request.json
    pusher_client.trigger('chat-channel', 'new-message', {
        'conversation_id': data.get('conversation_id'),
        'sender': data.get('sender'),
        'text': data.get('text')
    })
    return jsonify({"status": "success"})

# Start the Flask app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
 