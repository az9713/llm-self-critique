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

*This primer is based on arXiv:2512.24103v1. For the complete paper, see `docs/2512.24103v1.pdf`.*

*Last updated: January 2026*
