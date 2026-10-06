import os

import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv()


# =====================================================
# SETTINGS
# =====================================================

def get_setting(
    name: str,
    default: str = "",
):
    """
    Read from Streamlit Cloud secrets first,
    then fall back to local environment variables.
    """

    try:
        value = st.secrets[name]

        if value:
            return str(value)

    except (KeyError, FileNotFoundError):
        pass

    return os.getenv(
        name,
        default,
    )


API_BASE_URL = get_setting(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


SUPABASE_URL = get_setting(
    "SUPABASE_URL",
).rstrip("/")


SUPABASE_PUBLISHABLE_KEY = get_setting(
    "SUPABASE_PUBLISHABLE_KEY",
)


# =====================================================
# CUSTOM ERROR
# =====================================================

class InventoryAPIError(Exception):
    pass


# =====================================================
# GENERIC API REQUEST
# =====================================================

def api_request(
    method: str,
    endpoint: str,
    **kwargs,
):
    url = f"{API_BASE_URL}{endpoint}"

    headers = dict(
        kwargs.pop(
            "headers",
            {},
        )
    )

    # Automatically attach the logged-in user's token.
    access_token = st.session_state.get(
        "access_token"
    )

    if access_token:
        headers.setdefault(
            "Authorization",
            f"Bearer {access_token}",
        )

    try:
        timeout = kwargs.pop(
            "timeout",
            90,
        )

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
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


# =====================================================
# AUTHENTICATION
# =====================================================

def login_user(
    email: str,
    password: str,
):
    """
    Authenticate with Supabase Auth.
    """

    if (
        not SUPABASE_URL
        or not SUPABASE_PUBLISHABLE_KEY
    ):
        raise InventoryAPIError(
            "Supabase authentication is not configured."
        )

    url = (
        f"{SUPABASE_URL}"
        "/auth/v1/token?grant_type=password"
    )

    try:
        response = requests.post(
            url,
            headers={
                "apikey":
                    SUPABASE_PUBLISHABLE_KEY,

                "Content-Type":
                    "application/json",
            },
            json={
                "email": email,
                "password": password,
            },
            timeout=30,
        )

    except requests.RequestException as exc:
        raise InventoryAPIError(
            "Could not connect to the authentication service."
        ) from exc

    try:
        data = response.json()

    except ValueError:
        data = {}

    if not response.ok:
        raise InventoryAPIError(
            data.get("error_description")
            or data.get("msg")
            or data.get("message")
            or "Login failed."
        )

    return data


def get_my_profile():
    """
    Return the Inventory Agent user linked
    to the authenticated Supabase account.
    """

    return api_request(
        method="GET",
        endpoint="/auth/me",
    )


# =====================================================
# PRODUCTS
# =====================================================

def get_products():
    return api_request(
        method="GET",
        endpoint="/products",
    )


# =====================================================
# INVENTORY
# =====================================================

def get_inventory():
    return api_request(
        method="GET",
        endpoint="/inventory",
    )


# =====================================================
# REORDER
# =====================================================

def get_low_stock():
    return api_request(
        method="GET",
        endpoint="/reorder/low-stock",
    )


# =====================================================
# ALERTS
# =====================================================

def get_alerts(
    status: str | None = None,
):
    endpoint = "/alerts"

    if status:
        endpoint += f"?status={status}"

    return api_request(
        method="GET",
        endpoint=endpoint,
    )


def resolve_alert(
    alert_id: int,
    user_id: int,
    comment: str | None = None,
):
    """
    user_id remains in the request body temporarily
    for schema compatibility.

    FastAPI now ignores it and uses the authenticated
    user's identity.
    """

    return api_request(
        method="POST",
        endpoint=f"/alerts/{alert_id}/resolve",
        json={
            "performed_by_user_id":
                user_id,

            "comment":
                comment,
        },
    )


def sync_low_stock_alerts():
    return api_request(
        method="POST",
        endpoint="/alerts/sync-low-stock",
    )


# =====================================================
# PURCHASE REQUESTS
# =====================================================

def get_purchase_requests():
    return api_request(
        method="GET",
        endpoint="/purchase-requests",
    )


def prepare_purchase_request(
    product_id: int,
    location_id: int,
    user_id: int,
    notes: str | None = None,
):
    """
    user_id remains temporarily for request-schema
    compatibility.

    The backend ignores it and uses the logged-in user.
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
                notes,
        },
    )


def submit_purchase_request(
    purchase_request_id: int,
    user_id: int,
    comment: str | None = None,
):
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
    comment: str | None = None,
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


# =====================================================
# INVENTORY AGENT
# =====================================================

def chat_with_agent(
    message: str,
    user_id: int,
):
    """
    user_id is retained temporarily for compatibility
    with the current Streamlit UI.

    FastAPI ignores it and identifies the real user
    from the Bearer token.
    """

    return api_request(
        method="POST",
        endpoint="/agent/chat",
        json={
            "message":
                message,

            "user_id":
                user_id,
        },
        timeout=90,
    )


# =====================================================
# STOCK MOVEMENTS
# =====================================================

def get_stock_movements():
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
                reference,
        },
    )


# =====================================================
# AUDIT LOG
# =====================================================

def get_audit_logs():
    return api_request(
        method="GET",
        endpoint="/audit-logs",
    )


# =====================================================
# HANDOFFS
# =====================================================

def get_handoffs(
    status: str | None = None,
):
    endpoint = "/handoffs"

    if status:
        endpoint += f"?status={status}"

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


# =====================================================
# LOOKUPS
# =====================================================

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


def get_supplier_options(
    product_id: int,
):
    return api_request(
        method="GET",
        endpoint=(
            f"/suppliers/product/"
            f"{product_id}"
        ),
    )