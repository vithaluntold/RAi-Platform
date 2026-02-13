# Cyloid Project Architecture & Reference Guide

## 🎯 Project Overview

**Name:** Cyloid (RAI App - Robust AI)  
**Type:** Full-stack web application for financial/document workflow management
**Frontend:** Next.js 16 (React 19) with TypeScript + TailwindCSS  
**Backend:** FastAPI (Python) with SQLAlchemy ORM, PostgreSQL database  
**Auth:** Dual authentication - Local (JWT) + Keycloak/Active Directory (AD)

---

## 📁 HIGH-LEVEL STRUCTURE

```plaintext
Cyloid-Project/
├── backend/          ← FastAPI REST API
└── frontend/         ← Next.js React app
```

---

## 🔙 Backend Architecture

## Backend Location & Purpose

`/backend` - FastAPI REST server handling authentication, user management,
documents, workflows, dashboards

## Backend Core Tech Stack

- **Framework:** FastAPI (async Python web framework)
- **Database:** PostgreSQL + SQLAlchemy ORM
- **Auth:** JWT (local) + Keycloak/AD integration
- **Migrations:** Alembic for database versioning
- **Server:** Uvicorn ASGI server

## Backend Directory Breakdown

### 1. **app/main.py** - Application Entry Point

- FastAPI app initialization
- CORS middleware setup
- Database table creation (development only)
- Router registration at `/api/v1`

### 2. **app/core/** - Configuration & Security

**Files:**

- `config.py` - Environment settings (BaseSettings from pydantic-settings)
  - Database URL, JWT secret, Keycloak credentials, CORS origins
  - Settings loaded from `.env` file
- `security.py` - Password hashing, JWT token generation/validation
- `keycloak.py` - Keycloak/AD client integration

### 3. **app/db/** - Database Layer

**Files:**

- `session.py` - SQLAlchemy engine, session management, Base declarative
- `base.py` - Database base class

**Key Pattern:** SQLAlchemy declarative base → all models inherit from Base

### 4. **app/models/** - Database Models

**User Model** (`user.py`):

```python
├── id (UUID, primary key)
├── first_name, last_name (String)
├── email (String, unique, indexed)
├── hashed_password (nullable for AD users)
├── role (Enum: ADMIN, WORKER, CLIENT)
├── is_active (Boolean)
├── auth_provider (Enum: LOCAL or KEYCLOAK_AD)
├── ad_username (Keycloak AD username, unique/indexed)
├── keycloak_sub (Keycloak subject ID, unique/indexed)
├── created_at, updated_at (DateTime audit trail)
```

**Enums:**

- `UserRole`: ADMIN, WORKER, CLIENT
- `AuthProvider`: LOCAL, KEYCLOAK_AD

### 5. **app/schemas/** - Request/Response Validation (Pydantic)

**Purpose:** Define expected data structures for API endpoints

**Files:**

- `token.py` - Token response schemas
- `user.py` - User request/response schemas (includes UserOnboard)
- `ad_auth.py` - AD authentication schemas

### 6. **app/services/** - Business Logic Layer

**Pattern:** Pure business logic, no FastAPI dependencies

**Files:**

- `user_service.py` - `onboard_multiple_users()` - bulk user creation with validation
- `ad_auth_service.py` - Keycloak/AD user sync & verification

### 7. **app/api/v1/** - REST Endpoint Routing

**api.py** - Route aggregator:

```python
/api/v1/
├── auth.py       → POST /login, /logout, /refresh
├── ad_auth.py    → POST /ad-login, /ad-callback
├── users.py      → GET/POST /users/{id}, DELETE, etc.
├── documents.py  → GET/POST /documents, file handling
├── workflows.py  → GET/POST /workflows, task management
└── dashboard.py  → GET /dashboard/analytics, /insights
```

### 8. **Database Migrations** (Alembic)

**Location:** `alembic/versions/`

**Existing Migrations:**

1. `8a4cd8dd6f72_initial_tables.py` - Initial schema
2. `86c3eb25451f_add_keycloak_ad_fields_to_users.py` - AD fields
  (ad_username, keycloak_sub, auth_provider)

**Key Config:** `alembic.ini` defines revision strategy

### 9. **Dependencies**

**requirements.txt** - Key packages:

- `fastapi` - Web framework
- `sqlalchemy` - ORM
- `psycopg2-binary` - PostgreSQL driver
- `pydantic` & `pydantic-settings` - Data validation
- `python-jose` & `bcrypt` - JWT & password hashing
- `python-keycloak` - Keycloak client
- `uvicorn` - ASGI server
- `alembic` - Database migrations
- `python-dotenv` - Environment variables

---

## 🎨 Frontend Architecture

### Frontend Location & Purpose

`/frontend` - Next.js 16 single-page application with React 19 components and
TailwindCSS styling

### Frontend Tech Stack

- **Framework:** Next.js 16 (App Router)
- **UI:** React 19 (component-based)
- **Styling:** TailwindCSS 4 + PostCSS
- **Language:** TypeScript 5
- **Build Tool:** ESLint for code quality

### Frontend Directory Breakdown

#### 1. **Root Configuration Files**

- `next.config.ts` - Next.js build settings
- `tsconfig.json` - TypeScript configuration
- `postcss.config.mjs` - PostCSS (TailwindCSS plugin)
- `eslint.config.mjs` - Code linting rules
- `package.json` - Dependencies & scripts

**Scripts:**

- `npm run dev` - Start dev server (hot reload)
- `npm run build` - Production build
- `npm run start` - Start prod server
- `npm run lint` - Run ESLint

#### 2. **app/ Directory** - App Router Structure

**Root Layout** (`app/layout.tsx`):

- Global HTML structure
- Imports `globals.css` (Tailwind directives)
- Renders all child pages

**Root Page** (`app/page.tsx`) - **LOGIN PAGE**:

- `"use client"` directive (client component)
- Email/password form with "Show password" toggle
- Currently uses **dummy login** (accepts any credentials)
- Sets `localStorage.access_token` = "dummy-token"
- Redirects to `/dashboard` on submit
- Left panel with RAI branding + geometric pattern

#### 3. **app/dashboard/** - Protected Dashboard Area

**Layout** (`dashboard/layout.tsx`):

- Shared dashboard structure (inherited by all dashboard pages)
- Contains `<Sidebar />` component for navigation

**Route Structure:**

```plaintext
/dashboard
├── page.tsx              → Dashboard home/overview
├── documents/
│   └── page.tsx         → Document management
├── roles/
│   └── page.tsx         → Role management
├── users/
│   └── page.tsx         → User management
└── workflow/
    └── page.tsx         → Workflow management
```

#### 4. **app/components/** - Reusable UI Components

**Files:**

- `Sidebar.tsx` - Navigation sidebar (used in dashboard layout)

#### 5. **public/** - Static Assets

- `favicon.ico` - Website icon

#### 6. **Styling**

**Tailwind CSS Classes Used:**

- Color tokens: `bg-sidebar-bg`, `text-accent`
- Layout: `flex`, `min-h-screen`, `w-[480px]`
- Effects: `blur-[100px]`, `opacity-[0.03]`

---

## 🔄 API Flow

### Authentication Flow (Local)

```plaintext
Frontend LoginPage
  ↓ (POST) email + password
Backend /api/v1/auth
  ↓ validate credentials
Backend /api/v1/auth/login
  ↓ return JWT token
Frontend localStorage.access_token = token
  ↓
Frontend router.push(/dashboard)
```

### Authentication Flow (Keycloak/AD)

```plaintext
Frontend → BackendAD /api/v1/ad-login
  ↓
Keycloak redirect (browser)
  ↓
Backend /api/v1/ad-auth/callback
  ↓ sync user to DB
Frontend access_token stored
```

## 🗄️ Database Schema (Production)

**Primary Table:** `users`

```sql
id (UUID)
first_name, last_name (VARCHAR)
email (VARCHAR, UNIQUE)
hashed_password (VARCHAR, NULLABLE)
role (ENUM)
is_active (BOOLEAN)
auth_provider (ENUM)
ad_username (VARCHAR, UNIQUE, NULLABLE)
keycloak_sub (VARCHAR, UNIQUE, NULLABLE)
created_at, updated_at (DATETIME)
```

**Indexes:**

- email (fast lookups)
- ad_username (Keycloak sync)
- keycloak_sub (Keycloak mapping)

---

## 🌐 API Endpoints (v1)

| Method | Endpoint | Purpose | Auth |
| ------ | -------- | ------- | ---- |
| POST | `/auth/login` | Local login | None |
| POST | `/ad-login` | Keycloak login | None |
| POST | `/ad-auth/callback` | Keycloak callback | Token |
| GET | `/users/{id}` | Get user by ID | Token |
| POST | `/users` | Create user | Token |
| GET | `/documents` | List documents | Token |
| POST | `/documents` | Upload document | Token |
| GET | `/workflows` | List workflows | Token |
| POST | `/workflows` | Create workflow | Token |
| GET | `/dashboard/analytics` | Dashboard analytics | Token |

---

## 📊 Data Flow Diagrams

### User Onboarding (Backend)

```plaintext
CSV/JSON input
  ↓
/api/v1/users (POST)
  ↓
user_service.onboard_multiple_users()
  ├─ Check email uniqueness
  ├─ Parse full_name → first_name + last_name
  ├─ Hash password (or default "Welcome123!")
  ├─ Create User model
  └─ Commit to DB
  ↓
Response: { created: [], errors: [] }
```

### AD Sync Flow

```plaintext
Keycloak /ad-auth/callback
  ↓
ad_auth_service.sync_or_create_ad_user()
  ├─ Extract keycloak_sub, ad_username
  ├─ Upsert user in DB
  └─ Return user + JWT token
  ↓
Frontend stores token
```

---

## ⚙️ Environment Configuration

**Location:** `.env` (loaded by `core/config.py`)

**Required Variables:**

```bash
PROJECT_NAME=Cyloid-RAI
SECRET_KEY=<jwt-secret>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL=postgresql://user:pass@localhost/cyloid
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
KEYCLOAK_ENABLED=true
KEYCLOAK_SERVER_URL=https://keycloak.example.com
KEYCLOAK_REALM=cyloid
KEYCLOAK_CLIENT_ID=cyloid-backend
KEYCLOAK_CLIENT_SECRET=<secret>
KEYCLOAK_AD_DEFAULT_ROLE=worker
```

---

## 🚀 Common Tasks Reference

### Add New Backend Endpoint

1. Create function in `app/api/v1/endpoints/{feature}.py`
2. Define request/response Pydantic schemas in `app/schemas/{feature}.py`
3. Add business logic to `app/services/{feature}_service.py` (if complex)
4. Include router in `app/api/v1/api.py`

### Add New Frontend Page

1. Create directory under `app/dashboard/{feature}/`
2. Add `page.tsx` with `"use client"` (if interactive)
3. Import at top level in `dashboard/layout.tsx` if needed
4. Update `Sidebar.tsx` navigation

### Add New Database Field

1. Add column to `app/models/user.py`
2. Create Alembic migration: `alembic revision --autogenerate -m "description"`
3. Review generated migration in `alembic/versions/`
4. Run: `alembic upgrade head`

### Bulk User Creation

- Use `/api/v1/users` (POST) with CSV/JSON
- Backend handles duplicates gracefully, returns errors
- Passwords auto-set to "Welcome123!" if not provided

---

## 🔐 Security Practices

**✅ IMPLEMENTED:**

- UUID primary keys (prevents ID enumeration)
- Bcrypt password hashing
- JWT token-based auth
- Keycloak/AD integration for enterprise SSO
- CORS middleware (whitelisting origins)
- Audit trail (created_at, updated_at)
- Nullable passwords for AD users (no local password stored)

**❌ TODO:**

- Rate limiting on auth endpoints
- Refresh token rotation
- HTTPS enforcement (for production)
- Audit logging for sensitive operations

---

## 📦 Running the Project

### Backend

```bash
cd backend
pip install -r requirements.txt
export DATABASE_URL=postgresql://...
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Database

- PostgreSQL must be running on the configured DATABASE_URL
- Alembic migrations handle schema management

---

## 🎯 Key Mental Model

**Separation of Concerns:**

- **Frontend:** UI, routing, forms, localStorage token storage
- **Backend:** Auth logic, DB operations, API validation, Keycloak integration
- **Database:** Schema via SQLAlchemy models, migrations via Alembic

**Request Path:**

```plaintext
Frontend (React component) 
  → Fetch to /api/v1/{endpoint}
  → Backend route handler
  → Service layer (business logic)
  → Database layer (SQLAlchemy)
  → Response back to Frontend
```

**Authentication State:**

### Request/Response Pattern

- Frontend: Reads `localStorage.access_token` to attach to request headers
- Backend: Validates token using JWT secret from config
- Both: Dual-auth system (local JWT OR Keycloak/AD)

---

## 👥 Assignments Module (Advanced)

### Overview

Assignments enable distribution of workflow templates to clients with state
tracking and history. Key features:

- Template-based workflow assignments to clients
- Deep cloning of workflow stages/steps/tasks for customization
- Multi-level status tracking (assignment → stage → step → task)
- Progress monitoring and completion metrics
- Timeline management (start date, due date, completion date)

## Core Architecture

### Projects Database Tables

#### 1. **workflowAssignments** (Template Assignment)

**Key fields:**

- id (UUID, PK)
- workflow_id (FK → workflows)
- client_id (UUID)
- organization_id (UUID)
- status (draft, active, in_progress, completed, on_hold, cancelled)
- assigned_by (FK → users)
- notes (String)
- due_date, start_date (DateTime)
- priority (low, medium, high, urgent)
- metadata (JSON)
- created_at, updated_at (DateTime)

#### 2. **assignmentWorkflowStages** (Cloned Workflow Stages)

**Key fields:**

- id (UUID, PK)
- assignment_id (FK → workflow_assignments)
- template_stage_id (FK → workflow_stages)
- name, description (String)
- order (Integer)
- status (not_started, in_progress, completed)
- start_date, completed_date (DateTime)
- assigned_to (UUID)
- metadata (JSON)
- created_at, updated_at (DateTime)

#### 3. **assignmentWorkflowSteps** (Cloned Workflow Steps)

**Key fields:**

- id (UUID, PK)
- stage_id (FK → assignment_workflow_stages)
- template_step_id (FK → workflow_steps)
- name, description (String)
- order (Integer)
- status (not_started, in_progress, completed)
- assigned_to (UUID)
- due_date, completed_date (DateTime)
- metadata (JSON)
- created_at, updated_at (DateTime)

#### 4. **assignmentWorkflowTasks** (Cloned Workflow Tasks)

**Key fields:**

- id (UUID, PK)
- step_id (FK → assignment_workflow_steps)
- template_task_id (FK → workflow_tasks)
- name, description (String)
- order (Integer)
- status (not_started, in_progress, completed, blocked)
- assigned_to (UUID)
- due_date, completed_date (DateTime)
- estimated_hours, actual_hours (Numeric)
- metadata (JSON)
- created_at, updated_at (DateTime)

## API Endpoints

### List Assignments

```text
GET /api/v1/assignments?organizationId={id}
  &clientId={id}&status={status}&page={n}

Response:
{
  "data": [
    {
      "id": "uuid",
      "workflowName": "Quarterly Closing",
      "clientName": "Acme Corp",
      "status": "active",
      "priority": "high",
      "dueDate": "2026-03-31",
      "progress": 45
    }
  ],
  "pagination": { "total": 42, "page": 1, "limit": 20 }
}
```

**FastAPI Implementation:**

- File: `backend/app/api/v1/endpoints/assignments.py`
- Uses query params for org/client/status and paginates results

### Create Assignment

```text
POST /api/v1/assignments

Body:
{
  "workflowId": "uuid",
  "clientId": "uuid",
  "organizationId": "uuid",
  "priority": "medium|high|low|urgent",
  "dueDate": "2026-03-31",
  "startDate": "2026-02-15",
  "notes": "Special handling required"
}

Response: { "id": "uuid", "status": "draft" }
```

**FastAPI Implementation:**

- File: `backend/app/api/v1/endpoints/assignments.py`
- Validates org membership and creates a draft assignment

### Get Assignment with Full Hierarchy

```text
GET /api/v1/assignments/{id}

Response:
{
  "id": "uuid",
  "status": "active",
  "stages": [
    {
      "id": "uuid",
      "name": "Stage 1",
      "status": "in_progress",
      "progress": 50,
      "steps": [
        {
          "id": "uuid",
          "name": "Step 1",
          "tasks": [
            {
              "id": "uuid",
              "name": "Task 1",
              "status": "completed",
              "assignedTo": "uuid"
            }
          ]
        }
      ]
    }
  ]
}
```

**FastAPI Implementation:**

- File: `backend/app/api/v1/endpoints/assignments.py`
- Loads assignment and expands stages → steps → tasks

### Update Assignment Status

```text
PATCH /api/v1/assignments/{id}

Body:
{
  "status": "active|in_progress|completed|on_hold|cancelled",
  "priority": "low|medium|high|urgent"
}

When status changes to "active":
  → Triggers workflow cloning:
   1. Clone all stages → assignmentWorkflowStages
   2. Clone all steps → assignmentWorkflowSteps
   3. Clone all tasks → assignmentWorkflowTasks
```

**FastAPI Implementation:**

- File: `backend/app/api/v1/endpoints/assignments.py`
- Updates status and triggers clone on activation

### Update Assignment Task

```text
PATCH /api/v1/assignments/{assignmentId}/tasks/{taskId}

Body:
{
  "status": "not_started|in_progress|completed|blocked",
  "assignedTo": "uuid",
  "actualHours": 5.5
}
```

**FastAPI Implementation:**

- File: `backend/app/api/v1/endpoints/assignments.py`
- Updates task status, assignee, and actual hours

## Status Flow Diagram

```text
draft ──activate──> active ──start work──> in_progress ──complete──> completed
 │                   │                          │                        │
 └─────────────────pause─────────────────────on_hold◄────────────────────┘
                     │                          │
                     └──────────cancel──────────┘
```

## Key Operations

### Workflow Cloning (on assignment activation)

```text
Pseudo-code
async def activateAssignment(assignmentId):
    assignment = get_assignment(assignmentId)
    workflow = get_workflow(assignment.workflowId)
    
    # Clone all stages
    for stage in workflow.stages ordered by order:
        cloned_stage = insert assignmentWorkflowStages {
            assignmentId: assignmentId,
            templateStageId: stage.id,
            name: stage.name,
            order: stage.order,
            status: 'not_started'
        }
        
        # Clone all steps in stage
        for step in stage.steps ordered by order:
            cloned_step = insert assignmentWorkflowSteps {
                stageId: cloned_stage.id,
                templateStepId: step.id,
                name: step.name,
                order: step.order,
                status: 'not_started'
            }
            
            # Clone all tasks in step
            for task in step.tasks ordered by order:
                insert assignmentWorkflowTasks {
                    stepId: cloned_step.id,
                    templateTaskId: task.id,
                    name: task.name,
                    order: task.order,
                    status: 'not_started'
                }
    
    # Mark assignment as active
    update workflowAssignments set status = 'active'
```

## Frontend Components

### AssignmentList Component

- Display all assignments with filters (status, priority, client)
- Show progress bar for each assignment
- Status badges with color coding
- Quick actions (view details, edit, cancel)

### AssignmentDetail Component

- Hierarchical view: Stages → Steps → Tasks
- Drag-drop task reordering
- Inline status updates
- Time tracking display (estimated vs actual hours)
- Completion percentage calculation

### Assignment Card Display

```text
┌────────────────────────────────────┐
│ Quarterly Closing                 │
│ Client: Acme Corp                 │ [ACTIVE]
├────────────────────────────────────┤
│ Priority: HIGH | Due: 2026-03-31  │
│ Progress: ████████░░ 45%          │
│ Stages: 3 | Steps: 8 | Tasks: 24  │
└────────────────────────────────────┘
```

---

## 🎯 Projects Module (Kanban-Based)

### Projects Overview

Projects serve as containers for task management using a Kanban board paradigm.
Key features:

- Kanban board with drag-and-drop task management
- Multiple collaborators with role-based permissions
- Visual status columns (To Do, In Progress, Review, Completed)
- Task prioritization and time tracking
- Resource and output folder organization

## Projects Core Architecture

### Database Tables

#### 1. **projects** (Kanban Board Container)

**Key fields:**

- id (UUID, PK)
- organization_id (UUID)
- name, description (String)
- client_id (UUID)
- status (planning, active, review, completed, archived)
- priority (low, medium, high, urgent)
- owner_id (UUID)
- manager_ids (UUID[])
- resource_folder_id, output_folder_id (UUID)
- start_date, due_date (DateTime)
- visibility (private, team, organization)
- metadata (JSON)
- created_at, updated_at (DateTime)

#### 2. **projectTasks** (Kanban Cards)

**Key fields:**

- id (UUID, PK)
- project_id (FK → projects)
- title, description (String)
- status (todo, in_progress, review, completed)
- priority (low, medium, high, urgent)
- assignee_id (UUID)
- due_date (DateTime)
- position (Integer)
- estimated_hours, actual_hours (Numeric)
- resource_folder_id, output_folder_id (UUID)
- metadata (JSON)
- created_at, updated_at (DateTime)

#### 3. **projectCollaborators** (Multi-User Assignment)

**Key fields:**

- id (UUID, PK)
- project_id (FK → projects)
- user_id (FK → users)
- role (owner, editor, viewer, commenter)
- created_at, updated_at (DateTime)

## Projects API Endpoints

### List Projects

```text
GET /api/projects?organizationId={id}
  &status={status}&ownerId={id}&page={n}

Response:
{
  "data": [
    {
      "id": "uuid",
      "name": "Q1 2026 Planning",
      "status": "active",
      "priority": "high",
      "owner": { "id": "uuid", "name": "Jane Doe" },
      "taskCount": 24,
      "completedCount": 12,
      "dueDate": "2026-03-31"
    }
  ],
  "pagination": { ... }
}
```

### Create Project

```text
POST /api/projects

Body:
{
  "organizationId": "uuid",
  "name": "Q1 Planning",
  "description": "...",
  "clientId": "uuid",
  "ownerId": "uuid",
  "managerIds": ["uuid", "uuid"],
  "priority": "high",
  "dueDate": "2026-03-31",
  "visibility": "team"
}

Response: { "id": "uuid", "status": "planning" }
```

### Get Project with Kanban Columns

```text
GET /api/projects/{id}/kanban

Response:
{
  "project": { "id": "uuid", "name": "Q1 Planning" },
  "columns": {
    "todo": [
      { "id": "uuid", "title": "Design mockups", "priority": "high" }
    ],
    "in_progress": [...],
    "review": [...],
    "completed": [...]
  },
  "stats": {
    "total": 24,
    "completed": 12,
    "inProgress": 8,
    "pending": 4
  }
}
```

### Create Task

```text
POST /api/projects/{projectId}/tasks

Body:
{
  "title": "Task title",
  "description": "...",
  "priority": "high",
  "assigneeId": "uuid",
  "dueDate": "2026-02-28",
  "estimatedHours": 8
}

Response: { "id": "uuid", "status": "todo", "position": 0 }
```

### Move Task (Kanban Drag)

```text
PATCH /api/projects/tasks/{taskId}/move

Body:
{
  "status": "in_progress|review|completed",
  "position": 2
}

Behavior:
  - Moves task to new column
  - Re-positions tasks in destination column
  - Updates database atomically
```

## Kanban Board Visual Layout

```text
┌─────────────┬──────────────┬────────────┬────────────┐
│   TO DO     │ IN PROGRESS  │   REVIEW   │ COMPLETED  │
├─────────────┼──────────────┼────────────┼────────────┤
│ ┌─────────┐ │ ┌──────────┐ │ ┌────────┐ │ ┌────────┐ │
│ │ Design  │ │ │ Backend  │ │ │QA Test │ │ │ Deploy │ │
│ │mockups  │ │ │API route │ │ │passed  │ │ │Live    │ │
│ │HIGH     │ │ │MEDIUM    │ │ │LOW     │ │ │✓       │ │
│ │❌ John  │ │ │👤 Sarah  │ │ │👤 Mike │ │ │8h/8h   │ │
│ └─────────┘ │ └──────────┘ │ └────────┘ │ └────────┘ │
│             │              │            │            │
│ ┌─────────┐ │ ┌──────────┐ │            │ ┌────────┐ │
│ │Database │ │ │Frontend  │ │            │ │ Setup  │ │
│ │schema   │ │ │UI comp   │ │            │ │prod DB │ │
│ │HIGH     │ │ │HIGH      │ │            │ │6h/10h  │ │
│ │♻️ Unassn│ │ │👤 Dev    │ │            │ └────────┘ │
│ └─────────┘ │ └──────────┘ │            │            │
└─────────────┴──────────────┴────────────┴────────────┘
    5 tasks      4 tasks       2 tasks      3 tasks
```

## Status Transitions

```text
todo ──start──> in_progress ──review──> review ──approve──> completed
  │                  │                      │
  └──────────────────drag────────────────────┘
```

## Features

### Drag & Drop

- Move cards between columns (todo → in_progress → review → completed)
- Reorder cards within same column
- Smooth transitions and visual feedback

### Inline Editing

- Click task title to edit
- Inline description editing
- Priority selector
- Due date picker
- Assignee selector

### Time Tracking

- Estimated hours (planning)
- Actual hours (log time spent)
- Progress visualization

### Filtering & Search

- Filter by: assignee, priority, due date, status
- Search by task title/description
- Show/hide completed tasks

### Collaboration

- Multiple assignees support
- @mention notifications
- Comments on tasks
- Activity timeline

## Project Frontend Components

### KanbanBoard Component

- Four-column layout (todo, in_progress, review, completed)
- Drag-drop task management
- Progress stats (total, completed, in progress)
- Project metadata display

### KanbanColumn Component

- Column header with task count
- Sortable task list
- Add task button
- Drop zone for drag operations

### KanbanCard Component

- Task title and description
- Priority badge (color-coded)
- Assignee avatar
- Due date indication
- Time estimate display
- Click to expand detailed view

### ProjectForm Component

- Create/edit project details
- Name, description, client selection
- Owner and managers assignment
- Start/due date selection
- Visibility settings

---

## 🎨 Canvas Mode Implementation (Advanced Visual Workflows)

## Canvas Overview

Canvas mode provides a node-based visual representation of workflows for both
template design and assignment execution tracking.

## Canvas Features

### Workflow Nodes

```text
Node structure:
{
  id: "node-1",
  type: "stage" | "step" | "decision" | "output",
  data: { 
    label: "Stage Name",
    description: "...",
    icon: "..." 
  },
  position: { x: 100, y: 100 }
}
```

### Workflow Edges

```text
Edge structure:
{
  id: "edge-1",
  source: "node-1",
  target: "node-2",
  data: { label: "Success" } // Optional conditional label
}
```

### Canvas Viewport

```text
Viewport state:
{
  x: 0,          // Pan X
  y: 0,          // Pan Y
  zoom: 1,       // Zoom level (0.1 - 3)
  autoFit: false // Auto-fit to content
}
```

## Canvas API Endpoints

### Get Workflow for Canvas

```text
GET /api/canvas/workflows/{workflowId}

Response:
{
  "id": "uuid",
  "name": "Workflow Name",
  "nodes": [
    { "id": "node-1", "type": "stage", "data": {...}, "position": {...} }
  ],
  "edges": [
    { "id": "edge-1", "source": "node-1", "target": "node-2" }
  ],
  "viewport": { "x": 0, "y": 0, "zoom": 1 }
}
```

### Get Assignment Canvas (Read-Only with Status Overlay)

```text
GET /api/canvas/assignments/{assignmentId}

Returns workflow canvas with assignment-specific status overlays:
- Node colors change based on stage status
- Progress indicators
- Completion badges
```

## Canvas Frontend Components

### WorkflowCanvas Features

- SVG-based rendering for performance
- Drag nodes to reposition (template mode only)
- Zoom/pan controls (mouse wheel, drag)
- Node selection and inspection
- Real-time status overlays (for assignments)
- Connection preview on drag
- Context menu for node operations

### Node Status Colors

```text
Not Started: #E5E7EB (gray)
In Progress: #FCD34D (yellow)
Completed:   #86EFAC (green)
Blocked:     #F87171 (red)
```

### Canvas Interactions

```text
Template Mode:
  ├─ Click node → Show properties panel
  ├─ Drag node → Reposition
  ├─ Drag from port → Create connection
  ├─ Delete node → Remove from workflow
  └─ Scroll zoom → Adjust zoom level

Assignment Mode (Read-Only):
  ├─ Click node → Show stage details
  ├─ Hover node → Show status tooltip
  ├─ Pan/zoom → Navigate canvas
  └─ Show status overlay → Progress indicator
```

---

## 📝 File Reference Quick Lookup

- User Auth: Backend `endpoints/auth.py`, Frontend `page.tsx`, Database `User`
  model
- AD Auth: Backend `endpoints/ad_auth.py`, Database `User` + AD fields
- Users CRUD: Backend `endpoints/users.py`, Frontend `dashboard/users/page.tsx`,
  Database `User`
- Documents: Backend `endpoints/documents.py`, Frontend
  `dashboard/documents/page.tsx`
- Workflows: Backend `endpoints/workflows.py`, Frontend
  `dashboard/workflow/page.tsx`
- Assignments: Backend `endpoints/assignments.py`, Frontend
  `dashboard/assignments/page.tsx`, Database `workflowAssignments` + clones
- Projects: Backend `endpoints/projects.py`, Frontend
  `dashboard/projects/page.tsx`, Database `projects` + tasks + collaborators
- Canvas: Backend `endpoints/canvas.py`, Frontend
  `components/canvas/WorkflowCanvas.tsx`, Database `workflows.nodes/edges`
- Dashboard: Backend `endpoints/dashboard.py`, Frontend `dashboard/page.tsx`
- Roles: Frontend `dashboard/roles/page.tsx`

---

**Last Updated:** Feb 12, 2026  
**Project Status:** Active Development (Dummy auth, AD integration in progress)
