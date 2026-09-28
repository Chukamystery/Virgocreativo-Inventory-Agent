from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models


# =====================================================
# CALCULATE AVAILABLE STOCK
# =====================================================

def calculate_available_quantity(
    quantity_on_hand: int,
    reserved_quantity: int,
) -> int:

    available_quantity = (
        quantity_on_hand
        - reserved_quantity
    )

    if available_quantity < 0:
        raise ValueError(
            "Inventory data is invalid: "
            "reserved quantity exceeds "
            "quantity on hand"
        )

    return available_quantity


# =====================================================
# DETERMINE WHETHER STOCK IS LOW
# =====================================================

def is_low_stock(
    available_quantity: int,
    reorder_point: int,
) -> bool:

    return (
        available_quantity
        <= reorder_point
    )


# =====================================================
# CALCULATE REORDER QUANTITY
# =====================================================

def calculate_reorder_quantity(
    available_quantity: int,
    reorder_point: int,
    target_stock: int,
) -> int:

    if reorder_point < 0:
        raise ValueError(
            "reorder_point cannot be negative"
        )

    if target_stock < reorder_point:
        raise ValueError(
            "target_stock cannot be "
            "below reorder_point"
        )

    # If stock is healthy,
    # do not recommend a reorder yet.
    if not is_low_stock(
        available_quantity,
        reorder_point,
    ):
        return 0

    reorder_quantity = (
        target_stock
        - available_quantity
    )

    return max(
        reorder_quantity,
        0,
    )


# =====================================================
# BUILD ONE REORDER RECOMMENDATION
# =====================================================

def build_reorder_recommendation(
    inventory: models.Inventory,
    product: models.Product,
    location: models.Location,
):

    available_quantity = (
        calculate_available_quantity(
            inventory.quantity_on_hand,
            inventory.reserved_quantity,
        )
    )

    low_stock = is_low_stock(
        available_quantity,
        product.reorder_point,
    )

    reorder_quantity = (
        calculate_reorder_quantity(
            available_quantity,
            product.reorder_point,
            product.target_stock,
        )
    )

    return {
        "inventory_id":
            inventory.inventory_id,

        "product_id":
            product.product_id,

        "sku":
            product.sku,

        "product_name":
            product.name,

        "location_id":
            location.location_id,

        "location_name":
            location.name,

        "quantity_on_hand":
            inventory.quantity_on_hand,

        "reserved_quantity":
            inventory.reserved_quantity,

        "available_quantity":
            available_quantity,

        "reorder_point":
            product.reorder_point,

        "target_stock":
            product.target_stock,

        "is_low_stock":
            low_stock,

        "recommended_reorder_quantity":
            reorder_quantity,
    }


# =====================================================
# GET RECOMMENDATION FOR ONE PRODUCT / LOCATION
# =====================================================

def get_reorder_recommendation(
    db: Session,
    product_id: int,
    location_id: int,
):

    inventory = db.scalar(
        select(
            models.Inventory
        ).where(
            models.Inventory.product_id
            == product_id,

            models.Inventory.location_id
            == location_id,
        )
    )

    if inventory is None:
        raise ValueError(
            "Inventory record not found "
            "for this product and location"
        )

    product = db.get(
        models.Product,
        product_id,
    )

    location = db.get(
        models.Location,
        location_id,
    )

    if (
        product is None
        or location is None
    ):
        raise ValueError(
            "Related product or location "
            "not found"
        )

    return build_reorder_recommendation(
        inventory,
        product,
        location,
    )


# =====================================================
# GET ALL LOW-STOCK ITEMS
# =====================================================

def get_low_stock_items(
    db: Session,
):

    rows = db.execute(
        select(
            models.Inventory,
            models.Product,
            models.Location,
        )
        .join(
            models.Product,
            models.Inventory.product_id
            == models.Product.product_id,
        )
        .join(
            models.Location,
            models.Inventory.location_id
            == models.Location.location_id,
        )
        .where(
            models.Product.active.is_(True),
            models.Location.active.is_(True),
        )
    ).all()

    low_stock_items = []

    for (
        inventory,
        product,
        location,
    ) in rows:

        recommendation = (
            build_reorder_recommendation(
                inventory,
                product,
                location,
            )
        )

        if recommendation[
            "is_low_stock"
        ]:
            low_stock_items.append(
                recommendation
            )

    return low_stock_items