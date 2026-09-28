from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas


def create_product(
    db: Session,
    product: schemas.ProductCreate
):
    if product.target_stock < product.reorder_point:
        raise ValueError(
            "target_stock cannot be below reorder_point"
        )

    db_product = models.Product(
        **product.model_dump()
    )

    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    return db_product


def get_products(db: Session):
    statement = select(
        models.Product
    ).order_by(
        models.Product.product_id
    )

    return db.scalars(statement).all()


def get_product(
    db: Session,
    product_id: int
):
    return db.get(
        models.Product,
        product_id
    )


def update_product(
    db: Session,
    product_id: int,
    changes: schemas.ProductUpdate
):
    db_product = db.get(
        models.Product,
        product_id
    )

    if not db_product:
        return None

    update_data = changes.model_dump(
        exclude_unset=True
    )

    new_reorder_point = update_data.get(
        "reorder_point",
        db_product.reorder_point
    )

    new_target_stock = update_data.get(
        "target_stock",
        db_product.target_stock
    )

    if new_target_stock < new_reorder_point:
        raise ValueError(
            "target_stock cannot be below reorder_point"
        )

    for field, value in update_data.items():
        setattr(
            db_product,
            field,
            value
        )

    db.commit()
    db.refresh(db_product)

    return db_product


def get_inventory(db: Session):
    statement = select(
        models.Inventory
    ).order_by(
        models.Inventory.inventory_id
    )

    return db.scalars(statement).all()


def get_inventory_item(
    db: Session,
    inventory_id: int
):
    return db.get(
        models.Inventory,
        inventory_id
    )