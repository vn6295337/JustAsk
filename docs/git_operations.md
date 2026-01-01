# Git Operations

## Repository

**Main repository:** https://github.com/vn6295337/justask.git

---

## Workflow

1. Clone `justask` repo
2. Make changes in appropriate subdirectory
3. Commit and push to `main`
4. Deployments happen automatically:
   - Dashboard → GitHub Pages
   - API/Router → Render.com
   - Registry pipelines → GitHub Actions

---

## Branch Strategy

- `main` - Production branch, auto-deploys
- Feature branches as needed

---

## Local Development

```bash
# Clone
git clone https://github.com/vn6295337/justask.git
cd justask

# Work on specific component
cd justask-dashboard  # Dashboard
cd justask/api        # Backend API
cd justask/app        # Mobile app
cd justask-router     # Model router
cd justask-registry   # Data pipelines
```
