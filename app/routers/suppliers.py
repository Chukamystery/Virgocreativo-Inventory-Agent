from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.services.procurement_service import (
    get_supplier_options,
)


router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"],
)


@router.get(
    "/product/{product_id}",
    response_model=list[schemas.SupplierOptionRead],
)
def suppliers_for_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    results = get_supplier_options(
        db,
        product_id,
    )

    if not results:
        raise HTTPException(
            status_code=404,
            detail=(
                "No active supplier configured "
                "for this product"
            ),
        )

    return results