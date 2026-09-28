import pytest

from sqlalchemy.exc import IntegrityError

from app import models
from app.services.reorder_service import (
    calculate_available_quantity,
)


@pytest.fixture()
def sample_product_and_location(
    db_session,
):
    """
    Create one valid product and location
    inside the temporary test database.
    """

    product = models.Product(
        sku="TEST-001",
        name="Test Wireless Mouse",
        category="Electronics",
        unit_of_measure="unit",
        reorder_point=15,
        target_stock=50,
        active=True,
    )

    location = models.Location(
        code="TEST-WH",
        name="Test Warehouse",
        location_type="WAREHOUSE",
        active=True,
    )

    db_session.add_all(
        [
            product,
            location,
        ]
    )

    db_session.commit()

    db_session.refresh(product)
    db_session.refresh(location)

    return product, location


def test_available_quantity_calculation():
    """
    Available quantity must equal:

    quantity_on_hand - reserved_quantity
    """

    result = calculate_available_quantity(
        12,
        2,
    )

    assert result == 10


def test_valid_inventory_record_is_accepted(
    db_session,
    sample_product_and_location,
):
    """
    A valid inventory record should save.
    """

    product, location = (
        sample_product_and_location
    )

    inventory = models.Inventory(
        product_id=product.product_id,
        location_id=location.location_id,
        quantity_on_hand=8,
        reserved_quantity=2,
    )

    db_session.add(inventory)
    db_session.commit()
    db_session.refresh(inventory)

    assert inventory.quantity_on_hand == 8
    assert inventory.reserved_quantity == 2

    available = calculate_available_quantity(
        inventory.quantity_on_hand,
        inventory.reserved_quantity,
    )

    assert available == 6


def test_negative_on_hand_quantity_is_blocked(
    db_session,
    sample_product_and_location,
):
    """
    Negative physical stock must be rejected.
    """

    product, location = (
        sample_product_and_location
    )

    inventory = models.Inventory(
        product_id=product.product_id,
        location_id=location.location_id,
        quantity_on_hand=-1,
        reserved_quantity=0,
    )

    db_session.add(inventory)

    with pytest.raises(
        IntegrityError
    ):
        db_session.commit()

    db_session.rollback()


def test_reserved_quantity_cannot_exceed_on_hand(
    db_session,
    sample_product_and_location,
):
    """
    Reserved stock cannot exceed
    physical stock.
    """

    product, location = (
        sample_product_and_location
    )

    inventory = models.Inventory(
        product_id=product.product_id,
        location_id=location.location_id,
        quantity_on_hand=5,
        reserved_quantity=6,
    )

    db_session.add(inventory)

    with pytest.raises(
        IntegrityError
    ):
        db_session.commit()

    db_session.rollback()