from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app import schemas
from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.services.handoff_service import (
    create_handoff,
    get_handoffs,
    resolve_handoff,
)


router = APIRouter(
    prefix="/handoffs",
    tags=["Human Handoff"],
    dependencies=[
        Depends(get_current_user)
    ],
)


# =====================================================
# CREATE HUMAN HANDOFF
# =====================================================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def create_human_handoff(
    request: schemas.HumanHandoffCreate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    try:
        result = create_handoff(
            db=db,
            reason_code=request.reason_code,
            summary=request.summary,
            entity_type=request.entity_type,
            entity_id=request.entity_id,

            # Do not trust the ID from the request body.
            # Use the authenticated user instead.
            requested_by_user_id=(
                current_user.user_id
            ),

            context=request.context,
        )

        handoff = result[
            "handoff"
        ]

        return {
            "created":
                result["created"],

            "handoff_id":
                handoff.handoff_id,

            "reason_code":
                handoff.reason_code,

            "summary":
                handoff.summary,

            "status":
                handoff.status,

            "entity_type":
                handoff.entity_type,

            "entity_id":
                handoff.entity_id,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =====================================================
# LIST HUMAN HANDOFFS
# =====================================================

@router.get(
    "",
    response_model=list[
        schemas.HumanHandoffRead
    ],
)
def list_handoffs(
    status: str | None = None,
    db: Session = Depends(get_db),
):
    return get_handoffs(
        db=db,
        status=status,
    )


# =====================================================
# RESOLVE HUMAN HANDOFF
# =====================================================

@router.post(
    "/{handoff_id}/resolve",
    response_model=schemas.HumanHandoffRead,
)
def resolve_human_handoff(
    handoff_id: int,
    request: schemas.HumanHandoffResolveRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    try:
        return resolve_handoff(
            db=db,
            handoff_id=handoff_id,

            # Do not trust performed_by_user_id
            # from the frontend.
            performed_by_user_id=(
                current_user.user_id
            ),

            resolution_note=(
                request.resolution_note
            ),
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