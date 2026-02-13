from fastapi import APIRouter
from app.api.v1.endpoints import auth, ad_auth, users, documents, workflows, dashboard, assignments, projects, canvas, clients, contacts, agents, notifications, reminders

api_router = APIRouter()

api_router.include_router(auth.router, tags=["login"])
api_router.include_router(ad_auth.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(canvas.router, prefix="/canvas", tags=["canvas"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["reminders"])