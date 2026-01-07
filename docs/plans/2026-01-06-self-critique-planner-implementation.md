# Self-Critique Planning Platform - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a web-based planning platform that uses LLM self-critique to validate plans, allowing users to define domains in natural language.

**Architecture:** FastAPI backend with Next.js frontend. LLM Router abstracts multiple providers. Self-Critique Orchestrator implements the paper's algorithm with self-consistency voting. PostgreSQL for persistence, Redis for caching/sessions.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Next.js 14, TypeScript, PostgreSQL, Redis, Anthropic/OpenAI/Google SDKs

---

## Phase 1: Project Setup & Infrastructure

### Task 1.1: Initialize Backend Project

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/src/__init__.py`
- Create: `backend/src/main.py`
- Create: `backend/tests/__init__.py`

**Step 1: Create backend directory structure**

```bash
mkdir -p backend/src backend/tests
```

**Step 2: Create pyproject.toml**

```toml
[project]
name = "self-critique-planner"
version = "0.1.0"
description = "LLM Planning Platform with Intrinsic Self-Critique"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy[asyncio]>=2.0.25",
    "asyncpg>=0.29.0",
    "redis>=5.0.1",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "anthropic>=0.18.0",
    "openai>=1.10.0",
    "google-generativeai>=0.3.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "httpx>=0.26.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
target-version = "py311"
line-length = 100
```

**Step 3: Create minimal FastAPI app**

Create `backend/src/main.py`:
```python
from fastapi import FastAPI

app = FastAPI(
    title="Self-Critique Planner API",
    description="LLM Planning Platform with Intrinsic Self-Critique",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Step 4: Create test for health endpoint**

Create `backend/tests/test_main.py`:
```python
import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
```

**Step 5: Install dependencies and run test**

```bash
cd backend
pip install -e ".[dev]"
pytest tests/test_main.py -v
```
Expected: PASS

**Step 6: Commit**

```bash
git add backend/
git commit -m "feat: initialize backend project with FastAPI"
```

---

### Task 1.2: Database Configuration

**Files:**
- Create: `backend/src/config.py`
- Create: `backend/src/database.py`
- Create: `backend/tests/test_database.py`

**Step 1: Create configuration module**

Create `backend/src/config.py`:
```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/planner"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "dev-secret-key-change-in-production"

    # LLM API Keys (optional, users can provide their own)
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    google_api_key: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()
```

**Step 2: Create database module**

Create `backend/src/database.py`:
```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

**Step 3: Create database connection test**

Create `backend/tests/test_database.py`:
```python
import pytest
from sqlalchemy import text

from src.database import engine


async def test_database_connection():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
```

**Step 4: Start PostgreSQL (Docker) and run test**

```bash
docker run -d --name planner-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=planner -p 5432:5432 postgres:15
sleep 3
cd backend && pytest tests/test_database.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/config.py backend/src/database.py backend/tests/test_database.py
git commit -m "feat: add database configuration and connection"
```

---

### Task 1.3: Redis Configuration

**Files:**
- Create: `backend/src/cache.py`
- Create: `backend/tests/test_cache.py`

**Step 1: Create Redis cache module**

Create `backend/src/cache.py`:
```python
import redis.asyncio as redis

from src.config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)


async def get_redis() -> redis.Redis:
    return redis_client
```

**Step 2: Write failing test**

Create `backend/tests/test_cache.py`:
```python
import pytest

from src.cache import redis_client


async def test_redis_connection():
    await redis_client.set("test_key", "test_value")
    value = await redis_client.get("test_key")
    assert value == "test_value"
    await redis_client.delete("test_key")
```

**Step 3: Start Redis and run test**

```bash
docker run -d --name planner-redis -p 6379:6379 redis:7
cd backend && pytest tests/test_cache.py -v
```
Expected: PASS

**Step 4: Commit**

```bash
git add backend/src/cache.py backend/tests/test_cache.py
git commit -m "feat: add Redis cache configuration"
```

---

## Phase 2: Core Data Models

### Task 2.1: User Model

**Files:**
- Create: `backend/src/models/__init__.py`
- Create: `backend/src/models/user.py`
- Create: `backend/tests/models/__init__.py`
- Create: `backend/tests/models/test_user.py`

**Step 1: Write failing test for User model**

Create `backend/tests/models/test_user.py`:
```python
import pytest
from sqlalchemy import select

from src.database import async_session_maker, engine, Base
from src.models.user import User


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def test_create_user():
    async with async_session_maker() as session:
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
        )
        session.add(user)
        await session.commit()

        result = await session.execute(select(User).where(User.email == "test@example.com"))
        saved_user = result.scalar_one()

        assert saved_user.id is not None
        assert saved_user.email == "test@example.com"
        assert saved_user.created_at is not None
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/models/test_user.py -v
```
Expected: FAIL with "No module named 'src.models.user'"

**Step 3: Create User model**

Create `backend/src/models/__init__.py`:
```python
from src.models.user import User

__all__ = ["User"]
```

Create `backend/src/models/user.py`:
```python
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    settings: Mapped[dict | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/models/test_user.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/models/ backend/tests/models/
git commit -m "feat: add User model"
```

---

### Task 2.2: Workspace Model

**Files:**
- Modify: `backend/src/models/__init__.py`
- Create: `backend/src/models/workspace.py`
- Create: `backend/tests/models/test_workspace.py`

**Step 1: Write failing test**

Create `backend/tests/models/test_workspace.py`:
```python
import pytest
from sqlalchemy import select

from src.database import async_session_maker, engine, Base
from src.models.user import User
from src.models.workspace import Workspace, WorkspaceMember, WorkspaceRole


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def test_create_workspace_with_owner():
    async with async_session_maker() as session:
        user = User(email="owner@example.com", password_hash="hash")
        session.add(user)
        await session.flush()

        workspace = Workspace(name="Test Workspace", owner_id=user.id)
        session.add(workspace)
        await session.flush()

        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=user.id,
            role=WorkspaceRole.OWNER,
        )
        session.add(member)
        await session.commit()

        result = await session.execute(select(Workspace))
        saved_workspace = result.scalar_one()

        assert saved_workspace.name == "Test Workspace"
        assert saved_workspace.owner_id == user.id
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/models/test_workspace.py -v
```
Expected: FAIL

**Step 3: Create Workspace model**

Create `backend/src/models/workspace.py`:
```python
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class WorkspaceRole(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"
    PLANNER = "planner"
    VIEWER = "viewer"


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[WorkspaceRole] = mapped_column(SQLEnum(WorkspaceRole))
```

Update `backend/src/models/__init__.py`:
```python
from src.models.user import User
from src.models.workspace import Workspace, WorkspaceMember, WorkspaceRole

__all__ = ["User", "Workspace", "WorkspaceMember", "WorkspaceRole"]
```

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/models/test_workspace.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/models/ backend/tests/models/
git commit -m "feat: add Workspace and WorkspaceMember models"
```

---

### Task 2.3: Domain Model

**Files:**
- Create: `backend/src/models/domain.py`
- Create: `backend/tests/models/test_domain.py`
- Modify: `backend/src/models/__init__.py`

**Step 1: Write failing test**

Create `backend/tests/models/test_domain.py`:
```python
import pytest
from sqlalchemy import select

from src.database import async_session_maker, engine, Base
from src.models.user import User
from src.models.workspace import Workspace
from src.models.domain import Domain


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def test_create_domain():
    async with async_session_maker() as session:
        user = User(email="test@example.com", password_hash="hash")
        session.add(user)
        await session.flush()

        workspace = Workspace(name="Test", owner_id=user.id)
        session.add(workspace)
        await session.flush()

        domain = Domain(
            workspace_id=workspace.id,
            name="Morning Routine",
            description="Planning my morning tasks",
            pddl_definition="(define (domain morning)...)",
        )
        session.add(domain)
        await session.commit()

        result = await session.execute(select(Domain))
        saved = result.scalar_one()

        assert saved.name == "Morning Routine"
        assert saved.pddl_definition is not None
        assert saved.is_public is False
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/models/test_domain.py -v
```
Expected: FAIL

**Step 3: Create Domain model**

Create `backend/src/models/domain.py`:
```python
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Domain(Base):
    __tablename__ = "domains"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    pddl_definition: Mapped[str | None] = mapped_column(Text, default=None)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

Update `backend/src/models/__init__.py`:
```python
from src.models.user import User
from src.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from src.models.domain import Domain

__all__ = ["User", "Workspace", "WorkspaceMember", "WorkspaceRole", "Domain"]
```

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/models/test_domain.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/models/
git commit -m "feat: add Domain model"
```

---

### Task 2.4: PlanningSession and PlanIteration Models

**Files:**
- Create: `backend/src/models/planning.py`
- Create: `backend/tests/models/test_planning.py`
- Modify: `backend/src/models/__init__.py`

**Step 1: Write failing test**

Create `backend/tests/models/test_planning.py`:
```python
import pytest
from sqlalchemy import select

from src.database import async_session_maker, engine, Base
from src.models.user import User
from src.models.workspace import Workspace
from src.models.domain import Domain
from src.models.planning import PlanningSession, PlanIteration, SessionStatus, Verdict


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def test_create_planning_session_with_iteration():
    async with async_session_maker() as session:
        # Setup
        user = User(email="test@example.com", password_hash="hash")
        session.add(user)
        await session.flush()

        workspace = Workspace(name="Test", owner_id=user.id)
        session.add(workspace)
        await session.flush()

        domain = Domain(
            workspace_id=workspace.id,
            name="Test Domain",
            description="Test",
        )
        session.add(domain)
        await session.flush()

        # Create planning session
        planning_session = PlanningSession(
            domain_id=domain.id,
            initial_state="Block A on table",
            goal_state="Block A on Block B",
            llm_provider="claude",
        )
        session.add(planning_session)
        await session.flush()

        # Create iteration
        iteration = PlanIteration(
            session_id=planning_session.id,
            iteration_number=1,
            generated_plan="1. pickup A\n2. stack A B",
            critique_results=[{"verdict": "correct", "trace": "..."}],
            majority_verdict=Verdict.CORRECT,
            vote_breakdown={"correct": 4, "wrong": 1},
        )
        session.add(iteration)
        await session.commit()

        result = await session.execute(select(PlanIteration))
        saved = result.scalar_one()

        assert saved.majority_verdict == Verdict.CORRECT
        assert saved.vote_breakdown["correct"] == 4
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/models/test_planning.py -v
```
Expected: FAIL

**Step 3: Create Planning models**

Create `backend/src/models/planning.py`:
```python
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import String, DateTime, Text, Integer, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class SessionStatus(str, Enum):
    ELICITING = "eliciting"
    PLANNING = "planning"
    CRITIQUING = "critiquing"
    COMPLETE = "complete"
    FAILED = "failed"


class Verdict(str, Enum):
    CORRECT = "correct"
    WRONG = "wrong"
    GOAL_NOT_REACHED = "goal_not_reached"


class PlanningSession(Base):
    __tablename__ = "planning_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    domain_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("domains.id"))
    initial_state: Mapped[str | None] = mapped_column(Text, default=None)
    goal_state: Mapped[str | None] = mapped_column(Text, default=None)
    pddl_problem: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[SessionStatus] = mapped_column(
        SQLEnum(SessionStatus), default=SessionStatus.ELICITING
    )
    llm_provider: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PlanIteration(Base):
    __tablename__ = "plan_iterations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("planning_sessions.id"))
    iteration_number: Mapped[int] = mapped_column(Integer)
    generated_plan: Mapped[str] = mapped_column(Text)
    critique_results: Mapped[list] = mapped_column(JSON)
    majority_verdict: Mapped[Verdict] = mapped_column(SQLEnum(Verdict))
    vote_breakdown: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

Update `backend/src/models/__init__.py`:
```python
from src.models.user import User
from src.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from src.models.domain import Domain
from src.models.planning import PlanningSession, PlanIteration, SessionStatus, Verdict

__all__ = [
    "User",
    "Workspace",
    "WorkspaceMember",
    "WorkspaceRole",
    "Domain",
    "PlanningSession",
    "PlanIteration",
    "SessionStatus",
    "Verdict",
]
```

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/models/test_planning.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/models/ backend/tests/models/
git commit -m "feat: add PlanningSession and PlanIteration models"
```

---

### Task 2.5: PromptTemplate Models

**Files:**
- Create: `backend/src/models/prompts.py`
- Create: `backend/tests/models/test_prompts.py`
- Modify: `backend/src/models/__init__.py`

**Step 1: Write failing test**

Create `backend/tests/models/test_prompts.py`:
```python
import pytest
from sqlalchemy import select

from src.database import async_session_maker, engine, Base
from src.models.prompts import PromptTemplate, PromptVersion, PromptExemplar, PromptPurpose


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def test_create_prompt_with_version_and_exemplar():
    async with async_session_maker() as session:
        template = PromptTemplate(
            name="self_critique_few_shot",
            purpose=PromptPurpose.SELF_CRITIQUE,
        )
        session.add(template)
        await session.flush()

        version = PromptVersion(
            template_id=template.id,
            version=1,
            content="Given the domain definition:\n{domain_pddl}\n...",
            variables=["domain_pddl", "instance", "plan"],
            is_default=True,
        )
        session.add(version)
        await session.flush()

        exemplar = PromptExemplar(
            version_id=version.id,
            domain_type="blocksworld",
            exemplar_content="Example critique trace...",
            order=1,
        )
        session.add(exemplar)
        await session.commit()

        result = await session.execute(select(PromptVersion).where(PromptVersion.is_default == True))
        saved = result.scalar_one()

        assert "domain_pddl" in saved.variables
        assert saved.version == 1
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/models/test_prompts.py -v
```
Expected: FAIL

**Step 3: Create Prompt models**

Create `backend/src/models/prompts.py`:
```python
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import String, DateTime, Text, Integer, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class PromptPurpose(str, Enum):
    PLAN_GENERATION = "plan_generation"
    SELF_CRITIQUE = "self_critique"
    ELICITATION = "elicitation"
    PDDL_GENERATION = "pddl_generation"


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    purpose: Mapped[PromptPurpose] = mapped_column(SQLEnum(PromptPurpose))
    llm_provider: Mapped[str | None] = mapped_column(String(50), default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prompt_templates.id"))
    version: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    variables: Mapped[list] = mapped_column(JSON)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    performance_metrics: Mapped[dict | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PromptExemplar(Base):
    __tablename__ = "prompt_exemplars"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prompt_versions.id"))
    domain_type: Mapped[str] = mapped_column(String(100))
    exemplar_content: Mapped[str] = mapped_column(Text)
    order: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

Update `backend/src/models/__init__.py`:
```python
from src.models.user import User
from src.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from src.models.domain import Domain
from src.models.planning import PlanningSession, PlanIteration, SessionStatus, Verdict
from src.models.prompts import PromptTemplate, PromptVersion, PromptExemplar, PromptPurpose

__all__ = [
    "User",
    "Workspace",
    "WorkspaceMember",
    "WorkspaceRole",
    "Domain",
    "PlanningSession",
    "PlanIteration",
    "SessionStatus",
    "Verdict",
    "PromptTemplate",
    "PromptVersion",
    "PromptExemplar",
    "PromptPurpose",
]
```

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/models/test_prompts.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/models/ backend/tests/models/
git commit -m "feat: add PromptTemplate, PromptVersion, and PromptExemplar models"
```

---

## Phase 3: LLM Router

### Task 3.1: LLM Provider Interface

**Files:**
- Create: `backend/src/llm/__init__.py`
- Create: `backend/src/llm/base.py`
- Create: `backend/tests/llm/__init__.py`
- Create: `backend/tests/llm/test_base.py`

**Step 1: Write failing test**

Create `backend/tests/llm/test_base.py`:
```python
import pytest
from pydantic import ValidationError

from src.llm.base import LLMRequest, LLMResponse, LLMProvider


def test_llm_request_validation():
    request = LLMRequest(
        prompt="Test prompt",
        provider=LLMProvider.CLAUDE,
        model="claude-sonnet-4-20250514",
        temperature=0.7,
        max_tokens=1000,
    )
    assert request.provider == LLMProvider.CLAUDE


def test_llm_request_invalid_temperature():
    with pytest.raises(ValidationError):
        LLMRequest(
            prompt="Test",
            provider=LLMProvider.CLAUDE,
            temperature=2.5,  # Invalid: > 2.0
        )


def test_llm_response():
    response = LLMResponse(
        content="Test response",
        usage={"input_tokens": 10, "output_tokens": 20},
        latency_ms=150,
    )
    assert response.usage["input_tokens"] == 10
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/llm/test_base.py -v
```
Expected: FAIL

**Step 3: Create base LLM types**

Create `backend/src/llm/__init__.py`:
```python
from src.llm.base import LLMRequest, LLMResponse, LLMProvider

__all__ = ["LLMRequest", "LLMResponse", "LLMProvider"]
```

Create `backend/src/llm/base.py`:
```python
from enum import Enum
from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    CLAUDE = "claude"
    OPENAI = "openai"
    GEMINI = "gemini"


class LLMRequest(BaseModel):
    prompt: str
    provider: LLMProvider
    model: str | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=100000)
    stream: bool = False


class LLMResponse(BaseModel):
    content: str
    usage: dict
    latency_ms: int
    provider_metadata: dict | None = None
```

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/llm/test_base.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/llm/ backend/tests/llm/
git commit -m "feat: add LLM base types and provider enum"
```

---

### Task 3.2: Claude Adapter

**Files:**
- Create: `backend/src/llm/adapters/__init__.py`
- Create: `backend/src/llm/adapters/claude.py`
- Create: `backend/tests/llm/test_claude_adapter.py`

**Step 1: Write failing test with mock**

Create `backend/tests/llm/test_claude_adapter.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.llm.base import LLMRequest, LLMProvider
from src.llm.adapters.claude import ClaudeAdapter


@pytest.fixture
def mock_anthropic():
    with patch("src.llm.adapters.claude.AsyncAnthropic") as mock:
        client = AsyncMock()
        mock.return_value = client

        # Mock response
        response = MagicMock()
        response.content = [MagicMock(text="Test response")]
        response.usage.input_tokens = 10
        response.usage.output_tokens = 20
        client.messages.create = AsyncMock(return_value=response)

        yield client


async def test_claude_adapter_complete(mock_anthropic):
    adapter = ClaudeAdapter(api_key="test-key")

    request = LLMRequest(
        prompt="Test prompt",
        provider=LLMProvider.CLAUDE,
        model="claude-sonnet-4-20250514",
    )

    response = await adapter.complete(request)

    assert response.content == "Test response"
    assert response.usage["input_tokens"] == 10


async def test_claude_adapter_default_model():
    adapter = ClaudeAdapter(api_key="test-key")
    assert adapter.default_model == "claude-sonnet-4-20250514"
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/llm/test_claude_adapter.py -v
```
Expected: FAIL

**Step 3: Create Claude adapter**

Create `backend/src/llm/adapters/__init__.py`:
```python
from src.llm.adapters.claude import ClaudeAdapter

__all__ = ["ClaudeAdapter"]
```

Create `backend/src/llm/adapters/claude.py`:
```python
import time
from anthropic import AsyncAnthropic

from src.llm.base import LLMRequest, LLMResponse


class ClaudeAdapter:
    default_model = "claude-sonnet-4-20250514"

    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)

    async def complete(self, request: LLMRequest) -> LLMResponse:
        start_time = time.time()

        response = await self.client.messages.create(
            model=request.model or self.default_model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            messages=[{"role": "user", "content": request.prompt}],
        )

        latency_ms = int((time.time() - start_time) * 1000)

        return LLMResponse(
            content=response.content[0].text,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            latency_ms=latency_ms,
        )
```

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/llm/test_claude_adapter.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/llm/adapters/ backend/tests/llm/
git commit -m "feat: add Claude LLM adapter"
```

---

### Task 3.3: OpenAI Adapter

**Files:**
- Create: `backend/src/llm/adapters/openai.py`
- Create: `backend/tests/llm/test_openai_adapter.py`
- Modify: `backend/src/llm/adapters/__init__.py`

**Step 1: Write failing test with mock**

Create `backend/tests/llm/test_openai_adapter.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.llm.base import LLMRequest, LLMProvider
from src.llm.adapters.openai import OpenAIAdapter


@pytest.fixture
def mock_openai():
    with patch("src.llm.adapters.openai.AsyncOpenAI") as mock:
        client = AsyncMock()
        mock.return_value = client

        response = MagicMock()
        response.choices = [MagicMock(message=MagicMock(content="Test response"))]
        response.usage.prompt_tokens = 10
        response.usage.completion_tokens = 20
        client.chat.completions.create = AsyncMock(return_value=response)

        yield client


async def test_openai_adapter_complete(mock_openai):
    adapter = OpenAIAdapter(api_key="test-key")

    request = LLMRequest(
        prompt="Test prompt",
        provider=LLMProvider.OPENAI,
        model="gpt-4o",
    )

    response = await adapter.complete(request)

    assert response.content == "Test response"
    assert response.usage["input_tokens"] == 10
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/llm/test_openai_adapter.py -v
```
Expected: FAIL

**Step 3: Create OpenAI adapter**

Create `backend/src/llm/adapters/openai.py`:
```python
import time
from openai import AsyncOpenAI

from src.llm.base import LLMRequest, LLMResponse


class OpenAIAdapter:
    default_model = "gpt-4o"

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def complete(self, request: LLMRequest) -> LLMResponse:
        start_time = time.time()

        response = await self.client.chat.completions.create(
            model=request.model or self.default_model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            messages=[{"role": "user", "content": request.prompt}],
        )

        latency_ms = int((time.time() - start_time) * 1000)

        return LLMResponse(
            content=response.choices[0].message.content,
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            },
            latency_ms=latency_ms,
        )
```

Update `backend/src/llm/adapters/__init__.py`:
```python
from src.llm.adapters.claude import ClaudeAdapter
from src.llm.adapters.openai import OpenAIAdapter

__all__ = ["ClaudeAdapter", "OpenAIAdapter"]
```

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/llm/test_openai_adapter.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/llm/adapters/ backend/tests/llm/
git commit -m "feat: add OpenAI LLM adapter"
```

---

### Task 3.4: LLM Router

**Files:**
- Create: `backend/src/llm/router.py`
- Create: `backend/tests/llm/test_router.py`
- Modify: `backend/src/llm/__init__.py`

**Step 1: Write failing test**

Create `backend/tests/llm/test_router.py`:
```python
import pytest
from unittest.mock import AsyncMock, patch

from src.llm.base import LLMRequest, LLMResponse, LLMProvider
from src.llm.router import LLMRouter


@pytest.fixture
def mock_adapters():
    with patch("src.llm.router.ClaudeAdapter") as claude_mock, \
         patch("src.llm.router.OpenAIAdapter") as openai_mock:

        claude_instance = AsyncMock()
        claude_instance.complete = AsyncMock(return_value=LLMResponse(
            content="Claude response",
            usage={"input_tokens": 10, "output_tokens": 20},
            latency_ms=100,
        ))
        claude_mock.return_value = claude_instance

        openai_instance = AsyncMock()
        openai_instance.complete = AsyncMock(return_value=LLMResponse(
            content="OpenAI response",
            usage={"input_tokens": 15, "output_tokens": 25},
            latency_ms=150,
        ))
        openai_mock.return_value = openai_instance

        yield {"claude": claude_instance, "openai": openai_instance}


async def test_router_routes_to_claude(mock_adapters):
    router = LLMRouter(api_keys={"claude": "test-key"})

    request = LLMRequest(prompt="Test", provider=LLMProvider.CLAUDE)
    response = await router.complete(request)

    assert response.content == "Claude response"
    mock_adapters["claude"].complete.assert_called_once()


async def test_router_routes_to_openai(mock_adapters):
    router = LLMRouter(api_keys={"openai": "test-key"})

    request = LLMRequest(prompt="Test", provider=LLMProvider.OPENAI)
    response = await router.complete(request)

    assert response.content == "OpenAI response"


async def test_router_missing_api_key():
    router = LLMRouter(api_keys={})

    request = LLMRequest(prompt="Test", provider=LLMProvider.CLAUDE)

    with pytest.raises(ValueError, match="No API key configured"):
        await router.complete(request)
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/llm/test_router.py -v
```
Expected: FAIL

**Step 3: Create LLM router**

Create `backend/src/llm/router.py`:
```python
from src.llm.base import LLMRequest, LLMResponse, LLMProvider
from src.llm.adapters.claude import ClaudeAdapter
from src.llm.adapters.openai import OpenAIAdapter


class LLMRouter:
    def __init__(self, api_keys: dict[str, str]):
        self.adapters = {}

        if "claude" in api_keys:
            self.adapters[LLMProvider.CLAUDE] = ClaudeAdapter(api_keys["claude"])
        if "openai" in api_keys:
            self.adapters[LLMProvider.OPENAI] = OpenAIAdapter(api_keys["openai"])

    async def complete(self, request: LLMRequest) -> LLMResponse:
        if request.provider not in self.adapters:
            raise ValueError(f"No API key configured for provider: {request.provider}")

        adapter = self.adapters[request.provider]
        return await adapter.complete(request)
```

Update `backend/src/llm/__init__.py`:
```python
from src.llm.base import LLMRequest, LLMResponse, LLMProvider
from src.llm.router import LLMRouter

__all__ = ["LLMRequest", "LLMResponse", "LLMProvider", "LLMRouter"]
```

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/llm/test_router.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/llm/ backend/tests/llm/
git commit -m "feat: add LLM router with multi-provider support"
```

---

## Phase 4: Self-Critique Orchestrator

### Task 4.1: Critique Parser

**Files:**
- Create: `backend/src/critique/__init__.py`
- Create: `backend/src/critique/parser.py`
- Create: `backend/tests/critique/__init__.py`
- Create: `backend/tests/critique/test_parser.py`

**Step 1: Write failing test**

Create `backend/tests/critique/test_parser.py`:
```python
import pytest

from src.critique.parser import CritiqueParser, CritiqueResult
from src.models.planning import Verdict


def test_parse_correct_verdict():
    response = """
    Step 1: (pickup A)
    Preconditions: (clear A), (on-table A), (arm-empty)
    All preconditions met. Applying action.
    State: arm holding A

    Step 2: (stack A B)
    Preconditions: (holding A), (clear B)
    All preconditions met. Applying action.
    State: A on B, arm empty

    Goal reached. the plan is correct
    """

    result = CritiqueParser.parse(response)

    assert result.verdict == Verdict.CORRECT
    assert len(result.step_traces) == 2


def test_parse_wrong_verdict():
    response = """
    Step 1: (pickup A)
    Preconditions: (clear A), (on-table A), (arm-empty)
    Check: (clear A)? NO - B is on top of A
    PRECONDITION FAILED

    the plan is wrong
    """

    result = CritiqueParser.parse(response)

    assert result.verdict == Verdict.WRONG
    assert "PRECONDITION FAILED" in result.error_reason


def test_parse_goal_not_reached():
    response = """
    All steps executed successfully.
    Final state: A on table, B on table
    Goal: A on B

    goal not reached
    """

    result = CritiqueParser.parse(response)

    assert result.verdict == Verdict.GOAL_NOT_REACHED
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/critique/test_parser.py -v
```
Expected: FAIL

**Step 3: Create critique parser**

Create `backend/src/critique/__init__.py`:
```python
from src.critique.parser import CritiqueParser, CritiqueResult

__all__ = ["CritiqueParser", "CritiqueResult"]
```

Create `backend/src/critique/parser.py`:
```python
import re
from dataclasses import dataclass

from src.models.planning import Verdict


@dataclass
class CritiqueResult:
    verdict: Verdict
    step_traces: list[str]
    error_reason: str | None = None
    raw_response: str = ""


class CritiqueParser:
    VERDICT_PATTERNS = {
        Verdict.CORRECT: r"the plan is correct",
        Verdict.WRONG: r"the plan is wrong",
        Verdict.GOAL_NOT_REACHED: r"goal not reached",
    }

    @classmethod
    def parse(cls, response: str) -> CritiqueResult:
        verdict = cls._extract_verdict(response)
        step_traces = cls._extract_steps(response)
        error_reason = cls._extract_error(response) if verdict != Verdict.CORRECT else None

        return CritiqueResult(
            verdict=verdict,
            step_traces=step_traces,
            error_reason=error_reason,
            raw_response=response,
        )

    @classmethod
    def _extract_verdict(cls, response: str) -> Verdict:
        response_lower = response.lower()

        for verdict, pattern in cls.VERDICT_PATTERNS.items():
            if re.search(pattern, response_lower):
                return verdict

        return Verdict.WRONG  # Default to wrong if unclear

    @classmethod
    def _extract_steps(cls, response: str) -> list[str]:
        step_pattern = r"Step \d+:.*?(?=Step \d+:|$)"
        matches = re.findall(step_pattern, response, re.DOTALL | re.IGNORECASE)
        return [m.strip() for m in matches]

    @classmethod
    def _extract_error(cls, response: str) -> str | None:
        error_patterns = [
            r"PRECONDITION FAILED.*",
            r"Error:.*",
            r"Cannot.*",
        ]

        for pattern in error_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return match.group(0)

        return None
```

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/critique/test_parser.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/critique/ backend/tests/critique/
git commit -m "feat: add critique response parser"
```

---

### Task 4.2: Vote Aggregator

**Files:**
- Create: `backend/src/critique/voting.py`
- Create: `backend/tests/critique/test_voting.py`
- Modify: `backend/src/critique/__init__.py`

**Step 1: Write failing test**

Create `backend/tests/critique/test_voting.py`:
```python
import pytest

from src.critique.voting import VoteAggregator, VoteResult
from src.critique.parser import CritiqueResult
from src.models.planning import Verdict


def test_majority_correct():
    results = [
        CritiqueResult(verdict=Verdict.CORRECT, step_traces=[]),
        CritiqueResult(verdict=Verdict.CORRECT, step_traces=[]),
        CritiqueResult(verdict=Verdict.CORRECT, step_traces=[]),
        CritiqueResult(verdict=Verdict.WRONG, step_traces=[]),
        CritiqueResult(verdict=Verdict.WRONG, step_traces=[]),
    ]

    vote = VoteAggregator.aggregate(results)

    assert vote.majority_verdict == Verdict.CORRECT
    assert vote.breakdown == {Verdict.CORRECT: 3, Verdict.WRONG: 2}
    assert vote.confidence == 0.6


def test_majority_wrong():
    results = [
        CritiqueResult(verdict=Verdict.WRONG, step_traces=[], error_reason="Error 1"),
        CritiqueResult(verdict=Verdict.WRONG, step_traces=[], error_reason="Error 2"),
        CritiqueResult(verdict=Verdict.WRONG, step_traces=[], error_reason="Error 3"),
        CritiqueResult(verdict=Verdict.CORRECT, step_traces=[]),
        CritiqueResult(verdict=Verdict.CORRECT, step_traces=[]),
    ]

    vote = VoteAggregator.aggregate(results)

    assert vote.majority_verdict == Verdict.WRONG
    assert vote.best_critique.error_reason == "Error 1"


def test_low_confidence_flag():
    results = [
        CritiqueResult(verdict=Verdict.CORRECT, step_traces=[]),
        CritiqueResult(verdict=Verdict.CORRECT, step_traces=[]),
        CritiqueResult(verdict=Verdict.CORRECT, step_traces=[]),
        CritiqueResult(verdict=Verdict.WRONG, step_traces=[]),
        CritiqueResult(verdict=Verdict.WRONG, step_traces=[]),
    ]

    vote = VoteAggregator.aggregate(results)

    assert vote.is_low_confidence is True  # 60% < 80% threshold
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/critique/test_voting.py -v
```
Expected: FAIL

**Step 3: Create vote aggregator**

Create `backend/src/critique/voting.py`:
```python
from collections import Counter
from dataclasses import dataclass

from src.critique.parser import CritiqueResult
from src.models.planning import Verdict


@dataclass
class VoteResult:
    majority_verdict: Verdict
    breakdown: dict[Verdict, int]
    confidence: float
    is_low_confidence: bool
    best_critique: CritiqueResult


class VoteAggregator:
    LOW_CONFIDENCE_THRESHOLD = 0.8

    @classmethod
    def aggregate(cls, results: list[CritiqueResult]) -> VoteResult:
        verdicts = [r.verdict for r in results]
        counter = Counter(verdicts)

        majority_verdict, majority_count = counter.most_common(1)[0]
        confidence = majority_count / len(results)

        # Find best critique (first one with matching verdict)
        best_critique = next(r for r in results if r.verdict == majority_verdict)

        breakdown = {v: counter.get(v, 0) for v in Verdict}

        return VoteResult(
            majority_verdict=majority_verdict,
            breakdown=breakdown,
            confidence=confidence,
            is_low_confidence=confidence < cls.LOW_CONFIDENCE_THRESHOLD,
            best_critique=best_critique,
        )
```

Update `backend/src/critique/__init__.py`:
```python
from src.critique.parser import CritiqueParser, CritiqueResult
from src.critique.voting import VoteAggregator, VoteResult

__all__ = ["CritiqueParser", "CritiqueResult", "VoteAggregator", "VoteResult"]
```

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/critique/test_voting.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/critique/ backend/tests/critique/
git commit -m "feat: add self-consistency vote aggregator"
```

---

### Task 4.3: Self-Critique Orchestrator

**Files:**
- Create: `backend/src/critique/orchestrator.py`
- Create: `backend/tests/critique/test_orchestrator.py`
- Modify: `backend/src/critique/__init__.py`

**Step 1: Write failing test**

Create `backend/tests/critique/test_orchestrator.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.critique.orchestrator import SelfCritiqueOrchestrator, PlanResult
from src.llm.base import LLMResponse, LLMProvider
from src.models.planning import Verdict


@pytest.fixture
def mock_router():
    router = AsyncMock()
    return router


@pytest.fixture
def orchestrator(mock_router):
    return SelfCritiqueOrchestrator(
        llm_router=mock_router,
        provider=LLMProvider.CLAUDE,
        max_iterations=3,
        num_critique_samples=5,
    )


async def test_plan_validates_on_first_try(orchestrator, mock_router):
    # Mock plan generation
    mock_router.complete.side_effect = [
        # Plan generation
        LLMResponse(content="1. pickup A\n2. stack A B", usage={}, latency_ms=100),
        # 5 critique samples - all correct
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
    ]

    result = await orchestrator.run(
        domain_pddl="(define (domain test)...)",
        problem_pddl="(define (problem test)...)",
    )

    assert result.status == "valid"
    assert result.iterations == 1
    assert result.final_verdict == Verdict.CORRECT


async def test_plan_refines_after_critique(orchestrator, mock_router):
    mock_router.complete.side_effect = [
        # Iteration 1: Plan generation
        LLMResponse(content="1. pickup A", usage={}, latency_ms=100),
        # Iteration 1: 5 critiques - majority wrong
        LLMResponse(content="the plan is wrong", usage={}, latency_ms=100),
        LLMResponse(content="the plan is wrong", usage={}, latency_ms=100),
        LLMResponse(content="the plan is wrong", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is wrong", usage={}, latency_ms=100),
        # Iteration 2: Refined plan
        LLMResponse(content="1. pickup A\n2. stack A B", usage={}, latency_ms=100),
        # Iteration 2: 5 critiques - all correct
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
        LLMResponse(content="the plan is correct", usage={}, latency_ms=100),
    ]

    result = await orchestrator.run(
        domain_pddl="(define (domain test)...)",
        problem_pddl="(define (problem test)...)",
    )

    assert result.status == "valid"
    assert result.iterations == 2
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/critique/test_orchestrator.py -v
```
Expected: FAIL

**Step 3: Create orchestrator**

Create `backend/src/critique/orchestrator.py`:
```python
import asyncio
from dataclasses import dataclass, field

from src.llm.base import LLMRequest, LLMProvider
from src.llm.router import LLMRouter
from src.critique.parser import CritiqueParser
from src.critique.voting import VoteAggregator, VoteResult
from src.models.planning import Verdict


@dataclass
class PlanResult:
    plan: str
    status: str  # "valid", "max_iterations", "failed"
    iterations: int
    final_verdict: Verdict
    iteration_history: list[dict] = field(default_factory=list)


class SelfCritiqueOrchestrator:
    PLAN_PROMPT = """Given the domain definition:
{domain_pddl}

The problem to solve:
{problem_pddl}

{critique_history}

Generate a plan to solve this problem. Output only the numbered list of actions."""

    CRITIQUE_PROMPT = """Given the domain definition:
{domain_pddl}

So, for each action:
1. Take the action and its preconditions from the domain definition for the specific action.
2. Verify whether the preconditions are met for the action.
3. Apply the action and provide the resulting state.

The problem to solve:
{problem_pddl}

The suggested solution:
{plan}

Please carefully evaluate the plan. Verify each step as described above. Do not stop until each action is verified; please *do not* omit steps. Conclude with the assessment literally either with 'the plan is correct', 'the plan is wrong', or 'goal not reached'."""

    def __init__(
        self,
        llm_router: LLMRouter,
        provider: LLMProvider,
        max_iterations: int = 5,
        num_critique_samples: int = 5,
    ):
        self.router = llm_router
        self.provider = provider
        self.max_iterations = max_iterations
        self.num_critique_samples = num_critique_samples

    async def run(self, domain_pddl: str, problem_pddl: str) -> PlanResult:
        critique_history = ""
        iteration_history = []

        for iteration in range(1, self.max_iterations + 1):
            # Generate plan
            plan = await self._generate_plan(domain_pddl, problem_pddl, critique_history)

            # Run parallel critiques
            vote_result = await self._run_critiques(domain_pddl, problem_pddl, plan)

            iteration_history.append({
                "iteration": iteration,
                "plan": plan,
                "vote_result": vote_result,
            })

            if vote_result.majority_verdict == Verdict.CORRECT:
                return PlanResult(
                    plan=plan,
                    status="valid",
                    iterations=iteration,
                    final_verdict=Verdict.CORRECT,
                    iteration_history=iteration_history,
                )

            # Append critique for next iteration
            critique_history = f"\nPrevious attempt failed with: {vote_result.best_critique.error_reason}\nPlease fix this issue."

        return PlanResult(
            plan=plan,
            status="max_iterations",
            iterations=self.max_iterations,
            final_verdict=vote_result.majority_verdict,
            iteration_history=iteration_history,
        )

    async def _generate_plan(self, domain: str, problem: str, history: str) -> str:
        prompt = self.PLAN_PROMPT.format(
            domain_pddl=domain,
            problem_pddl=problem,
            critique_history=history,
        )

        response = await self.router.complete(LLMRequest(
            prompt=prompt,
            provider=self.provider,
        ))

        return response.content

    async def _run_critiques(self, domain: str, problem: str, plan: str) -> VoteResult:
        prompt = self.CRITIQUE_PROMPT.format(
            domain_pddl=domain,
            problem_pddl=problem,
            plan=plan,
        )

        tasks = [
            self.router.complete(LLMRequest(prompt=prompt, provider=self.provider))
            for _ in range(self.num_critique_samples)
        ]

        responses = await asyncio.gather(*tasks)
        results = [CritiqueParser.parse(r.content) for r in responses]

        return VoteAggregator.aggregate(results)
```

Update `backend/src/critique/__init__.py`:
```python
from src.critique.parser import CritiqueParser, CritiqueResult
from src.critique.voting import VoteAggregator, VoteResult
from src.critique.orchestrator import SelfCritiqueOrchestrator, PlanResult

__all__ = [
    "CritiqueParser",
    "CritiqueResult",
    "VoteAggregator",
    "VoteResult",
    "SelfCritiqueOrchestrator",
    "PlanResult",
]
```

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/critique/test_orchestrator.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/critique/ backend/tests/critique/
git commit -m "feat: add self-critique orchestrator with iterative refinement"
```

---

## Phase 5: API Endpoints (Core)

### Task 5.1: Domain API Endpoints

**Files:**
- Create: `backend/src/api/__init__.py`
- Create: `backend/src/api/domains.py`
- Create: `backend/src/schemas/__init__.py`
- Create: `backend/src/schemas/domain.py`
- Create: `backend/tests/api/__init__.py`
- Create: `backend/tests/api/test_domains.py`
- Modify: `backend/src/main.py`

**Step 1: Write failing test**

Create `backend/tests/api/test_domains.py`:
```python
import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.database import engine, Base, async_session_maker
from src.models import User, Workspace


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create test user and workspace
    async with async_session_maker() as session:
        user = User(email="test@example.com", password_hash="hash")
        session.add(user)
        await session.flush()

        workspace = Workspace(name="Test", owner_id=user.id)
        session.add(workspace)
        await session.commit()

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def test_create_domain(client):
    # First get workspace id
    async with async_session_maker() as session:
        from sqlalchemy import select
        from src.models import Workspace
        result = await session.execute(select(Workspace))
        workspace = result.scalar_one()
        workspace_id = str(workspace.id)

    response = await client.post("/api/v1/domains", json={
        "workspace_id": workspace_id,
        "name": "Morning Routine",
        "description": "Planning my morning tasks",
    })

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Morning Routine"
    assert "id" in data


async def test_list_domains(client):
    response = await client.get("/api/v1/domains")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/api/test_domains.py -v
```
Expected: FAIL

**Step 3: Create schemas**

Create `backend/src/schemas/__init__.py`:
```python
from src.schemas.domain import DomainCreate, DomainResponse

__all__ = ["DomainCreate", "DomainResponse"]
```

Create `backend/src/schemas/domain.py`:
```python
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class DomainCreate(BaseModel):
    workspace_id: UUID
    name: str
    description: str


class DomainResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    description: str
    pddl_definition: str | None
    is_public: bool
    is_template: bool
    created_at: datetime

    class Config:
        from_attributes = True
```

**Step 4: Create API router**

Create `backend/src/api/__init__.py`:
```python
from fastapi import APIRouter

from src.api.domains import router as domains_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(domains_router, prefix="/domains", tags=["domains"])
```

Create `backend/src/api/domains.py`:
```python
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Domain
from src.schemas.domain import DomainCreate, DomainResponse

router = APIRouter()


@router.post("", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def create_domain(domain: DomainCreate, db: AsyncSession = Depends(get_db)):
    db_domain = Domain(
        workspace_id=domain.workspace_id,
        name=domain.name,
        description=domain.description,
    )
    db.add(db_domain)
    await db.commit()
    await db.refresh(db_domain)
    return db_domain


@router.get("", response_model=list[DomainResponse])
async def list_domains(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Domain))
    return result.scalars().all()


@router.get("/{domain_id}", response_model=DomainResponse)
async def get_domain(domain_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain
```

Update `backend/src/main.py`:
```python
from fastapi import FastAPI

from src.api import api_router

app = FastAPI(
    title="Self-Critique Planner API",
    description="LLM Planning Platform with Intrinsic Self-Critique",
    version="0.1.0",
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Step 5: Run test to verify it passes**

```bash
cd backend && pytest tests/api/test_domains.py -v
```
Expected: PASS

**Step 6: Commit**

```bash
git add backend/src/api/ backend/src/schemas/ backend/tests/api/ backend/src/main.py
git commit -m "feat: add domain API endpoints"
```

---

## Remaining Phases (Summary)

The following phases follow the same TDD pattern. Due to length constraints, here's a summary of remaining tasks:

### Phase 6: Elicitation Engine
- Task 6.1: Elicitation state machine
- Task 6.2: Completeness checker
- Task 6.3: PDDL generation prompts
- Task 6.4: Chat API endpoint with WebSocket

### Phase 7: Planning Session API
- Task 7.1: Session CRUD endpoints
- Task 7.2: Plan generation endpoint
- Task 7.3: WebSocket for streaming results

### Phase 8: Frontend (Next.js)
- Task 8.1: Initialize Next.js project
- Task 8.2: Auth pages (login/register)
- Task 8.3: Domain library sidebar
- Task 8.4: Chat interface component
- Task 8.5: Plan visualization component
- Task 8.6: Critique trace viewer
- Task 8.7: Vote display component

### Phase 9: Execution Engine
- Task 9.1: Action mapper interface
- Task 9.2: Webhook integration
- Task 9.3: Execution monitor

### Phase 10: Collaboration
- Task 10.1: Workspace sharing endpoints
- Task 10.2: Permission checks middleware
- Task 10.3: Activity feed

### Phase 11: Analytics & Public API
- Task 11.1: Usage tracking middleware
- Task 11.2: Analytics dashboard endpoints
- Task 11.3: Public API with rate limiting
- Task 11.4: API key management

---

## Quick Reference: Run All Tests

```bash
cd backend && pytest tests/ -v --cov=src --cov-report=term-missing
```

## Quick Reference: Start Development

```bash
# Terminal 1: Database & Redis
docker-compose up -d

# Terminal 2: Backend
cd backend && uvicorn src.main:app --reload

# Terminal 3: Frontend
cd frontend && npm run dev
```
