# Quick Start Guide

Welcome! This guide will get you up and running with the Self-Critique Planning Platform in about 10 minutes. By the end, you'll have created your first AI-generated plan.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Your First Plan](#your-first-plan)
4. [10 Educational Use Cases](#10-educational-use-cases)
5. [Next Steps](#next-steps)

---

## Prerequisites

Before starting, make sure you have:

### Required Software

| Software | Version | Download Link | How to Check |
|----------|---------|---------------|--------------|
| Python | 3.11+ | [python.org](https://python.org) | `python --version` |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) | `node --version` |
| Git | Any | [git-scm.com](https://git-scm.com) | `git --version` |

### API Key (Required for AI Features)

You need an API key from either:
- **Anthropic (Claude)**: https://console.anthropic.com/ (Recommended)
- **OpenAI**: https://platform.openai.com/

**Getting an Anthropic API Key:**
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to "API Keys"
4. Click "Create Key"
5. Copy and save the key (starts with `sk-ant-`)

---

## Installation

### Step 1: Download the Project

Open your terminal (Command Prompt on Windows, Terminal on Mac/Linux):

```bash
# Clone the repository
git clone https://github.com/az9713/llm-self-critique.git

# Enter the project folder
cd llm-self-critique
```

**What just happened?**
- `git clone` downloaded the entire project to your computer
- `cd` changed your current directory to the project folder

### Step 2: Set Up the Backend

```bash
# Enter the backend folder
cd backend

# Create a virtual environment (keeps packages isolated)
python -m venv venv
```

**Activate the virtual environment:**

On **Windows** (Command Prompt):
```cmd
venv\Scripts\activate
```

On **Windows** (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```

On **Mac/Linux**:
```bash
source venv/bin/activate
```

You should see `(venv)` appear at the start of your command line.

```bash
# Install all required packages
pip install -e ".[dev]"
```

**What is a virtual environment?**
Think of it as a separate container for this project's packages. It prevents conflicts with other Python projects on your computer.

### Step 3: Configure Your API Key

**On Windows (Command Prompt):**
```cmd
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**On Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**On Mac/Linux:**
```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Step 4: Start the Backend Server

```bash
python -m uvicorn src.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

**Keep this terminal open!** The server needs to stay running.

### Step 5: Set Up the Frontend (New Terminal)

Open a **new terminal window** and navigate to the project:

```bash
cd path/to/llm-self-critique/frontend

# Install frontend packages
npm install

# Start the frontend
npm run dev
```

You should see:
```
- Local:        http://localhost:3000
- Ready in 2.5s
```

### Step 6: Open the Application

Open your web browser and go to: **http://localhost:3000**

🎉 **Congratulations!** The application is now running!

---

## Your First Plan

Let's create a simple plan together.

### Step 1: Create a New Domain

1. Click **"New Domain"** button on the dashboard
2. Enter a name: "Morning Routine"
3. Enter a description: "Plan my morning activities"
4. Click **"Create"**

### Step 2: Define Your Domain Through Chat

The chat interface will guide you. Try this conversation:

**You:** "I want to plan my morning routine"

**AI:** "I'd be happy to help you plan your morning routine. What activities do you need to include?"

**You:** "Wake up, shower, get dressed, eat breakfast, and leave for work"

**AI:** "Great! Are there any dependencies between these activities? For example, must some activities happen before others?"

**You:** "I need to wake up first, then shower, then get dressed. I can eat breakfast anytime after waking up but before leaving."

**AI:** "Got it. Any time constraints?"

**You:** "I need to leave by 8:00 AM"

### Step 3: Generate a Plan

1. Click **"Generate Plan"** button
2. Watch as the system:
   - Creates an initial plan
   - Has AI critics review it
   - Refines based on feedback
3. View the final optimized plan

### Step 4: Review the Results

The planning view shows:
- **Plan Steps**: Ordered sequence of actions
- **Critique Trace**: What each critic said
- **Iterations**: How the plan improved

---

## 10 Educational Use Cases

These examples progress from simple to complex. Try them in order to build your understanding.

### Use Case 1: Making a Sandwich 🥪
**Complexity:** Beginner | **Time:** 2 minutes

**Goal:** Learn basic sequential planning

**Domain Description:**
> "I want to make a peanut butter and jelly sandwich. I need to get bread, peanut butter, jelly, and a knife. Then spread peanut butter on one slice, jelly on the other, and put them together."

**What You'll Learn:**
- How to define simple sequential actions
- Basic preconditions (need knife before spreading)

**Expected Plan:**
1. Get bread slices
2. Get peanut butter jar
3. Get jelly jar
4. Get knife
5. Spread peanut butter on slice 1
6. Spread jelly on slice 2
7. Combine slices

---

### Use Case 2: Getting Ready for a Trip ✈️
**Complexity:** Beginner | **Time:** 3 minutes

**Goal:** Learn parallel actions

**Domain Description:**
> "I'm preparing for a trip. I need to pack clothes, pack toiletries, charge my phone, print boarding pass, and call a taxi. Packing can be done in any order. The taxi should be called last."

**What You'll Learn:**
- Some actions can happen in parallel
- Some actions must happen in specific order

**Expected Insight:**
The AI might suggest packing while phone charges to save time.

---

### Use Case 3: Cooking Pasta Dinner 🍝
**Complexity:** Beginner-Intermediate | **Time:** 5 minutes

**Goal:** Learn resource constraints

**Domain Description:**
> "I want to cook spaghetti with tomato sauce. I need to boil water, cook pasta, heat sauce, and prepare garlic bread. I only have one stove with two burners. The pasta takes 10 minutes, sauce takes 5 minutes."

**What You'll Learn:**
- Resource limitations affect planning
- Timing and parallelization

**Expected Critique:**
"Start sauce when pasta is halfway done so both finish together."

---

### Use Case 4: Home Cleaning Schedule 🧹
**Complexity:** Intermediate | **Time:** 5 minutes

**Goal:** Learn multi-room planning with dependencies

**Domain Description:**
> "Clean my apartment: living room, kitchen, bathroom, bedroom. Vacuum all rooms (one vacuum cleaner). Mop kitchen and bathroom after vacuuming. Clean bathroom last because I'll wash cleaning supplies there."

**What You'll Learn:**
- Shared resources (vacuum cleaner)
- Logical dependencies across locations

**Self-Critique Example:**
The efficiency critic might suggest: "Vacuum all rooms first, then mop, to avoid switching between tasks."

---

### Use Case 5: Event Planning - Birthday Party 🎂
**Complexity:** Intermediate | **Time:** 7 minutes

**Goal:** Learn deadline-driven planning

**Domain Description:**
> "Plan a birthday party for Saturday 3 PM. Tasks: send invitations (need 1 week advance), order cake (2 days advance), buy decorations, set up decorations (day of, takes 2 hours), prepare food (morning of party)."

**What You'll Learn:**
- Working backwards from deadlines
- Lead time requirements

**Expected Plan:**
The system will calculate when each task must start based on the party date.

---

### Use Case 6: Software Deployment 💻
**Complexity:** Intermediate | **Time:** 7 minutes

**Goal:** Learn technical workflow planning

**Domain Description:**
> "Deploy a web application. Steps: run tests, build application, backup database, stop current server, deploy new code, run database migrations, start server, verify deployment. If verification fails, rollback."

**What You'll Learn:**
- Sequential dependencies in technical processes
- Rollback planning

**Self-Critique Example:**
Safety critic: "Add a step to notify users before stopping the server."

---

### Use Case 7: Moving to a New Apartment 📦
**Complexity:** Intermediate-Advanced | **Time:** 10 minutes

**Goal:** Learn complex multi-day planning

**Domain Description:**
> "Move from apartment A to apartment B. Tasks: rent moving truck (1 day), pack boxes (3 days), disconnect utilities at A, connect utilities at B (needs 2-day advance notice), clean A after moving out, move furniture (needs truck and helpers), unpack (after furniture moved)."

**What You'll Learn:**
- Multi-day scheduling
- Coordinating multiple resources
- Advance notice requirements

**Expected Insights:**
- Utility scheduling must start early
- Packing can overlap with other preparations

---

### Use Case 8: Product Launch Campaign 🚀
**Complexity:** Advanced | **Time:** 10 minutes

**Goal:** Learn team coordination planning

**Domain Description:**
> "Launch a new product. Marketing team: create landing page (1 week), write press release (3 days), social media campaign (ongoing after launch). Engineering: final testing (1 week), fix critical bugs (depends on testing), deploy to production. Sales: prepare demo scripts (5 days), train sales team (2 days, after scripts ready). Launch date is fixed."

**What You'll Learn:**
- Cross-team dependencies
- Parallel workstreams
- Fixed deadline coordination

**Self-Critique Example:**
Completeness critic: "What if critical bugs take longer than expected? Add buffer time."

---

### Use Case 9: Manufacturing Assembly Line 🏭
**Complexity:** Advanced | **Time:** 12 minutes

**Goal:** Learn resource-constrained scheduling

**Domain Description:**
> "Assemble electronic devices. Stations: soldering (2 machines, 5 min/unit), testing (1 machine, 3 min/unit), packaging (2 workers, 2 min/unit). Need to produce 100 units. Each unit must go through all stations in order. Identify bottlenecks."

**What You'll Learn:**
- Bottleneck identification
- Throughput optimization
- Resource allocation

**Expected Analysis:**
Testing (1 machine) is the bottleneck limiting throughput to 20 units/hour.

---

### Use Case 10: Emergency Response Plan 🚨
**Complexity:** Expert | **Time:** 15 minutes

**Goal:** Learn conditional and priority-based planning

**Domain Description:**
> "Hospital emergency response for mass casualty event. Resources: 3 ER doctors, 10 nurses, 5 beds, 2 operating rooms. Incoming: 20 patients of varying severity (5 critical, 8 serious, 7 minor). Critical patients need immediate surgery. Serious need ER beds. Minor can wait. Goal: minimize deaths and waiting times."

**What You'll Learn:**
- Priority-based scheduling
- Resource allocation under constraints
- Triage logic

**Self-Critique Example:**
- Safety critic: "Critical patients must be seen within 10 minutes"
- Efficiency critic: "Minor injuries can be treated by nurses to free doctors"
- Completeness critic: "What if more critical patients arrive?"

---

## Next Steps

Now that you've completed these use cases, you're ready to:

1. **Create Your Own Domains** - Apply what you learned to your real planning problems

2. **Explore Advanced Features**:
   - API access for programmatic planning
   - Analytics dashboard for usage insights
   - PDDL export for formal planning tools

3. **Read the Full Documentation**:
   - [User Guide](USER_GUIDE.md) - Complete feature reference
   - [Developer Guide](DEVELOPER_GUIDE.md) - Build and extend the platform

4. **Experiment**:
   - Try modifying the use cases above
   - Add more constraints
   - See how the critiques change

## Troubleshooting Quick Start Issues

### "Command not found: python"
- Make sure Python is installed and in your PATH
- Try `python3` instead of `python`

### "npm: command not found"
- Install Node.js from https://nodejs.org
- Restart your terminal after installation

### "Connection refused" when opening localhost:3000
- Make sure both backend (port 8000) and frontend (port 3000) are running
- Check for error messages in the terminals

### "API key invalid"
- Double-check your API key is correct
- Make sure you're using the right environment variable name
- Try setting the key again in a new terminal

### Backend won't start
```bash
# Make sure virtual environment is activated
# You should see (venv) at the start of your command line

# If packages are missing:
pip install -e ".[dev]"
```

---

**Congratulations!** You've completed the Quick Start Guide. You now understand the fundamentals of the Self-Critique Planning Platform. Happy planning! 🎯
