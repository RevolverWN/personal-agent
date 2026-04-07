# Personal Agent

A personal AI agent with multi-model support, featuring a modern Web UI and flexible deployment options.

## Features

- 🤖 **Multi-Model Support**: OpenAI, Claude, DeepSeek, Moonshot (Kimi), and more
- 💬 **Chat Interface**: Real-time streaming chat with conversation history
- 🔧 **Customizable**: Configure model parameters, system prompts, and tools
- 📁 **File Management**: Upload and manage files for AI analysis
- 🎨 **Modern UI**: Clean, responsive interface built with React + Tailwind CSS
- 🐳 **Easy Deployment**: Docker support for quick deployment

## Tech Stack

### Backend
- FastAPI + Python 3.11+
- SQLAlchemy + SQLite/PostgreSQL
- LiteLLM for unified LLM access
- JWT authentication

### Frontend
- React 18 + TypeScript
- Vite + Tailwind CSS
- Zustand for state management
- React Query for data fetching

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker (optional)

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/personal-agent.git
cd personal-agent
```

2. **Setup Backend**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with your API keys
uvicorn app.main:app --reload
```

3. **Setup Frontend**
```bash
cd frontend
npm install
npm run dev
```

4. **Access the application**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Docker Deployment

```bash
# Production
docker-compose -f docker/docker-compose.yml up -d

# Development (with hot-reload)
docker-compose -f docker/docker-compose.dev.yml up -d
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required
SECRET_KEY=your-secret-key

# LLM API Keys (at least one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=sk-...
MOONSHOT_API_KEY=sk-...
```

## Project Structure

```
personal-agent/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/      # API routes
│   │   ├── agent/    # Agent core logic
│   │   ├── models/   # Database models
│   │   └── core/     # Security, exceptions
│   └── tests/
├── frontend/          # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── stores/
├── docker/           # Docker configurations
└── docs/             # Documentation
```

## Development

### Backend

```bash
cd backend

# Run tests
pytest

# Run linting
ruff check app tests
ruff format app tests

# Run type checker
mypy app
```

### Frontend

```bash
cd frontend

# Run linter
npm run lint

# Format code
npm run format
```

## API Documentation

When the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by [DeerFlow](https://github.com/bytedance/deer-flow), [nanobot](https://github.com/HKUDS/nanobot), and [CoPaw](https://github.com/agentscope-ai/CoPaw)
- Built with [FastAPI](https://fastapi.tiangolo.com/) and [React](https://react.dev/)
