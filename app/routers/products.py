from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud, schemas
from app.auth import get_current_user
from app.database import get_db


router = APIRouter(
    prefix="/products",
    tags=["Products"],
    dependencies=[
        Depends(get_current_user)
    ],
)


@router.post(
    "",
    response_model=schemas.ProductRead,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
):
    try:
        return crud.create_product(
            db,
            product,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "SKU already exists or "
                "data violates a database rule"
            ),
        )


@router.get(
    "",
    response_model=list[schemas.ProductRead],
)
def list_products(
    db: Session = Depends(get_db),
):
    return crud.get_products(db)


@router.get(
    "/{product_id}",
    response_model=schemas.ProductRead,
)
def read_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = crud.get_product(
        db,
        product_id,
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product


@router.patch(
    "/{product_id}",
    response_model=schemas.ProductRead,
)
def update_product(
    product_id: int,
    changes: schemas.ProductUpdate,
    db: Session = Depends(get_db),
):
    try:
        product = crud.update_product(
            db,
            product_id,
            changes,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product