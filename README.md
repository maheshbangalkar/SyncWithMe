# **SyncWithMe ChatBot**

*Your personal assistant to sync with the world 🌏 — powered by Gemini 💠*

---

## 🚀 **Overview**

**SyncWithMe** is a clarity-focused personal AI assistant designed to help users think better, learn faster, and stay aligned with their goals.
It combines **Google Gemini**, **Streamlit**, and a **minimal-memory architecture** to deliver fast, structured, human-friendly conversations.

The goal of SyncWithMe is simple:

> **Turn powerful AI capabilities into clear, calm, and useful guidance.**

---

## ✨ **Key Features**

### 🧠 **Dual Reasoning Modes**

* **Normal Mode** — fast, concise responses
* **Thinking Mode** — deep, step-by-step reasoning with a configurable thinking budget

### 🎯 **Minimal Context Window**

* Uses a small, focused history (`MAX_CONTEXT = 6`)
* Keeps responses fast, predictable, and cost-efficient

### 📜 **Persona-Driven System Instruction**

* Defines tone, behavior, reasoning depth, and safety
* Ensures consistent, friendly, clear communication

### 🔍 **Google Search Integration (Optional)**

* Allows extended research when needed

### 📊 **Google Sheet Logging**

* Lightweight observability — logs queries, responses, token usage, and metadata
* No database required

### ⚡ **Fast & Free**

* Built entirely using Gemini’s free tier
* Runs locally with zero cost

---

## 🌐 **Live App**
👉 Try SyncWithMe now: http://www.bit.ly/SyncWithMe

![SyncWithMe Live UI](https://raw.githubusercontent.com/maheshbangalkar/SyncWithMe/main/UI/images/home.png)

---
## 🛠️ **Tech Stack**

| Component      | Technology                                  |
| -------------- | ------------------------------------------- |
| Frontend       | Streamlit                                   |
| Backend Engine | Python                                      |
| AI Model       | Google Gemini (via generative-language API) |
| Logging        | Google Sheets (gspread / Sheets API)        |
| Memory         | Lightweight session history                 |
| Deployment     | Local / Streamlit Cloud                     |

---

## 📐 **Architecture Overview**

SyncWithMe uses a clean, modular architecture:

```
┌────────────────────┐
│  Streamlit UI       │
│ - Chat interface    │
│ - Mode selector     │
│ - History sidebar   │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  SyncWithMe Engine  │
│ - System instruction│
│ - Context window    │
│ - Model selection   │
│ - Thinking mode     │
│ - Response parsing  │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│   Gemini API        │
│ - Text reasoning    │
│ - ThinkingConfig    │
│ - Search tool       │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Google Sheet Logger │
│ - Questions         │
│ - Responses         │
│ - Token stats       │
└────────────────────┘
```

---

## 📦 **Installation**

### 1️⃣ Clone the repository

```bash
git clone https://github.com/maheshbangalkar/SyncWithMe.git
cd SyncWithMe
```

### 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Set environment variables

Create a `.env` file:

```
GEMINI_API_KEY=your_key
GOOGLE_SHEETS_CREDENTIALS=path_to_credentials.json
```

### 4️⃣ Run the app

```bash
streamlit run app.py
```

---

## 🎛️ **Configuration**

All assistant behavior is controlled via the `config.py` file:

```python
MAX_CONTEXT = 6
MODEL_NAME = "gemini-2.5-flash"
MODEL_THINKING_BUDGET = 500
SYSTEM_INSTRUCTION_FILE = "SYSTEM_INSTRUCTION.txt"
```

You can easily modify:

* Persona tone
* Reasoning depth
* Output limits
* Context size
* Thinking mode behavior

---

## 💡 **How It Works (Technical Flow)**

### **1. User enters a message in Streamlit**

UI collects:

* User query
* Selected mode (Normal / Thinking Mode)

### **2. Backend reconstructs small context**

```python
context = session_history[-MAX_CONTEXT:]
```

### **3. System instruction is injected**

Defines:

* Tone
* Style
* Clarity rules
* Behavior constraints
* Format

### **4. Gemini receives a structured request**

Including:

* System instruction
* Context
* User message
* Thinking config (optional)
* Token limits

### **5. Response is parsed and returned**

### **6. Everything is logged to Google Sheets**

---

## 🧪 **Sample Code Snippet — Thinking Mode**

```python
thinking_config = types.ThinkingConfig(
    include_thoughts=True,
    thinking_budget=MODEL_THINKING_BUDGET
)

response = client.models.generate_content(
    model=model,
    contents=context_text,
    config=GenerateContentConfig(
        thinking_config=thinking_config
    )
)
```

---

## 🤝 **Contributing**

Pull requests and suggestions are welcome!
Feel free to open an issue if you’d like to:

* Add new features
* Improve reasoning modes
* Extend architecture
* Enhance the UI

---

## 📄 **License**

MIT License — free to use, modify, and distribute.

---

## 🙌 **Acknowledgements**

This project was created as part of a personal learning journey exploring:

* AI reasoning
* System design
* Prompt engineering
* Human-friendly explanation design

Powered by:

* **Google Gemini**
* **Streamlit**
* **Python**

