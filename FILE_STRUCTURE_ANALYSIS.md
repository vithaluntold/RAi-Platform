# File Structure Analysis & Reorganization Plan

## 📊 CURRENT VS. OPTIMAL STRUCTURE

---

## BACKEND ANALYSIS

### 🔴 CURRENT BACKEND STRUCTURE

```
backend/
├── alembic/                    ✅ Good - DB migrations separated
├── app/
│   ├── api/
│   │   ├── deps.py            ✅ Dependencies (session, auth)
│   │   └── v1/
│   │       ├── api.py         ✅ Route aggregator
│   │       └── endpoints/     ✅ Feature endpoints (9 routers)
│   ├── core/
│   │   ├── config.py          ✅ Settings
│   │   ├── keycloak.py        ✅ AD auth
│   │   └── security.py        ✅ JWT, password hashing
│   ├── db/
│   │   ├── base.py            ✅ SQLAlchemy Base
│   │   └── session.py         ✅ Engine, session factory
│   ├── models/                ✅ 13 models mixed together
│   │   └── (13 files: user, workflow*, project*, assignment*)
│   ├── schemas/               ✅ Pydantic schemas (5 files)
│   ├── services/              ✅ Business logic (4 services)
│   └── main.py                ✅ FastAPI entry point
├── alembic.ini
├── command.txt
├── requirements.txt
└── .gitignore
```

### ❌ CURRENT ISSUES

1. **No `/utils` folder** - Utility functions scattered in services or endpoints
2. **No `/constants` folder** - Enums, mappings, defaults hardcoded
3. **No `/exceptions` folder** - Custom exceptions not centralized
4. **Models not grouped by domain** - 13 models in flat structure
5. **No `/middleware` folder** - CORS middleware in main.py
6. **Missing financial mappings** - No dictionary for financial statement synonyms
7. **Deps file is lonely** - Only one file in `/api` parent directory

### ✅ OPTIMAL BACKEND STRUCTURE

```
backend/
├── alembic/                    # Migrations (unchanged)
├── app/
│   ├── api/
│   │   ├── deps.py            # Dependency injection
│   │   ├── middleware.py       # Custom middleware (new)
│   │   └── v1/
│   │       ├── api.py         # Route aggregator
│   │       └── endpoints/     # Feature routers
│   ├── core/
│   │   ├── config.py          # Settings
│   │   ├── keycloak.py        # AD auth
│   │   ├── security.py        # JWT, hashing
│   │   └── exceptions.py       # Custom exceptions (new)
│   ├── db/
│   │   ├── base.py            # SQLAlchemy Base
│   │   └── session.py         # Engine, session
│   ├── models/                # Domain-grouped models (improved)
│   │   ├── __init__.py
│   │   ├── user.py            # User model
│   │   ├── workflow/          # Workflow domain (new)
│   │   │   ├── __init__.py
│   │   │   ├── workflow.py
│   │   │   ├── workflow_stage.py
│   │   │   ├── workflow_step.py
│   │   │   └── workflow_task.py
│   │   ├── project/           # Project domain (new)
│   │   │   ├── __init__.py
│   │   │   ├── project.py
│   │   │   ├── project_task.py
│   │   │   └── project_collaborator.py
│   │   └── assignment/        # Assignment domain (new)
│   │       ├── __init__.py
│   │       ├── workflow_assignment.py
│   │       ├── assignment_workflow_stage.py
│   │       ├── assignment_workflow_step.py
│   │       └── assignment_workflow_task.py
│   ├── schemas/               # Pydantic schemas (unchanged)
│   ├── services/              # Business logic (unchanged)
│   ├── constants/             # Enums, mappings (new)
│   │   ├── __init__.py
│   │   ├── user_enums.py      # UserRole, AuthProvider
│   │   ├── financial_mappings.py  # Financial statement synonyms
│   │   └── defaults.py        # Default values, constants
│   ├── utils/                 # Utility functions (new)
│   │   ├── __init__.py
│   │   ├── parsers.py         # Data parsing functions
│   │   ├── validators.py      # Custom validators
│   │   ├── financial_normalizer.py  # Financial name normalization
│   │   └── helpers.py         # Generic helpers
│   └── main.py                # FastAPI entry point
├── alembic.ini
├── command.txt
├── requirements.txt
└── .gitignore
```

### 🔑 BACKEND IMPROVEMENTS

| Item | Current | Optimal | Benefit |
|------|---------|---------|---------|
| Models organization | 13 flat files | 4 domains (user, workflow, project, assignment) | Better maintainability, clearer relationships |
| Constants | Scattered | `/constants` folder | Single source of truth |
| Exceptions | In endpoints | `/core/exceptions.py` | Reusable, consistent error handling |
| Utilities | In services | `/utils` folder | Separation of concerns |
| Financial mappings | None | `/constants/financial_mappings.py` | Financial statement synonyms |
| Middleware | In main.py | `/api/middleware.py` | Better organization |

---

## FRONTEND ANALYSIS

### 🔴 CURRENT FRONTEND STRUCTURE

```
frontend/
├── app/
│   ├── components/
│   │   └── Sidebar.tsx        ❌ Only 1 component, no subfolders
│   ├── dashboard/
│   │   ├── documents/         ✅ Feature page
│   │   ├── roles/             ✅ Feature page
│   │   ├── users/             ✅ Feature page
│   │   ├── workflow/          ✅ Feature page
│   │   ├── layout.tsx         ✅ Shared layout
│   │   └── page.tsx           ✅ Main dashboard
│   ├── globals.css            ✅ Global styles
│   ├── layout.tsx             ✅ Root layout
│   ├── page.tsx               ✅ Root page (login)
│   └── favicon.ico
├── public/
├── config files (eslint, tsconfig, next.config, etc.)
└── package.json
```

### ❌ CURRENT ISSUES

1. **No `/lib` folder** - Utility functions scattered or missing
2. **No `/types` folder** - TypeScript types/interfaces undefined
3. **No `/api` folder** - API calls scattered in components (violates separation)
4. **No `/hooks` folder** - Custom React hooks undefined
5. **No `/context` folder** - Context providers undefined
6. **Components not organized** - Only Sidebar.tsx, no feature-based subfolders
7. **No `/utils` folder** - Helper functions missing
8. **No constants/config** - API base URL, endpoints hardcoded

### ✅ OPTIMAL FRONTEND STRUCTURE

```
frontend/
├── app/
│   ├── api/                   # API client functions (new)
│   │   ├── __init__.ts
│   │   ├── client.ts          # Axios or fetch wrapper
│   │   ├── auth.ts            # Auth endpoints
│   │   ├── users.ts           # User endpoints
│   │   ├── workflows.ts       # Workflow endpoints
│   │   ├── documents.ts       # Document endpoints
│   │   ├── projects.ts        # Project endpoints
│   │   └── dashboard.ts       # Dashboard endpoints
│   ├── components/            # Shared components
│   │   ├── __init__.ts
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx         # If exists
│   │   ├── auth/              # Auth-related components
│   │   │   └── LoginForm.tsx
│   │   └── common/            # Reusable UI components
│   │       ├── Button.tsx
│   │       ├── Modal.tsx
│   │       └── ...
│   ├── context/               # React Context (new)
│   │   ├── __init__.ts
│   │   ├── AuthContext.tsx
│   │   └── UserContext.tsx
│   ├── dashboard/
│   │   ├── documents/
│   │   │   └── page.tsx
│   │   ├── roles/
│   │   │   └── page.tsx
│   │   ├── users/
│   │   │   └── page.tsx
│   │   ├── workflow/
│   │   │   └── page.tsx
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── hooks/                 # Custom hooks (new)
│   │   ├── __init__.ts
│   │   ├── useAuth.ts         # Auth hook
│   │   ├── useFetch.ts        # Data fetching hook
│   │   └── useLocalStorage.ts # LocalStorage hook
│   ├── lib/                   # Utility libraries (new)
│   │   ├── __init__.ts
│   │   ├── api-config.ts      # API base URL, endpoints
│   │   └── utils.ts           # Generic utilities
│   ├── types/                 # TypeScript types (new)
│   │   ├── __init__.ts
│   │   ├── auth.ts            # Auth-related types
│   │   ├── user.ts            # User types
│   │   ├── workflow.ts        # Workflow types
│   │   ├── document.ts        # Document types
│   │   ├── project.ts         # Project types
│   │   └── common.ts          # Common types
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
├── public/
├── eslint.config.mjs
├── next-env.d.ts
├── next.config.ts
├── package.json
├── postcss.config.mjs
├── README.md
└── tsconfig.json
```

### 🔑 FRONTEND IMPROVEMENTS

| Item | Current | Optimal | Benefit |
|------|---------|---------|---------|
| API calls | In components | `/api` folder | Centralized, testable |
| Types/Interfaces | None | `/types` folder | Type safety, documentation |
| Utilities | Scattered | `/lib` + `/utils` | Reusable, maintainable |
| Custom hooks | None | `/hooks` folder | Reusable logic |
| Global state | None | `/context` folder | State management |
| Components | No subdirs | Feature-based | Better organization |
| API config | Hardcoded | `/lib/api-config.ts` | Single source of truth |

---

## SUMMARY OF CHANGES

### Backend (13 changes)
1. ✅ Move models to domain folders (workflow/, project/, assignment/)
2. ✅ Create `/core/exceptions.py`
3. ✅ Create `/api/middleware.py`
4. ✅ Create `/constants/` with enums and mappings
5. ✅ Create `/utils/` with helpers and validators
6. ✅ Update all imports accordingly

### Frontend (12 changes)
1. ✅ Create `/api/` folder for API client functions
2. ✅ Create `/types/` folder for TypeScript interfaces
3. ✅ Create `/hooks/` folder for custom hooks
4. ✅ Create `/context/` folder for React Context
5. ✅ Create `/lib/` folder for utilities and config
6. ✅ Organize components by feature
7. ✅ Update all imports accordingly

---

## NEXT STEPS

1. Create new folders
2. Move files to appropriate locations
3. Update all import statements
4. Test that everything still works
5. Delete empty old directories

