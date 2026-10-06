from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app import schemas
from app.auth import get_current_user
from app.database import get_db
from app.services.reorder_service import (
    get_low_stock_items,
    get_reorder_recommendation,
)


router = APIRouter(
    prefix="/reorder",
    tags=["Reorder"],
    dependencies=[
        Depends(get_current_user)
    ],
)


@router.get(
    "/low-stock",
    response_model=schemas.ReorderSummaryRead,
)
def list_low_stock_items(
    db: Session = Depends(get_db),
):
    items = get_low_stock_items(db)

    return {
        "low_stock_count": len(items),
        "items": items,
    }


@router.get(
    "/recommendation",
    response_model=schemas.ReorderRecommendationRead,
)
def get_recommendation(
    product_id: int,
    location_id: int,
    db: Session = Depends(get_db),
):
    try:
        return get_reorder_recommendation(
            db,
            product_id,
            location_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )