from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.services.stock_service import (
    get_audit_logs,
)


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


@router.get(
    "",
    response_model=list[schemas.AuditLogRead],
)
def list_audit_logs(
    db: Session = Depends(get_db),
):
    return get_audit_logs(db)