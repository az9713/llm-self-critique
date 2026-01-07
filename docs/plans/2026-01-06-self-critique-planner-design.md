# Self-Critique Planning Platform - Design Document

**Date:** 2026-01-06
**Status:** Validated
**Based on:** Google DeepMind paper "Enhancing LLM Planning Capabilities through Intrinsic Self-Critique" (arXiv:2512.24103)

---

## 1. Overview

### 1.1 Problem Statement

Large Language Models (LLMs) struggle with complex planning tasks, often generating plans that violate preconditions or fail to achieve goals. The Google DeepMind paper demonstrates that LLMs can significantly improve their planning accuracy through intrinsic self-critique—verifying their own plans step-by-step without external symbolic verifiers.

### 1.2 Solution

Build a web-based planning platform that:
- Allows users to define planning domains in **natural language** (no PDDL knowledge required)
- Automatically generates PDDL representations behind the scenes
- Implements the paper's self-critique algorithm with self-consistency voting
- Provides full transparency into the critique process
- Supports execution of validated plans through external integrations

### 1.3 Key Design Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Domain Input | Natural language | Lower barrier to entry, LLM handles PDDL generation |
| Algorithm | Full paper implementation | Self-consistency voting improves accuracy by ~15% |
| LLM Support | Multi-provider | Flexibility, cost optimization, resilience |
| Transparency | Full critique visibility | Builds trust, aids debugging |
| Scope | Full platform | Collaboration, execution, analytics, API |

---

## 2. Architecture

### 2.1 High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Next.js Frontend                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Chat UI      │  │ Plan Viewer  │  │ Domain Library       │  │
│  │ (guided)     │  │ (steps+state)│  │ (templates/history)  │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │ WebSocket + REST
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Elicitation  │  │ Self-Critique│  │ Execution Engine     │  │
│  │ Engine       │  │ Orchestrator │  │ (external APIs)      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ LLM Router   │  │ PDDL Store   │  │ Analytics Service    │  │
│  │ (multi-prov) │  │              │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│  PostgreSQL (users, domains, plans, history)                    │
│  Redis (sessions, caching, rate limiting)                       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

| Layer | Technology | Justification |
|-------|------------|---------------|
| Frontend | Next.js 14+ (TypeScript) | Industry standard, React ecosystem, SSR support |
| Backend | Python 3.11+ / FastAPI | Excellent LLM SDK support, async-first, fast |
| Database | PostgreSQL 15+ | Robust, JSON support, proven at scale |
| Cache | Redis | Sessions, rate limiting, response caching |
| Real-time | WebSockets | Stream LLM responses to frontend |

---

## 3. Core Algorithm

### 3.1 Planning Pipeline

Based on Algorithm 1 from the paper:

```
User Input (natural language)
        │
        ▼
┌───────────────────────────────────────┐
│  1. DOMAIN ELICITATION                │
│  Chat guides user to specify:         │
│  • Objects/types (blocks, locations)  │
│  • Actions (pick up, move, stack)     │
│  • Constraints (can't stack on small) │
│           │                           │
│           ▼                           │
│  LLM generates PDDL domain definition │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│  2. PROBLEM SPECIFICATION             │
│  Chat elicits:                        │
│  • Initial state                      │
│  • Goal state                         │
│           │                           │
│           ▼                           │
│  LLM generates PDDL problem instance  │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│  3. PLAN GENERATION                   │
│  Prompt: domain + problem → plan      │
│  Output: sequence of actions          │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  4. SELF-CRITIQUE LOOP (max k=5 iterations)           │
│  ┌─────────────────────────────────────────────────┐  │
│  │  For each iteration:                            │  │
│  │  • Run N=5 critique samples (self-consistency)  │  │
│  │  • Each critique checks:                        │  │
│  │    1. Action preconditions against state        │  │
│  │    2. Apply effects, update state               │  │
│  │    3. Verdict: correct/wrong/goal not reached   │  │
│  │  • Majority vote determines outcome             │  │
│  │  • If wrong: append critique to prompt, retry   │  │
│  └─────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────┘
        │
        ▼
   Validated Plan + Execution Trace
```

### 3.2 Self-Critique Prompts

The system stores prompts A.1 (few-shot) and A.2 (zero-shot) from the paper as versioned templates in the database. Key prompt structure:

```
Given the domain definition:
{domain_pddl}

[Optional: Few-shot exemplars for A.1]
{self_evaluations_exemplars}

So, for each action:
1. Take the action and its preconditions from the domain definition.
2. Verify whether the preconditions are met for the action.
3. Apply the action and provide the resulting state.

The problem to solve:
{instance}

The suggested solution:
{plan}

Please carefully evaluate the plan. Verify each step as described above.
Do not stop until each action is verified; please *do not* omit steps.
Conclude with the assessment literally either with 'the plan is correct',
'the plan is wrong', or 'goal not reached'.
```

### 3.3 Self-Consistency Voting

- Run 5 parallel critique passes for each plan
- Each pass independently verifies all steps
- Majority vote (≥3/5) determines verdict
- If margin < 60%, flag as "low confidence"

---

## 4. Data Model

### 4.1 Core Entities

```
User
├── id: UUID (PK)
├── email: string (unique)
├── password_hash: string
├── created_at: timestamp
└── settings: JSON

Workspace
├── id: UUID (PK)
├── name: string
├── owner_id: FK → User
└── created_at: timestamp

WorkspaceMember
├── workspace_id: FK → Workspace
├── user_id: FK → User
└── role: enum (owner, editor, planner, viewer)

Domain
├── id: UUID (PK)
├── workspace_id: FK → Workspace
├── name: string
├── description: text (natural language)
├── pddl_definition: text (generated PDDL)
├── is_public: boolean
├── is_template: boolean
└── created_at: timestamp

PlanningSession
├── id: UUID (PK)
├── domain_id: FK → Domain
├── initial_state: text (natural language)
├── goal_state: text (natural language)
├── pddl_problem: text (generated)
├── status: enum (eliciting, planning, critiquing, complete, failed)
├── llm_provider: string
└── created_at: timestamp

PlanIteration
├── id: UUID (PK)
├── session_id: FK → PlanningSession
├── iteration_number: int
├── generated_plan: text
├── critique_results: JSON[]
├── majority_verdict: enum (correct, wrong, goal_not_reached)
├── vote_breakdown: JSON
└── created_at: timestamp
```

### 4.2 Prompt Management

```
PromptTemplate
├── id: UUID (PK)
├── name: string (e.g., "self_critique_few_shot")
├── purpose: enum (plan_generation, self_critique, elicitation)
├── llm_provider: string | null (null = universal)
├── is_active: boolean
└── created_at: timestamp

PromptVersion
├── id: UUID (PK)
├── template_id: FK → PromptTemplate
├── version: int
├── content: text (prompt with {placeholders})
├── variables: JSON (list of placeholder names)
├── is_default: boolean
├── performance_metrics: JSON
└── created_at: timestamp

PromptExemplar
├── id: UUID (PK)
├── version_id: FK → PromptVersion
├── domain_type: string
├── exemplar_content: text
├── order: int
└── created_at: timestamp
```

---

## 5. Component Details

### 5.1 Elicitation Engine

Guides users through problem specification via chat:

**State Machine:**
```
DOMAIN_SCOPE → OBJECTS_AND_ACTIONS → INITIAL_STATE → GOAL_STATE → COMPLETE
```

**Completeness Checker:**
- At least one action defined
- All actions have clear preconditions/effects
- Initial state is concrete
- Goal state is achievable

### 5.2 LLM Router

**Features:**
- Unified interface across providers (Claude, OpenAI, Gemini)
- Streaming support via WebSocket relay
- Automatic failover to backup provider
- Per-user, per-provider rate limiting (Redis)
- Token usage tracking and cost estimation
- Response caching for identical prompts

**Configuration:**
- Users can bring their own API keys
- Or use platform-provided credits
- Configurable fallback order

### 5.3 Execution Engine

**Capabilities:**
- Map PDDL actions to external API calls
- Integration adapters: Webhooks, Zapier, Calendar APIs, Custom REST
- Execution modes: Dry run, Step-by-step, Autonomous, Export only
- Progress monitoring and failure recovery

---

## 6. User Interface

### 6.1 Main Layout

- **Left sidebar:** Domain library (my domains, templates, shared)
- **Main workspace:** Chat interface with elicitation progress indicator
- **Plan view:** Generated plan steps, state visualization, critique traces
- **Vote display:** Self-consistency results with expandable details

### 6.2 Key Screens

1. **Domain Library** - Browse, create, share domains
2. **Chat Interface** - Guided elicitation with progress tracker
3. **Plan Validation** - Step-by-step critique visualization
4. **Execution Monitor** - Track plan execution against external systems
5. **Analytics Dashboard** - Usage, success rates, LLM comparison

---

## 7. Collaboration

### 7.1 Permission Model

| Role | Domains | Sessions | Execute | Admin |
|------|---------|----------|---------|-------|
| Owner | CRUD | CRUD | Yes | Yes |
| Editor | CRUD | CRUD | Yes | No |
| Planner | Read | Create/Read | No | No |
| Viewer | Read | Read | No | No |

### 7.2 Sharing Features

- Share domains with workspace members
- Public link sharing (view/duplicate)
- Publish to template library
- Activity feed per workspace

---

## 8. Public API

### 8.1 Endpoints

```
DOMAINS
POST   /domains                    Create domain
GET    /domains                    List domains
GET    /domains/{id}               Get domain
PUT    /domains/{id}               Update domain
DELETE /domains/{id}               Delete domain

SESSIONS
POST   /sessions                   Start session
GET    /sessions/{id}              Get status
POST   /sessions/{id}/message      Send chat message
GET    /sessions/{id}/plan         Get final plan

DIRECT PLANNING
POST   /plan                       Natural language → plan
POST   /plan/pddl                  Raw PDDL → plan

EXECUTION
POST   /sessions/{id}/execute      Execute plan
GET    /sessions/{id}/execution    Get execution status

WEBHOOKS
POST   /webhooks                   Register webhook
```

### 8.2 Rate Limits

| Tier | Requests/min | Sessions/day | Concurrent |
|------|--------------|--------------|------------|
| Free | 10 | 20 | 2 |
| Pro | 60 | 500 | 10 |
| Enterprise | 300 | Unlimited | 50 |

---

## 9. Error Handling

### 9.1 Failure Taxonomy

| Failure Mode | Detection | Recovery |
|--------------|-----------|----------|
| Ambiguous input | Completeness checker | Ask clarifying questions |
| Invalid PDDL | Syntax validator | Auto-retry with fix prompt |
| Unsolvable problem | Max iterations | Report blocker, suggest modifications |
| LLM timeout | HTTP error | Retry with backoff, failover |
| Critique disagreement | Vote margin < 60% | Flag low confidence, offer more samples |
| Execution failure | API error | Pause, offer retry/skip/abort |

---

## 10. Testing Strategy

### 10.1 Test Pyramid

- **Unit tests:** PDDL parser, vote aggregation, state machine logic
- **Integration tests:** API endpoints, LLM mocking, database operations
- **E2E tests:** Critical user journeys with Playwright

### 10.2 LLM Testing

- **Golden test suite:** 50 problems with known-correct plans
- Run weekly against each provider
- Track success rate, iterations, critique accuracy
- Alert on >5% degradation

---

## 11. Analytics

### 11.1 Platform Metrics

- Plans generated (total, by domain type)
- Success rate (overall, by provider)
- Average iterations to validation
- Critique accuracy (TP, TN, FP, FN)

### 11.2 User Metrics

- Token usage by provider
- Estimated cost
- Plan quota usage

### 11.3 System Health

- API response time
- LLM queue depth
- Critique timeout rate
- Database connection pool

---

## 12. Security Considerations

- API key encryption at rest
- Per-user rate limiting
- Input sanitization for PDDL generation
- Audit logging for all plan executions
- Workspace isolation

---

## 13. Future Considerations (Out of Scope for v1)

- Mobile application
- On-premise deployment option
- Custom LLM fine-tuning
- Visual domain builder (drag-and-drop)
- Plan versioning and diff
- Real-time collaborative editing

---

## Appendix A: Reference Prompts

### A.1 Self-Critique Prompt (Few-Shot)

See paper arXiv:2512.24103, Appendix A.1

### A.2 Self-Critique Prompt (Zero-Shot)

See paper arXiv:2512.24103, Appendix A.2
