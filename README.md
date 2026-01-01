# JustAsk

**Just ask. No signup. Forever free.**

[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

| Resource | Link |
|----------|------|
| Product Demo | [Watch Demo](https://github.com/vn6295337/JustAsk/issues/1) |
| Mobile App | [Install via Expo Go](#mobile-app) |
| Dashboard | [justask-dashboard.vercel.app](https://justask-dashboard.vercel.app/) |
| Business Guide | [BUSINESS_README.md](BUSINESS_README.md) |

---

## The Problem

The AI model landscape is fragmented and constantly shifting:

- **User Friction** — Want to ask a question? First choose a provider, sign up, get an API key, learn their interface. Hit a rate limit? Start over with another provider.
- **Vendor Lock-In** — Commit to one provider and you're stuck when pricing changes or better models emerge elsewhere.
- **Moving Target** — 50+ models across 3 providers, each with different APIs, pricing, rate limits, and strengths. The "best" model today may be outdated next week.

## The Solution

A privacy-focused AI assistant platform with intelligent model routing:

- **Zero Friction** — Open the app, type a question, get an answer. No signup, no API keys, no configuration.
- **Intelligent Routing** — 5-factor scoring algorithm selects optimal model in 5-6ms with automatic failover.
- **Privacy First** — All data stored locally on device. No history, no tracking, no cloud sync.

## Why This Matters

Most AI tools require technical setup that blocks non-technical users. JustAsk abstracts away provider complexity entirely—when a better model launches anywhere, it automatically becomes available. The pattern demonstrates how to build user-facing AI infrastructure that adapts as the landscape evolves.

---

## Architecture

```
User Query
    │
    ▼
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│ JustAsk App │────▶│ JustAsk Router  │────▶│ LLM Provider │
│  (Mobile)   │     │ (Model Select)  │     │ (Gemini/Groq)│
└─────────────┘     └─────────────────┘     └──────────────┘
                           │
                           ▼
                    ┌─────────────────┐
                    │ JustAsk Registry│
                    │ (Model Metadata)│
                    └─────────────────┘
```

### Data Flow

```
Registry Pipeline (daily) → Supabase → Router (query-time) → App → User
                                    → Dashboard (visualization)
```

---

## Platform Overview

```
justask/
├── justask/                 # Mobile app + API backend
│   ├── app/                 # React Native (Expo) Android app
│   └── api/                 # Node.js Express backend
├── justask-router/          # Intelligent model selection service
├── justask-registry/        # AI model discovery pipeline
└── justask-dashboard/       # Model visualization dashboard
```

---

## Components

| Component | Purpose | Tech Stack |
|-----------|---------|------------|
| **JustAsk App** | Privacy-focused mobile AI assistant | React Native, Expo, Redux, SQLite |
| **JustAsk Router** | Intelligent model selection (5-6ms latency) | Node.js, Express, Supabase |
| **JustAsk Registry** | 37-stage ETL pipeline for model discovery | Python, GitHub Actions |
| **JustAsk Dashboard** | Model analytics and visualization | React, TypeScript, Chart.js |

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Mobile | React Native, Expo, Redux |
| Backend | Node.js, Express |
| Data Pipeline | Python, GitHub Actions |
| Database | Supabase (PostgreSQL) |
| Frontend | React, TypeScript, Vite, Tailwind |

---

## Quick Start

### Dashboard (Visualization)

```bash
cd justask-dashboard
npm install
cp .env.example .env
# Edit .env with Supabase credentials
npm run dev
```

### Router (Model Selection)

```bash
cd justask-router/selector-service
npm install
cp .env.example .env
# Edit .env with Supabase credentials
npm run dev
```

### Registry (Data Pipeline)

```bash
cd justask-registry
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.local.example .env.local
# Edit .env.local with credentials
python -m src.main --pipeline openrouter
```

### Mobile App + API

```bash
# Backend
cd justask/api
npm install
cp .env.example .env
npm run dev

# Mobile App
cd justask/app
npm install
npx expo start
```

---

## Mobile App

### Installation

1. Download **Expo Go** on your phone:

| Platform | Link |
|----------|------|
| Android | [Google Play Store](https://play.google.com/store/apps/details?id=host.exp.exponent) |
| iPhone | [Apple App Store](https://apps.apple.com/app/expo-go/id982107779) |

2. Open Expo Go and scan the QR code provided

### Usage

1. Type your question in the text box
2. Tap **Send**
3. Wait for the AI response

No account needed.

### Features

| Feature | Description |
|---------|-------------|
| Offline Support | Chat history saved locally on device |
| Smart Caching | Repeated questions load instantly |
| Multi-Model | Automatically picks the best available AI |

### Troubleshooting

| Problem | Solution |
|---------|----------|
| App won't load | Check your internet connection |
| QR code not working | Update Expo Go to latest version |
| Slow response | AI service may be busy, wait a moment |

---

## Configuration

**Required (all components):**
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_KEY` — Supabase anon key

**Optional:**
- `SELECTOR_SERVICE_URL` — Router service URL (default: localhost:3001)
- `PORT` — Service port

See component READMEs for full configuration details.

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request

---

## License

MIT License
