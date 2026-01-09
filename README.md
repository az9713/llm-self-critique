# Self-Critique Planning Platform

> **About:** AI planning platform using LLM intrinsic self-critique. Based on Google DeepMind research (arXiv:2512.24103). Built with Claude Code + Opus 4.5.

> **Status:** This project is under active development. Features may be incomplete or subject to change.

An intelligent planning system that uses Large Language Models (LLMs) with intrinsic self-critique to generate high-quality plans. Based on Google DeepMind's research on improving LLM planning through iterative refinement.

## What This Application Does

This platform helps you:

1. **Define Planning Domains** - Describe your planning problem in plain English through a conversational interface
2. **Generate PDDL Specifications** - Automatically convert natural language to formal planning language
3. **Create Optimized Plans** - Generate action sequences that achieve your goals
4. **Self-Critique and Refine** - Multiple AI "critics" review and improve plans iteratively

### Example Use Case

Imagine you're planning a kitchen renovation:
- Tell the system about your tasks: "I need to remove old cabinets, install new ones, paint walls, and install flooring"
- Specify constraints: "Painting must happen before installing cabinets, flooring comes last"
- The system generates an optimal sequence of actions
- AI critics review: "Installing flooring should happen before painting to avoid paint drips on new floor"
- The plan is refined based on critique

## Quick Links

| Document | Description |
|----------|-------------|
| [Quick Start Guide](docs/QUICK_START.md) | Get running in 10 minutes with hands-on examples |
| [User Guide](docs/USER_GUIDE.md) | Complete guide for using the application |
| [Developer Guide](docs/DEVELOPER_GUIDE.md) | Technical documentation for developers |
| [API Reference](docs/API_REFERENCE.md) | Complete API documentation |
| [Architecture Overview](docs/ARCHITECTURE.md) | System design and components |

## System Requirements

### For Users (Running Pre-built Application)
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection for AI features

### For Developers (Building from Source)
- **Python 3.11 or higher** - Backend runtime
- **Node.js 18 or higher** - Frontend runtime
- **Git** - Version control
- **4GB RAM minimum** - 8GB recommended
- **API Keys** - Anthropic (Claude) or OpenAI API key

## Quick Start (5 Minutes)

### Step 1: Clone the Repository
```bash
git clone https://github.com/az9713/llm-self-critique.git
cd llm-self-critique
```

### Step 2: Set Up Backend
```bash
# Navigate to backend
cd backend

# Create virtual environment (isolates Python packages)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Set your API key (get one from https://console.anthropic.com/)
# On Windows:
set ANTHROPIC_API_KEY=your-key-here
# On Mac/Linux:
export ANTHROPIC_API_KEY=your-key-here

# Start the backend server
python -m uvicorn src.main:app --reload --port 8000
```

### Step 3: Set Up Frontend (New Terminal)
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Step 4: Open the Application
Open your browser and go to: **http://localhost:3000**

## Project Structure Overview

```
llm-self-critique/
│
├── backend/                 # Python FastAPI server
│   ├── src/                 # Source code
│   │   ├── api/             # REST API endpoints
│   │   ├── models/          # Database models
│   │   ├── llm/             # AI/LLM integration
│   │   ├── critique/        # Self-critique system
│   │   ├── elicitation/     # Conversation engine
│   │   └── pddl/            # Planning language parser
│   └── tests/               # Automated tests
│
├── frontend/                # Next.js React application
│   └── src/
│       ├── app/             # Pages and routes
│       ├── components/      # UI components
│       └── hooks/           # React hooks
│
└── docs/                    # Documentation
```

## Key Features

### 1. Natural Language Domain Definition
Talk to the system in plain English to define your planning problem. No need to learn complex formal languages.

### 2. Multi-Agent Self-Critique
Three AI "critics" with different perspectives review generated plans:
- **Completeness Critic**: Are all goals achievable?
- **Efficiency Critic**: Is this the optimal approach?
- **Safety Critic**: Are there any risks or conflicts?

### 3. Real-Time Progress Updates
Watch the planning process unfold with live updates via WebSocket connections.

### 4. PDDL Validation
Automatically validates generated planning specifications for correctness.

### 5. Analytics Dashboard
Track usage, monitor performance, and analyze planning patterns.

### 6. API Access
Programmatic access with rate limiting and API key management.

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Next.js 14 | React-based web interface |
| Backend | FastAPI | High-performance Python API |
| Database | SQLite/PostgreSQL | Data persistence |
| AI | Claude/OpenAI | Language model integration |
| Real-time | WebSocket | Live updates |

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

All 182 tests should pass.

## Getting Help

1. Check the [User Guide](docs/USER_GUIDE.md) for usage questions
2. Check the [Developer Guide](docs/DEVELOPER_GUIDE.md) for technical questions
3. Search existing issues on GitHub
4. Open a new issue with detailed description

## Contributing

We welcome contributions! Please read our contributing guidelines before submitting pull requests.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

### Research Foundation
This work is inspired by the paper ["Enhancing LLM Planning Capabilities through Intrinsic Self-Critique"](https://arxiv.org/abs/2512.24103) (arXiv:2512.24103v1) by Google DeepMind. See our [Arxiv Paper Primer](docs/ARXIV_PAPER_PRIMER.md) for details.

### Development Methodology
This project was built using skills from the [Superpowers plugin](https://github.com/superpowers-ai/superpowers) for Claude Code:
- **brainstorming** - Initial ideation and design exploration
- **writing-plans** - Creating detailed implementation plans
- **subagent-driven-development** - Executing plans with fresh subagents per task and two-stage review

### AI-Generated Codebase
All code and documentation in this project were generated by [Claude Code](https://claude.ai/claude-code) using **Claude Opus 4.5**. The initial project brainstorming was conducted using Claude Code's `AskUserQuestion` tool for interactive requirement gathering.

### Technologies
Built with FastAPI, Next.js, and modern AI APIs.
