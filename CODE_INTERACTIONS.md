# Cyloid Project - Code Interaction & Data Flow Map

## 🔗 COMPONENT RELATIONSHIPS

### Frontend ↔ Backend API Calls

```text
LOGIN PAGE (frontend/app/page.tsx)
├─ Form submission
├─ POST /api/v1/auth/login
│  └─ Payload: { email, password }
│
└─ Response: { access_token, token_type }
   └─ Stored in localStorage.access_token
```

```text
DASHBOARD (frontend/app/dashboard/layout.tsx)
├─ Shares Sidebar.tsx across all pages
├─ GET /api/v1/dashboard/analytics
├─ GET /api/v1/users
├─ GET /api/v1/documents
└─ GET /api/v1/workflows
```

```text
USER MANAGEMENT (frontend/app/dashboard/users/page.tsx)
├─ GET /api/v1/users
│  └─ Display user list
├─ POST /api/v1/users (create)
│  └─ Bulk onboarding
└─ DELETE /api/v1/users/{id}
   └─ Remove user
```

---

## 📡 BACKEND REQUEST HANDLING

### Authentication Request Path

```text
1. Client sends POST /api/v1/auth/login
   └─ Body: { email: str, password: str }

2. FastAPI routes to: endpoints/auth.py::login_endpoint()
   ├─ Import: from app.api.deps import get_db
   ├─ Parameter: db: Session = Depends(get_db)
   └─ Creates SQLAlchemy session automatically

3. Endpoint handler logic:
   ├─ Query DB: User.query.filter(User.email == email)
   ├─ Check if user exists
   └─ Verify password: bcrypt.verify(password, hashed_password)

4. If valid:
   ├─ Import: from app.core.security import create_access_token
   ├─ Generate JWT: create_access_token(data={"sub": user.email})
   └─ Return: { "access_token": "...", "token_type": "bearer" }

5. Client receives token
   └─ localStorage.setItem("access_token", token)
```

### User Creation Request Path

```text
1. Client sends POST /api/v1/users
   └─ Body: [{ email, full_name, password }]
   └─ HeaderAuth: Authorization: Bearer {token}

2. FastAPI routes to: endpoints/users.py::create_users()
   ├─ Dependency: get_current_user (validates JWT)
   ├─ Dependency: get_db (creates session)
   └─ Parameter: users: list[UserCreate]

3. Call service layer:
   └─ user_service.onboard_multiple_users(db, users)

4. Service logic:
   ├─ For each user in list:
   │  ├─ Check: db.query(User).filter(email).first()
   │  ├─ If exists: add to errors[]
   │  ├─ If new:
   │  │  ├─ Parse full_name → first_name, last_name
   │  │  ├─ Hash password: get_password_hash(password)
   │  │  ├─ Create User object
   │  │  └─ db.add(user)
   │  └─ Continue loop
   └─ db.commit() [atomic]

5. Return response:
   └─ { "created": [emails], "errors": [errors], "status": "success" }
```

### Protected Endpoint Request Path

```text
1. Client sends GET /api/v1/users/{id}
   └─ Header: Authorization: Bearer {access_token}

2. FastAPI dependency: get_current_user
   ├─ Import: from app.core.security import verify_token
   ├─ Extract token from header
   ├─ Verify JWT signature (use SECRET_KEY from config)
   ├─ Decode payload: {"sub": email}
   └─ Return: current_user object

3. If token invalid/expired:
   └─ Raise HTTPException(status_code=401, detail="Unauthorized")

4. If valid, endpoint executes:
   ├─ Query: User.query.filter(User.id == id).first()
   └─ Return: User object

5. Response serialized by Pydantic schema (UserOut)
```

---

## 🗄️ DATABASE OPERATION FLOW

```text
Backend Endpoint Handler
  │
  ├─ Receives: db: Session = Depends(get_db)
  │  └─ Session created by get_db() in app/api/deps.py
  │
  ├─ Imports: from app.db.session import SessionLocal
  │  └─ SessionLocal = sessionmaker(bind=engine)
  │  └─ engine = create_engine(DATABASE_URL)
  │
  ├─ Imports: from app.models.user import User, Base
  │  └─ User class defined with __tablename__ = "users"
  │  └─ Base = declarative_base() from SQLAlchemy
  │
  ├─ Query executed:
  │  └─ db.query(User).filter(User.email == email).first()
  │  └─ Translates to SQL: SELECT * FROM users WHERE email = ?
  │
  ├─ Modification executed:
  │  ├─ Create object: user = User(first_name=..., email=...)
  │  ├─ Add to session: db.add(user)
  │  ├─ Commit: db.commit()
  │  └─ Optional refresh: db.refresh(user)
  │
  └─ Changes persisted to PostgreSQL
```

### Migration Workflow

```text
Developer modifies app/models/user.py
  │
  ├─ Run: alembic revision --autogenerate -m "description"
  │  └─ Generates new file: alembic/versions/{timestamp}_{name}.py
  │
  ├─ Alembic compares:
  │  ├─ Current schema (from DB via __table_args__)
  │  └─ Updated model (from app/models/)
  │
  ├─ Generated migration contains:
  │  ├─ def upgrade() [apply changes]
  │  └─ def downgrade() [revert changes]
  │
  ├─ Developer reviews migration file
  │
  ├─ Run: alembic upgrade head
  │  └─ Executes all pending migrations
  │
  └─ PostgreSQL schema updated
     └─ Next time app starts, Base.metadata.create_all() finds matching schema
```

---

## 🔐 AUTHENTICATION FLOW DETAILS

### Local JWT Flow

```text
User submits credentials (Frontend)
  │
  ├─ POST /api/v1/auth/login
  │  ├─ Endpoint: endpoints/auth.py::login()
  │  └─ Handler queries User from DB
  │
  ├─ Password verification:
  │  ├─ Import: from passlib.context import CryptContext
  │  ├─ crypt_context = CryptContext(schemes=["bcrypt"])
  │  └─ crypt_context.verify(plaintext, hashed) → bool
  │
  ├─ If valid:
  │  ├─ Import: from app.core.security import create_access_token
  │  ├─ Import from core.config: SECRET_KEY, ALGORITHM
  │  ├─ Payload: { "sub": user.email, "exp": now + 24h }
  │  ├─ Token: jwt.encode(payload, SECRET_KEY, ALGORITHM)
  │  └─ Return: { "access_token": token, "token_type": "bearer" }
  │
  └─ Client stores: localStorage.access_token = token
     └─ For future requests, attach header:
        └─ Authorization: Bearer {token}
```

### Keycloak/AD OAuth Flow

```text
User clicks "Sign in with AD" (Frontend)
  │
  ├─ Redirect to Keycloak login:
  │  ├─ KEYCLOAK_SERVER_URL from config
  │  ├─ KEYCLOAK_REALM = "cyloid"
  │  ├─ KEYCLOAK_CLIENT_ID = "cyloid-backend"
  │  └─ Redirect URI points back to: /api/v1/ad-auth/callback
  │
  ├─ User enters AD credentials in Keycloak
  │
  ├─ Keycloak redirects with auth code:
  │  └─ GET /api/v1/ad-auth/callback?code=xxx&state=yyy
  │
  ├─ Backend handler:
  │  ├─ Endpoint: endpoints/ad_auth.py::callback()
  │  ├─ Exchange code for token:
  │  │  └─ Service: ad_auth_service.exchange_code_for_token(code)
  │  ├─ Extract JWT from Keycloak
  │  ├─ Decode JWT (Keycloak public key)
  │  ├─ Extract claims: keycloak_sub, username, email
  │  └─ Call: ad_auth_service.sync_or_create_ad_user()
  │
  ├─ Service: sync_or_create_ad_user()
  │  ├─ Check: User.query.filter(User.keycloak_sub == sub).first()
  │  ├─ If found:
  │  │  ├─ Update: user.ad_username, user.keycloak_sub
  │  │  └─ db.commit()
  │  ├─ If not found:
  │  │  ├─ Create: User(keycloak_sub=sub, auth_provider="KEYCLOAK_AD", ...)
  │  │  └─ db.add(), db.commit()
  │  └─ Return: user object
  │
  ├─ Backend generates JWT:
  │  ├─ Payload: { "sub": user.email }
  │  └─ Return: { "access_token": jwt_token }
  │
  └─ Frontend stores token
     └─ localStorage.access_token = jwt_token
```

---

## 🔗 DEPENDENCY INJECTION CHAIN

### How FastAPI gives you the database session

```text
1. Endpoint signature includes dependency:
   └─ db: Session = Depends(get_db)

2. FastAPI looks up get_db:
   ├─ Location: app/api/deps.py
   ├─ Function: def get_db():
   ├─ Yields: SessionLocal()
   └─ Cleans up: finally: db.close()

3. SessionLocal is defined:
   ├─ Location: app/db/session.py
   ├─ SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
   ├─ Engine: create_engine(DATABASE_URL)
   └─ DATABASE_URL from: app/core/config.py (from .env)

4. Result:
   └─ Endpoint receives fresh DB session
      └─ Lasts for request duration
      └─ Automatically closed after response
```

### How FastAPI validates authentication

```text
1. Endpoint includes dependency:
   └─ current_user: User = Depends(get_current_user)

2. FastAPI looks up get_current_user:
   ├─ Location: app/api/deps.py
   ├─ Function: def get_current_user(token: str = Depends(get_token)):
   ├─ Extracts token from request header
   ├─ Calls: verify_token(token)
   │  └─ Uses core/security.py
   │  └─ Validates JWT signature
   │  └─ Checks expiration
   └─ Returns: User object if valid

3. If token invalid:
   ├─ Raises: HTTPException(status_code=401)
   └─ Request blocked, endpoint never executes

4. If valid:
   └─ Endpoint receives current_user
      └─ Can use for row-level security
```

---

## 📦 IMPORT CHAINS

### What happens when app starts

```text
1. Entry: backend/app/main.py

2. app = FastAPI()

3. from app.core.config import settings
   └─ Loads environment from .env via pydantic-settings
   └─ Validates required fields (SECRET_KEY, DATABASE_URL, etc.)

4. from app.db.session import engine, Base
   ├─ Creates PostgreSQL connection pool
   ├─ Imports User model
   └─ Base.metadata.create_all(bind=engine)
      └─ Creates missing tables (development only)
      └─ Checks existing schema matches models

5. Add CORS middleware
   └─ Uses settings.BACKEND_CORS_ORIGINS

6. app.include_router(api_router, prefix="/api/v1")
   └─ Routes loaded from app/api/v1/api.py
   ├─ Each endpoint imports its own dependencies
   ├─ Each endpoint imports relevant schemas & services
   └─ All routes registered with FastAPI

7. App ready to receive requests
```

---

## 🎯 REQUEST LIFECYCLE

```text
CLIENT SENDS REQUEST
  │
  ├─ HTTP arrives at FastAPI (port 8000)
  │
  ├─ CORS middleware checks origin
  │  └─ If not in BACKEND_CORS_ORIGINS → 403
  │
  ├─ Route matching: /api/v1/... → api_router
  │
  ├─ Dependency injection:
  │  ├─ get_db() → creates Session
  │  ├─ get_current_user() → validates JWT
  │  ├─ Other custom dependencies
  │  └─ All run before handler
  │
  ├─ REQUEST HANDLER EXECUTES
  │  ├─ Has access to: db: Session, current_user: User, request body, etc.
  │  ├─ Can query DB
  │  ├─ Can call service functions
  │  ├─ Can modify database
  │  └─ Returns response (serialized via Pydantic)
  │
  ├─ RESPONSE SERIALIZATION
  │  ├─ Handler return value matches schema
  │  ├─ Pydantic validates
  │  └─ JSON serialized
  │
  ├─ MIDDLEWARE CLEANUP
  │  ├─ DB session closed
  │  ├─ Correlation IDs logged
  │  └─ Response headers set
  │
  └─ HTTP RESPONSE SENT
     └─ Client receives JSON
```

---

## 🔄 COMMON MODIFICATION PATTERNS

### Pattern 1: Add new endpoint

```text
File: app/api/v1/endpoints/feature.py
────────────────────────────────────
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.schemas.feature import FeatureCreate, FeatureOut
from app.services.feature_service import create_feature
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=FeatureOut)
def create_new_feature(
    payload: FeatureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_feature(db, payload, current_user)


File: app/api/v1/api.py
───────────────────────
from app.api.v1.endpoints import feature

api_router.include_router(feature.router, prefix="/feature", tags=["feature"])
```

### Pattern 2: Update database model

```text
File: app/models/user.py
─────────────────────────
# Add column
new_field = Column(String(100), nullable=True, index=True)


Terminal:
──────────
alembic revision --autogenerate -m "add new_field to users"
alembic upgrade head


File: app/schemas/user.py
──────────────────────────
# Add to schema
class UserBase(BaseModel):
    new_field: str | None = None

class UserCreate(UserBase):
    pass

class UserOut(UserBase):
    id: str
    # ... other fields
```

### Pattern 3: Create new service

```text
File: app/services/feature_service.py
──────────────────────────────────────
from sqlalchemy.orm import Session
from app.models.feature import Feature
from app.schemas.feature import FeatureCreate

def create_feature(db: Session, data: FeatureCreate, user):
    """Business logic here"""
    feature = Feature(
        name=data.name,
        owner_id=user.id,
        ...
    )
    db.add(feature)
    db.commit()
    db.refresh(feature)
    return feature


File: app/api/v1/endpoints/feature.py
──────────────────────────────────────
from app.services.feature_service import create_feature

# In endpoint:
result = create_feature(db, payload, current_user)
return result
```

---

## 🎨 FRONTEND COMPONENT PATTERN

### Pattern: Dashboard Page with API Call

```typescript
// app/dashboard/feature/page.tsx

"use client";

import { useState, useEffect } from "react";

export default function FeaturePage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem("access_token");
        const response = await fetch("/api/v1/feature", {
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
          }
        });
        
        if (!response.ok) throw new Error("Failed to fetch");
        
        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="p-6 space-y-4">
      {/* Render data */}
      {data?.items?.map((item) => (
        <div key={item.id} className="bg-white p-4 rounded">
          {item.name}
        </div>
      ))}
    </div>
  );
}
```

---

**Version:** 1.0  
**Created:** Feb 12, 2026  
**Purpose:** Deep technical understanding of code flows and interactions
