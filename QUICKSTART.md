# MetaPilot-AI Quick Start Guide

Get MetaPilot-AI running in just a few minutes!

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10 or higher**
- **Node.js 18 or higher**
- **PostgreSQL** (or use the included Docker setup)
- **Docker & Docker Compose** (recommended)
- **Git**

## Quick Installation

### Option 1: Docker (Recommended)

The easiest way to run MetaPilot-AI is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/abdulraheemnohri/MetaPilot-AI.git
cd MetaPilot-AI

# Copy environment files
cp .env.example .env
cp frontend/.env.example frontend/.env

# Edit .env and add your API keys
# You'll need at least one AI provider API key
nano .env

# Start all services (backend, frontend, database)
docker-compose up -d

# Access the application at http://localhost:3000
```

### Option 2: Local Development

For development without Docker:

```bash
# Clone the repository
git clone https://github.com/abdulraheemnohri/MetaPilot-AI.git
cd MetaPilot-AI

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venvScriptsactivate

# Install backend dependencies
pip install -r requirements.txt

# Set up frontend
cd frontend
npm install
cd ..

# Configure environment
cp .env.example .env
cp frontend/.env.example frontend/.env
# Edit both .env files with your settings

# Start PostgreSQL (if not using Docker)
# Make sure PostgreSQL is running and create a database

# Initialize database
python scripts/dev.py --init-db

# Start backend in one terminal
python scripts/start.py

# Start frontend in another terminal
cd frontend
npm run dev

# Access at http://localhost:3000
```

## Configuration

### Required API Keys

Edit the `.env` file and add at least one AI provider API key:

```ini
# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key

# Mistral
MISTRAL_API_KEY=your_mistral_api_key

# Google
GOOGLE_AI_API_KEY=your_google_api_key

# Perplexity
PERPLEXITY_API_KEY=your_perplexity_api_key
```

> **Note:** You only need one provider to start. Add more as needed.

### Database Configuration

In `.env`:

```ini
# PostgreSQL (default)
DATABASE_URL=postgresql://user:password@localhost:5432/metapilot

# Or SQLite for development
DATABASE_URL=sqlite:///./metapilot.db
```

### Frontend Configuration

In `frontend/.env`:

```ini
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## First Run

After starting the application:

1. **Register an account** at http://localhost:3000/register
2. **Log in** with your credentials
3. **Go to Settings** to configure your AI providers
4. **Start a new chat** and test your first query!

## Using the API Directly

The backend API is available at `http://localhost:8000`:

```bash
# Health check
curl http://localhost:8000/health

# List available providers
curl -H "Authorization: Bearer YOUR_TOKEN"      http://localhost:8000/api/providers

# Send a query
curl -X POST      -H "Authorization: Bearer YOUR_TOKEN"      -H "Content-Type: application/json"      -d '{"query": "Hello, world!"}'      http://localhost:8000/api/chat
```

## Troubleshooting

### Common Issues

**1. Port already in use**
```bash
# Find and kill the process
lsof -i :3000  # or :8000
kill -9 PID
```

**2. Missing Python dependencies**
```bash
pip install -r requirements.txt
```

**3. Database connection failed**
- Ensure PostgreSQL is running
- Check your `.env` database URL
- Try SQLite for development

**4. Frontend not loading**
- Ensure Node.js is installed
- Run `npm install` in the frontend directory
- Check for errors in the browser console

### Get Help

- **Documentation**: Check the [README.md](README.md)
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Contributing**: Read [CONTRIBUTING.md](CONTRIBUTING.md)
- **Issues**: Open an issue on [GitHub](https://github.com/abdulraheemnohri/MetaPilot-AI/issues)

---

**Enjoy using MetaPilot-AI!** 🚀

*Last Updated: July 4, 2026*