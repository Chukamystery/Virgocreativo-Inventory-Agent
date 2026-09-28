from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.services.stock_service import (
    get_stock_movements,
    record_stock_movement,
)


router = APIRouter(
    prefix="/stock-movements",
    tags=["Stock Movements"],
)


@router.post(
    "",
    response_model=schemas.StockMovementRead,
    status_code=status.HTTP_201_CREATED,
)
def create_stock_movement(
    movement: schemas.StockMovementCreate,
    db: Session = Depends(get_db),
):
    try:
        return record_stock_movement(
            db,
            movement,
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


@router.get(
    "",
    response_model=list[schemas.StockMovementRead],
)
def list_stock_movements(
    db: Session = Depends(get_db),
):
    return get_stock_movements(db)