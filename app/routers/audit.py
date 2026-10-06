from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from app import schemas
from app.auth import get_current_user
from app.database import get_db
from app.services.stock_service import (
    get_audit_logs,
)


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
    dependencies=[
        Depends(get_current_user)
    ],
)


@router.get(
    "",
    response_model=list[schemas.AuditLogRead],
)
def list_audit_logs(
    db: Session = Depends(get_db),
):
    return get_audit_logs(db)