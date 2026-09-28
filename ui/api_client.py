import os

import requests
from dotenv import load_dotenv


load_dotenv()


API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


class InventoryAPIError(Exception):
    pass


def api_request(
    method: str,
    endpoint: str,
    **kwargs,
):
    url = f"{API_BASE_URL}{endpoint}"

    try:
        timeout = kwargs.pop("timeout", 10)

        response = requests.request(
            method=method,
            url=url,
            timeout=timeout,
            **kwargs,
        )

    except requests.RequestException as exc:
        raise InventoryAPIError(
            "Could not connect to the Inventory Agent API."
        ) from exc

    try:
        response_data = response.json()

    except ValueError:
        response_data = None

    if not response.ok:

        if (
            isinstance(response_data, dict)
            and response_data.get("detail")
        ):
            message = response_data["detail"]

        else:
            message = (
                "The Inventory Agent API "
                "returned an error."
            )

        raise InventoryAPIError(
            message
        )

    return response_data


def get_products():
    return api_request(
        method="GET",
        endpoint="/products",
    )

def get_inventory():
    """
    Retrieve current inventory balances.
    """

    return api_request(
        method="GET",
        endpoint="/inventory",
    )


def get_low_stock():
    """
    Retrieve current low-stock items and
    reorder recommendations.
    """

    return api_request(
        method="GET",
        endpoint="/reorder/low-stock",
    )


def get_alerts(
    status: str | None = None,
):
    """
    Retrieve alerts.

    Optionally filter by OPEN or RESOLVED.
    """

    endpoint = "/alerts"

    if status:
        endpoint += f"?status={status}"

    return api_request(
        method="GET",
        endpoint=endpoint,
    )


def get_purchase_requests():
    """
    Retrieve purchase requests.
    """

    return api_request(
        method="GET",
        endpoint="/purchase-requests",
    )

def chat_with_agent(
    message: str,
    user_id: int,
):
    """
    Send a user message to the Inventory Agent.
    """

    return api_request(
        method="POST",
        endpoint="/agent/chat",
        json={
            "message": message,
            "user_id": user_id,
        },
        timeout=60,
    )

def approve_purchase_request(
    purchase_request_id: int,
    user_id: int,
    comment: str | None = None,
):
    return api_request(
        method="POST",
        endpoint=(
            f"/purchase-requests/"
            f"{purchase_request_id}/approve"
        ),
        json={
            "performed_by_user_id":
                user_id,

            "comment":
                comment,
        },
    )


def reject_purchase_request(
    purchase_request_id: int,
    user_id: int,
    comment: str,
):
    return api_request(
        method="POST",
        endpoint=(
            f"/purchase-requests/"
            f"{purchase_request_id}/reject"
        ),
        json={
            "performed_by_user_id":
                user_id,

            "comment":
                comment,
        },
    )


def resolve_alert(
    alert_id: int,
    user_id: int,
    comment: str | None = None,
):
    return api_request(
        method="POST",
        endpoint=(
            f"/alerts/"
            f"{alert_id}/resolve"
        ),
        json={
            "performed_by_user_id":
                user_id,

            "comment":
                comment,
        },
    )


def get_handoffs(
    status: str | None = None,
):
    endpoint = "/handoffs"

    if status:
        endpoint += (
            f"?status={status}"
        )

    return api_request(
        method="GET",
        endpoint=endpoint,
    )


def resolve_handoff(
    handoff_id: int,
    user_id: int,
    resolution_note: str,
):
    return api_request(
        method="POST",
        endpoint=(
            f"/handoffs/"
            f"{handoff_id}/resolve"
        ),
        json={
            "performed_by_user_id":
                user_id,

            "resolution_note":
                resolution_note,
        },
    )

def get_stock_movements():
    """
    Retrieve stock movement history.
    """

    return api_request(
        method="GET",
        endpoint="/stock-movements",
    )


def record_stock_movement(
    product_id: int,
    location_id: int,
    movement_type: str,
    quantity: int,
    user_id: int,
    reason: str,
    reference: str | None = None,
):
    """
    Record a controlled inventory movement
    through FastAPI.
    """

    return api_request(
        method="POST",
        endpoint="/stock-movements",
        json={
            "product_id":
                product_id,

            "location_id":
                location_id,

            "movement_type":
                movement_type,

            "quantity":
                quantity,

            "performed_by_user_id":
                user_id,

            "reason":
                reason,

            "reference":
                reference or None,
        },
    )

def get_locations():
    return api_request(
        method="GET",
        endpoint="/lookups/locations",
    )


def get_suppliers():
    return api_request(
        method="GET",
        endpoint="/lookups/suppliers",
    )

def get_audit_logs():
    """
    Retrieve the system audit trail.
    """

    return api_request(
        method="GET",
        endpoint="/audit-logs",
    )

def get_supplier_options(
    product_id: int,
):
    """
    Retrieve approved supplier options
    for a product.
    """

    return api_request(
        method="GET",
        endpoint=(
            f"/suppliers/product/"
            f"{product_id}"
        ),
    )


def prepare_purchase_request(
    product_id: int,
    location_id: int,
    user_id: int,
    notes: str | None = None,
):
    """
    Prepare a replenishment purchase request.

    The backend calculates the reorder quantity
    and selects the appropriate supplier.
    """

    return api_request(
        method="POST",
        endpoint="/purchase-requests/prepare",
        json={
            "product_id":
                product_id,

            "location_id":
                location_id,

            "requested_by_user_id":
                user_id,

            "notes":
                notes or None,
        },
    )


def submit_purchase_request(
    purchase_request_id: int,
    user_id: int,
    comment: str | None = None,
):
    """
    Submit a draft purchase request
    for management approval.
    """

    return api_request(
        method="POST",
        endpoint=(
            f"/purchase-requests/"
            f"{purchase_request_id}/submit"
        ),
        json={
            "performed_by_user_id":
                user_id,

            "comment":
                comment,
        },
    )