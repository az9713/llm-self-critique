# Architecture Overview

Comprehensive technical architecture documentation for the Self-Critique Planning Platform.

## Table of Contents

1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Backend Architecture](#backend-architecture)
4. [Frontend Architecture](#frontend-architecture)
5. [Data Flow](#data-flow)
6. [Self-Critique System](#self-critique-system)
7. [Database Design](#database-design)
8. [Security Architecture](#security-architecture)
9. [Scalability Considerations](#scalability-considerations)
10. [Technology Decisions](#technology-decisions)

---

## System Overview

### Purpose

The Self-Critique Planning Platform is designed to:

1. **Accept natural language** descriptions of planning problems
2. **Generate formal specifications** (PDDL) automatically
3. **Create optimized plans** using LLM-based planning
4. **Iteratively improve** plans through self-critique
5. **Provide real-time feedback** during the planning process

### Key Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Separation of Concerns** | Distinct layers for API, business logic, data |
| **Async First** | All I/O operations are asynchronous |
| **Provider Abstraction** | LLM providers are interchangeable |
| **Real-time Communication** | WebSocket for live updates |
| **API-First Design** | All functionality exposed via REST API |

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         Next.js Frontend                               │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐ │  │
│  │  │  Pages  │  │Components│  │  Hooks  │  │  State  │  │   API       │ │  │
│  │  │         │  │         │  │         │  │         │  │   Client    │ │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    HTTP/REST         │         WebSocket
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                               API GATEWAY LAYER                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                           FastAPI Application                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │  │
│  │  │  Middleware  │  │   Routers    │  │  WebSocket   │                 │  │
│  │  │  - Rate Limit│  │   - Domains  │  │  Handlers    │                 │  │
│  │  │  - Tracking  │  │   - Planning │  │              │                 │  │
│  │  │  - Auth      │  │   - Chat     │  │              │                 │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                 │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BUSINESS LOGIC LAYER                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   Elicitation   │  │    Critique     │  │      PDDL       │             │
│  │     Engine      │  │     System      │  │    Processor    │             │
│  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │             │
│  │  │   State   │  │  │  │Orchestrator│  │  │  │  Parser   │  │             │
│  │  │  Machine  │  │  │  └───────────┘  │  │  └───────────┘  │             │
│  │  └───────────┘  │  │  ┌───────────┐  │  │  ┌───────────┐  │             │
│  │  ┌───────────┐  │  │  │  Voting   │  │  │  │ Validator │  │             │
│  │  │   Chat    │  │  │  └───────────┘  │  │  └───────────┘  │             │
│  │  │  Handler  │  │  │  ┌───────────┐  │  │                 │             │
│  │  └───────────┘  │  │  │  Parser   │  │  │                 │             │
│  │  ┌───────────┐  │  │  └───────────┘  │  │                 │             │
│  │  │   PDDL    │  │  │                 │  │                 │             │
│  │  │ Generator │  │  │                 │  │                 │             │
│  │  └───────────┘  │  │                 │  │                 │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INTEGRATION LAYER                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                          LLM Router                                  │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │    │
│  │  │   Claude    │  │   OpenAI    │  │   Future    │                  │    │
│  │  │   Adapter   │  │   Adapter   │  │  Adapters   │                  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         SQLAlchemy ORM                               │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │    │
│  │  │  User   │  │ Domain  │  │  Plan   │  │ Session │  │Analytics│   │    │
│  │  │  Model  │  │  Model  │  │  Model  │  │  Model  │  │ Models  │   │    │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
│                                      ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │              SQLite (Dev) / PostgreSQL (Production)                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Backend Architecture

### Layer Responsibilities

#### 1. API Layer (`src/api/`)

**Purpose**: Handle HTTP requests, validate input, format responses

**Components**:
- `domains.py` - Domain CRUD operations
- `planning.py` - Planning session management
- `chat.py` - Chat message handling
- `validation.py` - PDDL validation endpoints
- `analytics.py` - Usage statistics
- `api_keys.py` - API key management
- `websocket.py` - WebSocket endpoints

**Pattern**: Router-based with dependency injection

```python
# Example: API endpoint structure
@router.post("", response_model=DomainResponse)
async def create_domain(
    request: DomainCreate,           # Validated input
    db: AsyncSession = Depends(get_db),  # Injected dependency
) -> DomainResponse:
    # Business logic
    domain = Domain(**request.model_dump())
    db.add(domain)
    await db.commit()
    return domain
```

#### 2. Business Logic Layer

**Elicitation Engine** (`src/elicitation/`):
- `state_machine.py` - Conversation state management
- `chat_handler.py` - Process user messages, generate responses
- `completeness.py` - Check if domain is fully specified
- `pddl_generator.py` - Convert conversation to PDDL

**Critique System** (`src/critique/`):
- `orchestrator.py` - Manage critique iterations
- `parser.py` - Parse LLM critique responses
- `voting.py` - Aggregate feedback from critics

**PDDL Processor** (`src/pddl/`):
- `parser.py` - Parse PDDL syntax
- `validator.py` - Validate semantic correctness

#### 3. Integration Layer (`src/llm/`)

**Purpose**: Abstract LLM provider differences

```python
# Base interface
class LLMAdapter(ABC):
    @abstractmethod
    async def generate(self, messages, max_tokens, temperature) -> str:
        pass

# Provider implementations
class ClaudeAdapter(LLMAdapter):
    async def generate(self, messages, max_tokens, temperature) -> str:
        # Anthropic-specific implementation

class OpenAIAdapter(LLMAdapter):
    async def generate(self, messages, max_tokens, temperature) -> str:
        # OpenAI-specific implementation

# Router for provider selection
class LLMRouter:
    def get_adapter(self, provider: str) -> LLMAdapter:
        # Return appropriate adapter
```

#### 4. Data Layer (`src/models/`, `src/database.py`)

**Purpose**: Data persistence and retrieval

**ORM Pattern**: SQLAlchemy 2.0 with async support

```python
# Model definition
class Domain(Base):
    __tablename__ = "domains"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    pddl_domain: Mapped[str | None] = mapped_column(Text)

# Async session management
async def get_db():
    async with async_session_maker() as session:
        yield session
```

### Middleware Stack

```
Request → Rate Limiting → Usage Tracking → Authentication → Router → Handler
                                                                        ↓
Response ← Rate Headers ← Usage Logged ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ←
```

---

## Frontend Architecture

### Next.js App Router Structure

```
src/app/
├── layout.tsx          # Root layout (shared across all pages)
├── page.tsx            # Landing page
├── globals.css         # Global styles
│
├── (auth)/             # Route group for auth pages
│   ├── layout.tsx      # Auth-specific layout
│   ├── login/page.tsx  # /login
│   └── register/page.tsx # /register
│
└── dashboard/          # Dashboard section
    ├── layout.tsx      # Dashboard layout (sidebar)
    ├── page.tsx        # /dashboard
    └── domain/[id]/    # Dynamic route
        ├── page.tsx    # /dashboard/domain/:id
        └── plan/page.tsx # /dashboard/domain/:id/plan
```

### Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Page Component                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                      Layout Component                       │ │
│  │  ┌──────────┐  ┌─────────────────────────────────────────┐ │ │
│  │  │          │  │           Content Area                   │ │ │
│  │  │ Sidebar  │  │  ┌─────────────────────────────────────┐│ │ │
│  │  │          │  │  │       Feature Components            ││ │ │
│  │  │          │  │  │  ┌──────────┐  ┌──────────┐        ││ │ │
│  │  │          │  │  │  │   Chat   │  │ Planning │        ││ │ │
│  │  │          │  │  │  │Component │  │Component │        ││ │ │
│  │  │          │  │  │  └──────────┘  └──────────┘        ││ │ │
│  │  │          │  │  │  ┌──────────┐  ┌──────────┐        ││ │ │
│  │  │          │  │  │  │Validation│  │ Domain   │        ││ │ │
│  │  │          │  │  │  │Component │  │Component │        ││ │ │
│  │  │          │  │  │  └──────────┘  └──────────┘        ││ │ │
│  │  │          │  │  └─────────────────────────────────────┘│ │ │
│  │  └──────────┘  └─────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### State Management Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                         Component                                │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Custom Hooks                          │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │    │
│  │  │useWebSocket │  │useValidation│  │usePlanningWS    │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    API Client                            │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │    │
│  │  │  fetch()    │  │ WebSocket   │  │  Error Handler  │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                             │                                    │
│                             ▼                                    │
│                      Backend API                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Domain Creation Flow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  User   │───▶│ Frontend│───▶│ Backend │───▶│   DB    │
│ Action  │    │   UI    │    │   API   │    │         │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │              │
     │  Click       │  POST        │  INSERT      │
     │  "New        │  /domains    │  domain      │
     │  Domain"     │              │              │
     │              │              │              │
     │              │◀─────────────│◀─────────────│
     │              │  JSON        │  Domain      │
     │◀─────────────│  Response    │  object      │
     │  Show        │              │              │
     │  new domain  │              │              │
```

### Planning Flow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  User   │───▶│ Frontend│───▶│ Backend │───▶│Critique │───▶│   LLM   │
└─────────┘    └─────────┘    └─────────┘    │ System  │    │  API    │
     │              │              │         └─────────┘    └─────────┘
     │              │              │              │              │
     │  Start       │  POST        │  Create      │              │
     │  Planning    │  /sessions   │  session     │              │
     │              │              │              │              │
     │              │              │  Generate    │  Initial     │
     │              │              │─────────────▶│  plan        │
     │              │              │              │──────────────▶
     │              │              │              │◀──────────────
     │              │              │              │              │
     │              │  WS:         │  Critique    │  Review      │
     │              │  progress    │─────────────▶│  plan        │
     │              │◀─────────────│              │──────────────▶
     │              │              │              │◀──────────────
     │              │              │              │              │
     │              │              │  Voting &    │              │
     │              │              │  Refinement  │              │
     │              │              │◀─────────────│              │
     │              │              │              │              │
     │              │  WS:         │              │              │
     │              │  complete    │              │              │
     │◀─────────────│◀─────────────│              │              │
```

### Chat Elicitation Flow

Chat sessions are linked to domains. When elicitation completes, PDDL is automatically generated and saved to the domain.

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  User   │◀──▶│  Chat   │◀──▶│  Chat   │◀──▶│  State  │◀──▶│   LLM   │
│         │    │   UI    │    │ Handler │    │ Machine │    │  API    │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │              │              │
     │  Start       │  POST        │  Create      │              │
     │  session     │  /start      │  session     │              │
     │  (domain_id) │  {domain_id} │  linked to   │              │
     │─────────────▶│─────────────▶│  domain      │              │
     │              │              │              │              │
     │  "I want to  │  POST        │  Process     │  Update      │
     │  plan..."    │  /message    │  message     │  state       │
     │─────────────▶│─────────────▶│─────────────▶│─────────────▶│
     │              │              │              │              │
     │              │              │  Generate    │              │
     │              │              │  response    │──────────────▶
     │              │              │◀─────────────│◀──────────────
     │              │              │              │              │
     │              │  JSON        │              │              │
     │              │  response +  │              │              │
     │◀─────────────│  messages    │              │              │
     │              │              │              │              │
     │  (Conversation continues until domain is complete)        │
     │  (Messages persist - navigate away and back)              │
     │              │              │              │              │
     │              │              │  Check       │              │
     │              │              │  completeness│              │
     │              │              │─────────────▶│              │
     │              │              │◀─────────────│              │
     │              │              │              │              │
     │              │              │  Generate    │              │
     │              │              │  PDDL        │──────────────▶
     │              │              │◀─────────────│◀──────────────
     │              │              │              │              │
     │              │              │  Save PDDL   │              │
     │              │              │  to Domain   │              │
     │              │              │  (DB)        │              │
```

---

## Self-Critique System

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Critique Orchestrator                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Iteration Loop                           │ │
│  │                                                             │ │
│  │  ┌─────────────┐                                           │ │
│  │  │   Initial   │                                           │ │
│  │  │    Plan     │                                           │ │
│  │  └──────┬──────┘                                           │ │
│  │         │                                                   │ │
│  │         ▼                                                   │ │
│  │  ┌─────────────────────────────────────────────────────┐   │ │
│  │  │              Critics (Parallel Execution)            │   │ │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │ │
│  │  │  │Completeness│  │Efficiency│  │  Safety  │          │   │ │
│  │  │  │  Critic   │  │  Critic  │  │  Critic  │          │   │ │
│  │  │  └──────────┘  └──────────┘  └──────────┘          │   │ │
│  │  └─────────────────────────────────────────────────────┘   │ │
│  │         │              │              │                     │ │
│  │         └──────────────┼──────────────┘                     │ │
│  │                        ▼                                    │ │
│  │  ┌─────────────────────────────────────────────────────┐   │ │
│  │  │                  Voting System                       │   │ │
│  │  │  ┌────────────────────────────────────────────────┐ │   │ │
│  │  │  │ Feedback Item    | Comp | Eff | Safe | Score   │ │   │ │
│  │  │  ├────────────────────────────────────────────────┤ │   │ │
│  │  │  │ "Add backup"     | 0.4  | 0.1 | 0.5  | 1.0 ✓  │ │   │ │
│  │  │  │ "Parallelize"    | 0.0  | 0.5 | 0.0  | 0.5 ✓  │ │   │ │
│  │  │  │ "Remove step 3"  | 0.1  | 0.2 | 0.0  | 0.3 ✗  │ │   │ │
│  │  │  └────────────────────────────────────────────────┘ │   │ │
│  │  └─────────────────────────────────────────────────────┘   │ │
│  │                        │                                    │ │
│  │                        ▼                                    │ │
│  │  ┌─────────────────────────────────────────────────────┐   │ │
│  │  │                Plan Refinement                       │   │ │
│  │  │  Incorporate feedback items with score > threshold   │   │ │
│  │  └─────────────────────────────────────────────────────┘   │ │
│  │                        │                                    │ │
│  │                        ▼                                    │ │
│  │  ┌─────────────────────────────────────────────────────┐   │ │
│  │  │            Convergence Check                         │   │ │
│  │  │  - No more critical feedback?                        │   │ │
│  │  │  - Max iterations reached?                           │   │ │
│  │  │  - Score improvement < threshold?                    │   │ │
│  │  └─────────────────────────────────────────────────────┘   │ │
│  │                        │                                    │ │
│  │         ┌──────────────┴──────────────┐                    │ │
│  │         │                             │                     │ │
│  │         ▼                             ▼                     │ │
│  │  ┌─────────────┐              ┌─────────────┐              │ │
│  │  │  Continue   │              │   Return    │              │ │
│  │  │  Iteration  │              │ Final Plan  │              │ │
│  │  └─────────────┘              └─────────────┘              │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Critic Perspectives

| Critic | Focus | Weight | Example Feedback |
|--------|-------|--------|------------------|
| Completeness | Goal achievement | 0.4 | "Step 5 doesn't contribute to any goal" |
| Efficiency | Optimal execution | 0.3 | "Steps 2 and 3 can be parallelized" |
| Safety | Risk mitigation | 0.3 | "No rollback plan if deployment fails" |

### Voting Algorithm

```python
def calculate_weighted_vote(feedback_item, critic_votes):
    """
    Calculate weighted score for a feedback item.

    Args:
        feedback_item: The suggestion being evaluated
        critic_votes: Dict of {critic_name: vote_value}
                      vote_value: 1.0 (agree), 0.5 (neutral), 0.0 (disagree)

    Returns:
        Weighted score between 0 and 1
    """
    weights = {
        "completeness": 0.4,
        "efficiency": 0.3,
        "safety": 0.3,
    }

    total_score = sum(
        weights[critic] * vote
        for critic, vote in critic_votes.items()
    )

    return total_score  # Threshold typically 0.5
```

---

## Database Design

### Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│      User       │       │     Domain      │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │───┐   │ id (PK)         │
│ email           │   │   │ workspace_id(FK)│◀──┐
│ password_hash   │   └──▶│ name            │   │
│ created_at      │       │ description     │   │
│ preferences     │       │ domain_pddl     │   │
└─────────────────┘       │ problem_pddl    │   │
                          │ is_public       │   │
                          │ is_template     │   │
                          │ created_at      │   │
                          │ updated_at      │   │
                          └────────┬────────┘   │
                                   │            │
                                   │            │
┌─────────────────┐                │            │
│ PlanningSession │                │            │
├─────────────────┤                │            │
│ id (PK)         │                │            │
│ domain_id (FK)  │◀───────────────┘            │
│ user_id (FK)    │◀────────────────────────────┘
│ status          │
│ current_iter    │       ┌─────────────────┐
│ max_iterations  │       │    Iteration    │
│ final_plan      │       ├─────────────────┤
│ created_at      │───────│ id (PK)         │
│ completed_at    │       │ session_id (FK) │
└─────────────────┘       │ iteration_num   │
                          │ plan_version    │
                          │ critiques       │
                          │ aggregated_score│
                          │ created_at      │
                          └─────────────────┘

┌─────────────────┐       ┌─────────────────┐
│     APIKey      │       │    UsageLog     │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ user_id (FK)    │       │ user_id (FK)    │
│ name            │       │ api_key_id (FK) │
│ key_hash        │       │ endpoint        │
│ key_prefix      │       │ method          │
│ status          │       │ status_code     │
│ rate_limit      │       │ latency_ms      │
│ last_used_at    │       │ ip_address      │
│ expires_at      │       │ extra_data      │
│ created_at      │       │ created_at      │
└─────────────────┘       └─────────────────┘
```

### Model Definitions

```python
# Core models
class User(Base):
    id: UUID (PK)
    email: String (unique, indexed)
    password_hash: String
    preferences: JSON

class Domain(Base):
    id: UUID (PK)
    workspace_id: UUID (FK → Workspace)
    name: String
    description: Text
    domain_pddl: Text (nullable)
    problem_pddl: Text (nullable)
    is_public: Boolean
    is_template: Boolean
    updated_at: DateTime

class PlanningSession(Base):
    id: UUID (PK)
    domain_id: UUID (FK → Domain)
    user_id: UUID (FK → User)
    status: Enum (pending, running, completed, failed)
    current_iteration: Integer
    max_iterations: Integer
    final_plan: JSON (nullable)

# Analytics models
class APIKey(Base):
    id: UUID (PK)
    user_id: UUID (FK → User)
    key_hash: String (unique, indexed)
    key_prefix: String
    status: Enum (active, revoked, expired)
    rate_limit: Integer

class UsageLog(Base):
    id: UUID (PK)
    user_id: UUID (FK, nullable)
    api_key_id: UUID (FK, nullable)
    endpoint: String (indexed)
    method: String
    status_code: Integer
    latency_ms: Integer
    extra_data: JSON
```

---

## Security Architecture

### Authentication Flow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Client  │    │   API   │    │  Auth   │    │   DB    │
│         │    │ Gateway │    │ Service │    │         │
└────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘
     │              │              │              │
     │  Request +   │              │              │
     │  API Key     │              │              │
     │─────────────▶│              │              │
     │              │  Validate    │              │
     │              │  API Key     │              │
     │              │─────────────▶│              │
     │              │              │  Query       │
     │              │              │  APIKey      │
     │              │              │─────────────▶│
     │              │              │◀─────────────│
     │              │              │              │
     │              │  Valid/      │              │
     │              │  Invalid     │              │
     │              │◀─────────────│              │
     │              │              │              │
     │  Response    │              │              │
     │◀─────────────│              │              │
```

### API Key Security

1. **Key Generation**: Cryptographically secure random bytes
2. **Storage**: Only hash stored in database
3. **Transmission**: Key shown once at creation
4. **Validation**: Hash comparison on each request
5. **Rotation**: Create new key, revoke old automatically

### Rate Limiting Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                     Rate Limiter                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   Sliding Window                            │ │
│  │                                                             │ │
│  │  Time ─────────────────────────────────────────────────▶   │ │
│  │       │◀──────── 60 seconds ────────▶│                     │ │
│  │       │                              │                      │ │
│  │  ┌────┴────┐                   ┌────┴────┐                 │ │
│  │  │ Window  │                   │ Current │                 │ │
│  │  │  Start  │                   │  Time   │                 │ │
│  │  └─────────┘                   └─────────┘                 │ │
│  │                                                             │ │
│  │  Request count in window: 45                                │ │
│  │  Limit: 100                                                 │ │
│  │  Remaining: 55                                              │ │
│  │  Reset in: 32 seconds                                       │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Scalability Considerations

### Current Architecture (Single Server)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Single Server                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   FastAPI   │  │   SQLite    │  │  In-Memory  │             │
│  │   (uvicorn) │  │             │  │ Rate Limit  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### Scaled Architecture (Production)

```
                            Load Balancer
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
            ▼                     ▼                     ▼
   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
   │  API Server 1   │   │  API Server 2   │   │  API Server 3   │
   └────────┬────────┘   └────────┬────────┘   └────────┬────────┘
            │                     │                     │
            └─────────────────────┼─────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
           ┌─────────────────┐        ┌─────────────────┐
           │   PostgreSQL    │        │      Redis      │
           │   (Primary)     │        │  (Rate Limits)  │
           └────────┬────────┘        │  (Sessions)     │
                    │                 └─────────────────┘
                    ▼
           ┌─────────────────┐
           │   PostgreSQL    │
           │   (Replica)     │
           └─────────────────┘
```

### Scaling Recommendations

| Component | Scale Strategy |
|-----------|----------------|
| API Servers | Horizontal (add more instances) |
| Database | Vertical first, then read replicas |
| Rate Limiting | Move to Redis for distributed state |
| WebSocket | Sticky sessions or Redis pub/sub |
| LLM Calls | Queue-based for long operations |

---

## Technology Decisions

### Why FastAPI?

| Requirement | FastAPI Feature |
|-------------|-----------------|
| High performance | ASGI, async support |
| API documentation | Auto-generated OpenAPI |
| Type safety | Pydantic integration |
| WebSocket support | Built-in |
| Easy to learn | Minimal boilerplate |

### Why Next.js?

| Requirement | Next.js Feature |
|-------------|-----------------|
| SEO (landing page) | Server-side rendering |
| Fast navigation | Client-side routing |
| Developer experience | File-based routing |
| TypeScript | First-class support |
| Modern React | App Router, Server Components |

### Why SQLAlchemy 2.0?

| Requirement | SQLAlchemy Feature |
|-------------|---------------------|
| Async operations | AsyncSession support |
| Type hints | Mapped[] annotations |
| Multiple databases | Driver abstraction |
| Migrations | Alembic integration |
| Complex queries | Full SQL expression language |

### Why Separate LLM Layer?

| Benefit | Explanation |
|---------|-------------|
| Provider independence | Switch providers without code changes |
| Testing | Mock LLM responses in tests |
| Fallback | Automatic failover between providers |
| Cost optimization | Route to cheaper providers for simple tasks |

---

*Last updated: January 2026*
