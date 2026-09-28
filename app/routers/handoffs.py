from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.services.handoff_service import (
    create_handoff,
    get_handoffs,
    resolve_handoff,
)


router = APIRouter(
    prefix="/handoffs",
    tags=["Human Handoff"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def create_human_handoff(
    request: schemas.HumanHandoffCreate,
    db: Session = Depends(get_db),
):
    try:
        result = create_handoff(
            db=db,
            reason_code=request.reason_code,
            summary=request.summary,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            requested_by_user_id=(
                request.requested_by_user_id
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


@router.post(
    "/{handoff_id}/resolve",
    response_model=schemas.HumanHandoffRead,
)
def resolve_human_handoff(
    handoff_id: int,
    request: schemas.HumanHandoffResolveRequest,
    db: Session = Depends(get_db),
):
    try:
        return resolve_handoff(
            db=db,
            handoff_id=handoff_id,
            performed_by_user_id=(
                request.performed_by_user_id
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