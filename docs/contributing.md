# Contributing

## Setup

```bash
# Backend
cd justask/api
npm install
export SUPABASE_URL=...
export SUPABASE_KEY=...
npm start

# Frontend
cd justask/app
npm install
expo start
```

## Code Style

- **Backend:** Node.js, express conventions
- **Frontend:** React/React Native patterns, Redux
- **Format:** Use existing code as reference
- **Comments:** Only for complex logic

## Testing

**Backend:**
```bash
cd justask/api
npm test
```

**Frontend:** See `e2e.md`, `stress.md`, `security.md`

## Git Workflow

1. Create branch: `git checkout -b feature/description`
2. Commit changes: `git commit -m "Brief description"`
3. Push: `git push origin feature/description`
4. Create PR with description

## PR Checklist

- [ ] Code tested
- [ ] No console errors/warnings
- [ ] Documentation updated
- [ ] No secrets committed

## Reporting Issues

GitHub Issues: https://github.com/vn6295337/justask/issues

Include:
- Reproduction steps
- Expected vs actual
- Environment (OS, version)
- Relevant code/logs

## Feature Requests

GitHub Discussions: https://github.com/vn6295337/justask/discussions

Describe:
- Use case
- Why needed
- Alternative approaches
