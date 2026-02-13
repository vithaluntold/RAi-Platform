# Cyloid Project - Quick Mental Maps & Checklists

## 🧠 MENTAL MAPS

### Map 1: Backend Request Handler Chain

```text
User submits form (Frontend)
│
├─ Request arrives: POST /api/v1/{endpoint}
│
├─ Route Handler (app/api/v1/endpoints/{feature}.py)
│  ├─ Validate input with Pydantic schema
│  ├─ Check JWT token (get_current_user dependency)
│  └─ Call service function
│
├─ Service Layer (app/services/{feature}_service.py)
│  ├─ Business logic (calculations, validations)
│  └─ Return result
│
├─ Database Query (via SQLAlchemy Session)
│  ├─ Query/Insert/Update User/other models
│  └─ Commit transaction
│
└─ Response returned to Frontend
```

### Map 2: Frontend Component Structure

```text
page.tsx (root or dashboard route)
│
├─ "use client" directive (client-side rendering)
├─ useState hooks (for form state, loading, errors)
├─ useRouter hook (for navigation)
├─ Event handlers (form submit, button clicks)
│
├─ JSX rendering
│  ├─ Tailwind classes for styling
│  ├─ Conditional rendering (loading states, errors)
│  └─ Form inputs with value/onChange bindings
│
└─ Fetch calls (async)
   ├─ POST to /api/v1/{endpoint}
   ├─ Store token in localStorage
   └─ Navigate on success
```

### Map 3: Authentication State Flow

```text
┌─────────────────────┐
│  User Unauthenticated
│  (page.tsx shows login form)
│  localStorage.access_token = null
└──────────┬──────────┘
           │
           │ User enters email + password, clicks "Sign In"
           │
           ↓
┌─────────────────────┐
│  POST /api/v1/auth/login
│  Backend validates credentials
│  Returns JWT token
└──────────┬──────────┘
           │
           │ Token received
           │
           ↓
┌─────────────────────┐
│  User Authenticated
│  localStorage.access_token = "jwt-xxx..."
│  Router.push(/dashboard)
└──────────┬──────────┘
           │
           │ Frontend now attaches token to all API calls
           │ Authorization: Bearer {token}
           │
           ↓
┌─────────────────────┐
│  Backend validates token
│  If valid → proceed
│  If invalid/expired → 401 Unauthorized
└─────────────────────┘
```

### Map 4: User Onboarding (Bulk Creation)

```text
Admin uploads CSV/JSON with user data
│
├─ Field mapping:
│  ├─ email (required, unique)
│  ├─ full_name (parsed into first_name + last_name)
│  ├─ password (optional, defaults to "Welcome123!")
│  └─ role (defaults to "worker")
│
├─ POST /api/v1/users (with list)
│
├─ Service: user_service.onboard_multiple_users()
│  ├─ For each user:
│  │  ├─ Check if email exists
│  │  │  ├─ If yes → add to errors[], skip
│  │  │  └─ If no → create User object
│  │  ├─ Hash password with get_password_hash()
│  │  ├─ Set auth_provider = LOCAL (default)
│  │  └─ Add to session
│  └─ Commit all at once
│
└─ Response: { created: [...emails], errors: [...] }
```

### Map 5: AD/Keycloak Integration

```text
User clicks "Sign in with AD"
│
├─ Frontend redirects to Keycloak
│
├─ User enters AD credentials in Keycloak UI
│
├─ Keycloak redirects back to:
│  POST /api/v1/ad-auth/callback?code=...&state=...
│
├─ Backend:
│  ├─ Exchange code for Keycloak token
│  ├─ Extract keycloak_sub, ad_username, email
│  ├─ Check if user exists in DB
│  │  ├─ If yes → update user (ad_username, keycloak_sub)
│  │  └─ If no → create new user (auth_provider = KEYCLOAK_AD)
│  └─ Generate JWT token
│
└─ Frontend stores JWT, navigates to dashboard
```

---

## ✅ COMMON WORKFLOWS

### 🔧 Adding a New Feature (Full Stack)

**Steps:**

1. **Database Layer**
   - [ ] Add fields to `app/models/user.py` (or create new model)
   - [ ] Create Alembic migration
   - [ ] Test migration locally

2. **Backend API**
   - [ ] Create schema in `app/schemas/{feature}.py`
   - [ ] Create service in `app/services/{feature}_service.py`
   - [ ] Create endpoint in `app/api/v1/endpoints/{feature}.py`
   - [ ] Register router in `app/api/v1/api.py`
   - [ ] Test with curl/Postman

3. **Frontend**
   - [ ] Create page at `app/dashboard/{feature}/page.tsx`
   - [ ] Design UI with Tailwind + React components
   - [ ] Write fetch call to backend endpoint
   - [ ] Add error handling + loading states
   - [ ] Test in browser

### 🐛 Debugging a Backend Issue

**Checklist:**

1. [ ] Check if request reaches the backend (turn on logs)
2. [ ] Validate request body with Pydantic schema
3. [ ] Check JWT token validity
4. [ ] Verify database connection
5. [ ] Check SQL query in logs
6. [ ] Inspect database state directly
7. [ ] Review Alembic migration status

### 🎨 Styling a Frontend Component

**Tailwind Usage Pattern:**

```tsx
// Layout: flex, grid, w-[...], h-[...]
<div className="flex min-h-screen lg:w-120">

// Colors: bg-sidebar-bg, text-accent
<div className="bg-sidebar-bg text-white">

// Effects: opacity, blur, rounded
<div className="absolute opacity-[0.03] blur-[100px] rounded-full">

// Responsive: hidden lg:flex, sm:w-[...]
<div className="hidden lg:flex">
```

### 🔑 Adding New Auth Fields

#### Example: Add phone_number to User

1. **Model** (`app/models/user.py`):

   ```python
   phone_number = Column(String(20), nullable=True)
   ```

2. **Migration** (`alembic/versions/{timestamp}...py`):

   ```python
   op.add_column('users', 
       sa.Column('phone_number', sa.String(20), nullable=True)
   )
   ```

3. **Schema** (`app/schemas/user.py`):

   ```python
   class UserCreate(BaseModel):
       phone_number: str | None = None
   ```

4. **Endpoint** (`app/api/v1/endpoints/users.py`):

   ```python
   @router.post("/")
   def create_user(user: UserCreate, db: Session = Depends(get_db)):
       new_user = User(
           ...
           phone_number=user.phone_number,
       )
   ```

---

## 📍 FILE LOCATIONS BY PURPOSE

### If I need to

**Handle a user login:**

- Frontend: `frontend/app/page.tsx`
- Backend: `backend/app/api/v1/endpoints/auth.py`
- Service: `backend/app/services/user_service.py`
- Security: `backend/app/core/security.py`

**Create/update user:**

- Schema: `backend/app/schemas/user.py`
- Model: `backend/app/models/user.py`
- Endpoint: `backend/app/api/v1/endpoints/users.py`
- Service: `backend/app/services/user_service.py`

**Change database schema:**

- Model changes: `backend/app/models/user.py`
- Migration: `backend/alembic/versions/` (generate with alembic)
- Config: `backend/alembic.ini`

**Add new page to dashboard:**

- Page: `frontend/app/dashboard/{feature}/page.tsx`
- Layout: `frontend/app/dashboard/layout.tsx` (if shared)
- Components: `frontend/app/components/` (reusable parts)
- Sidebar: `frontend/app/components/Sidebar.tsx` (add link)

**Modify authentication:**

- Local JWT: `backend/app/core/security.py` + `auth.py` endpoint
- Keycloak/AD: `backend/app/core/keycloak.py` + `ad_auth.py` endpoint

**Change API settings:**

- Config: `backend/app/core/config.py`
- Env file: `backend/.env`

**Add new API route:**

- Endpoint handler: `backend/app/api/v1/endpoints/{feature}.py`
- Router registration: `backend/app/api/v1/api.py`
- Request/response schemas: `backend/app/schemas/{feature}.py`

---

## 🚨 IMPORTANT GOTCHAS

### Frontend

- ❌ Don't forget `"use client"` directive in interactive pages
- ❌ localStorage is browser-only, won't work on server
- ❌ Always check `access_token` before making authenticated requests
- ✅ Use `useRouter` from `next/navigation` (not next/router)

### Backend

- ❌ Don't hardcode passwords in code
- ❌ Password must be hashed before saving to DB
- ✅ Always use SQLAlchemy Session for DB operations
- ✅ Validate input with Pydantic schemas
- ❌ Don't commit DB changes manually; let FastAPI dependency inject session

### Database

- ❌ Never manually edit `__pycache__` or migration files
- ✅ Always create migrations with Alembic, then run `upgrade head`
- ❌ Don't delete columns without creating a migration first
- ✅ Keep migration files in `alembic/versions/`

### Auth

- ❌ Don't store tokens in plain text on backend
- ✅ Token should be JWT with expiration
- ❌ Don't allow CORS for all origins in production
- ✅ Auth header format: `Authorization: Bearer {token}`

---

## 🧪 TESTING QUICK REFERENCE

### Test Local Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

### Test User Creation

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '[{"email": "newuser@example.com", "full_name": "John Doe"}]'
```

### Check Database

```bash
psql -U postgres -d cyloid -c "SELECT * FROM users;"
```

### Run Frontend Dev Server

```bash
cd frontend && npm run dev
# Navigate to http://localhost:3000
```

### Run Backend Dev Server

```bash
cd backend && uvicorn app.main:app --reload
# API on http://localhost:8000
# Docs on http://localhost:8000/docs
```

---

## 🎯 QUICK DECISION TREE

```text
"I need to modify the system, where do I start?"

├─ Is it UI/form related?
│  └─ Edit frontend/app/...
│
├─ Is it database schema related?
│  ├─ Modify app/models/user.py
│  └─ Create Alembic migration
│
├─ Is it API endpoint related?
│  ├─ Create/edit app/api/v1/endpoints/...
│  └─ Add schema in app/schemas/...
│
├─ Is it business logic related?
│  └─ Create/edit app/services/...
│
├─ Is it authentication related?
│  ├─ For local JWT: app/core/security.py
│  └─ For Keycloak/AD: app/core/keycloak.py
│
└─ Is it configuration related?
   └─ Edit app/core/config.py or .env
```

---

## 📊 STATE OF PROJECT

**✅ Implemented:**

- User model with UUID, roles, AD fields
- Local JWT authentication (basic)
- Keycloak/AD integration structure
- Bulk user onboarding
- Database migrations
- CORS setup
- Dummy frontend login

**🚧 In Progress:**

- AD authentication flows
- Keycloak callback handling
- Frontend dashboard pages
- Document management
- Workflow management

**❌ TODO:**

- Real API calls from frontend
- Error handling refinement
- Role-based access control
- Rate limiting
- Refresh token strategy
- Email notifications
- Audit logging

---

**Version:** 1.0  
**Created:** Feb 12, 2026
