# AI Projects — Archive and Recovery Reference

> [!important] These five projects were **removed from local disk on 2026-09-01** to free ~273 MB.
> Every repository was verified pushed before deletion; local-only files were rescued to
> `~/secrets/project-configs/` (see its `MANIFEST.md`). This document is the recovery entry point.

Technical review below was written 2026-03-18. Archive status blocks added 2026-09-01.

## Recovery at a glance

| # | Project | Remote (authoritative) | HEAD at archive | Was |
| --- | --- | --- | --- | --- |
| 1 | `justAsk` | github.com/vn6295337/JustAsk | `2ebf7e7` | 30 MB |
| 2 | `enterpriseAIGateway` | github.com/vn6295337/Enterprise-AI-Gateway | `f20645b` | 73 MB |
| 3 | `instantSWOTAgent` | github.com/vn6295337/Instant-SWOT-Agent | `b543bba` | 19 MB |
| 4 | `researcherAgent` | github.com/vn6295337/Researcher-Agent | `5115fb8` | 27 MB |
| 5 | `ragDocumentAssistant` | github.com/vn6295337/RAG-document-assistant | `a810c06` | 124 MB |

### To restore any project

    git clone https://<remote> ~/<project>
    cp -rp ~/secrets/project-configs/<project>/. ~/<project>/

The second step replaces gitignored config that git cannot carry. Projects with no
entry under `~/secrets/project-configs/` need no restore step.

### Verification performed before deletion

Each repo was checked against **live remotes** via `git ls-remote`, not local
tracking refs, which can be stale — `justAsk` in particular had never fetched its
remote HEAD. `git log --branches --not --remotes` returned zero for all five:
no commit existed only on this machine.

---

## 1. JustAsk
**Tagline:** "Just ask. No signup. Forever free."

### Overview
A privacy-first AI assistant platform that abstracts the complexity of the fragmented AI model landscape. It provides a seamless user experience by automatically routing queries to the most optimal model based on real-time performance metrics.

### Architecture & Tech Stack
*   **Mobile App:** React Native (Expo), Redux, SQLite (Offline-first).
*   **API Backend:** Node.js (Express).
*   **Router Service:** Node.js (Express), Supabase. Features a 5-factor weighted scoring algorithm.
*   **Registry Pipeline:** Python ETL (37 stages) running via GitHub Actions to discover and benchmark models.
*   **Dashboard:** React, TypeScript, Vite, Tailwind CSS.

### Key Innovations
*   **Intelligent Routing:** A 5-factor scoring algorithm (Intelligence, Latency, Rate Limits, Geography, License) selects models in 5-6ms.
*   **Zero-Friction UX:** No signups or API keys required from the end-user.
*   **Privacy-First:** Local chat history (SQLite) and no cloud tracking.

---

**Archive status.** `justAsk` · 30 MB on disk · HEAD `2ebf7e7` on github.com/vn6295337/JustAsk.

Local clone was **142 commits behind** (CI pipeline outputs) — the remote is authoritative. 6 gitignored `CLAUDE.md` files and 2 `.env` files rescued to `~/secrets/project-configs/`. An uncommitted 7-line `README.md` ASCII-diagram edit was abandoned.

## 2. Enterprise AI Gateway
**Tagline:** "Resilient AI Mesh - Secure, Cost-Aware, Speed-Optimized."

### Overview
A security-first API gateway designed for enterprise LLM adoption, focusing on reliability, safety, and compliance.

### Architecture & Tech Stack
*   **Framework:** FastAPI (Python) with Pydantic validation.
*   **Security:** SlowAPI (Rate limiting), Regex-based PII/Injection detection, Gemini-based toxicity classification.
*   **Deployment:** Docker-ready, Hugging Face Spaces compatible.

### Key Innovations
*   **4-Layer Security Pipeline:** Auth/Rate Limiting -> Input Guard (PII/Injection) -> AI Safety (Toxicity) -> LLM Router.
*   **Cascade Failover:** Automatic fallback through providers (Gemini -> Groq -> OpenRouter) ensuring 99.8% uptime.
*   **Observability:** Returns `cascade_path`, `latency_ms`, and `cost_estimate_usd` with every response.

---

**Archive status.** `enterpriseAIGateway` · 73 MB on disk · HEAD `f20645b` on github.com/vn6295337/Enterprise-AI-Gateway.

Identical on both remotes. 72 MB of the 73 MB was `.git`; the worktree is 620 KB. No local-only files.

## 3. Instant SWOT Agent
**Tagline:** "Multi-agent workflow with self-correcting feedback."

### Overview
An agentic AI system that automates strategic SWOT analysis for companies using a self-correcting loop to ensure high-quality output.

### Architecture & Tech Stack
*   **Orchestration:** LangGraph (native support for cyclic workflows).
*   **Agents:** Researcher, Analyst, Critic, Editor.
*   **Backend:** Python (FastAPI), LangChain.
*   **Frontend:** React, TypeScript, Vite, Tailwind CSS.

### Key Innovations
*   **Self-Correcting Loop:** The 'Critic' agent scores the 'Analyst's' draft; if below 7/10, the 'Editor' revises it based on feedback (up to 3 iterations).
*   **MCP Integration:** Uses 6 specialized Model Context Protocol (MCP) servers for real-time data gathering (Financials, Volatility, Macro, Valuation, News, Sentiment).

---

**Archive status.** `instantSWOTAgent` · 19 MB on disk · HEAD `b543bba` on github.com/vn6295337/Instant-SWOT-Agent.

`AgentAsk.pdf` (19pp) and `SWOT_Boeing.pdf` (5pp) were caught by a blanket `*.pdf` ignore rule and existed only locally — now committed with negation exceptions and pushed to GitHub. The HF Space rejected them (pre-receive hook requires Git LFS) and sits one commit behind. `.env` rescued to `~/secrets/project-configs/`.

## 4. Researcher Agent
**Tagline:** "Financial research service implementing Google's A2A protocol."

### Overview
A specialized microservice that acts as a data provider for other agents (like the SWOT agent), focusing on deep financial and macroeconomic data retrieval.

### Architecture & Tech Stack
*   **Protocol:** Google A2A (Agent-to-Agent) using JSON-RPC 2.0.
*   **Interface:** TRUE MCP (Subprocess + JSON-RPC) for communication with data "baskets".
*   **Data Sources:** SEC EDGAR, Yahoo Finance, FRED, Tavily, Finnhub.

### Key Innovations
*   **True MCP Handshake:** Implements the official MCP specification (initialize -> initialized -> tools/call).
*   **Streaming Metrics:** Provides `partial_metrics` during execution to allow for real-time UI progress updates.
*   **Sequential Priority:** Orchestrates 6 MCP servers in a specific order to optimize data dependency handling.

---

**Archive status.** `researcherAgent` · 27 MB on disk · HEAD `5115fb8` on github.com/vn6295337/Researcher-Agent.

Identical across all three remotes. `.env` rescued to `~/secrets/project-configs/`. `.venv-sentiment` (16 MB) discarded — regenerable.

## 5. RAG Document Assistant
**Tagline:** "Privacy-first document search with zero storage."

### Overview
A Retrieval-Augmented Generation (RAG) system that allows users to chat with their own documents (via Dropbox) without ever storing the document text on a server.

### Architecture & Tech Stack
*   **Parsing:** Docling (IBM) for high-fidelity document structure extraction.
*   **Vector DB:** Pinecone (stores embeddings and metadata only).
*   **Auth/Source:** Dropbox OAuth.
*   **LLM:** Multi-provider fallback (Gemini, Groq, OpenRouter).

### Key Innovations
*   **Zero-Disk Processing:** Uses RAM-only streams (BytesIO) during parsing; text is never written to server disk.
*   **Embeddings-Only Storage:** Only mathematical vectors and character positions are stored in Pinecone.
*   **Query-Time Re-fetch:** Raw text is re-fetched from the user's Dropbox at the moment of the query, ensuring the user retains absolute control over their data.

---
*Technical review 2026-03-18 · archive status 2026-09-01*

**Archive status.** `ragDocumentAssistant` · 124 MB on disk · HEAD `a810c06` on github.com/vn6295337/RAG-document-assistant.

GitHub is exact; the HF Space is 31 commits behind (deployment lag, not a backup gap). `.env` and `frontend/.env` rescued to `~/secrets/project-configs/` — **neither has a `.env.example` in git**, so their shape existed nowhere else.
