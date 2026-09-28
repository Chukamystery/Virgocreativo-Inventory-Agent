import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.services.reorder_service import (
    get_reorder_recommendation,
)


ALLOWED_DRAFT_ROLES = {
    "PROCUREMENT_OFFICER",
    "INVENTORY_MANAGER",
    "ADMIN",
}


def get_supplier_options(
    db: Session,
    product_id: int,
):
    """
    Return active supplier options for a product.

    Supplier facts come from structured database
    records, never from the LLM.
    """

    rows = db.execute(
        select(
            models.ProductSupplier,
            models.Supplier,
        )
        .join(
            models.Supplier,
            models.ProductSupplier.supplier_id
            == models.Supplier.supplier_id,
        )
        .where(
            models.ProductSupplier.product_id
            == product_id,
            models.Supplier.active.is_(True),
        )
        .order_by(
            models.ProductSupplier.preferred.desc(),
            models.Supplier.supplier_id,
        )
    ).all()

    return [
        {
            "supplier_id":
                supplier.supplier_id,

            "supplier_code":
                supplier.supplier_code,

            "supplier_name":
                supplier.name,

            "supplier_sku":
                link.supplier_sku,

            "unit_cost":
                link.unit_cost,

            "minimum_order_qty":
                link.minimum_order_qty,

            "lead_time_days":
                supplier.lead_time_days,

            "currency":
                supplier.currency,

            "preferred":
                link.preferred,
        }
        for link, supplier in rows
    ]


def choose_supplier_for_draft(
    supplier_options: list[dict],
):
    """
    Deterministic supplier-selection rule.

    Exactly one preferred supplier:
        use it.

    Only one supplier exists:
        use it.

    Otherwise:
        stop and require human selection.
    """

    if not supplier_options:
        raise ValueError(
            "No active supplier is configured "
            "for this product"
        )

    preferred = [
        option
        for option in supplier_options
        if option["preferred"]
    ]

    if len(preferred) == 1:
        return preferred[0]

    if len(preferred) > 1:
        raise ValueError(
            "Multiple preferred suppliers are configured. "
            "Human supplier selection is required."
        )

    if len(supplier_options) == 1:
        return supplier_options[0]

    raise ValueError(
        "Multiple suppliers are available but none is "
        "uniquely preferred. Human supplier selection "
        "is required."
    )


def prepare_purchase_request(
    db: Session,
    product_id: int,
    location_id: int,
    requested_by_user_id: int,
    notes: str | None = None,
):
    """
    Prepare a DRAFT purchase request.

    This function does NOT approve the request and
    does NOT place an order with a supplier.
    """

    user = db.get(
        models.User,
        requested_by_user_id,
    )

    if user is None or not user.active:
        raise PermissionError(
            "Requesting user not found or inactive"
        )

    if user.role not in ALLOWED_DRAFT_ROLES:
        raise PermissionError(
            "User role is not allowed to prepare "
            "purchase-request drafts"
        )

    product = db.get(
        models.Product,
        product_id,
    )

    if product is None or not product.active:
        raise ValueError(
            "Product not found or inactive"
        )

    location = db.get(
        models.Location,
        location_id,
    )

    if location is None or not location.active:
        raise ValueError(
            "Location not found or inactive"
        )

    recommendation = (
        get_reorder_recommendation(
            db,
            product_id,
            location_id,
        )
    )

    recommended_qty = recommendation[
        "recommended_reorder_quantity"
    ]

    if recommended_qty <= 0:
        raise ValueError(
            "No reorder is currently recommended "
            "for this product and location"
        )

    supplier_options = get_supplier_options(
        db,
        product_id,
    )

    supplier = choose_supplier_for_draft(
        supplier_options
    )

    minimum_order_qty = supplier[
        "minimum_order_qty"
    ]

    draft_quantity = max(
        recommended_qty,
        minimum_order_qty,
    )

    request_number = (
        "PR-"
        + datetime.now().strftime(
            "%Y%m%d%H%M%S%f"
        )
    )

    purchase_request = models.PurchaseRequest(
        request_number=request_number,
        requested_by_user_id=(
            requested_by_user_id
        ),
        supplier_id=supplier[
            "supplier_id"
        ],
        status="DRAFT",
        notes=notes,
    )

    try:
        db.add(
            purchase_request
        )

        db.flush()

        line = models.PurchaseRequestLine(
            purchase_request_id=(
                purchase_request.purchase_request_id
            ),
            product_id=product_id,
            location_id=location_id,
            quantity=draft_quantity,
            unit_cost=supplier[
                "unit_cost"
            ],
            reorder_recommendation=(
                recommended_qty
            ),
            minimum_order_qty=(
                minimum_order_qty
            ),
        )

        db.add(
            line
        )

        db.flush()

        audit_details = {
            "request_number":
                request_number,

            "product_id":
                product_id,

            "location_id":
                location_id,

            "supplier_id":
                supplier["supplier_id"],

            "reorder_recommendation":
                recommended_qty,

            "minimum_order_qty":
                minimum_order_qty,

            "draft_quantity":
                draft_quantity,

            "status":
                "DRAFT",
        }

        audit = models.AuditLog(
            user_id=requested_by_user_id,
            action=(
                "PURCHASE_REQUEST_DRAFT_CREATED"
            ),
            entity_type="purchase_request",
            entity_id=(
                purchase_request.purchase_request_id
            ),
            details=json.dumps(
                audit_details
            ),
        )

        db.add(
            audit
        )

        db.commit()

        db.refresh(
            purchase_request
        )

        db.refresh(
            line
        )

        return {
            "purchase_request":
                purchase_request,

            "lines":
                [line],

            "supplier":
                supplier,

            "reorder_recommendation":
                recommended_qty,

            "draft_quantity":
                draft_quantity,
        }

    except Exception:
        db.rollback()
        raise


def get_purchase_requests(
    db: Session,
):
    return db.scalars(
        select(
            models.PurchaseRequest
        )
        .order_by(
            models.PurchaseRequest
            .purchase_request_id
        )
    ).all()


def get_purchase_request_lines(
    db: Session,
    purchase_request_id: int,
):
    return db.scalars(
        select(
            models.PurchaseRequestLine
        )
        .where(
            models.PurchaseRequestLine
            .purchase_request_id
            == purchase_request_id
        )
        .order_by(
            models.PurchaseRequestLine
            .purchase_request_line_id
        )
    ).all()