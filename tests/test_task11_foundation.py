def test_products_endpoint_uses_test_database(
    client,
):
    """
    The temporary database starts empty.

    Therefore GET /products should work
    successfully and return an empty list.
    """

    response = client.get(
        "/products"
    )

    assert response.status_code == 200

    assert response.json() == []