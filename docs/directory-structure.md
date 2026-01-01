# JustAsk Directory Structure

```
JustAsk/
├── .github/                    # GitHub configuration
│   ├── ISSUE_TEMPLATE/         # Bug reports, feature requests
│   └── workflows/              # CI/CD pipelines
│
├── docs/                       # All documentation
│   ├── api/                    # API endpoints, schema, deployment
│   ├── app/                    # Mobile app architecture
│   ├── registry/               # Data pipeline docs
│   └── router/                 # Model selection docs
│
├── justask/                    # Core product
│   ├── api/                    # Backend API (Node.js/Express)
│   └── app/                    # Mobile app (React Native/Expo)
│
├── justask-dashboard/          # Analytics dashboard (React/Vite)
│
├── justask-registry/           # Data pipelines (Python)
│   ├── config/                 # Pipeline configurations
│   ├── outputs/                # Pipeline outputs (JSON)
│   ├── src/pipelines/          # Google, Groq, OpenRouter pipelines
│   └── tests/                  # Unit and integration tests
│
└── justask-router/             # Model selection service (Node.js)
    └── selector-service/       # 5-factor scoring algorithm
```

## Services

| Service | Directory | Tech Stack | Hosted On |
|---------|-----------|------------|-----------|
| API | `justask/api` | Node.js, Express | Render |
| Mobile App | `justask/app` | React Native, Expo | Expo Go |
| Dashboard | `justask-dashboard` | React, Vite | Vercel |
| Router | `justask-router/selector-service` | Node.js | Render |
| Registry | `justask-registry` | Python | GitHub Actions |

## Database

All services connect to a shared **Supabase** PostgreSQL database.
