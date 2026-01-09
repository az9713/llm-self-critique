# Primer: Enhancing LLM Planning Capabilities through Intrinsic Self-Critique

A comprehensive guide to the research paper (arXiv:2512.24103v1) that forms the theoretical foundation of this platform.

## Table of Contents

1. [Paper Overview](#paper-overview)
2. [The Problem](#the-problem)
3. [The Solution: Intrinsic Self-Critique](#the-solution-intrinsic-self-critique)
4. [The Algorithm](#the-algorithm)
5. [Key Results](#key-results)
6. [Ablation Studies](#ablation-studies)
7. [Implications for This Platform](#implications-for-this-platform)
8. [Glossary of Terms](#glossary-of-terms)
9. [Appendix: Prompt Implementation Mapping](#appendix-prompt-implementation-mapping)

---

## Paper Overview

**Title:** Enhancing LLM Planning Capabilities through Intrinsic Self-Critique

**Authors:** Bernd Bohnet, Azade Nova, Marek Fiedel, and team at Google DeepMind

**Published:** December 2024

**Core Contribution:** A method to dramatically improve LLM planning accuracy by having the model critique and revise its own plans without external verification tools.

### Key Takeaway

> Large Language Models can significantly improve their planning accuracy (from ~50% to ~89% on benchmark tasks) by iteratively critiquing and revising their own outputs, without requiring external planners or verification systems.

---

## The Problem

### Why Planning is Hard for LLMs

LLMs struggle with planning tasks because:

1. **State Tracking**: Plans require maintaining accurate world state across many steps
2. **Constraint Satisfaction**: Each action has preconditions that must be met
3. **Goal Achievement**: The final state must satisfy all goal conditions
4. **Combinatorial Complexity**: The number of possible action sequences grows exponentially

### Traditional Solutions (and Their Limitations)

| Approach | Description | Limitation |
|----------|-------------|------------|
| **External Planners** | Use classical AI planners (STRIPS, FastDownward) | Requires perfect PDDL translation |
| **External Verifiers** | Validate plans with separate tools | Adds complexity, may not be available |
| **Fine-tuning** | Train LLMs specifically on planning | Expensive, may not generalize |
| **Prompting** | Better prompts for planning | Limited improvement ceiling |

### The Gap

Previous work showed LLMs could critique plans when given external feedback. But what if:
- No external verifier is available?
- The domain is too complex for formal verification?
- We want a general-purpose solution?

---

## The Solution: Intrinsic Self-Critique

### Core Insight

LLMs can effectively critique their own plans by:
1. Simulating plan execution step-by-step
2. Checking preconditions at each step
3. Identifying where plans fail
4. Using this feedback to generate better plans

### What "Intrinsic" Means

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTRINSIC Critique                        │
│                                                              │
│  LLM → Plan → External Verifier → Feedback → LLM → New Plan │
│                      ↑                                       │
│              (Separate System)                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    INTRINSIC Critique                        │
│                                                              │
│        LLM → Plan → Same LLM Critiques → LLM → New Plan     │
│                          ↑                                   │
│                   (Self-Contained)                           │
└─────────────────────────────────────────────────────────────┘
```

**Intrinsic** = The same model that generates the plan also critiques it. No external tools required.

### Why This Works

1. **LLMs are good critics**: Even when generation fails, LLMs can often identify flaws
2. **Critique is easier than generation**: Finding a bug is easier than writing bug-free code
3. **Structured feedback helps**: Knowing *why* a plan failed enables targeted fixes
4. **Iteration compounds**: Each cycle improves on the previous attempt

---

## The Algorithm

### Algorithm 1: Iterative Self-Critique

```
Input: Domain D, Problem P, Max iterations K
Output: Plan (or failure)

1. Generate initial plan using few-shot prompting
2. For i = 1 to K:
   a. CRITIQUE: Ask LLM to verify plan step-by-step
   b. If critique says "VALID": return plan
   c. REVISE: Ask LLM to fix identified issues
   d. plan = revised plan
3. Return final plan (or FAILED if still invalid)
```

### The Three Prompts

#### 1. Plan Generation Prompt

```
Given this planning domain and problem:
[Domain Definition]
[Problem: Initial State, Goal]

Generate a plan as a sequence of actions.
[Few-shot examples]
```

#### 2. Self-Critique Prompt

```
Verify this plan step by step:
[Plan]

For each action:
1. State the current world state
2. Check if preconditions are satisfied
3. Apply effects to update state
4. Continue to next action

If all preconditions are met and goal is achieved: output "VALID"
Otherwise: identify the FIRST action that fails and explain why.
```

#### 3. Revision Prompt

```
The plan has an error:
[Original Plan]
[Critique identifying the error]

Generate a corrected plan that fixes this issue.
```

### Visual Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   GENERATE  │────→│   CRITIQUE  │────→│    VALID?   │
│    Plan     │     │    Plan     │     │             │
└─────────────┘     └─────────────┘     └──────┬──────┘
       ↑                                       │
       │            ┌─────────────┐           │
       └────────────│   REVISE    │←──────────┘
                    │    Plan     │        (if invalid)
                    └─────────────┘
```

---

## Key Results

### Blocksworld Benchmark

The classic AI planning domain where blocks must be stacked in a goal configuration.

| Method | 3-5 Blocks | 6-8 Blocks | 9-11 Blocks |
|--------|------------|------------|-------------|
| Direct Generation | 49.8% | 23.7% | 11.5% |
| + Self-Critique (1 iter) | 75.2% | 45.3% | 28.1% |
| + Self-Critique (3 iter) | 85.4% | 58.2% | 35.6% |
| + Self-Consistency (5 votes) | **89.3%** | **64.1%** | **42.3%** |

**Key Insight**: Self-critique nearly doubles accuracy on medium-difficulty problems.

### Across Models

The method works across different LLMs:

| Model | Baseline | + Self-Critique | Improvement |
|-------|----------|-----------------|-------------|
| Gemini 1.5 Pro | 49.8% | 89.3% | +79% relative |
| Claude 3.5 Sonnet | 52.1% | 86.7% | +66% relative |
| GPT-4o | 47.3% | 84.2% | +78% relative |

### Other Domains

| Domain | Baseline | + Self-Critique |
|--------|----------|-----------------|
| Logistics | 34.2% | 67.8% |
| Mini-grid | 28.5% | 52.1% |
| AutoPlanBench (avg) | 31.4% | 58.9% |

---

## Ablation Studies

The paper systematically tested what matters most.

### What Improves Performance

| Factor | Impact | Why It Matters |
|--------|--------|----------------|
| **Including Domain Definition** | +23% | LLM needs action semantics to verify |
| **Step-by-Step Instructions** | +18% | Structured critique catches more errors |
| **"Verify Each Action" Prompt** | +15% | Forces systematic checking |
| **Multiple Iterations** | +12% per iter | Compounds improvements |
| **Self-Consistency Voting** | +8% | Reduces variance |

### What Doesn't Help Much

| Factor | Impact | Why |
|--------|--------|-----|
| More few-shot examples (>5) | +2% | Diminishing returns |
| Longer reasoning chains | +1% | Quality > quantity |
| Temperature tuning | ~0% | Default works fine |

### The "Sweet Spot"

```
Optimal Configuration:
├── Iterations: 3-5 (diminishing returns after)
├── Self-Consistency Votes: 5 (cost vs. accuracy tradeoff)
├── Few-shot Examples: 3-5 (enough to demonstrate format)
└── Critique Depth: Full state tracking (not shortcuts)
```

---

## Implications for This Platform

### How We Apply These Findings

This platform implements the paper's methodology with practical enhancements:

#### 1. Multi-Critic Architecture

The paper uses a single self-critique prompt. We extend this with specialized critics:

| Paper | This Platform |
|-------|---------------|
| Single critique prompt | Completeness Critic |
| | Efficiency Critic |
| | Safety Critic |

**Why**: Different critics catch different issues. Completeness ensures goals are met, efficiency optimizes, safety prevents risks.

#### 2. Weighted Voting

The paper uses majority voting. We add weighted aggregation:

```python
# Paper approach
final_decision = majority_vote(critiques)

# Our approach
score = sum(critic.weight * critic.vote for critic in critics)
final_decision = "incorporate" if score > threshold else "reject"
```

**Why**: Some critics (e.g., safety) should have higher weight for certain domains.

#### 3. Natural Language Interface

The paper uses raw PDDL. We add:
- Chat-based domain elicitation
- Automatic PDDL generation
- Human-readable plan explanations

**Why**: Makes the technology accessible to non-experts.

#### 4. Real-Time Visibility

The paper reports final metrics. We show:
- Live critique progress
- Iteration-by-iteration improvements
- Detailed critique traces

**Why**: Users can understand and trust the planning process.

### Theoretical Alignment

| Paper Principle | Platform Implementation |
|-----------------|------------------------|
| Iterative refinement | Multiple critique rounds until consensus |
| Step-by-step verification | State tracking in critique prompts |
| Self-consistency | Aggregated multi-critic voting |
| Domain grounding | PDDL generation from natural language |

---

## Glossary of Terms

| Term | Definition |
|------|------------|
| **Intrinsic Critique** | Model critiques its own output without external tools |
| **Extrinsic Critique** | External system validates model output |
| **Self-Consistency** | Generate multiple samples, vote on best answer |
| **PDDL** | Planning Domain Definition Language - formal planning notation |
| **Blocksworld** | Classic planning domain with stackable blocks |
| **Precondition** | What must be true for an action to be valid |
| **Effect** | What changes when an action is executed |
| **State Tracking** | Maintaining accurate world state through plan execution |
| **Few-shot Prompting** | Including examples in the prompt to guide output |
| **Ablation Study** | Systematically removing components to measure impact |

---

## Further Reading

### From the Paper

- **Section 3**: Full algorithm details and prompt templates
- **Section 4**: Experimental setup and benchmark descriptions
- **Section 5**: Detailed results and analysis
- **Section 6**: Ablation studies
- **Appendix A**: Complete prompt examples

### Related Work

- **ReAct** (Yao et al., 2023): Reasoning and acting in LLMs
- **Chain-of-Thought** (Wei et al., 2022): Step-by-step reasoning
- **Self-Refine** (Madaan et al., 2023): Iterative self-improvement
- **Tree of Thoughts** (Yao et al., 2023): Structured reasoning paths

### Planning Background

- **STRIPS** (Fikes & Nilsson, 1971): Classical planning formalism
- **FastDownward**: State-of-the-art classical planner
- **PDDL** (McDermott et al., 1998): Planning specification language

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│           INTRINSIC SELF-CRITIQUE: KEY POINTS               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  WHAT: LLM critiques its own plans, no external verifier    │
│                                                             │
│  HOW: Generate → Critique → Revise → Repeat                 │
│                                                             │
│  WHY: Critique is easier than generation; iteration helps   │
│                                                             │
│  RESULTS: ~50% → ~89% accuracy on standard benchmarks       │
│                                                             │
│  KEY FACTORS:                                               │
│    ✓ Include domain definition in critique prompt           │
│    ✓ Step-by-step state tracking                            │
│    ✓ 3-5 iterations optimal                                 │
│    ✓ Self-consistency voting helps                          │
│                                                             │
│  THIS PLATFORM ADDS:                                        │
│    • Multiple specialized critics                           │
│    • Weighted voting                                        │
│    • Natural language interface                             │
│    • Real-time visibility                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Appendix: Prompt Implementation Mapping

This section maps the prompts from the DeepMind paper (Appendix A and B) to their implementation in this codebase and shows which UI workflow step triggers each prompt.

### Paper Prompts Overview

| Prompt | Paper Section | Purpose | Implementation Status |
|--------|---------------|---------|----------------------|
| **A.1** | Appendix A.1 | Self-Critique (Few-Shot) | Partial - Zero-shot variant used |
| **A.2** | Appendix A.2 | Self-Critique (Zero-Shot) | ✅ Implemented |
| **A.3** | Appendix A.3 | Plan Generation (Few-Shot) | ✅ Implemented |
| **A.4** | Appendix A.4 | Plan Revision with Feedback | ✅ Implemented |
| **A.5** | Appendix A.5 | Many-Shot Self-Critique | Not implemented |
| **B.1** | Appendix B.1 | Domain-Specific Exemplars (Blocksworld) | Not implemented |

---

### Prompt A.1 / A.2: Self-Critique Prompt

**Paper Description:** Verifies a plan step-by-step by checking preconditions and applying effects.

**Code Location:** `backend/src/critique/orchestrator.py:31-45`

```python
CRITIQUE_PROMPT = """Given the domain definition:
{domain_pddl}

So, for each action:
1. Take the action and its preconditions from the domain definition.
2. Verify whether the preconditions are met for the action.
3. Apply the action and provide the resulting state.

The problem to solve:
{problem_pddl}

The suggested solution:
{plan}

Please carefully evaluate the plan. Verify each step as described above.
Do not stop until each action is verified; please *do not* omit steps.
Conclude with the assessment literally either with 'the plan is correct',
'the plan is wrong', or 'goal not reached'."""
```

**UI Workflow Trigger:**
1. User clicks **"Generate Plan"** in the Plan view
2. System generates initial plan using A.3
3. **→ A.2 is invoked 5 times in parallel** (self-consistency voting)
4. Results aggregated via majority vote

**Method Call Chain:**
```
UI: Generate Plan button
→ POST /api/v1/planning/sessions/{id}/plan
→ SelfCritiqueOrchestrator.run()
→ SelfCritiqueOrchestrator._run_critiques()  ← A.2 prompt used here
→ CritiqueParser.parse() → VoteAggregator.aggregate()
```

**Note:** A.1 (few-shot) would include exemplar critique traces before the plan. Our implementation uses A.2 (zero-shot) for simplicity. Few-shot exemplars could be added via the `PromptExemplar` database model.

---

### Prompt A.3: Plan Generation Prompt

**Paper Description:** Generates a plan given domain and problem PDDL.

**Code Location:** `backend/src/critique/orchestrator.py:21-29`

```python
PLAN_PROMPT = """Given the domain definition:
{domain_pddl}

The problem to solve:
{problem_pddl}

{critique_history}

Generate a plan to solve this problem. Output only the numbered list of actions."""
```

**UI Workflow Trigger:**
1. User clicks **"Generate Plan"** in the Plan view
2. **→ A.3 is invoked** to generate the initial plan
3. Plan is then verified using A.2

**Method Call Chain:**
```
UI: Generate Plan button
→ POST /api/v1/planning/sessions/{id}/plan
→ SelfCritiqueOrchestrator.run()
→ SelfCritiqueOrchestrator._generate_plan()  ← A.3 prompt used here
```

---

### Prompt A.4: Plan Revision Prompt

**Paper Description:** Revises a plan based on critique feedback.

**Code Location:** `backend/src/critique/orchestrator.py:86` (injected via `{critique_history}`)

The revision is implemented by appending the critique feedback to the plan generation prompt:

```python
critique_history = f"\nPrevious attempt failed with: {vote_result.best_critique.error_reason}\nPlease fix this issue."
```

This transforms A.3 into A.4 on subsequent iterations.

**UI Workflow Trigger:**
1. Initial plan generated (A.3)
2. Plan verified (A.2) → verdict is "wrong" or "goal not reached"
3. **→ A.4 is invoked** (A.3 + critique history)
4. New plan verified (A.2)
5. Loop repeats up to `max_iterations` (default: 5)

**Method Call Chain:**
```
SelfCritiqueOrchestrator.run() loop:
  iteration 1: _generate_plan() (A.3) → _run_critiques() (A.2)
  if wrong:
    iteration 2: _generate_plan() with critique_history (A.4) → _run_critiques() (A.2)
    ...
```

---

### Prompt A.5: Many-Shot Self-Critique

**Paper Description:** Uses extensive examples (50-200) in the critique prompt.

**Implementation Status:** Not implemented

**How to Implement:** Use the `PromptExemplar` model to store many exemplars and inject them into A.2's prompt before the plan verification section.

---

### Prompt B.1: Domain-Specific Exemplars (Blocksworld)

**Paper Description:** Benchmark-specific few-shot examples for Blocksworld domain.

**Implementation Status:** Not implemented

**How to Implement:** Store in `PromptExemplar` with `domain_type="blocksworld"` and inject when domain matches.

---

### Additional Platform-Specific Prompts

These prompts extend beyond the paper to enable natural language interaction:

#### Domain Elicitation Prompt

**Purpose:** Guides users through defining a planning domain via conversation.

**Code Location:** `backend/src/elicitation/chat_handler.py:10-38`

```python
SYSTEM_PROMPT = """You are a helpful AI assistant that guides users through
defining a planning domain. Your goal is to collect enough information to
generate a PDDL specification.

Current conversation phase: {phase}
Information collected so far:
- Domain name: {domain_name}
- Objects: {objects}
- Predicates: {predicates}
- Actions: {actions}
...
"""
```

**UI Workflow Trigger:**
1. User creates a new domain
2. User navigates to **"Define Domain"** tab
3. User sends a chat message
4. **→ Elicitation prompt is invoked**
5. Assistant guides through phases: INTRO → OBJECTS → PREDICATES → ACTIONS → INITIAL → GOAL → COMPLETE

**Method Call Chain:**
```
UI: Chat input in Define Domain tab
→ POST /api/v1/chat/message
→ ElicitationChatHandler.handle_message()  ← Elicitation prompt used here
```

---

#### PDDL Domain Generation Prompt

**Purpose:** Converts elicited natural language domain to formal PDDL syntax.

**Code Location:** `backend/src/elicitation/pddl_generator.py:9-28`

```python
DOMAIN_PROMPT = """You are an expert in PDDL.
Generate a valid PDDL domain definition based on the following information:

Domain Name: {domain_name}
Objects/Types: {objects}
Predicates: {predicates}
Actions: {actions}
...
Output ONLY valid PDDL code, no explanations."""
```

**UI Workflow Trigger:**
1. Elicitation conversation reaches **COMPLETE** phase
2. **→ PDDL Domain prompt is invoked**
3. Generated PDDL is saved to domain

**Method Call Chain:**
```
ElicitationPhase reaches COMPLETE
→ PDDLGenerator.generate_domain()  ← PDDL Domain prompt used here
→ Domain.domain_pddl = generated_pddl
```

---

#### PDDL Problem Generation Prompt

**Purpose:** Converts initial/goal states to formal PDDL problem syntax.

**Code Location:** `backend/src/elicitation/pddl_generator.py:30-50`

```python
PROBLEM_PROMPT = """You are an expert in PDDL.
Generate a valid PDDL problem definition based on the following:

Domain Definition: {domain_pddl}
Objects: {objects}
Initial State: {initial_state}
Goal State: {goal_state}
...
Output ONLY valid PDDL code, no explanations."""
```

**UI Workflow Trigger:**
1. Elicitation conversation reaches **COMPLETE** phase
2. PDDL Domain generated
3. **→ PDDL Problem prompt is invoked**
4. Generated PDDL problem is saved

**Method Call Chain:**
```
PDDLGenerator.generate_full()
→ generate_domain()  ← PDDL Domain prompt
→ generate_problem()  ← PDDL Problem prompt
→ Domain.problem_pddl = generated_problem
```

---

### Complete UI-to-Prompt Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE FLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. CREATE DOMAIN                                                            │
│     └── User clicks "New Domain"                                             │
│         └── No prompts invoked (database only)                               │
│                                                                              │
│  2. DEFINE DOMAIN (Chat Tab)                                                 │
│     └── User sends chat messages                                             │
│         └── 📝 ELICITATION PROMPT (chat_handler.py:10)                      │
│             Guides user through: INTRO → OBJECTS → PREDICATES →              │
│             ACTIONS → INITIAL → GOAL phases                                  │
│                                                                              │
│  3. COMPLETE ELICITATION                                                     │
│     └── Chat reaches COMPLETE phase                                          │
│         └── 📝 PDDL DOMAIN PROMPT (pddl_generator.py:9)                      │
│         └── 📝 PDDL PROBLEM PROMPT (pddl_generator.py:30)                    │
│             Auto-saves to Domain entity                                      │
│                                                                              │
│  4. VIEW PDDL (PDDL Tab)                                                     │
│     └── User views generated PDDL                                            │
│         └── No prompts invoked (read from database)                          │
│                                                                              │
│  5. GENERATE PLAN (Plan Tab)                                                 │
│     └── User clicks "Generate Plan"                                          │
│         │                                                                    │
│         ├── ITERATION 1:                                                     │
│         │   └── 📝 A.3: PLAN_PROMPT (orchestrator.py:21)                    │
│         │       └── 📝 A.2: CRITIQUE_PROMPT × 5 (orchestrator.py:31)        │
│         │           └── Majority vote: CORRECT? → Done!                      │
│         │                             WRONG?   → Continue                    │
│         │                                                                    │
│         ├── ITERATION 2+ (if needed):                                        │
│         │   └── 📝 A.4: PLAN_PROMPT + critique_history (orchestrator.py:86) │
│         │       └── 📝 A.2: CRITIQUE_PROMPT × 5                             │
│         │           └── Majority vote...                                     │
│         │                                                                    │
│         └── Max 5 iterations, then returns best plan                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Prompt Configuration Database Schema

Prompts can be managed and versioned via the database:

```
PromptTemplate
├── id, name, purpose (SELF_CRITIQUE, PLAN_GENERATION, ELICITATION, PDDL_GENERATION)
│
└── PromptVersion
    ├── version, content (the prompt text with {placeholders})
    ├── variables (list of placeholder names)
    ├── is_default (which version to use)
    │
    └── PromptExemplar (for few-shot prompts like A.1, A.5, B.1)
        ├── domain_type (e.g., "blocksworld", "logistics")
        ├── exemplar_content (the example text)
        └── order (sequence in prompt)
```

This allows adding few-shot exemplars (A.1, A.5, B.1) without code changes.

---

*This primer is based on arXiv:2512.24103v1. For the complete paper, see `docs/2512.24103v1.pdf`.*

*Last updated: January 2026*
