# 🧠 thebrain
> A personal AI intelligence layer built with multi-agent orchestration, RAG, and MCP servers on top of household app data

TheBrain connects to my real household data — meals, nutrition, weekly plans — 
and answers questions across all of it using multi-agent orchestration, RAG, 
custom MCP servers, and proactive scheduled summaries.

This is a portfolio project built to demonstrate production-level agentic AI 
system design. Every component maps to a real skill used in AI engineering roles.

---

## 🎯 What It Does

**Ask questions across your household data in natural language**
> "What have we been cooking most this month? Are we hitting our protein goals?"

**Get proactive weekly summaries pushed to your phone**
> Every Sunday, OurBrain sends a digest of nutrition patterns, meal variety, 
> and personalized suggestions for the week ahead.

**Receive coaching based on your actual patterns**
> "You haven't cooked a high-protein meal in 5 days — here's a suggestion 
> based on your preferences and what's already in your weekly planner."

---

## 🏗️ Architecture
User / Phone
(natural language question or scheduled SMS summary)
│
▼
Orchestrator Agent
Routes questions to the right sub-agent,
synthesizes responses, manages context
│
┌────┴────┬──────────────┐
▼         ▼              ▼
Nutrition  Planner      Suggestion
Agent      Agent         Agent
│         │              │
└────┬────┘──────────────┘
│
▼
Custom MCP Server
Exposes OurKitchen Firebase data as tools
Claude can call (meals, planner, prefs)
│
┌────┴────────────────────┐
▼                         ▼
Firebase Firestore       ChromaDB Vector Store
(live data)              (meal history + prefs
as embeddings for RAG)


## 🧩 AI Concepts Demonstrated

| Concept | Where It Appears |
|---|---|
| **MCP Server** | Custom Python server exposing Firestore as Claude tools |
| **Multi-Agent Orchestration** | Orchestrator routes to Nutrition, Planner, and Suggestion agents |
| **RAG** | Meal history and preferences embedded in ChromaDB for semantic retrieval |
| **Tool Use** | Agents call Firestore tools to fetch live data before reasoning |
| **Evals** | Test suite scoring accuracy and usefulness of OurBrain responses |
| **Scheduled Agents** | Cron-triggered weekly summary delivered via SMS |

---

## 📦 Tech Stack

- **Language:** Python
- **LLM:** Anthropic Claude API (`claude-sonnet-4-6`)
- **Data Source:** Firebase Firestore (OurKitchen app)
- **Vector Store:** ChromaDB
- **Delivery:** Twilio SMS / OpenClaw
- **Development:** Jupyter Notebooks → Python modules
- **Version Control:** GitHub

---

## 🗂️ Project Structure
ourbrain/
├── notebooks/
│   ├── 01_firestore_connection.ipynb     # Connect to OurKitchen Firebase
│   ├── 02_mcp_server.ipynb               # Build and test MCP server
│   ├── 03_rag_pipeline.ipynb             # Embed meal data, test retrieval
│   ├── 04_agents.ipynb                   # Orchestrator + sub-agents
│   ├── 05_evals.ipynb                    # Eval framework and test cases
│   └── 06_scheduled_summary.ipynb        # Weekly summary + SMS delivery
├── src/
│   ├── mcp_server.py                     # Production MCP server
│   ├── agents.py                         # Orchestrator + sub-agent logic
│   ├── rag.py                            # Embedding + retrieval pipeline
│   └── evals.py                          # Eval suite
├── README.md
└── requirements.txt

---

## 🗺️ Build Roadmap

- [ ] **Phase 1 — Data Foundation**
  - [ ] Connect to OurKitchen Firestore from Python
  - [ ] Explore and document data structure
  - [ ] Build basic Q&A over raw data

- [ ] **Phase 2 — MCP Server**
  - [ ] Define tools: `get_meals`, `get_weekly_history`, `get_preferences`
  - [ ] Build and test MCP server locally
  - [ ] Verify Claude can call tools and reason over results

- [ ] **Phase 3 — RAG Pipeline**
  - [ ] Embed meal history into ChromaDB
  - [ ] Test semantic retrieval ("find high protein meals we've made")
  - [ ] Wire RAG results into agent context

- [ ] **Phase 4 — Multi-Agent Orchestration**
  - [ ] Build Nutrition Agent
  - [ ] Build Planner Agent
  - [ ] Build Suggestion Agent
  - [ ] Build Orchestrator that routes and synthesizes

- [ ] **Phase 5 — Evals**
  - [ ] Define 20 test questions with expected answers
  - [ ] Build scoring logic
  - [ ] Run evals after any major change

- [ ] **Phase 6 — Scheduled Delivery**
  - [ ] Build weekly summary prompt
  - [ ] Set up cron job
  - [ ] Wire to SMS delivery

---

## 🔗 Related Projects

This project is part of a personal household app ecosystem:
- **[OurKitchen]** — Shared household meal planner and grocery list (Firebase + Claude API)
- **[OurFitness]** — Shared household workout tracker (coming soon as a data source)

---

## 👤 About

Built by Sagar — exploring agentic AI system design as a pathway into AI Product 
roles. Background in [your current field], self-taught builder, shipped multiple 
household apps before this project.
