import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas


# Temporary authorization rule for Task 5.
# Proper authentication/approval handling comes later.
ALLOWED_EXECUTION_ROLES = {
    "INVENTORY_MANAGER",
    "ADMIN",
}


def record_stock_movement(
    db: Session,
    movement: schemas.StockMovementCreate
):
    """
    Safely record a stock movement.

    The function:

    1. Validates the product.
    2. Validates the location.
    3. Validates the user.
    4. Checks the user's role.
    5. Finds the inventory balance.
    6. Calculates the new quantity.
    7. Updates inventory.
    8. Creates a stock movement.
    9. Creates an audit log.
    10. Commits everything together.

    If anything fails, everything is rolled back.
    """

    try:

        # ======================================
        # 1. VALIDATE PRODUCT
        # ======================================

        product = db.get(
            models.Product,
            movement.product_id
        )

        if not product or not product.active:
            raise ValueError(
                "Product not found or inactive"
            )


        # ======================================
        # 2. VALIDATE LOCATION
        # ======================================

        location = db.get(
            models.Location,
            movement.location_id
        )

        if not location or not location.active:
            raise ValueError(
                "Location not found or inactive"
            )


        # ======================================
        # 3. VALIDATE USER
        # ======================================

        user = db.get(
            models.User,
            movement.performed_by_user_id
        )

        if not user or not user.active:
            raise PermissionError(
                "User not found or inactive"
            )


        # ======================================
        # 4. CHECK USER ROLE
        # ======================================

        if user.role not in ALLOWED_EXECUTION_ROLES:
            raise PermissionError(
                "This user is not allowed "
                "to execute stock movements"
            )


        # ======================================
        # 5. FIND CURRENT INVENTORY BALANCE
        # ======================================

        inventory = db.scalar(
            select(
                models.Inventory
            ).where(
                models.Inventory.product_id
                == movement.product_id,

                models.Inventory.location_id
                == movement.location_id
            )
        )


        # ======================================
        # 6. HANDLE MISSING INVENTORY RECORD
        # ======================================

        if inventory is None:

            # We can create a new balance when
            # stock is arriving.

            if movement.movement_type not in {
                "RECEIPT",
                "ADJUSTMENT_IN",
            }:
                raise ValueError(
                    "No inventory balance exists "
                    "for this product and location"
                )

            inventory = models.Inventory(
                product_id=movement.product_id,
                location_id=movement.location_id,
                quantity_on_hand=0,
                reserved_quantity=0
            )

            db.add(inventory)

            db.flush()


        # ======================================
        # 7. READ CURRENT QUANTITIES
        # ======================================

        previous_quantity = (
            inventory.quantity_on_hand
        )

        reserved_quantity = (
            inventory.reserved_quantity
        )

        available_quantity = (
            previous_quantity
            - reserved_quantity
        )


        # ======================================
        # 8. CALCULATE NEW BALANCE
        # ======================================

        if movement.movement_type in {
            "RECEIPT",
            "ADJUSTMENT_IN",
        }:

            new_quantity = (
                previous_quantity
                + movement.quantity
            )


        elif movement.movement_type == "ISSUE":

            if movement.quantity > available_quantity:
                raise ValueError(
                    "Issue quantity exceeds "
                    "available stock"
                )

            new_quantity = (
                previous_quantity
                - movement.quantity
            )


        elif (
            movement.movement_type
            == "ADJUSTMENT_OUT"
        ):

            new_quantity = (
                previous_quantity
                - movement.quantity
            )

            if (
                new_quantity
                < reserved_quantity
            ):
                raise ValueError(
                    "Adjustment would reduce "
                    "on-hand stock below "
                    "reserved quantity"
                )


        else:
            raise ValueError(
                "Unsupported movement type"
            )


        # ======================================
        # 9. UPDATE INVENTORY BALANCE
        # ======================================

        inventory.quantity_on_hand = (
            new_quantity
        )


        # ======================================
        # 10. CREATE STOCK MOVEMENT RECORD
        # ======================================

        db_movement = models.StockMovement(
            product_id=movement.product_id,

            location_id=movement.location_id,

            movement_type=movement.movement_type,

            quantity=movement.quantity,

            previous_quantity=(
                previous_quantity
            ),

            new_quantity=new_quantity,

            performed_by_user_id=(
                movement.performed_by_user_id
            ),

            reason=movement.reason,

            reference=movement.reference
        )

        db.add(db_movement)

        # We need the movement ID before
        # creating the audit log.
        db.flush()


        # ======================================
        # 11. PREPARE AUDIT DETAILS
        # ======================================

        audit_details = {
            "movement_type":
                movement.movement_type,

            "product_id":
                movement.product_id,

            "location_id":
                movement.location_id,

            "quantity":
                movement.quantity,

            "previous_quantity":
                previous_quantity,

            "new_quantity":
                new_quantity,

            "reference":
                movement.reference,
        }


        # ======================================
        # 12. CREATE AUDIT LOG
        # ======================================

        audit = models.AuditLog(
            user_id=(
                movement.performed_by_user_id
            ),

            action=(
                "STOCK_MOVEMENT_RECORDED"
            ),

            entity_type=(
                "stock_movement"
            ),

            entity_id=(
                db_movement.movement_id
            ),

            details=json.dumps(
                audit_details
            )
        )

        db.add(audit)


        # ======================================
        # 13. COMMIT EVERYTHING TOGETHER
        # ======================================

        db.commit()

        db.refresh(
            db_movement
        )

        return db_movement


    except Exception:

        # If ANYTHING fails,
        # undo all uncommitted changes.
        db.rollback()

        raise


def get_stock_movements(
    db: Session
):
    statement = (
        select(
            models.StockMovement
        )
        .order_by(
            models.StockMovement.movement_id
        )
    )

    return db.scalars(
        statement
    ).all()


def get_audit_logs(
    db: Session
):
    statement = (
        select(
            models.AuditLog
        )
        .order_by(
            models.AuditLog.audit_id
        )
    )

    return db.scalars(
        statement
    ).all()