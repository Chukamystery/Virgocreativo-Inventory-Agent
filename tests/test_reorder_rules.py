from app.services.reorder_service import (
    calculate_reorder_quantity,
    is_low_stock,
)


def test_stock_above_reorder_point_is_not_low():
    """
    Available quantity above the reorder point
    should NOT be considered low stock.
    """

    available_quantity = 16
    reorder_point = 15
    target_stock = 50

    low_stock = is_low_stock(
        available_quantity,
        reorder_point,
    )

    reorder_quantity = (
        calculate_reorder_quantity(
            available_quantity,
            reorder_point,
            target_stock,
        )
    )

    assert low_stock is False
    assert reorder_quantity == 0


def test_stock_equal_to_reorder_point_is_low():
    """
    Boundary test:

    available == reorder_point

    Our business rule uses <=,
    so this MUST trigger low stock.
    """

    available_quantity = 15
    reorder_point = 15
    target_stock = 50

    low_stock = is_low_stock(
        available_quantity,
        reorder_point,
    )

    reorder_quantity = (
        calculate_reorder_quantity(
            available_quantity,
            reorder_point,
            target_stock,
        )
    )

    assert low_stock is True

    # 50 target - 15 available
    assert reorder_quantity == 35


def test_stock_below_reorder_point_is_low():
    """
    Stock below the reorder point should trigger
    a reorder recommendation.
    """

    available_quantity = 8
    reorder_point = 15
    target_stock = 50

    low_stock = is_low_stock(
        available_quantity,
        reorder_point,
    )

    reorder_quantity = (
        calculate_reorder_quantity(
            available_quantity,
            reorder_point,
            target_stock,
        )
    )

    assert low_stock is True

    # 50 target - 8 available
    assert reorder_quantity == 42


def test_zero_available_stock_reorders_to_target():
    """
    If no stock is available, reorder enough
    to reach the target stock level.
    """

    available_quantity = 0
    reorder_point = 15
    target_stock = 50

    low_stock = is_low_stock(
        available_quantity,
        reorder_point,
    )

    reorder_quantity = (
        calculate_reorder_quantity(
            available_quantity,
            reorder_point,
            target_stock,
        )
    )

    assert low_stock is True
    assert reorder_quantity == 50