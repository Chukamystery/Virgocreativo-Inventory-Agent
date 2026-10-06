from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app import crud, schemas
from app.auth import get_current_user
from app.database import get_db


router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"],
    dependencies=[
        Depends(get_current_user)
    ],
)


@router.get(
    "",
    response_model=list[schemas.InventoryRead],
)
def list_inventory(
    db: Session = Depends(get_db),
):
    return crud.get_inventory(db)


@router.get(
    "/{inventory_id}",
    response_model=schemas.InventoryRead,
)
def read_inventory(
    inventory_id: int,
    db: Session = Depends(get_db),
):
    item = crud.get_inventory_item(
        db,
        inventory_id,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Inventory record not found",
        )

    return item