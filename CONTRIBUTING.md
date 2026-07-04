# Contributing to MetaPilot-AI

We welcome contributions from the community! Here's how you can help make MetaPilot-AI better.

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL
- Docker & Docker Compose
- Git

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/abdulraheemnohri/MetaPilot-AI.git
cd MetaPilot-AI
```

2. **Set up the backend:**
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venvScriptsactivate

# Install dependencies
pip install -r requirements.txt
```

3. **Set up the frontend:**
```bash
cd frontend
npm install
cd ..
```

4. **Configure environment variables:**
```bash
# Copy example files
cp .env.example .env
cp frontend/.env.example frontend/.env

# Edit with your API keys
nano .env
nano frontend/.env
```

5. **Run the application:**
```bash
# Start backend
docker-compose up -d

# Or run locally
python scripts/start.py

# Start frontend (in another terminal)
cd frontend
npm run dev
```

## Development Workflow

### Backend Development

- All backend code is in the `backend/` directory
- API routes are defined in `backend/api/`
- AI providers are in `backend/providers/`
- Database models are in `backend/database/`

### Frontend Development

- All frontend code is in the `frontend/` directory
- React components are in `frontend/src/components/`
- Pages are in `frontend/src/pages/`
- State management uses Zustand

### Adding a New AI Provider

1. Create a new file in `backend/providers/` following the pattern of existing providers
2. Implement the `BaseProvider` interface from `base.py`
3. Register the provider in `registry.py`
4. Add configuration options to `config.py`

### Adding a New Frontend Page

1. Create a new file in `frontend/src/pages/`
2. Add a route in the main router
3. Add navigation link in the sidebar

## Code Style

### Python
- Follow PEP 8 guidelines
- Use type hints
- Use async/await for I/O operations
- Keep functions focused and single-purpose

### TypeScript
- Use TypeScript strict mode
- Define interfaces for API responses
- Use functional components with React hooks
- Follow React best practices

### Git Commit Messages
- Use conventional commits
- Keep messages clear and concise
- Reference issues when applicable

## Testing

### Backend Tests
```bash
# Run all tests
python -m pytest backend/tests/

# Run with coverage
python -m pytest --cov=backend backend/tests/
```

### Frontend Tests
```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage
```

## Pull Request Guidelines

1. **Fork the repository** and create your branch from `main`
2. **Give your branch a descriptive name** (e.g., `feat/add-openai-provider`)
3. **Add tests** for new functionality
4. **Update documentation** if needed
5. **Ensure all tests pass** before submitting
6. **Use clear commit messages**
7. **Reference any relevant issues**

## Reporting Issues

When reporting issues, please include:

- Your operating system
- Python/Node.js versions
- Steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable
- Error logs

## License

By contributing to MetaPilot-AI, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).

---

Thank you for contributing to MetaPilot-AI! Your help makes this project better for everyone.

*Last Updated: July 4, 2026*