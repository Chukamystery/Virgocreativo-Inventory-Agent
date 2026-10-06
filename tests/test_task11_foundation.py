def test_products_endpoint_requires_authentication(
    client,
):
    """
    Product data must not be available
    to unauthenticated users.
    """

    response = client.get(
        "/products"
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail":
            "Authentication required."
    }


def test_products_endpoint_uses_test_database(
    authenticated_client,
):
    """
    An authenticated user should be able
    to access the products endpoint.

    The temporary test database starts empty,
    so the endpoint should return an empty list.
    """

    response = authenticated_client.get(
        "/products"
    )

    assert response.status_code == 200

    assert response.json() == []