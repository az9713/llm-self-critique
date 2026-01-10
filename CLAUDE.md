# CLAUDE.md - Instructions for Claude Code

This file provides context and guidelines for Claude Code when working on this project.

## Project Overview

**Self-Critique Planning Platform** - An LLM-powered planning system implementing Google DeepMind's intrinsic self-critique methodology. The platform helps users define planning domains through natural language conversation, generates PDDL (Planning Domain Definition Language) specifications, and creates optimized plans through iterative self-critique.

## Tech Stack

### Backend (Python 3.11+)
- **FastAPI** - Async web framework for REST APIs and WebSockets
- **SQLAlchemy 2.0** - Async ORM with PostgreSQL/SQLite support
- **Pydantic** - Data validation and serialization
- **Anthropic SDK** - Claude API integration
- **OpenAI SDK** - OpenAI API integration (alternative provider)
- **pytest** - Testing framework with async support

### Frontend (Node.js 18+)
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Component library

## Project Structure

```
llm-self-critique/
├── backend/
│   ├── src/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── database.py          # SQLAlchemy async setup
│   │   ├── api/                  # REST API endpoints
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── llm/                  # LLM provider adapters
│   │   ├── critique/             # Self-critique orchestration
│   │   ├── elicitation/          # Domain elicitation chatbot
│   │   ├── pddl/                 # PDDL parser and validator
│   │   ├── websocket/            # Real-time communication
│   │   └── middleware/           # Request middleware
│   └── tests/                    # pytest test suite
├── frontend/
│   └── src/
│       ├── app/                  # Next.js App Router pages
│       ├── components/           # React components
│       ├── hooks/                # Custom React hooks
│       ├── lib/                  # Utility functions
│       └── types/                # TypeScript types
└── docs/                         # Documentation and plans
```

## Running the Project

### Backend
```bash
cd backend
pip install -e ".[dev]"
python -m uvicorn src.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Running Tests
```bash
cd backend
python -m pytest tests/ -v
```

## Key Architectural Decisions

### 1. Async Everything
All database operations and API endpoints use async/await. When adding new code:
- Use `async def` for all endpoint handlers
- Use `await` for database operations
- Use `AsyncSession` from SQLAlchemy

### 2. LLM Provider Abstraction
The `src/llm/` module provides a unified interface for multiple LLM providers:
- `LLMAdapter` base class defines the interface
- `ClaudeAdapter` and `OpenAIAdapter` implement provider-specific logic
- `LLMRouter` handles provider selection and fallback
- Default model: `claude-3-5-haiku-20241022` (Claude 3.5 Haiku)

### 3. Self-Critique Loop
The critique system (`src/critique/`) implements:
1. Initial plan generation
2. Multi-perspective critique (3 critics by default)
3. Weighted voting to aggregate feedback
4. Iterative refinement until consensus or max iterations

### 4. WebSocket Real-time Updates
Planning sessions stream progress via WebSocket:
- `ws://localhost:8000/ws/plan/{session_id}` for planning updates
- `ws://localhost:8000/ws/chat/{session_id}` for chat messages

## Common Development Tasks

### Adding a New API Endpoint
1. Create/update schemas in `src/schemas/`
2. Add endpoint in appropriate `src/api/` module
3. Register router in `src/main.py` if new file
4. Add tests in `tests/api/`

### Adding a New Database Model
1. Create model in `src/models/`
2. Export from `src/models/__init__.py`
3. Create Alembic migration (if using migrations)
4. Add corresponding Pydantic schemas

### Adding a New LLM Provider
1. Create adapter in `src/llm/adapters/`
2. Implement `LLMAdapter` interface
3. Register in `LLMRouter`

## Testing Conventions

- All tests use pytest with async support
- Test files mirror source structure: `src/api/domains.py` → `tests/api/test_domains.py`
- Use fixtures for database setup/teardown
- Mock external services (LLM APIs) in unit tests

## Code Style

- Follow PEP 8 for Python
- Use type hints everywhere
- Docstrings for public functions
- Keep functions focused and small
- Prefer composition over inheritance

## Code Simplification

This project uses the `code-simplifier:code-simplifier` Claude Code plugin to maintain code quality.

### Running Code Simplifier
```
Use code-simplifier on recently modified files
```

### What It Does
- Removes unused imports and dead code
- Extracts repeated logic into helper functions
- Replaces print statements with proper logging
- Adds missing type annotations
- Standardizes error handling patterns

### When to Use
- After completing a feature or bug fix
- Before creating a pull request
- During code review to identify cleanup opportunities

### Documentation
See `docs/CODE_SIMPLIFIER_CHANGELOG.md` for a history of refinements made by this tool.

## Environment Variables

Create a `.env` file in the `backend/` directory (copy from `.env.example`):

```bash
# Required for LLM features (at least one)
ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...

# Optional
# DATABASE_URL=sqlite+aiosqlite:///./app.db
# LOG_LEVEL=INFO
```

The backend automatically loads `.env` on startup using python-dotenv.

## Important Notes

1. **Database**: Default is SQLite for development. For production, use PostgreSQL.

2. **Rate Limiting**: Enabled by default (100 req/min). Adjust in `src/main.py`.

3. **PDDL Validation**: The validator checks syntax and semantics but doesn't execute plans.

4. **WebSocket Connections**: Always handle disconnection gracefully.

5. **API Keys**: Never commit API keys. Use environment variables.

## Troubleshooting

### "Module not found" errors
```bash
cd backend
pip install -e ".[dev]"
```

### Database errors
```bash
# Reset database
rm backend/*.db
# Restart server to recreate tables
```

### WebSocket connection issues
- Check CORS settings in `src/main.py`
- Ensure frontend uses correct WebSocket URL

## Current Test Coverage

- 184 tests passing
- Coverage areas: API, LLM, Critique, Elicitation, PDDL, WebSocket, Middleware

## Future Development Areas

1. **Authentication**: Currently no auth. Add JWT-based authentication.
2. **Plan Execution**: Add actual PDDL solver integration.
3. **Collaboration**: Multi-user domain editing.
4. **Plan History**: Version control for plans.
5. **Export**: Export domains/plans to various formats.
