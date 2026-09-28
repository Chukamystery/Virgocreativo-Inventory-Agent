from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app import models
from app.services.handoff_service import (
    create_handoff,
)
from app.services.procurement_service import (
    get_supplier_options,
)
from app.services.reorder_service import (
    calculate_available_quantity,
    get_low_stock_items,
    get_reorder_recommendation,
)


# =====================================================
# PRODUCT SEARCH
# =====================================================

def find_products(
    db: Session,
    query: str,
):
    search_term = f"%{query.strip()}%"

    statement = (
        select(models.Product)
        .where(
            models.Product.active.is_(True),
            or_(
                models.Product.name.ilike(
                    search_term
                ),
                models.Product.sku.ilike(
                    search_term
                ),
            ),
        )
        .order_by(
            models.Product.product_id
        )
        .limit(10)
    )

    products = db.scalars(
        statement
    ).all()

    return [
        {
            "product_id":
                product.product_id,

            "sku":
                product.sku,

            "name":
                product.name,

            "category":
                product.category,

            "unit_of_measure":
                product.unit_of_measure,
        }
        for product in products
    ]


# =====================================================
# LOCATION SEARCH
# =====================================================

def find_locations(
    db: Session,
    query: str,
):
    search_term = f"%{query.strip()}%"

    statement = (
        select(models.Location)
        .where(
            models.Location.active.is_(True),
            or_(
                models.Location.name.ilike(
                    search_term
                ),
                models.Location.code.ilike(
                    search_term
                ),
            ),
        )
        .order_by(
            models.Location.location_id
        )
        .limit(10)
    )

    locations = db.scalars(
        statement
    ).all()

    return [
        {
            "location_id":
                location.location_id,

            "code":
                location.code,

            "name":
                location.name,

            "location_type":
                location.location_type,
        }
        for location in locations
    ]


# =====================================================
# CURRENT INVENTORY BALANCE
# =====================================================

def get_inventory_balance(
    db: Session,
    product_id: int,
    location_id: int,
):
    inventory = db.scalar(
        select(
            models.Inventory
        )
        .where(
            models.Inventory.product_id
            == product_id,

            models.Inventory.location_id
            == location_id,
        )
    )

    if inventory is None:
        return {
            "found": False,
            "error": (
                "Inventory record not found "
                "for this product and location"
            ),
        }

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
        return {
            "found": False,
            "error": (
                "Related product or location "
                "record could not be verified"
            ),
        }

    available_quantity = (
        calculate_available_quantity(
            inventory.quantity_on_hand,
            inventory.reserved_quantity,
        )
    )

    return {
        "found": True,

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
    }


# =====================================================
# REORDER RECOMMENDATION
# =====================================================

def reorder_recommendation(
    db: Session,
    product_id: int,
    location_id: int,
):
    try:
        return get_reorder_recommendation(
            db,
            product_id,
            location_id,
        )

    except ValueError as exc:
        return {
            "found": False,
            "error": str(exc),
        }


# =====================================================
# LOW STOCK
# =====================================================

def low_stock_items(
    db: Session,
):
    items = get_low_stock_items(
        db
    )

    return {
        "low_stock_count":
            len(items),

        "items":
            items,
    }


# =====================================================
# CENTRAL TOOL DISPATCHER
# =====================================================

def execute_inventory_tool(
    db: Session,
    tool_name: str,
    arguments: dict,
    actor_user_id: int | None = None,
):
    """
    Allowlisted tool dispatcher.

    tool_name:
        Tool requested by the LLM.

    arguments:
        Validated function arguments.

    actor_user_id:
        Verified demo user who initiated
        the current agent conversation.

    The LLM does not get arbitrary Python
    or database access.
    """

    # =================================================
    # PRODUCT SEARCH
    # =================================================

    if tool_name == "find_products":

        return find_products(
            db,
            query=arguments[
                "query"
            ],
        )

    # =================================================
    # LOCATION SEARCH
    # =================================================

    if tool_name == "find_locations":

        return find_locations(
            db,
            query=arguments[
                "query"
            ],
        )

    # =================================================
    # INVENTORY BALANCE
    # =================================================

    if tool_name == "get_inventory_balance":

        return get_inventory_balance(
            db,
            product_id=arguments[
                "product_id"
            ],
            location_id=arguments[
                "location_id"
            ],
        )

    # =================================================
    # REORDER RECOMMENDATION
    # =================================================

    if (
        tool_name
        == "get_reorder_recommendation"
    ):

        return reorder_recommendation(
            db,
            product_id=arguments[
                "product_id"
            ],
            location_id=arguments[
                "location_id"
            ],
        )

    # =================================================
    # LOW-STOCK LIST
    # =================================================

    if tool_name == "list_low_stock_items":

        return low_stock_items(
            db
        )

    # =================================================
    # SUPPLIER OPTIONS
    # =================================================

    if tool_name == "get_supplier_options":

        return get_supplier_options(
            db,
            product_id=arguments[
                "product_id"
            ],
        )

    # =================================================
    # HUMAN HANDOFF
    # =================================================

    if tool_name == "create_human_handoff":

        if actor_user_id is None:
            raise ValueError(
                "A verified acting user is "
                "required to create a human "
                "handoff"
            )

        result = create_handoff(
            db=db,

            reason_code=arguments[
                "reason_code"
            ],

            summary=arguments[
                "summary"
            ],

            entity_type=arguments[
                "entity_type"
            ],

            entity_id=arguments[
                "entity_id"
            ],

            requested_by_user_id=(
                actor_user_id
            ),

            context={
                "created_by":
                    "inventory_agent",

                "actor_user_id":
                    actor_user_id,
            },
        )

        handoff = result[
            "handoff"
        ]

        return {
            "created":
                result["created"],

            "handoff_id":
                handoff.handoff_id,

            "status":
                handoff.status,

            "reason_code":
                handoff.reason_code,

            "summary":
                handoff.summary,

            "requested_by_user_id":
                handoff.requested_by_user_id,
        }

    # =================================================
    # BLOCK EVERYTHING ELSE
    # =================================================

    raise ValueError(
        f"Tool not allowed: {tool_name}"
    )