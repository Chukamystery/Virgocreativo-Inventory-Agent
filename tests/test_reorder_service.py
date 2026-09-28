from app import models
from app.services.reorder_service import (
    get_reorder_recommendation,
)


def test_database_backed_reorder_recommendation(
    db_session,
):
    """
    Test the complete reorder service using
    real records inside the isolated test DB.
    """

    # -----------------------------------------
    # CREATE PRODUCT
    # -----------------------------------------

    product = models.Product(
        sku="REORDER-001",
        name="Test Wireless Mouse",
        category="Electronics",
        unit_of_measure="unit",
        reorder_point=15,
        target_stock=50,
        active=True,
    )

    # -----------------------------------------
    # CREATE LOCATION
    # -----------------------------------------

    location = models.Location(
        code="TEST-MAIN",
        name="Test Main Warehouse",
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

    # -----------------------------------------
    # CREATE INVENTORY
    # -----------------------------------------

    inventory = models.Inventory(
        product_id=product.product_id,
        location_id=location.location_id,
        quantity_on_hand=10,
        reserved_quantity=2,
    )

    db_session.add(inventory)
    db_session.commit()

    # -----------------------------------------
    # CALL THE REAL SERVICE
    # -----------------------------------------

    result = get_reorder_recommendation(
        db=db_session,
        product_id=product.product_id,
        location_id=location.location_id,
    )

    # -----------------------------------------
    # VERIFY RESULT
    # -----------------------------------------

    assert result[
        "product_id"
    ] == product.product_id

    assert result[
        "location_id"
    ] == location.location_id

    assert result[
        "quantity_on_hand"
    ] == 10

    assert result[
        "reserved_quantity"
    ] == 2

    # Available = 10 - 2
    assert result[
        "available_quantity"
    ] == 8

    assert result[
        "reorder_point"
    ] == 15

    assert result[
        "target_stock"
    ] == 50

    assert result[
        "is_low_stock"
    ] is True

    # Target 50 - available 8
    assert result[
        "recommended_reorder_quantity"
    ] == 42