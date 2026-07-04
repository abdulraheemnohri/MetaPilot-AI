# MetaPilot AI

> "One Request. Multiple AI Systems. One Intelligent Result."

MetaPilot AI is a completely local-first AI orchestration platform. It uses a lightweight on-device AI model for planning and reasoning, while delegating specialized work to multiple supported AI providers using official APIs or user-authorized browser integrations.

## 🌟 Core Vision

The platform automatically:
- **Understands user intent** via local reasoning.
- **Breaks large tasks** into smaller, manageable subtasks.
- **Selects the most suitable AI/provider** for each subtask.
- **Executes tasks in parallel** where possible.
- **Collects and validates responses** (deduplication, contradiction detection).
- **Scores and merges results** into one polished final response.

## 🏗️ Architecture

```
User
 ↓
MetaPilot AI
 ↓
Intent Analyzer → Planner → Task Splitter → Routing Engine
 ↓
Capability Database
 ↓
Execution Manager → Parallel Workers
 ↓
[ Supported AI Providers | Local Models | MCP Servers | Tools | Knowledge Bases ]
 ↓
Response Collector → Validator → Fact Checker → Ranking Engine → Merge Engine
 ↓
Final Result
```

## 🚀 Key Modules

### 💻 Home Dashboard
- Recent conversations and running tasks.
- Real-time AI status and model usage.
- Local model stats (GPU/CPU/RAM) and queue monitor.

### 💬 Chat Workspace
- Modern AI chat with Markdown, Code blocks, and Tables.
- File uploads and voice input/output support.
- Multi-turn memory and project-specific context.

### 🧠 AI Router & Planner
- **Intelligent Routing**: Automatically selects the best provider (e.g., Coding → Local/DeepSeek, Research → Perplexity).
- **Task Splitting**: Decomposes complex prompts (e.g., "Build a React app") into subtasks (Frontend, Backend, Auth, etc.).
- **Dependency Graph**: Manages execution order and retry strategies.

### 🌐 Browser Integration
- User-authorized browser automation for services without official APIs.
- Supports tab management, login session reuse, and DOM extraction.

## 🛠️ Technology Stack

- **Frontend**: React, TypeScript, Tailwind CSS, Zustand.
- **Backend**: Python, FastAPI, SQLAlchemy.
- **Database**: SQLite (local-first), PostgreSQL support.
- **AI Engine**: GGUF via llama-cpp-python, ONNX Runtime, Transformers.
- **Automation**: Playwright.

## 🔌 Supported Providers

### Browser-based (Playwright)
- ChatGPT (Browser)
- Claude (Browser)
- Gemini (Browser)
- Perplexity (Browser)
- DeepSeek (Browser)
- Mistral (Browser)
- HuggingChat (Browser)

### API-based
- OpenAI, Anthropic, Mistral, Google, Perplexity.
- Local GGUF models.

## 🛠️ Getting Started

### Prerequisites
- Python 3.10+
- Node.js & npm
- Playwright browsers: `playwright install chromium`

### Installation
1. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Install frontend dependencies:
   ```bash
   cd frontend && npm install
   ```

### Running the Platform
Use the provided development script:
`bash
python scripts/dev.py
`
Backend will run on `http://localhost:8000` and Frontend on `http://localhost:3000`.

## 📜 License
This project is licensed under the MIT License.
