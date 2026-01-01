# JustAsk Documentation Index

**Organized by topic for easy navigation.**

---

## Navigation

**Start here:** [README.md](../README.md)

**Then choose path:**
- [Getting Started](#getting-started) - New users
- [Development](#development) - Developers
- [Architecture](#architecture) - System design
- [API](#api) - Endpoint reference
- [Database](#database) - Data model
- [Testing](#testing) - Test guides
- [Deployment](#deployment) - Build & release
- [Operations](#operations) - Config & troubleshooting

---

## Getting Started
*User installation and quick start*

- [installation.md](./getting-started/installation.md) - Install APK, first run, features
- [quick-start.md](./getting-started/quick-start.md) - 30-min build checklist

---

## Development
*Setup, contribution, code style*

- [contributing.md](./development/contributing.md) - Setup, git workflow, PR checklist

---

## Architecture
*System design, data flows*

- [system-overview.md](./architecture/system-overview.md) - System layers, data flows, routing
- [app-how-it-works.md](./architecture/app-how-it-works.md) - Mobile app architecture and flow

---

## API
*Endpoint reference, examples*

- [endpoints.md](./api/endpoints.md) - Endpoints, request/response, examples

---

## Database
*Schema, tables, lifecycle*

- [schema.md](./database/schema.md) - Tables, columns, indexes, relations

---

## Testing
*Test guides for all phases*

- [e2e.md](./testing/e2e.md) - 15 E2E scenarios
- [stress.md](./testing/stress.md) - 10 stress tests
- [security.md](./testing/security.md) - 10 security tests
- [accessibility.md](./testing/accessibility.md) - 12 accessibility tests

---

## Deployment
*Backend & APK build, release*

- [backend.md](./deployment/backend.md) - Backend deployment to Render
- [apk-build.md](./deployment/apk-build.md) - Detailed build steps
- [apk-release.md](./deployment/apk-release.md) - GitHub release, version control

---

## Operations
*Configuration, troubleshooting*

- [configuration.md](./operations/configuration.md) - Environment variables, rates
- [troubleshooting.md](./operations/troubleshooting.md) - Installation, runtime, offline issues

---

## Quick References

| Task | Document |
|------|----------|
| Install app | [installation.md](./getting-started/installation.md) |
| Set up dev | [contributing.md](./development/contributing.md) |
| Understand system | [system-overview.md](./architecture/system-overview.md) |
| Call API | [endpoints.md](./api/endpoints.md) |
| View database | [schema.md](./database/schema.md) |
| Test app | [testing/](./testing/) |
| Deploy backend | [backend.md](./deployment/backend.md) |
| Build APK | [apk-build.md](./deployment/apk-build.md) |
| Configure | [configuration.md](./operations/configuration.md) |
| Fix issues | [troubleshooting.md](./operations/troubleshooting.md) |

---

## File Organization

```
justask/
├── README.md                             (project overview)
├── LICENSE                               (MIT license)
│
├── docs/                                 (all documentation)
│   ├── index.md                          (this file - navigation)
│   │
│   ├── getting-started/
│   │   ├── installation.md
│   │   └── quick-start.md
│   │
│   ├── development/
│   │   └── contributing.md
│   │
│   ├── architecture/
│   │   ├── system-overview.md
│   │   └── app-how-it-works.md
│   │
│   ├── api/
│   │   └── endpoints.md
│   │
│   ├── database/
│   │   └── schema.md
│   │
│   ├── testing/
│   │   ├── e2e.md
│   │   ├── stress.md
│   │   ├── security.md
│   │   └── accessibility.md
│   │
│   ├── deployment/
│   │   ├── backend.md
│   │   ├── apk-build.md
│   │   └── apk-release.md
│   │
│   └── operations/
│       ├── configuration.md
│       └── troubleshooting.md
│
├── app/                                  (React Native mobile app)
│   └── README.md
│
└── api/                                  (Node.js backend)
    └── README.md
```
