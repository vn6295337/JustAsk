# JustAsk - Dependencies Documentation

**Last Updated**: 2025-12-30
**Purpose**: Consolidated dependency documentation across all JustAsk platform projects

---

## Project 1: justask (Client Package)

### API (Node.js Backend)
**Location**: `justask/api/package.json`

**Runtime Requirements:**
- Node.js: >=18.0.0
- npm: >=9.0.0

**Production Dependencies:**
```json
express: ^4.18.2          # Web framework
cors: ^2.8.5              # CORS middleware
express-rate-limit: ^7.1.5 # Rate limiting
axios: ^1.6.2             # HTTP client
dotenv: ^16.3.1           # Environment variables
helmet: ^7.1.0            # Security headers
compression: ^1.7.4        # Response compression
fs-extra: ^11.2.0         # File system utilities
jszip: ^3.10.1            # ZIP file handling
```

**Development Dependencies:**
```json
nodemon: ^3.0.2           # Auto-restart server
jest: ^29.7.0             # Testing framework
eslint: ^8.54.0           # Linting
supertest: ^6.3.3         # HTTP testing
```

### App (React Native Mobile)
**Location**: `justask/app/package.json`

**Runtime Requirements:**
- Node.js: >=18.0.0
- Expo SDK: 53+
- React Native: 0.76+

**Key Dependencies:**
- Expo framework and modules
- React Navigation
- Supabase client
- AsyncStorage for offline-first

---

## Project 2: justask-registry

### Python Pipeline
**Location**: `justask-registry/openrouter_pipeline/requirements.txt`

**Runtime Requirements:**
- Python: 3.11+
- pip: Latest version

**Core HTTP and Web Scraping:**
```
requests>=2.32.0          # HTTP library
httpx>=0.28.0             # Async HTTP client
beautifulsoup4>=4.13.0    # HTML parsing
lxml>=6.0.0               # XML/HTML parser
```

**Data Processing:**
```
pandas>=2.3.0             # Data manipulation
numpy>=2.3.0              # Numerical computing
```

**Database and API:**
```
supabase>=2.18.0          # Supabase client
psycopg2-binary>=2.9.9    # PostgreSQL adapter
huggingface-hub>=0.20.0   # HuggingFace API
```

**Configuration and Environment:**
```
python-dotenv>=1.1.0      # Environment variables
```

**Validation and Typing:**
```
pydantic>=2.11.0          # Data validation
typing-extensions>=4.15.0  # Type hints
```

**Date and Time:**
```
python-dateutil>=2.9.0    # Date utilities
pytz>=2025.2              # Timezone handling
```

**Security and Encoding:**
```
PyJWT>=2.10.0             # JWT tokens
certifi>=2025.8.0         # SSL certificates
charset-normalizer>=3.4.0  # Character encoding
```

**HTTP Core:**
```
httpcore>=1.0.0           # HTTP protocol
h11>=0.16.0               # HTTP/1.1 protocol
anyio>=4.10.0             # Async I/O
idna>=3.10                # Internationalized domain names
urllib3>=2.5.0            # HTTP library
```

**Utilities:**
```
six>=1.17.0               # Python 2/3 compatibility
packaging>=25.0           # Package version handling
soupsieve>=2.8            # CSS selector library
websockets>=15.0.0        # WebSocket support
```

**Installation:**
```bash
pip install -r requirements.txt
# OR from root:
pip install -r openrouter_pipeline/requirements.txt
```

---

## Project 3: justask-dashboard

### React Dashboard
**Location**: `justask-dashboard/package.json`

**Runtime Requirements:**
- Node.js: >=18.0.0 (recommended)
- npm: >=9.0.0

**Core Framework:**
```json
react: ^18.3.1            # React library
react-dom: ^18.3.1        # React DOM renderer
vite: ^5.4.1              # Build tool
typescript: ^5.5.3        # TypeScript
```

**UI Components (Radix UI + shadcn/ui):**
```json
@radix-ui/react-* (27 components)  # Headless UI primitives
class-variance-authority: ^0.7.1   # CSS variants
clsx: ^2.1.1                        # Conditional classes
tailwind-merge: ^2.5.2              # Tailwind utilities
lucide-react: ^0.462.0              # Icon library
```

**Charts and Visualization:**
```json
chart.js: ^4.5.0                    # Chart library
react-chartjs-2: ^5.3.0             # React wrapper for Chart.js
chartjs-adapter-date-fns: ^3.0.0    # Date adapter
recharts: ^2.12.7                   # Alternative charts
date-fns: ^3.6.0                    # Date utilities
```

**State Management and Data:**
```json
@tanstack/react-query: ^5.56.2      # Server state
@supabase/supabase-js: ^2.57.2      # Supabase client
react-hook-form: ^7.53.0            # Form handling
@hookform/resolvers: ^3.9.0         # Form validation
zod: ^3.23.8                        # Schema validation
```

**Routing and Navigation:**
```json
react-router-dom: ^6.26.2           # Client-side routing
```

**Styling:**
```json
tailwindcss: ^3.4.11                # CSS framework
autoprefixer: ^10.4.20              # CSS prefixing
postcss: ^8.4.47                    # CSS processing
tailwindcss-animate: ^1.0.7         # Tailwind animations
@tailwindcss/typography: ^0.5.15    # Typography plugin
next-themes: ^0.3.0                 # Theme management
```

**Utilities:**
```json
jszip: ^3.10.1                      # ZIP file handling
input-otp: ^1.2.4                   # OTP input
embla-carousel-react: ^8.3.0        # Carousel
cmdk: ^1.0.0                        # Command menu
sonner: ^1.5.0                      # Toast notifications
vaul: ^0.9.3                        # Drawer component
react-resizable-panels: ^2.1.3      # Resizable layouts
react-day-picker: ^8.10.1           # Date picker
```

**Analytics and Monitoring:**
```json
@vercel/analytics: ^1.5.0           # Vercel Analytics
```

**Development Tools:**
```json
@vitejs/plugin-react-swc: ^3.5.0    # Vite React plugin
eslint: ^9.9.0                      # Linting
typescript-eslint: ^8.0.1           # TypeScript ESLint
gh-pages: ^6.3.0                    # GitHub Pages deployment
lovable-tagger: ^1.1.7              # Code tagging
```

---

## Project 4: justask-router

### Selector Service (Node.js)
**Location**: `justask-router/selector-service/package.json`

**Runtime Requirements:**
- Node.js: >=18.0.0
- npm: >=9.0.0

**Key Dependencies:**
- Express.js web framework
- Supabase client for model data
- Rate limit calculation utilities

---

## External Services and APIs

### All Projects Use:

**Supabase (PostgreSQL)**
- Database: PostgreSQL via Supabase
- Authentication: Anon key for read-only access
- Row-level security (RLS) policies

**Environment Variables Required:**
```bash
# justask-registry
OPENROUTER_API_KEY=xxx
HUGGINGFACE_API_KEY=xxx
SUPABASE_URL=xxx
SUPABASE_KEY=xxx

# justask-dashboard
VITE_SUPABASE_URL=xxx
VITE_SUPABASE_ANON_KEY=xxx

# justask/api
GOOGLE_API_KEY=xxx
MISTRAL_API_KEY=xxx
LLAMA_API_KEY=xxx
```

### API Providers:

**AI Model Providers:**
- OpenRouter API
- Google Gemini API
- Mistral AI API
- Llama API
- Groq API
- Cohere API
- Together AI API
- HuggingFace Hub (metadata only)

---

## Dependency Summary

### Language Distribution:
- **JavaScript/TypeScript**: 3 projects (justask/api, justask-dashboard, justask-router)
- **Python**: 1 project (justask-registry)
- **React Native**: 1 project (justask/app)

### Package Managers:
- **npm**: justask/api, justask/app, justask-dashboard, justask-router
- **pip**: justask-registry

### Total Dependencies:
- **justask/api**: 12 dependencies + 4 devDependencies
- **justask-registry**: 45 Python packages
- **justask-dashboard**: 71 dependencies + 13 devDependencies
- **Total**: ~140+ packages across all projects

### Common Patterns:
- **Database**: All use Supabase/PostgreSQL
- **Environment Config**: All use dotenv pattern
- **HTTP Clients**: axios (Node), requests/httpx (Python)
- **Testing**: jest (Node)

---

## Security Considerations

### Dependency Security:
- All use specific version ranges (^) for minor updates
- Security-focused packages: helmet, express-rate-limit, PyJWT
- SSL certificate handling: certifi

### Best Practices:
- Environment variables for sensitive data
- .gitignore excludes .env files
- Rate limiting on backend
- CORS configuration
- Security headers (Helmet.js)

---

## Installation Quick Reference

### justask/api:
```bash
cd justask/api
npm install
```

### justask/app:
```bash
cd justask/app
npm install
npx expo start
```

### justask-registry:
```bash
cd justask-registry
python3 -m venv venv
source venv/bin/activate
pip install -r openrouter_pipeline/requirements.txt
```

### justask-dashboard:
```bash
cd justask-dashboard
npm install
```

### justask-router:
```bash
cd justask-router/selector-service
npm install
```

---

## Maintenance Notes

### Update Frequency:
- **Monthly**: Check for security updates
- **Quarterly**: Update minor versions
- **Annually**: Review major version upgrades

---

**Repository**: https://github.com/vn6295337/justask
