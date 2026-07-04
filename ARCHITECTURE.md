# MetaPilot-AI Architecture

## Overview

MetaPilot-AI is a multi-AI orchestration system that combines multiple AI providers to deliver intelligent, aggregated results from a single request.

## System Architecture

```
MetaPilot-AI
├── Backend (FastAPI + Python)
│   ├── api/              # API Routes (AI, Auth, Merge)
│   ├── browser/          # Browser Automation
│   ├── database/         # Database Models & Connection
│   ├── export/           # Export Managers (HTML, JSON, Markdown)
│   ├── knowledge/        # Knowledge Base & Document Processing
│   ├── memory/           # Memory System & Vector Store
│   ├── merge/            # Conflict Resolution & Result Merging
│   ├── providers/        # AI Providers (OpenAI, Anthropic, Mistral, etc.)
│   ├── ranking/          # Result Ranking System
│   ├── scheduler/        # Task Scheduling
│   ├── security/         # Security & Authentication
│   ├── tests/            # Unit & Integration Tests
│   └── validator/        # Input Validation
│
├── Frontend (React + TypeScript + Tailwind)
│   ├── components/       # React Components
│   ├── context/          # React Context Providers
│   ├── hooks/            # Custom React Hooks
│   ├── pages/            # Application Pages
│   ├── services/         # API Services
│   ├── store/            # State Management (Zustand)
│   ├── types/            # TypeScript Types
│   └── utils/            # Utility Functions
│
├── Configs              # Configuration Files
├── Docker               # Container Configuration
├── Scripts              # Development & Startup Scripts
└── Knowledge Base       # Document Storage & Embeddings
```

## Core Components

### 1. API Layer
- **ai_router.py**: Handles AI request routing
- **auth_router.py**: Authentication and authorization
- **merge_router.py**: Result merging and aggregation

### 2. AI Providers
- **base.py**: Base provider interface
- **openai_provider.py**: OpenAI API integration
- **anthropic_provider.py**: Anthropic API integration
- **mistral_provider.py**: Mistral API integration
- **google_provider.py**: Google AI integration
- **perplexity_provider.py**: Perplexity AI integration
- **local_gguf.py**: Local GGUF model support

### 3. Database
- **models.py**: SQLAlchemy models
- **connection.py**: Database connection management
- **seed.py**: Database seeding
- **migrations/**: Alembic migrations

### 4. Frontend Structure
- **App.tsx**: Main application component
- **main.tsx**: Application entry point
- **pages/**: All application pages
- **components/**: Reusable UI components
- **store/**: Zustand state management
- **services/**: API service layer

## Data Flow

```
User Request -> API Router -> Provider Selection -> Parallel AI Calls 
                          -> Result Aggregation -> Ranking -> Final Response
```

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.10+
- **Database**: SQLAlchemy + PostgreSQL
- **Async**: asyncio
- **AI Libraries**: openai, anthropic, mistralai, google-genai

### Frontend
- **Framework**: React 18+
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Build Tool**: Vite
- **State Management**: Zustand
- **HTTP Client**: Axios

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **CI/CD**: GitHub Actions

## Security
- JWT Authentication
- Rate Limiting
- Input Validation
- API Key Management
- HTTPS Enforcement

## Scalability
- Horizontal scaling with Docker
- Load balancing support
- Caching mechanisms
- Async processing for long-running tasks

---

*Last Updated: July 4, 2026*