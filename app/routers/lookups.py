from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db


router = APIRouter(
    prefix="/lookups",
    tags=["Lookups"],
    dependencies=[
        Depends(get_current_user)
    ],
)


@router.get(
    "/locations",
    response_model=list[
        schemas.LocationLookupRead
    ],
)
def list_locations(
    db: Session = Depends(get_db),
):
    statement = (
        select(
            models.Location
        )
        .where(
            models.Location.active.is_(True)
        )
        .order_by(
            models.Location.location_id
        )
    )

    return db.scalars(
        statement
    ).all()


@router.get(
    "/suppliers",
    response_model=list[
        schemas.SupplierLookupRead
    ],
)
def list_suppliers(
    db: Session = Depends(get_db),
):
    statement = (
        select(
            models.Supplier
        )
        .where(
            models.Supplier.active.is_(True)
        )
        .order_by(
            models.Supplier.supplier_id
        )
    )

    return db.scalars(
        statement
    ).all()