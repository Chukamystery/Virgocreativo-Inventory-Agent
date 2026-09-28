import pytest

from sqlalchemy import select

from app import models
from app.schemas import StockMovementCreate
from app.services.stock_service import (
    record_stock_movement,
)


# =====================================================
# TEST DATA
# =====================================================

@pytest.fixture()
def stock_test_data(
    db_session,
):
    """
    Create isolated users, product, location,
    and inventory records for stock movement tests.

    Initial inventory:
        On hand = 10
        Reserved = 2
        Available = 8
    """

    staff_user = models.User(
        full_name="Test Inventory Staff",
        role="INVENTORY_STAFF",
        active=True,
    )

    manager_user = models.User(
        full_name="Test Inventory Manager",
        role="INVENTORY_MANAGER",
        active=True,
    )

    product = models.Product(
        sku="MOVE-TEST-001",
        name="Movement Test Product",
        category="Electronics",
        unit_of_measure="unit",
        reorder_point=5,
        target_stock=20,
        active=True,
    )

    location = models.Location(
        code="MOVE-WH",
        name="Movement Test Warehouse",
        location_type="WAREHOUSE",
        active=True,
    )

    db_session.add_all(
        [
            staff_user,
            manager_user,
            product,
            location,
        ]
    )

    db_session.commit()

    db_session.refresh(staff_user)
    db_session.refresh(manager_user)
    db_session.refresh(product)
    db_session.refresh(location)

    inventory = models.Inventory(
        product_id=product.product_id,
        location_id=location.location_id,
        quantity_on_hand=10,
        reserved_quantity=2,
    )

    db_session.add(inventory)
    db_session.commit()
    db_session.refresh(inventory)

    return {
        "staff": staff_user,
        "manager": manager_user,
        "product": product,
        "location": location,
        "inventory": inventory,
    }


# =====================================================
# TEST 1
# INVENTORY STAFF CANNOT ISSUE STOCK
# =====================================================

def test_inventory_staff_cannot_issue_stock(
    db_session,
    stock_test_data,
):
    """
    INVENTORY_STAFF is not an authorized
    stock execution role.

    The stock movement must therefore fail.
    """

    data = stock_test_data

    movement = StockMovementCreate(
        product_id=(
            data["product"].product_id
        ),
        location_id=(
            data["location"].location_id
        ),
        movement_type="ISSUE",
        quantity=1,
        performed_by_user_id=(
            data["staff"].user_id
        ),
        reason="Unauthorized test issue",
        reference="TEST-UNAUTH-001",
    )

    with pytest.raises(
        PermissionError
    ):
        record_stock_movement(
            db=db_session,
            movement=movement,
        )

    db_session.rollback()

    inventory = db_session.get(
        models.Inventory,
        data["inventory"].inventory_id,
    )

    # Stock must remain unchanged.
    assert inventory.quantity_on_hand == 10
    assert inventory.reserved_quantity == 2

    movements = db_session.scalars(
        select(
            models.StockMovement
        )
    ).all()

    # Failed operation must not create
    # a movement record.
    assert len(movements) == 0


# =====================================================
# TEST 2
# MANAGER CAN ISSUE VALID STOCK
# =====================================================

def test_manager_can_issue_valid_stock(
    db_session,
    stock_test_data,
):
    """
    Initial inventory:

        On hand = 10
        Reserved = 2
        Available = 8

    Manager issues 3 units.

    Expected:

        On hand = 7
        Reserved = 2
        Available = 5
    """

    data = stock_test_data

    movement = StockMovementCreate(
        product_id=(
            data["product"].product_id
        ),
        location_id=(
            data["location"].location_id
        ),
        movement_type="ISSUE",
        quantity=3,
        performed_by_user_id=(
            data["manager"].user_id
        ),
        reason="Valid test issue",
        reference="TEST-VALID-001",
    )

    result = record_stock_movement(
        db=db_session,
        movement=movement,
    )

    db_session.refresh(
        data["inventory"]
    )

    assert (
        data["inventory"].quantity_on_hand
        == 7
    )

    assert (
        data["inventory"].reserved_quantity
        == 2
    )

    assert result.movement_type == "ISSUE"
    assert result.quantity == 3

    assert (
        result.previous_quantity
        == 10
    )

    assert (
        result.new_quantity
        == 7
    )

    assert (
        result.performed_by_user_id
        == data["manager"].user_id
    )


# =====================================================
# TEST 3
# CANNOT ISSUE MORE THAN AVAILABLE STOCK
# =====================================================

def test_issue_more_than_available_is_blocked(
    db_session,
    stock_test_data,
):
    """
    On hand = 10
    Reserved = 2

    Available = 8.

    An attempt to issue 9 units
    must therefore fail.
    """

    data = stock_test_data

    movement = StockMovementCreate(
        product_id=(
            data["product"].product_id
        ),
        location_id=(
            data["location"].location_id
        ),
        movement_type="ISSUE",
        quantity=9,
        performed_by_user_id=(
            data["manager"].user_id
        ),
        reason="Excessive issue test",
        reference="TEST-EXCESS-001",
    )

    with pytest.raises(
        ValueError
    ):
        record_stock_movement(
            db=db_session,
            movement=movement,
        )

    db_session.rollback()

    inventory = db_session.get(
        models.Inventory,
        data["inventory"].inventory_id,
    )

    # Inventory must still contain
    # its original values.
    assert inventory.quantity_on_hand == 10
    assert inventory.reserved_quantity == 2

    movements = db_session.scalars(
        select(
            models.StockMovement
        )
    ).all()

    # Failed transaction must not leave
    # a movement record behind.
    assert len(movements) == 0


# =====================================================
# TEST 4
# SUCCESSFUL MOVEMENT CREATES AUDIT TRAIL
# =====================================================

def test_successful_movement_creates_audit_trail(
    db_session,
    stock_test_data,
):
    """
    A successful stock movement must create:

    1. StockMovement history
    2. AuditLog history

    Both must identify the manager
    who performed the operation.
    """

    data = stock_test_data

    movement = StockMovementCreate(
        product_id=(
            data["product"].product_id
        ),
        location_id=(
            data["location"].location_id
        ),
        movement_type="ISSUE",
        quantity=2,
        performed_by_user_id=(
            data["manager"].user_id
        ),
        reason="Audit trail test",
        reference="TEST-AUDIT-001",
    )

    result = record_stock_movement(
        db=db_session,
        movement=movement,
    )

    stock_movements = db_session.scalars(
        select(
            models.StockMovement
        )
    ).all()

    audit_logs = db_session.scalars(
        select(
            models.AuditLog
        )
    ).all()

    assert len(stock_movements) == 1
    assert len(audit_logs) == 1

    stored_movement = (
        stock_movements[0]
    )

    audit = (
        audit_logs[0]
    )

    assert (
        stored_movement.movement_id
        == result.movement_id
    )

    assert (
        stored_movement.product_id
        == data["product"].product_id
    )

    assert (
        stored_movement.location_id
        == data["location"].location_id
    )

    assert (
        stored_movement.performed_by_user_id
        == data["manager"].user_id
    )

    assert (
        audit.user_id
        == data["manager"].user_id
    )

    assert (
        audit.entity_type
        is not None
    )

    assert (
        audit.action
        is not None
    )

    assert (
        audit.details
        is not None
    )