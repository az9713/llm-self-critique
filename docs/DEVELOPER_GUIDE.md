# Developer Guide

Complete technical guide for developers working on the Self-Critique Planning Platform. This guide assumes you have programming experience (C, C++, Java, etc.) but may be new to Python web development and modern JavaScript frameworks.

## Table of Contents

1. [Introduction for Traditional Developers](#introduction-for-traditional-developers)
2. [Development Environment Setup](#development-environment-setup)
3. [Project Architecture](#project-architecture)
4. [Backend Deep Dive](#backend-deep-dive)
5. [Frontend Deep Dive](#frontend-deep-dive)
6. [Database Layer](#database-layer)
7. [Testing Guide](#testing-guide)
8. [Adding New Features](#adding-new-features)
9. [Common Patterns](#common-patterns)
10. [Debugging Guide](#debugging-guide)
11. [Deployment](#deployment)
12. [Contributing](#contributing)

---

## Introduction for Traditional Developers

If you're coming from C, C++, or Java, here's what's different:

### Python vs C/C++/Java

| Concept | C/C++/Java | Python |
|---------|------------|--------|
| Compilation | Compiled to binary | Interpreted at runtime |
| Type System | Static, explicit | Dynamic, optional hints |
| Memory | Manual/GC | Automatic GC |
| Entry Point | `main()` function | Script execution or `if __name__ == "__main__"` |
| Packages | Include/Import, compile | pip install, import |
| Build System | Make/CMake/Maven | pip/setuptools |

### JavaScript/TypeScript vs Traditional Languages

| Concept | Traditional | JavaScript/TypeScript |
|---------|------------|----------------------|
| Execution | Compiled | Interpreted (browser/Node.js) |
| Concurrency | Threads | Single-threaded event loop |
| Types | Static | Dynamic (TS adds static) |
| UI | GUI frameworks | HTML/CSS/DOM |

### Async Programming

This project uses **async/await** extensively. If you're used to threading:

**Traditional Threading (Java):**
```java
Thread thread = new Thread(() -> {
    String result = fetchData();
    processResult(result);
});
thread.start();
```

**Async/Await (Python):**
```python
async def main():
    result = await fetch_data()  # Non-blocking wait
    process_result(result)
```

**Key Insight**: Async doesn't create new threads. It lets one thread handle many operations by switching between them when they wait for I/O.

---

## Development Environment Setup

### Step 1: Install Required Software

#### Python 3.11+

**Windows:**
1. Download from https://python.org
2. Run installer
3. ✅ Check "Add Python to PATH"
4. Verify: `python --version`

**Mac:**
```bash
brew install python@3.11
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

#### Node.js 18+

**All Platforms:**
1. Download from https://nodejs.org (LTS version)
2. Run installer
3. Verify: `node --version` and `npm --version`

#### Git

**Windows:**
Download from https://git-scm.com

**Mac:**
```bash
xcode-select --install
```

**Linux:**
```bash
sudo apt install git
```

#### IDE Recommendation

**VS Code** with extensions:
- Python (Microsoft)
- Pylance
- ESLint
- Prettier
- TypeScript and JavaScript Language Features

### Step 2: Clone and Setup

```bash
# Clone repository
git clone https://github.com/az9713/llm-self-critique.git
cd llm-self-critique
```

### Step 3: Backend Setup

```bash
cd backend

# Create virtual environment
# This isolates project dependencies from system Python
python -m venv venv

# Activate virtual environment
# Windows CMD:
venv\Scripts\activate
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Mac/Linux:
source venv/bin/activate

# Your prompt should now show (venv)

# Install project in development mode
# -e means "editable" - changes take effect immediately
# [dev] includes testing dependencies
pip install -e ".[dev]"
```

**Understanding pip install -e ".[dev]":**
- `.` = current directory (where pyproject.toml is)
- `-e` = editable mode (like Java's source folders)
- `[dev]` = include development dependencies (pytest, etc.)

### Step 4: Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install
```

**Understanding npm install:**
- Reads `package.json` for dependencies
- Downloads packages to `node_modules/`
- Creates `package-lock.json` (lock file)

### Step 5: Environment Variables

Create a `.env` file in the backend directory:

```bash
# backend/.env
ANTHROPIC_API_KEY=sk-ant-your-key-here
DATABASE_URL=sqlite+aiosqlite:///./app.db
LOG_LEVEL=DEBUG
```

**Or set in terminal:**
```bash
# Windows CMD
set ANTHROPIC_API_KEY=sk-ant-xxx

# Windows PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-xxx"

# Mac/Linux
export ANTHROPIC_API_KEY=sk-ant-xxx
```

### Step 6: Verify Setup

```bash
# Backend tests
cd backend
python -m pytest tests/ -v

# Expected: 182 tests passed

# Start backend
python -m uvicorn src.main:app --reload --port 8000

# In new terminal, start frontend
cd frontend
npm run dev
```

Open http://localhost:3000 - you should see the application.

---

## Project Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                │
│                     (Next.js/React)                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │  Pages  │  │Components│  │  Hooks  │  │   API   │           │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘           │
└───────┼────────────┼────────────┼────────────┼──────────────────┘
        │            │            │            │
        └────────────┴────────────┴────────────┘
                          │
              HTTP/REST   │   WebSocket
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Backend                                 │
│                       (FastAPI)                                │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │   API   │  │   LLM   │  │Critique │  │  PDDL   │           │
│  │ Routes  │  │ Router  │  │ System  │  │ Parser  │           │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘           │
│       │            │            │            │                  │
│       └────────────┴────────────┴────────────┘                  │
│                          │                                      │
│                    ┌─────┴─────┐                                │
│                    │  Database │                                │
│                    │(SQLAlchemy)│                               │
│                    └───────────┘                                │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                            │
│         ┌─────────────┐    ┌─────────────┐                     │
│         │  Anthropic  │    │   OpenAI    │                     │
│         │  (Claude)   │    │   (GPT)     │                     │
│         └─────────────┘    └─────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

### Directory Structure Explained

```
llm-self-critique/
│
├── backend/                      # Python FastAPI application
│   ├── pyproject.toml           # Python project config (like pom.xml/build.gradle)
│   │
│   ├── src/                     # Source code
│   │   ├── __init__.py          # Makes this a Python package
│   │   ├── main.py              # Application entry point
│   │   ├── database.py          # Database connection setup
│   │   │
│   │   ├── api/                 # HTTP endpoints (REST API)
│   │   │   ├── __init__.py      # Router aggregation
│   │   │   ├── domains.py       # /api/v1/domains/*
│   │   │   ├── planning.py      # /api/v1/planning/*
│   │   │   ├── chat.py          # /api/v1/chat/*
│   │   │   ├── validation.py    # /api/v1/validation/*
│   │   │   ├── analytics.py     # /api/v1/analytics/*
│   │   │   └── api_keys.py      # /api/v1/api-keys/*
│   │   │
│   │   ├── models/              # Database models (like JPA entities)
│   │   │   ├── __init__.py
│   │   │   ├── user.py          # User model
│   │   │   ├── domain.py        # Domain model
│   │   │   ├── planning.py      # Plan model
│   │   │   └── analytics.py     # Usage tracking models
│   │   │
│   │   ├── schemas/             # Data transfer objects (DTOs)
│   │   │   ├── domain.py        # Domain request/response schemas
│   │   │   └── planning.py      # Planning request/response schemas
│   │   │
│   │   ├── llm/                 # LLM integration layer
│   │   │   ├── base.py          # Abstract base class
│   │   │   ├── router.py        # Provider selection
│   │   │   └── adapters/        # Provider implementations
│   │   │       ├── claude.py    # Anthropic adapter
│   │   │       └── openai.py    # OpenAI adapter
│   │   │
│   │   ├── critique/            # Self-critique system
│   │   │   ├── orchestrator.py  # Main critique loop
│   │   │   ├── parser.py        # Parse critique responses
│   │   │   └── voting.py        # Aggregate feedback
│   │   │
│   │   ├── elicitation/         # Domain elicitation chatbot
│   │   │   ├── state_machine.py # Conversation state
│   │   │   ├── chat_handler.py  # Process messages
│   │   │   ├── completeness.py  # Check domain completeness
│   │   │   └── pddl_generator.py# Convert to PDDL
│   │   │
│   │   ├── pddl/                # PDDL handling
│   │   │   ├── parser.py        # Parse PDDL syntax
│   │   │   └── validator.py     # Validate semantics
│   │   │
│   │   ├── websocket/           # Real-time communication
│   │   │   ├── manager.py       # Connection management
│   │   │   └── notifications.py # Send updates
│   │   │
│   │   └── middleware/          # Request processing
│   │       ├── usage_tracking.py# Log API usage
│   │       └── rate_limiting.py # Rate limit enforcement
│   │
│   └── tests/                   # Test suite (mirrors src/ structure)
│       ├── api/
│       ├── llm/
│       ├── critique/
│       ├── elicitation/
│       ├── pddl/
│       ├── websocket/
│       └── middleware/
│
├── frontend/                    # Next.js React application
│   ├── package.json            # Node.js project config
│   ├── tsconfig.json           # TypeScript configuration
│   ├── tailwind.config.ts      # CSS framework config
│   │
│   └── src/
│       ├── app/                 # Next.js App Router (pages)
│       │   ├── layout.tsx       # Root layout
│       │   ├── page.tsx         # Home page (/)
│       │   ├── (auth)/          # Auth pages group
│       │   │   ├── login/
│       │   │   └── register/
│       │   └── dashboard/       # Dashboard pages
│       │       ├── page.tsx     # /dashboard
│       │       └── domain/[id]/ # /dashboard/domain/:id
│       │
│       ├── components/          # React components
│       │   ├── chat/            # Chat interface
│       │   ├── planning/        # Planning display
│       │   ├── validation/      # Validation display
│       │   └── layout/          # Layout components
│       │
│       ├── hooks/               # Custom React hooks
│       │   ├── useWebSocket.ts  # WebSocket connection
│       │   └── useValidation.ts # Validation API
│       │
│       ├── lib/                 # Utility functions
│       │   └── api.ts           # API client
│       │
│       └── types/               # TypeScript type definitions
│           └── index.ts
│
└── docs/                        # Documentation
    ├── QUICK_START.md
    ├── USER_GUIDE.md
    ├── DEVELOPER_GUIDE.md       # This file
    ├── API_REFERENCE.md
    └── ARCHITECTURE.md
```

---

## Backend Deep Dive

### FastAPI Basics

FastAPI is a modern Python web framework. If you know Express.js (Node), Flask (Python), or Spring Boot (Java), it's similar.

**Entry Point (src/main.py):**
```python
from fastapi import FastAPI

app = FastAPI(
    title="Self-Critique Planner API",
    description="LLM Planning Platform",
    version="0.1.0",
)

# Add middleware (runs for every request)
app.add_middleware(UsageTrackingMiddleware, enabled=True)
app.add_middleware(RateLimitMiddleware, enabled=True)

# Include routers (like controllers)
app.include_router(api_router)
app.include_router(websocket_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### Creating an Endpoint

**Step-by-Step: Add a new endpoint**

1. **Create/Update Schema** (src/schemas/example.py):
```python
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class ExampleCreate(BaseModel):
    """Request body for creating an example."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class ExampleResponse(BaseModel):
    """Response body for an example."""
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mode
```

2. **Create Model** (src/models/example.py):
```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base
import uuid

class Example(Base):
    __tablename__ = "examples"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
```

3. **Create Endpoint** (src/api/example.py):
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db
from src.models.example import Example
from src.schemas.example import ExampleCreate, ExampleResponse

router = APIRouter(prefix="/api/v1/examples", tags=["examples"])

@router.post("", response_model=ExampleResponse)
async def create_example(
    request: ExampleCreate,
    db: AsyncSession = Depends(get_db),  # Dependency injection
) -> ExampleResponse:
    """Create a new example."""
    example = Example(
        name=request.name,
        description=request.description,
    )
    db.add(example)
    await db.commit()
    await db.refresh(example)
    return example

@router.get("/{example_id}", response_model=ExampleResponse)
async def get_example(
    example_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ExampleResponse:
    """Get an example by ID."""
    result = await db.execute(
        select(Example).where(Example.id == example_id)
    )
    example = result.scalar_one_or_none()

    if not example:
        raise HTTPException(status_code=404, detail="Example not found")

    return example
```

4. **Register Router** (src/main.py):
```python
from src.api.example import router as example_router

app.include_router(example_router, tags=["examples"])
```

5. **Export Model** (src/models/__init__.py):
```python
from src.models.example import Example
```

6. **Add Tests** (tests/api/test_example.py):
```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_create_example():
    response = client.post(
        "/api/v1/examples",
        json={"name": "Test", "description": "A test example"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test"
    assert "id" in data
```

### Understanding Dependency Injection

FastAPI uses `Depends()` for dependency injection (similar to Spring's `@Autowired`):

```python
from fastapi import Depends

# Define a dependency
async def get_db():
    async with async_session_maker() as session:
        yield session  # Generator - cleanup happens after request

# Use the dependency
@router.get("/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    # db is automatically injected
    ...
```

### The LLM Layer

**Base Class (src/llm/base.py):**
```python
from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel

class Message(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str

class LLMAdapter(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """Generate a response."""
        pass
```

**Claude Adapter (src/llm/adapters/claude.py):**
```python
import anthropic
from src.llm.base import LLMAdapter, Message

class ClaudeAdapter(LLMAdapter):
    def __init__(self, api_key: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def generate(
        self,
        messages: List[Message],
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        return response.content[0].text
```

### WebSocket Communication

**Manager (src/websocket/manager.py):**
```python
from fastapi import WebSocket
from typing import Dict, Set

class ConnectionManager:
    def __init__(self):
        # session_id -> set of websocket connections
        self.connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.connections:
            self.connections[session_id] = set()
        self.connections[session_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, session_id: str):
        self.connections[session_id].discard(websocket)

    async def broadcast(self, session_id: str, message: dict):
        if session_id in self.connections:
            for connection in self.connections[session_id]:
                await connection.send_json(message)
```

**Endpoint (src/api/websocket.py):**
```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.websocket.manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()

@router.websocket("/ws/planning/{session_id}")
async def planning_websocket(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_json()
            # Process incoming messages
            await manager.broadcast(session_id, {"type": "ack", "data": data})
    except WebSocketDisconnect:
        await manager.disconnect(websocket, session_id)
```

---

## Frontend Deep Dive

### Next.js App Router

Next.js 14 uses file-based routing. The file structure determines URL paths:

```
src/app/
├── page.tsx              → /
├── layout.tsx            → Wraps all pages
├── dashboard/
│   ├── page.tsx          → /dashboard
│   └── domain/
│       └── [id]/
│           ├── page.tsx  → /dashboard/domain/:id
│           └── plan/
│               └── page.tsx → /dashboard/domain/:id/plan
└── (auth)/               → Route group (doesn't affect URL)
    ├── layout.tsx        → Auth layout
    ├── login/
    │   └── page.tsx      → /login
    └── register/
        └── page.tsx      → /register
```

### React Component Basics

**For developers from traditional backgrounds:**

React components are functions that return UI:

```tsx
// Traditional approach (like a function that builds HTML)
function Greeting({ name }: { name: string }) {
    return <h1>Hello, {name}!</h1>;
}

// Usage
<Greeting name="World" />
```

**State Management:**
```tsx
import { useState } from 'react';

function Counter() {
    // useState returns [currentValue, setterFunction]
    const [count, setCount] = useState(0);

    return (
        <div>
            <p>Count: {count}</p>
            <button onClick={() => setCount(count + 1)}>
                Increment
            </button>
        </div>
    );
}
```

### Custom Hooks

Hooks encapsulate reusable logic:

```tsx
// src/hooks/useWebSocket.ts
import { useEffect, useState, useCallback } from 'react';

export function useWebSocket(url: string) {
    const [socket, setSocket] = useState<WebSocket | null>(null);
    const [messages, setMessages] = useState<any[]>([]);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        const ws = new WebSocket(url);

        ws.onopen = () => setIsConnected(true);
        ws.onclose = () => setIsConnected(false);
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            setMessages(prev => [...prev, data]);
        };

        setSocket(ws);

        // Cleanup when component unmounts
        return () => ws.close();
    }, [url]);

    const send = useCallback((data: any) => {
        if (socket && isConnected) {
            socket.send(JSON.stringify(data));
        }
    }, [socket, isConnected]);

    return { messages, isConnected, send };
}
```

**Usage:**
```tsx
function PlanningView({ sessionId }: { sessionId: string }) {
    const { messages, isConnected, send } = useWebSocket(
        `ws://localhost:8000/ws/planning/${sessionId}`
    );

    return (
        <div>
            <p>Status: {isConnected ? 'Connected' : 'Disconnected'}</p>
            {messages.map((msg, i) => (
                <div key={i}>{JSON.stringify(msg)}</div>
            ))}
        </div>
    );
}
```

### API Client

```tsx
// src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchDomains() {
    const response = await fetch(`${API_BASE}/api/v1/domains`);
    if (!response.ok) {
        throw new Error('Failed to fetch domains');
    }
    return response.json();
}

export async function createDomain(data: { name: string; description: string }) {
    const response = await fetch(`${API_BASE}/api/v1/domains`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        throw new Error('Failed to create domain');
    }
    return response.json();
}
```

---

## Database Layer

### SQLAlchemy ORM Basics

SQLAlchemy is like Hibernate (Java) or Entity Framework (.NET).

**Model Definition:**
```python
from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    # Relationship to domains
    domains: Mapped[list["Domain"]] = relationship(back_populates="user")


class Domain(Base):
    __tablename__ = "domains"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    pddl_domain: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship back to user
    user: Mapped["User"] = relationship(back_populates="domains")
```

### Async Database Operations

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_domains(db: AsyncSession, user_id: UUID) -> list[Domain]:
    """Get all domains for a user."""
    result = await db.execute(
        select(Domain)
        .where(Domain.user_id == user_id)
        .order_by(Domain.created_at.desc())
    )
    return list(result.scalars().all())

async def create_domain(db: AsyncSession, user_id: UUID, name: str) -> Domain:
    """Create a new domain."""
    domain = Domain(user_id=user_id, name=name)
    db.add(domain)
    await db.commit()
    await db.refresh(domain)  # Load auto-generated fields
    return domain
```

---

## Testing Guide

### Running Tests

```bash
cd backend

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/api/test_domains.py -v

# Run specific test function
python -m pytest tests/api/test_domains.py::test_create_domain -v

# Run with coverage report
python -m pytest tests/ --cov=src --cov-report=html
```

### Writing Tests

**Test Structure:**
```python
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.database import engine, Base, async_session_maker

client = TestClient(app)

# Fixture that runs before each test
@pytest.fixture(autouse=True)
async def setup_database():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # Test runs here

    # Cleanup after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# Test functions
def test_create_domain():
    response = client.post(
        "/api/v1/domains",
        json={"name": "Test Domain", "description": "A test"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Domain"

def test_get_domain_not_found():
    response = client.get("/api/v1/domains/nonexistent-id")
    assert response.status_code == 404
```

### Test Conventions

1. **File naming**: `test_*.py`
2. **Function naming**: `test_*` or `*_test`
3. **One assertion per test** (ideally)
4. **Use fixtures** for setup/teardown
5. **Mock external services** (LLM APIs)

---

## Adding New Features

### Feature Checklist

When adding a new feature, follow these steps:

- [ ] **Design**: Write down what the feature does
- [ ] **Schema**: Create Pydantic models for request/response
- [ ] **Model**: Create SQLAlchemy model if storing data
- [ ] **Endpoint**: Create FastAPI route
- [ ] **Tests**: Write tests before or alongside implementation
- [ ] **Frontend**: Add UI components if needed
- [ ] **Documentation**: Update relevant docs

### Example: Adding User Preferences

**1. Schema (src/schemas/preferences.py):**
```python
from pydantic import BaseModel
from typing import Optional

class UserPreferences(BaseModel):
    theme: str = "light"
    notifications_enabled: bool = True
    default_model: str = "claude"
```

**2. Model (src/models/user.py):**
```python
# Add to existing User model
preferences: Mapped[dict | None] = mapped_column(JSON, default=dict)
```

**3. Endpoint (src/api/users.py):**
```python
@router.get("/me/preferences", response_model=UserPreferences)
async def get_preferences(
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user(db, user_id)
    return UserPreferences(**(user.preferences or {}))

@router.put("/me/preferences", response_model=UserPreferences)
async def update_preferences(
    preferences: UserPreferences,
    user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user(db, user_id)
    user.preferences = preferences.model_dump()
    await db.commit()
    return preferences
```

**4. Tests (tests/api/test_users.py):**
```python
def test_update_preferences():
    response = client.put(
        "/api/v1/users/me/preferences",
        json={"theme": "dark", "notifications_enabled": False}
    )
    assert response.status_code == 200
    assert response.json()["theme"] == "dark"
```

---

## Common Patterns

### Error Handling

```python
from fastapi import HTTPException

# Simple error
raise HTTPException(status_code=404, detail="Resource not found")

# Detailed error
raise HTTPException(
    status_code=400,
    detail={
        "error": "validation_error",
        "message": "Invalid input",
        "field": "email",
    }
)
```

### Background Tasks

```python
from fastapi import BackgroundTasks

async def send_notification(user_id: str, message: str):
    # Long-running task
    ...

@router.post("/notify")
async def notify_user(
    user_id: str,
    message: str,
    background_tasks: BackgroundTasks,
):
    # Add task to run after response is sent
    background_tasks.add_task(send_notification, user_id, message)
    return {"status": "notification queued"}
```

### Pagination

```python
from typing import List, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')

class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int

@router.get("/items", response_model=Page[ItemResponse])
async def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size

    # Get total count
    count_result = await db.execute(select(func.count(Item.id)))
    total = count_result.scalar()

    # Get page of items
    result = await db.execute(
        select(Item).offset(offset).limit(page_size)
    )
    items = result.scalars().all()

    return Page(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )
```

---

## Debugging Guide

### Backend Debugging

**Enable Debug Logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Use Breakpoints (VS Code):**
1. Click left of line number to set breakpoint
2. Run "Python: FastAPI" debug configuration
3. Make request to trigger breakpoint

**Print Debugging:**
```python
import json
print(f"DEBUG: {json.dumps(data, indent=2, default=str)}")
```

### Frontend Debugging

**Browser DevTools:**
1. Open DevTools (F12)
2. Console tab: See logs and errors
3. Network tab: See API requests
4. React DevTools: Inspect component state

**Add Console Logs:**
```tsx
console.log('State:', state);
console.log('Props:', props);
```

### Common Issues

**CORS Errors:**
```python
# Add to main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Database Connection Issues:**
```bash
# Check database file exists
ls backend/*.db

# Reset database
rm backend/*.db
# Restart server
```

**Import Errors:**
```bash
# Make sure you're in virtual environment
# (venv) should appear in prompt

# Reinstall packages
pip install -e ".[dev]"
```

---

## Deployment

### Production Checklist

- [ ] Set secure `SECRET_KEY`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS
- [ ] Set appropriate CORS origins
- [ ] Configure rate limiting
- [ ] Set up logging and monitoring
- [ ] Use production WSGI server (gunicorn)

### Docker Deployment

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db/app
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=app
```

---

## Contributing

### Git Workflow

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes
3. Run tests: `python -m pytest tests/ -v`
4. Commit: `git commit -m "feat: add my feature"`
5. Push: `git push origin feature/my-feature`
6. Create Pull Request

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
- `feat(api): add user preferences endpoint`
- `fix(planning): handle empty goal state`
- `docs: update developer guide`

### Code Review Checklist

- [ ] Tests pass
- [ ] Code follows project style
- [ ] No unnecessary changes
- [ ] Documentation updated
- [ ] No secrets committed

---

*Last updated: January 2026*
