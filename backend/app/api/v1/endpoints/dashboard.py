from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User

router = APIRouter()

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(deps.get_db), current_user = Depends(deps.get_current_user)):
    user_count = db.query(User).count()
    return {
        "total_users": user_count,
        "active_workflows": 5,
        "documents_processed": 120,
        "storage_used": "1.2 GB"
    }