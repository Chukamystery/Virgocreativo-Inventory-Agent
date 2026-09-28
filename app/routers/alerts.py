from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.services.alert_service import (
    get_alerts,
    resolve_alert,
    sync_low_stock_alerts,
)


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
)


@router.get(
    "",
    response_model=list[
        schemas.AlertRead
    ],
)
def list_alerts(
    status: str | None = None,
    alert_type: str | None = None,
    db: Session = Depends(get_db),
):
    return get_alerts(
        db=db,
        status=status,
        alert_type=alert_type,
    )


@router.post(
    "/sync-low-stock",
)
def sync_low_stock(
    db: Session = Depends(get_db),
):
    return sync_low_stock_alerts(
        db
    )


@router.post(
    "/{alert_id}/resolve",
    response_model=schemas.AlertRead,
)
def resolve_existing_alert(
    alert_id: int,
    request: schemas.AlertResolveRequest,
    db: Session = Depends(get_db),
):
    try:
        return resolve_alert(
            db=db,
            alert_id=alert_id,
            performed_by_user_id=(
                request.performed_by_user_id
            ),
            comment=request.comment,
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )