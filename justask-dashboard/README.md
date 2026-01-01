# JustAsk Dashboard

**Version:** 1.0.0

Interactive React dashboard that visualizes AI models from multiple providers, helping developers discover and compare available models.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  JUSTASK PLATFORM                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [1] Registry Pipeline  →  [2] Dashboard  →  [3] Client        │
│                                                                 │
│      justask-registry      justask-         justask/           │
│                            dashboard        (api + app)         │
│                                                                 │
│  • 37-stage automation    • Daily updates     • Smart routing  │
│  • Daily updates          • 50+ models        • Multi-provider │
│  • Zero manual work       • Decision support  • Secure access  │
└─────────────────────────────────────────────────────────────────┘
```

**Data Flow:**
Registry Pipeline → Supabase (`ai_models_main` table) → Dashboard + API

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-Provider Support** | Aggregates models from 7+ AI providers |
| **Interactive Visualizations** | Bar charts with provider and task type breakdowns |
| **Real-time Updates** | Auto-refreshes every 5 minutes |
| **Responsive Design** | Works on desktop and mobile devices |
| **Task Type Filtering** | Groups small categories for cleaner visualization |

---

## Quick Start

```bash
npm install
cp .env.example .env
# Edit .env with your Supabase credentials
npm run dev
```

---

## Configuration

**Required:**
```env
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

---

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend | React 18, TypeScript | Component-based UI |
| Build Tool | Vite | Fast development server |
| Styling | Tailwind CSS, shadcn/ui | Utility-first CSS |
| Charts | Chart.js, react-chartjs-2 | Interactive visualizations |
| Database | Supabase (PostgreSQL) | Real-time data |
| Deployment | GitHub Pages | Static hosting |

---

## Development

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
```

---

## License

MIT License - See LICENSE file for details.
