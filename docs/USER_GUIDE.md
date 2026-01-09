# User Guide

Complete guide for using the Self-Critique Planning Platform. This guide assumes no prior experience with planning systems or AI tools.

## Table of Contents

1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [Getting Started](#getting-started)
4. [The Dashboard](#the-dashboard)
5. [Creating Planning Domains](#creating-planning-domains)
6. [The Elicitation Chat](#the-elicitation-chat)
7. [Generating Plans](#generating-plans)
8. [Understanding Self-Critique](#understanding-self-critique)
9. [Viewing and Analyzing Plans](#viewing-and-analyzing-plans)
10. [PDDL Validation](#pddl-validation)
11. [Using the API](#using-the-api)
12. [Analytics Dashboard](#analytics-dashboard)
13. [Tips and Best Practices](#tips-and-best-practices)
14. [Glossary](#glossary)

---

## Introduction

### What is This Platform?

The Self-Critique Planning Platform is a tool that helps you create optimal plans for complex tasks. Instead of manually figuring out the best sequence of actions, you describe your problem in plain English, and AI generates, critiques, and refines a plan for you.

### Who is This For?

- **Project Managers** planning complex projects
- **Operations Teams** optimizing workflows
- **Individuals** planning events, moves, or complex tasks
- **Developers** building planning features into applications
- **Researchers** studying AI planning systems

### What Makes It Special?

Traditional planning tools require you to learn complex formal languages. This platform:
- Accepts **natural language** descriptions
- Uses **multiple AI critics** to find problems
- **Iteratively improves** plans based on feedback
- Provides **real-time** visibility into the planning process

---

## Core Concepts

Before diving in, let's understand the key terms you'll encounter.

### Planning Domain

A **domain** defines the "world" in which planning happens. It includes:
- **Objects**: Things that exist (e.g., rooms, items, people)
- **Predicates**: Properties and relationships (e.g., "is clean", "is in room")
- **Actions**: Things that can be done (e.g., "clean room", "move item")

**Example Domain: Kitchen Cleaning**
- Objects: kitchen, sponge, soap, sink, counter
- Predicates: is_dirty(surface), has_item(location, item)
- Actions: scrub(surface), rinse(surface), put_away(item)

### Planning Problem

A **problem** is a specific instance within a domain:
- **Initial State**: How things are now
- **Goal State**: How you want things to be

**Example Problem:**
- Initial: counter is dirty, sink is dirty, sponge is dry
- Goal: counter is clean, sink is clean

### Plan

A **plan** is a sequence of actions that transforms the initial state into the goal state.

**Example Plan:**
1. wet_sponge(sponge, sink)
2. scrub(counter, sponge)
3. rinse(counter)
4. scrub(sink, sponge)
5. rinse(sink)

### Self-Critique

The process where AI reviews its own work:
1. Generate initial plan
2. Multiple AI "critics" identify issues
3. Address the issues
4. Repeat until plan is good enough

### PDDL

**Planning Domain Definition Language** - A formal language for describing planning problems. You don't need to write it; the system generates it from your natural language descriptions.

---

## Getting Started

### First-Time Setup

1. **Open the Application**
   - Navigate to http://localhost:3000 in your browser
   - You'll see the landing page

2. **Create an Account** (if authentication is enabled)
   - Click "Register"
   - Enter your email and password
   - Verify your email if required

3. **Navigate to Dashboard**
   - Click "Dashboard" or "Get Started"
   - You'll see your planning workspace

### Interface Overview

```
┌─────────────────────────────────────────────────────────────┐
│  [Logo]  Self-Critique Planner        [User] [Settings]     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌───────────────────────────────────┐│
│  │                 │  │                                   ││
│  │    Sidebar      │  │         Main Content Area         ││
│  │                 │  │                                   ││
│  │  - Dashboard    │  │   (Changes based on selection)    ││
│  │  - Domains      │  │                                   ││
│  │  - Analytics    │  │                                   ││
│  │  - Settings     │  │                                   ││
│  │                 │  │                                   ││
│  └─────────────────┘  └───────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## The Dashboard

The dashboard is your home base. Here's what you'll find:

### Domain List

Shows all your planning domains:
- **Name**: The domain's title
- **Description**: Brief summary
- **Status**: Draft, Complete, or Has Plan
- **Last Modified**: When it was last updated

### Quick Actions

- **New Domain**: Create a new planning domain
- **Import**: Import a domain from PDDL file
- **Recent**: Jump to recently viewed domains

### Statistics Panel

- Total domains created
- Plans generated
- Average critique iterations
- Success rate

---

## Creating Planning Domains

### Method 1: Through the Chat Interface (Recommended)

This is the easiest way to create a domain.

1. **Click "New Domain"**
2. **Enter Basic Information**:
   - Name: A descriptive title
   - Description: One-line summary
3. **Click "Create"**
4. **Start Chatting**

The AI will guide you through defining:
- What objects exist in your domain
- What actions are possible
- What conditions must be met for actions
- What effects actions have

### Method 2: Direct PDDL Input (Advanced)

If you already have PDDL knowledge:

1. Click "New Domain"
2. Select "Advanced Mode"
3. Paste or type your PDDL code
4. Click "Validate" to check for errors
5. Click "Save"

### Domain Best Practices

**DO:**
- Start simple, add complexity gradually
- Be specific about preconditions
- Think about what could go wrong
- Include all necessary objects

**DON'T:**
- Try to model everything at once
- Forget about dependencies
- Assume implicit knowledge
- Skip the validation step

---

## The Elicitation Chat

The chat interface is where you define your domain through conversation.

### How It Works

The AI asks questions to understand your planning problem:

```
AI: "What type of planning problem would you like to solve?"

You: "I need to plan a software release"

AI: "I can help with that. What are the main activities
     involved in your release process?"

You: "Code freeze, testing, bug fixes, staging deployment,
     production deployment, and announcement"

AI: "Great. Are there dependencies between these activities?
     For example, must testing happen before bug fixes?"

You: "Yes, testing must happen first to find bugs. Bug fixes
     come after. Staging deployment needs testing and bug fixes
     complete. Production needs successful staging. Announcement
     is last."

AI: "I understand. Are there any resources or constraints?
     For example, limited servers or team availability?"
```

### Chat Features

#### Message Types
- **Your Messages**: Light background, right-aligned
- **AI Messages**: Dark background, left-aligned
- **System Messages**: Centered, italic

#### Quick Responses
Some AI questions include buttons for common answers:
- "Yes" / "No"
- "Add more" / "That's all"
- "Continue" / "Go back"

#### Progress Indicator
Shows which phase of elicitation you're in:
1. Overview
2. Objects
3. Actions
4. Preconditions
5. Effects
6. Review

### Session Persistence

Your chat sessions are automatically linked to domains:

- **Conversations are saved**: Navigate away and come back - your chat history remains
- **Domain linking**: When you create a domain and start chatting, the session is linked to that domain
- **PDDL auto-generation**: When elicitation completes, PDDL is automatically generated and saved to the domain
- **Manual regeneration**: You can regenerate PDDL at any time using the "Generate PDDL" button

### Tips for Better Conversations

1. **Be Specific**: Instead of "things", say "documents, servers, databases"

2. **Think About Order**: What must happen before what?

3. **Consider Failures**: What if something goes wrong?

4. **Include Resources**: What's limited? (time, people, equipment)

5. **State Goals Clearly**: What does "done" look like?

---

## Generating Plans

Once your domain is defined, you can generate plans.

### Starting Plan Generation

1. Navigate to your domain
2. Click "Generate Plan"
3. Enter the planning problem:
   - Initial state: Current situation
   - Goal state: Desired outcome

### The Planning Process

```
┌─────────────────────────────────────────────────┐
│           Planning Progress                      │
├─────────────────────────────────────────────────┤
│                                                  │
│  ✓ Initializing planner                         │
│  ✓ Generating initial plan                      │
│  ◐ Running critique iteration 1/5               │
│    ├── Completeness Critic: reviewing...        │
│    ├── Efficiency Critic: reviewing...          │
│    └── Safety Critic: reviewing...              │
│  ○ Aggregating feedback                         │
│  ○ Refining plan                                │
│  ○ Final validation                             │
│                                                  │
│  [━━━━━━━━━━━━━━━━━━━━░░░░░░░░░░] 60%           │
│                                                  │
│  Elapsed: 45s | Est. remaining: 30s             │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Real-Time Updates

The interface updates in real-time showing:
- Current phase of planning
- What each critic is doing
- Preliminary results
- Time estimates

---

## Understanding Self-Critique

The self-critique system is what makes this platform special.

### The Three Critics

#### 1. Completeness Critic
**Question**: "Does this plan achieve all goals?"

**Looks For**:
- Missing steps
- Unachievable goals
- Incomplete sequences

**Example Feedback**:
> "The plan doesn't include a step to notify stakeholders before the release. This is required by the domain definition."

#### 2. Efficiency Critic
**Question**: "Is this the best way to do it?"

**Looks For**:
- Unnecessary steps
- Suboptimal ordering
- Parallelization opportunities

**Example Feedback**:
> "Steps 3 and 4 have no dependencies and could be executed in parallel, reducing total time by 30%."

#### 3. Safety Critic
**Question**: "Could anything go wrong?"

**Looks For**:
- Risk conditions
- Missing error handling
- Dangerous sequences

**Example Feedback**:
> "Deploying to production before backup creates risk of data loss. Recommend adding backup step first."

### The Voting System

After critics provide feedback, the system aggregates it:

```
Feedback Item: "Add notification step"
├── Completeness Critic: AGREE (weight: 0.4)
├── Efficiency Critic: NEUTRAL (weight: 0.3)
└── Safety Critic: AGREE (weight: 0.3)

Weighted Score: 0.7 (threshold: 0.5)
Decision: INCORPORATE
```

### Iteration Process

1. **Initial Plan**: AI generates first attempt
2. **Critique Round**: All critics review
3. **Voting**: Feedback is aggregated
4. **Refinement**: Plan is updated
5. **Repeat**: Until consensus or max iterations

Typically 2-4 iterations are needed.

---

## Viewing and Analyzing Plans

### Plan View Components

#### Step List
Shows each action in order:
```
┌─────────────────────────────────────────────────┐
│ Step 1: code_freeze                             │
│   Preconditions: all_features_merged            │
│   Effects: code_is_frozen                       │
├─────────────────────────────────────────────────┤
│ Step 2: run_tests                               │
│   Preconditions: code_is_frozen                 │
│   Effects: tests_complete, bugs_identified      │
├─────────────────────────────────────────────────┤
│ Step 3: fix_bugs                                │
│   Preconditions: bugs_identified                │
│   Effects: bugs_fixed                           │
└─────────────────────────────────────────────────┘
```

#### Critique Trace
Shows what critics said at each iteration:
```
Iteration 1:
├── Completeness: "Missing rollback procedure"
├── Efficiency: "Can parallelize steps 4-5"
└── Safety: "No backup before deploy"

Iteration 2:
├── Completeness: "All steps present" ✓
├── Efficiency: "Parallelization implemented" ✓
└── Safety: "Backup added, rollback defined" ✓
```

#### Timeline View
Visual representation of the plan:
```
Time →
─────────────────────────────────────────────────
code_freeze  ████
run_tests         ████████
fix_bugs                   ████
staging                         ██████
production                             ████
announce                                    ██
─────────────────────────────────────────────────
```

### Exporting Plans

Click "Export" to save plans as:
- **PDF**: Formatted document
- **JSON**: Machine-readable
- **PDDL**: Formal planning format
- **Markdown**: Documentation format

---

## PDDL Validation

The platform validates PDDL specifications automatically.

### Validation Types

#### Syntax Validation
Checks for correct PDDL grammar:
- Proper parentheses matching
- Valid keywords
- Correct structure

#### Semantic Validation
Checks for logical correctness:
- Referenced objects exist
- Actions have valid preconditions
- Effects are consistent

### Validation Results

```
┌─────────────────────────────────────────────────┐
│ Validation Results                              │
├─────────────────────────────────────────────────┤
│ ✓ Syntax: Valid                                 │
│ ✗ Semantic: 2 errors, 1 warning                 │
│                                                 │
│ ERRORS:                                         │
│ Line 15: Action 'deploy' references undefined   │
│          object 'staging-server'                │
│                                                 │
│ Line 23: Precondition 'is-tested' never becomes │
│          true (no action produces it)           │
│                                                 │
│ WARNINGS:                                       │
│ Line 8: Object 'backup-server' defined but      │
│         never used in any action                │
└─────────────────────────────────────────────────┘
```

### Fixing Validation Errors

1. Click on the error to jump to the location
2. Review the issue description
3. Edit the PDDL or regenerate through chat
4. Re-validate

---

## Using the API

For programmatic access, use the REST API.

### Getting an API Key

1. Go to Settings → API Keys
2. Click "Create New Key"
3. Enter a name for the key
4. Set rate limit (requests per minute)
5. Copy the key immediately (only shown once!)

### Basic API Usage

**Create a Domain:**
```bash
curl -X POST http://localhost:8000/api/v1/domains \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Domain",
    "description": "A test domain"
  }'
```

**Generate a Plan:**
```bash
curl -X POST http://localhost:8000/api/v1/planning/sessions \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "uuid-here",
    "problem": "...",
    "max_iterations": 5
  }'
```

### Rate Limits

- Default: 100 requests per minute
- Customizable per API key
- Headers show remaining quota:
  - `X-RateLimit-Limit`: Your limit
  - `X-RateLimit-Remaining`: Requests left
  - `X-RateLimit-Reset`: Seconds until reset

---

## Analytics Dashboard

Monitor your usage and planning performance.

### Usage Summary
- Total requests
- Success/failure rates
- Average latency
- Token usage

### Endpoint Statistics
See which features you use most:
- Planning sessions created
- Domains defined
- Chat messages sent

### Daily Trends
Graph showing usage over time:
- Identify peak usage times
- Track growth
- Spot anomalies

---

## Tips and Best Practices

### For Better Domains

1. **Start Small**: Define 3-5 actions first, then expand
2. **Be Explicit**: Don't assume the AI knows industry jargon
3. **Test Incrementally**: Validate after each major addition
4. **Use Examples**: Provide concrete examples when describing actions

### For Better Plans

1. **Clear Goals**: Ambiguous goals lead to ambiguous plans
2. **Check Assumptions**: Review initial state carefully
3. **Review Critiques**: The critics often catch subtle issues
4. **Iterate**: Don't expect perfection on first try

### For Better Performance

1. **Batch Requests**: Combine related API calls
2. **Cache Results**: Store generated plans for reference
3. **Use Webhooks**: For long-running operations
4. **Monitor Usage**: Stay within rate limits

---

## Glossary

| Term | Definition |
|------|------------|
| **Action** | A single step that can be taken in a plan |
| **Critique** | AI-generated feedback on a plan |
| **Domain** | The "world" definition including objects and actions |
| **Effect** | What changes when an action is performed |
| **Elicitation** | The process of extracting domain info through conversation |
| **Goal State** | The desired end condition |
| **Initial State** | The starting condition |
| **Iteration** | One cycle of plan → critique → refine |
| **PDDL** | Planning Domain Definition Language |
| **Plan** | A sequence of actions to achieve a goal |
| **Precondition** | What must be true for an action to be possible |
| **Problem** | A specific instance combining initial and goal states |
| **Self-Critique** | AI reviewing and improving its own output |
| **Validation** | Checking PDDL for correctness |

---

## Getting Help

If you're stuck:

1. **Check this guide** for answers to common questions
2. **Review the Quick Start** for basic setup issues
3. **Check the Developer Guide** for technical problems
4. **Open an issue** on GitHub for bugs
5. **Community forum** for discussions

---

*Last updated: January 2026*
