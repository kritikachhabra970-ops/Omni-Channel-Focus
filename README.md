# 🤖 Omni-Channel Support Focus — AI Customer Support Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-black?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SocketIO](https://img.shields.io/badge/Socket.io-4.7-blueviolet?style=for-the-badge&logo=socket.io&logoColor=white)](https://socket.io/)
[![Gemini API](https://img.shields.io/badge/Google%20Gemini-Flash--Lite-violet?style=for-the-badge&logo=google-gemini&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](https://opensource.org/licenses/MIT)

***An enterprise-grade, production-ready, omni-channel customer support ecosystem powered by Google Gemini AI, featuring real-time bi-directional human-agent handover.***

---

## 📖 Overview

The **Omni-Channel AI Customer Support Platform** is a modern, high-performance customer service suite designed to address the fragmentation of traditional customer support systems. By unifying communications across web chat, emails, and messaging integrations, the platform ensures **omni-channel state preservation** so that customer context is never lost during agent handovers or channel transitions.

At its core, the platform operates a primary automated **NLP Engine** using Gemini models to handle intent classification, semantic matching, and sentiment analysis. When an inquiry requires human touch, the platform initiates a hot-swapping **Live Agent Handover** flow, routing the conversation history and automated context summaries to a centralized **Agent Workspace Interface** via low-latency WebSocket streams.

---

## ✨ Key Features & Capabilities

| Module | Capabilities |
| :--- | :--- |
| **🧠 NLP & Sentiment Engine** | • Fully automated, low-latency intent classification using `gemini-flash-lite-latest`. <br>• Dynamic context preservation and conversational history processing (windowed up to 10 messages). <br>• Semantic query processing with automated fallback paths for pricing, refunds, and general support. |
| **🔄 Live Agent Handover** | • Hot-swapping routing logic that escalates complex or frustrated queries to live human queues. <br>• High-performance real-time bi-directional streaming using Flask-SocketIO. <br>• Smooth transition states alerting the user when an operator connects. |
| **✨ Agent Workspace** | • Intuitive, modern live agent dashboard featuring quick queue access, client logs, and chat controls. <br>• **AI Assist**: Direct integration generating proposed agent replies based on live context with one click. <br>• Live telemetry dashboard reporting average deflection rate, bot processing times, and escalation metrics. |
| **📁 Unified Data Layer** | • Unified CRM profile aggregation for ongoing conversation states and unresolved user query logging. <br>• Real-time database telemetry integration to store metrics, resolved intents, and logs. |
| **🖼️ Rich Media Processing** | • Custom image rendering engine using Bing search and Pollinations AI to serve visual prompts dynamically. |

---

## 🛠️ Technology Stack & Core Architecture

| Layer | Technology | Version / Stack |
| :--- | :--- | :--- |
| **Core Runtime** | Python | `3.10` / `3.11` |
| **Backend Framework** | Flask & Flask-SocketIO | Flask `3.0.0+` / Socket.IO `4.7.2` |
| **AI Model Engine** | Google Generative AI | `gemini-flash-lite-latest` (Primary), `gemini-1.5-flash` (Fallback) |
| **Client Interface** | Vanilla HTML5 / Modern CSS | HSL-tailored premium dark styling, glassmorphism, responsive grids |
| **Markdown Parser** | Marked.js | `marked.min.js` (Client-side markdown & rich text renderer) |
| **Runtime Networking** | Eventlet / Gunicorn | Asynchronous eventlet worker class (`0.33.3+`) |

---

## 📂 Project Structure

Below is the directory map illustrating the structural layout of the platform:

```tree
website1/
├── .env                     # Local secrets configuration (ignored in commits)
├── .gitignore               # Clean standard Git exclusions
├── app.py                   # Central Flask gateway, API endpoints, & WebSocket rooms
├── Dockerfile               # High-performance multi-stage Docker build config
├── render.yaml              # Production environment deploy configuration
├── requirements.txt         # Pinned pip dependency manifest
├── test_gemini.py           # Gemini API connection and validation test script
├── static/                  # Static assets repository
│   ├── dashboard.js         # Live Agent Workspace logic & charts telemetry
│   ├── script.js            # Customer Web Chat application script
│   └── style.css            # Unified CSS layout with harmonious styling
├── templates/               # Client Jinja HTML templates
│   ├── dashboard.html       # Live Agent Workspace console UI
│   └── index.html           # Customer Web Chat portal
└── venv/                    # Local isolated Python environment
```

---

## ⚙️ Prerequisites & Setup Guide

### 📋 Prerequisites
* **Python**: Version `3.10` or `3.11`
* **Pip**: Latest version of Python package manager
* **Virtualenv**: Python virtual environments helper

### 🚀 Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/omnichannel-support-focus.git
   cd omnichannel-support-focus
   ```

2. **Establish a Secure Virtual Environment**
   ```powershell
   # Windows PowerShell
   python -m venv venv
   .\venv\Scripts\activate
   ```
   ```bash
   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Stack Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Your Secrets Environment**
   Create a `.env` file in the root directory (this file is excluded from commits via `.gitignore`):
   ```env
   GEMINI_API_KEY=your_secure_gemini_api_key_here
   PORT=5000
   ```

---

## 🏃 Running the Application

To fire up the high-performance local server, execute:

```bash
python app.py
```

Upon launching, the local server will run secure startup checks on your Gemini API key and boot up:

```text
SUCCESS: Gemini API Key verified successfully!
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### 🔗 Local Portals
* 💬 **Customer Web Chat Interface**: [http://localhost:5000/](http://localhost:5000/)
* 📊 **Live Agent Workspace & Analytics**: [http://localhost:5000/dashboard](http://localhost:5000/dashboard)

---

## 🧪 Testing & License

### 🧪 Executing Verification Tests
To run API integration connectivity tests, execute the built-in validator script:
```bash
python test_gemini.py
```

### 📄 License
Distributed under the **MIT License**. For detailed information, see the license terms within the repository.

---

## 🤝 Acknowledgements & Support

### ❤️ Acknowledgements
* [Google DeepMind](https://deepmind.google/) for providing the low-latency Gemini LLM APIs.
* [Flask & Flask-SocketIO](https://flask-socketio.readthedocs.io/) for high-performance event-driven networking.
* [Marked.js](https://marked.js.org/) for modern browser markdown translation.
* [Pollinations AI](https://pollinations.ai/) for real-time custom prompt-to-image synthesis fallbacks.

### 📞 Need Help?
Have questions, suggestions, or found a bug? 
* Open a **GitHub Issue** detailing your request.
* Explore the **Discussions Hub** to share feedback with the community.
* Reach out to the core engineering team at **support@omnichannel.com** for direct enterprise queries.
