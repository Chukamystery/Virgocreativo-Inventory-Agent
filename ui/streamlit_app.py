import json
import pandas as pd
import streamlit as st

from api_client import (
    API_BASE_URL,
    InventoryAPIError,
    approve_purchase_request,
    chat_with_agent,
    get_alerts,
    get_audit_logs,
    get_handoffs,
    get_inventory,
    get_locations,
    get_low_stock,
    get_my_profile,
    get_products,
    get_purchase_requests,
    get_stock_movements,
    get_supplier_options,
    get_suppliers,
    get_users,
    login_user,
    prepare_purchase_request,
    record_stock_movement,
    reject_purchase_request,
    resolve_alert,
    resolve_handoff,
    submit_purchase_request,
)


# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Virgocreativo Inventory Agent",
    page_icon="📦",
    layout="wide",
)

# =====================================================
# DASHBOARD STYLING
# =====================================================

st.markdown(
    """
    <style>

    /* Main page spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    /* Main heading */
    h1 {
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    /* Section headings */
    h2, h3 {
        font-weight: 600;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: rgba(120, 120, 120, 0.06);
        border: 1px solid rgba(120, 120, 120, 0.15);
        padding: 18px;
        border-radius: 12px;
    }

    /* Metric values */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
    }

    /* Tabs */
    button[data-baseweb="tab"] {
        font-weight: 600;
    }

    /* Buttons */
    .stButton > button,
    .stFormSubmitButton > button {
        border-radius: 8px;
        font-weight: 600;
    }

    /* Dataframe */
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(120, 120, 120, 0.15);
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================================
# AUTHENTICATION
# =====================================================

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "current_user" not in st.session_state:
    st.session_state.current_user = None


def logout():
    """
    Clear the authenticated Streamlit session.

    Clearing all session state also prevents one user
    from seeing another user's cached chat/widget state
    after logout on the same browser.
    """
    st.session_state.clear()
    st.rerun()


# -----------------------------------------------------
# LOGIN SCREEN
# -----------------------------------------------------

if not st.session_state.access_token:

    st.markdown(
        "# 📦 Virgocreativo Inventory Agent"
    )

    st.markdown(
        """
        **Secure access to inventory operations,
        procurement and AI assistance.**
        """
    )

    st.divider()

    login_col, _ = st.columns(
        [1, 1]
    )

    with login_col:

        st.subheader(
            "Sign in"
        )

        with st.form(
            "login_form"
        ):

            email = st.text_input(
                "Email"
            )

            password = st.text_input(
                "Password",
                type="password",
            )

            submitted = st.form_submit_button(
                "Sign in",
                use_container_width=True,
            )

        if submitted:

            if (
                not email.strip()
                or not password
            ):
                st.error(
                    "Enter your email and password."
                )

            else:
                try:
                    auth_data = login_user(
                        email=email.strip(),
                        password=password,
                    )

                    access_token = (
                        auth_data.get(
                            "access_token"
                        )
                    )

                    if not access_token:
                        raise InventoryAPIError(
                            "Login succeeded but no access token was returned."
                        )

                    st.session_state.access_token = (
                        access_token
                    )

                    profile = get_my_profile()

                    st.session_state.current_user = (
                        profile
                    )

                    st.rerun()

                except InventoryAPIError as exc:

                    st.session_state.access_token = None
                    st.session_state.current_user = None

                    st.error(
                        str(exc)
                    )

    st.stop()


# -----------------------------------------------------
# RESTORE USER PROFILE IF NEEDED
# -----------------------------------------------------

if (
    st.session_state.access_token
    and not st.session_state.current_user
):
    try:
        st.session_state.current_user = (
            get_my_profile()
        )

    except InventoryAPIError:
        st.session_state.access_token = None
        st.session_state.current_user = None

        st.error(
            "Your session is no longer valid. "
            "Please sign in again."
        )

        st.stop()


current_user = (
    st.session_state.current_user
)

if not current_user:
    st.session_state.access_token = None
    st.error(
        "Unable to identify the signed-in user. "
        "Please sign in again."
    )
    st.stop()

# The acting user now comes only from the verified
# /auth/me response. There is no manual user selector.
acting_user_id = (
    current_user["user_id"]
)


# =====================================================
# HEADER
# =====================================================

st.markdown(
    """
    # 📦 Virgocreativo Inventory Agent
    """
)

st.markdown(
    """
    **AI-assisted inventory operations, procurement,
    approvals and exception management.**
    """
)

st.caption(
    "Live operational data • Controlled AI actions • "
    "Human-in-the-loop governance"
)

st.divider()


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.markdown(
        "## 📦 Inventory Agent"
    )

    st.caption(
        "Virgocreativo Business Systems & AI"
    )

    st.divider()
    st.write(
        "Backend API"
    )

    st.success(
    "● Backend connected"
)

    st.code(
        API_BASE_URL
    )

    st.divider()

    st.subheader(
        "Signed in user"
    )

    display_role = (
    current_user.get("business_role")
    or current_user["role"]
        .replace("_", " ")
        .title()
)

role_descriptions = {
    "Inventory Staff":
        "Handles day-to-day inventory activities.",

    "Inventory Manager":
        "Manages stock movements and inventory operations.",

    "Procurement Officer":
        "Prepares and submits purchase requests.",

    "Approver / Manager":
        "Reviews and approves or rejects purchase requests.",

    "Administrator":
        "Oversees system administration and operations.",
}

st.write(
    f"**{current_user['full_name']}**"
)

st.markdown(
    f"### {display_role}"
)

st.caption(
    role_descriptions.get(
        display_role,
        "Authorized Inventory Agent user.",
    )
)

st.caption(
    f"System access: {current_user['role']}"
)

st.divider()

if st.button(
    "Log out",
    use_container_width=True,
):
    logout()

if st.button(
    "🔄 Refresh Dashboard",
    use_container_width=True,
):
    st.rerun()


# =====================================================
# LOAD DATA
# =====================================================

try:

    products = get_products()

    inventory = get_inventory()

    audit_logs = get_audit_logs()

    low_stock_payload = (
        get_low_stock()
    )

    open_alerts = get_alerts(
        "OPEN"
    )

    purchase_requests = (
        get_purchase_requests()
    )

    open_handoffs = get_handoffs(
        "OPEN"
    )

    stock_movements = (
        get_stock_movements()
    )

    locations = get_locations()
    
    suppliers = get_suppliers()

    users = get_users()

except InventoryAPIError as exc:

    st.error(
        str(exc)
    )

    st.warning(
        "The Inventory Agent backend is currently unavailable. "
        "Please wait a moment and try again."
    )

    st.stop()


# =====================================================
# DATA PREPARATION
# =====================================================

low_stock_items = (
    low_stock_payload.get(
        "items",
        [],
    )
)

low_stock_count = (
    low_stock_payload.get(
        "low_stock_count",
        len(low_stock_items),
    )
)


# -----------------------------------------------------
# PRODUCT LOOKUP
# -----------------------------------------------------

product_map = {
    product["product_id"]:
        product
    for product in products
}


# -----------------------------------------------------
# LOCATION LOOKUP
#
# Our current inventory endpoint returns
# location IDs but not location names.
#
# Low-stock results contain the names,
# so we use those when available.
# -----------------------------------------------------

location_map = {
    location["location_id"]:
        location["name"]
    for location in locations
}


supplier_map = {
    supplier["supplier_id"]:
        supplier["name"]
    for supplier in suppliers
}

# =====================================================
# USER NAME LOOKUP
# =====================================================

# Human-readable names for the seeded business users.
# These are display labels only; authorization never
# depends on this mapping.
user_name_map = {
    user["user_id"]:
        user["full_name"]
    for user in users
}

# Keep the currently authenticated user available
# as a fallback.
user_name_map[
    current_user["user_id"]
] = current_user["full_name"]

# -----------------------------------------------------
# LOW STOCK LOOKUP
# -----------------------------------------------------

low_stock_by_inventory = {
    item["inventory_id"]:
        item
    for item in low_stock_items
}


# -----------------------------------------------------
# INVENTORY TABLE
# -----------------------------------------------------

inventory_rows = []

for record in inventory:

    product = product_map.get(
        record["product_id"],
        {},
    )

    low_stock_record = (
        low_stock_by_inventory.get(
            record["inventory_id"]
        )
    )

    available_quantity = (
        record["quantity_on_hand"]
        - record["reserved_quantity"]
    )

    if low_stock_record:

        status = "LOW STOCK"

        reorder_quantity = (
            low_stock_record[
                "recommended_reorder_quantity"
            ]
        )

    else:

        status = "OK"

        reorder_quantity = 0

    inventory_rows.append(
        {
            "Inventory ID":
                record["inventory_id"],

            "SKU":
                product.get(
                    "sku",
                    f"Product {record['product_id']}",
                ),

            "Product":
                product.get(
                    "name",
                    f"Product {record['product_id']}",
                ),

            "Location":
                location_map.get(
                    record["location_id"],
                    f"Location {record['location_id']}",
                ),

            "On Hand":
                record[
                    "quantity_on_hand"
                ],

            "Reserved":
                record[
                    "reserved_quantity"
                ],

            "Available":
                available_quantity,

            "Status":
                status,

            "Recommended Reorder":
                reorder_quantity,
        }
    )


inventory_df = pd.DataFrame(
    inventory_rows
)


# -----------------------------------------------------
# PURCHASE REQUEST METRICS
# -----------------------------------------------------

pending_approvals = [
    pr
    for pr in purchase_requests
    if pr["status"]
    == "PENDING_APPROVAL"
]


approved_requests = [
    pr
    for pr in purchase_requests
    if pr["status"]
    == "APPROVED"
]


rejected_requests = [
    pr
    for pr in purchase_requests
    if pr["status"]
    == "REJECTED"
]


# -----------------------------------------------------
# STOCK TOTALS
# -----------------------------------------------------

total_on_hand = sum(
    item["quantity_on_hand"]
    for item in inventory
)

total_reserved = sum(
    item["reserved_quantity"]
    for item in inventory
)

total_available = (
    total_on_hand
    - total_reserved
)


# =====================================================
# CONNECTION STATUS
# =====================================================

st.success(
    "Inventory Agent API connected."
)


# =====================================================
# KPI CARDS
# =====================================================

st.subheader(
    "Operations Overview"
)

st.caption(
    "Live operational health across inventory, "
    "alerts and procurement workflows."
)

col1, col2, col3, col4 = (
    st.columns(4)
)

with col1:

    st.metric(
        label="Products",
        value=len(products),
    )

with col2:

    st.metric(
        label="Low Stock",
        value=low_stock_count,
    )

with col3:

    st.metric(
        label="Open Alerts",
        value=len(open_alerts),
    )

with col4:

    st.metric(
        label="Pending Approvals",
        value=len(
            pending_approvals
        ),
    )


col5, col6, col7, col8 = (
    st.columns(4)
)

with col5:

    st.metric(
        label="On Hand",
        value=total_on_hand,
    )

with col6:

    st.metric(
        label="Reserved",
        value=total_reserved,
    )

with col7:

    st.metric(
        label="Available",
        value=total_available,
    )

with col8:

    st.metric(
        label="Inventory Records",
        value=len(inventory),
    )


# =====================================================
# MAIN DASHBOARD TABS
# =====================================================

(
    overview_tab,
    inventory_tab,
    low_stock_tab,
    alerts_tab,
    procurement_tab,
    assistant_tab,
    actions_tab,
    movements_tab,
    activity_tab,
) = st.tabs(
    [
        "🏠 Overview",
        "📦 Inventory",
        "⚠️ Reorder",
        "🔔 Exceptions",
        "🧾 Procurement",
        "🤖 AI Assistant",
        "✅ Approvals",
        "🔁 Stock Movements",
        "📜 Activity Log",
    ]
)


# =====================================================
# OVERVIEW TAB
# =====================================================

with overview_tab:

    st.markdown(
        "### System Status"
    )

    status1, status2, status3, status4 = (
        st.columns(4)
    )

    with status1:
        st.success(
            "Inventory API\n\nOnline"
        )

    with status2:
        st.success(
            "Rules Engine\n\nActive"
        )

    with status3:
        st.success(
            "AI Assistant\n\nAvailable"
        )

    with status4:

        if open_alerts:
            st.warning(
                f"Exceptions\n\n"
                f"{len(open_alerts)} Open"
            )
        else:
            st.success(
                "Exceptions\n\nNone"
            )

    st.divider()

    st.subheader(
        "Items Requiring Attention"
    )

    if low_stock_items:

        attention_rows = []

        for item in low_stock_items:

            attention_rows.append(
                {
                    "Product":
                        item[
                            "product_name"
                        ],

                    "Location":
                        item[
                            "location_name"
                        ],

                    "Available":
                        item[
                            "available_quantity"
                        ],

                    "Reorder Point":
                        item[
                            "reorder_point"
                        ],

                    "Recommended Reorder":
                        item[
                            "recommended_reorder_quantity"
                        ],
                }
            )

        st.dataframe(
            pd.DataFrame(
                attention_rows
            ),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.success(
            "No low-stock items "
            "require attention."
        )


    st.subheader(
        "Workflow Status"
    )

    workflow_col1, workflow_col2, workflow_col3 = (
        st.columns(3)
    )

    with workflow_col1:

        st.metric(
            "Approved Requests",
            len(
                approved_requests
            ),
        )

    with workflow_col2:

        st.metric(
            "Pending Approval",
            len(
                pending_approvals
            ),
        )

    with workflow_col3:

        st.metric(
            "Rejected Requests",
            len(
                rejected_requests
            ),
        )


    st.subheader(
        "Open Exceptions"
    )

    if open_alerts:

        for alert in open_alerts[:5]:

            st.warning(
                f"{alert['alert_type']} — "
                f"{alert['message']}"
            )

    else:

        st.success(
            "No open alerts."
        )


# =====================================================
# INVENTORY TAB
# =====================================================

with inventory_tab:

    st.subheader(
        "Live Inventory"
    )

    st.caption(
        "Available = On Hand - Reserved"
    )

    if not inventory_df.empty:

        status_filter = (
            st.selectbox(
                "Filter inventory",
                [
                    "All",
                    "LOW STOCK",
                    "OK",
                ],
            )
        )

        filtered_inventory = (
            inventory_df
        )

        if status_filter != "All":

            filtered_inventory = (
                inventory_df[
                    inventory_df[
                        "Status"
                    ]
                    == status_filter
                ]
            )

        st.dataframe(
            filtered_inventory,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No inventory records found."
        )


# =====================================================
# LOW STOCK TAB
# =====================================================

with low_stock_tab:

    st.subheader(
        "Low-Stock & Reorder Recommendations"
    )

    st.caption(
        "These recommendations are calculated "
        "by deterministic backend rules."
    )

    if low_stock_items:

        low_stock_rows = []

        for item in low_stock_items:

            low_stock_rows.append(
                {
                    "SKU":
                        item["sku"],

                    "Product":
                        item[
                            "product_name"
                        ],

                    "Location":
                        item[
                            "location_name"
                        ],

                    "On Hand":
                        item[
                            "quantity_on_hand"
                        ],

                    "Reserved":
                        item[
                            "reserved_quantity"
                        ],

                    "Available":
                        item[
                            "available_quantity"
                        ],

                    "Reorder Point":
                        item[
                            "reorder_point"
                        ],

                    "Target Stock":
                        item[
                            "target_stock"
                        ],

                    "Recommended Reorder":
                        item[
                            "recommended_reorder_quantity"
                        ],
                }
            )

        st.dataframe(
            pd.DataFrame(
                low_stock_rows
            ),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.success(
            "All inventory items are "
            "above their reorder thresholds."
        )


# =====================================================
# ALERTS TAB
# =====================================================

with alerts_tab:

    st.subheader(
        "Open Alerts"
    )

    st.caption(
        "Operational exceptions requiring "
        "attention."
    )

    if open_alerts:

        alert_rows = []

        for alert in open_alerts:

            alert_rows.append(
                {
                    "Alert ID":
                        alert[
                            "alert_id"
                        ],

                    "Type":
                        alert[
                            "alert_type"
                        ],

                    "Severity":
                        alert[
                            "severity"
                        ],

                    "Message":
                        alert[
                            "message"
                        ],

                    "Entity":
                        alert[
                            "entity_type"
                        ],

                    "Entity ID":
                        alert[
                            "entity_id"
                        ],

                    "Status":
                        alert[
                            "status"
                        ],

                    "Created":
                        alert[
                            "created_at"
                        ],
                }
            )

        alerts_df = (
            pd.DataFrame(
                alert_rows
            )
        )

        alert_type_options = [
            "All"
        ] + sorted(
            alerts_df[
                "Type"
            ].unique().tolist()
        )

        selected_alert_type = (
            st.selectbox(
                "Alert type",
                alert_type_options,
            )
        )

        if (
            selected_alert_type
            != "All"
        ):

            alerts_df = (
                alerts_df[
                    alerts_df["Type"]
                    == selected_alert_type
                ]
            )

        st.dataframe(
            alerts_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.success(
            "No open operational alerts."
        )


# =====================================================
# PURCHASE REQUEST TAB
# =====================================================

with procurement_tab:

        # =================================================
    # PROCUREMENT WORKFLOW
    # =================================================

    st.subheader(
        "Replenishment Workflow"
    )

    st.caption(
        "Create purchase requests directly from "
        "verified low-stock recommendations."
    )

    st.info(
        f"Signed in as: {current_user['full_name']} "
        f"({current_user['role']})"
    )


    # =================================================
    # PREPARE PURCHASE REQUEST
    # =================================================

    st.markdown(
        "### 1. Prepare Purchase Request"
    )

    if low_stock_items:

        procurement_options = {}

        for item in low_stock_items:

            label = (
                f"{item['product_name']} | "
                f"{item['location_name']} | "
                f"Available: "
                f"{item['available_quantity']} | "
                f"Recommended: "
                f"{item['recommended_reorder_quantity']}"
            )

            procurement_options[
                label
            ] = item


        selected_procurement_label = (
            st.selectbox(
                "Select low-stock item",
                options=list(
                    procurement_options.keys()
                ),
                key="procurement_item",
            )
        )


        selected_reorder_item = (
            procurement_options[
                selected_procurement_label
            ]
        )


        # ---------------------------------------------
        # REORDER INFORMATION
        # ---------------------------------------------

        p_col1, p_col2, p_col3, p_col4 = (
            st.columns(4)
        )

        with p_col1:

            st.metric(
                "Available",
                selected_reorder_item[
                    "available_quantity"
                ],
            )

        with p_col2:

            st.metric(
                "Reorder Point",
                selected_reorder_item[
                    "reorder_point"
                ],
            )

        with p_col3:

            st.metric(
                "Target Stock",
                selected_reorder_item[
                    "target_stock"
                ],
            )

        with p_col4:

            st.metric(
                "Recommended Order",
                selected_reorder_item[
                    "recommended_reorder_quantity"
                ],
            )


        # ---------------------------------------------
        # SUPPLIER OPTIONS
        # ---------------------------------------------

        st.markdown(
            "#### Supplier Options"
        )

        supplier_options = []

        try:

            supplier_options = (
                get_supplier_options(
                    selected_reorder_item[
                        "product_id"
                    ]
                )
            )

            if supplier_options:

                supplier_options_df = (
                    pd.DataFrame(
                        supplier_options
                    )
                )

                st.dataframe(
                    supplier_options_df,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.warning(
                    "No approved supplier options "
                    "were found for this product."
                )

        except InventoryAPIError as exc:

            st.error(
                f"Could not load supplier options: "
                f"{exc}"
            )


        # ---------------------------------------------
        # CHECK FOR OPEN REQUEST
        # ---------------------------------------------

        existing_open_request = None

        for request in purchase_requests:

            if request["status"] not in {
                "DRAFT",
                "PENDING_APPROVAL",
            }:
                continue

            for line in request.get(
                "lines",
                [],
            ):

                same_product = (
                    line["product_id"]
                    == selected_reorder_item[
                        "product_id"
                    ]
                )

                same_location = (
                    line["location_id"]
                    == selected_reorder_item[
                        "location_id"
                    ]
                )

                if (
                    same_product
                    and same_location
                ):

                    existing_open_request = (
                        request
                    )

                    break

            if existing_open_request:
                break


        if existing_open_request:

            st.warning(
                "An open purchase request already "
                "exists for this product and "
                "location: "
                f"{existing_open_request['request_number']} "
                f"({existing_open_request['status']})."
            )


        procurement_notes = st.text_area(
            "Purchase request notes",
            placeholder=(
                "Example: Replenishment based on "
                "low-stock recommendation."
            ),
            key="procurement_notes",
        )


        if st.button(
            "Prepare Purchase Request",
            key="prepare_purchase_request_button",
            use_container_width=True,
            disabled=(
                existing_open_request
                is not None
            ),
        ):

            try:

                prepared_request = (
                    prepare_purchase_request(
                        product_id=(
                            selected_reorder_item[
                                "product_id"
                            ]
                        ),
                        location_id=(
                            selected_reorder_item[
                                "location_id"
                            ]
                        ),
                        user_id=(
                            acting_user_id
                        ),
                        notes=(
                            procurement_notes.strip()
                            if procurement_notes
                            else None
                        ),
                    )
                )

                st.success(
                    "Purchase request prepared "
                    "successfully."
                )

                st.json(
                    prepared_request
                )

                st.rerun()

            except InventoryAPIError as exc:

                st.error(
                    str(exc)
                )

    else:

        st.success(
            "There are currently no low-stock "
            "items requiring replenishment."
        )


    st.divider()


    # =================================================
    # SUBMIT DRAFT PURCHASE REQUESTS
    # =================================================

    st.markdown(
        "### 2. Submit Draft for Approval"
    )

    draft_requests = [
        request
        for request in purchase_requests
        if request["status"] == "DRAFT"
    ]


    if draft_requests:

        for request in draft_requests:

            request_id = (
                request[
                    "purchase_request_id"
                ]
            )

            request_number = (
                request[
                    "request_number"
                ]
            )

            with st.expander(
                f"{request_number} — DRAFT"
            ):

                supplier_name = (
                    supplier_map.get(
                        request[
                            "supplier_id"
                        ],
                        (
                            f"Supplier "
                            f"{request['supplier_id']}"
                        ),
                    )
                )

                requester_name = (
                    user_name_map.get(
                        request[
                            "requested_by_user_id"
                        ],
                        (
                            f"User "
                            f"{request['requested_by_user_id']}"
                        ),
                    )
                )

                st.write(
                    f"**Supplier:** "
                    f"{supplier_name}"
                )

                st.write(
                    f"**Requested By:** "
                    f"{requester_name}"
                )

                st.write(
                    f"**Notes:** "
                    f"{request.get('notes') or '-'}"
                )


                lines = request.get(
                    "lines",
                    [],
                )

                if lines:

                    draft_line_rows = []

                    for line in lines:

                        draft_line_rows.append(
                            {
                                "Product":
                                    product_map.get(
                                        line[
                                            "product_id"
                                        ],
                                        {},
                                    ).get(
                                        "name",
                                        (
                                            f"Product "
                                            f"{line['product_id']}"
                                        ),
                                    ),

                                "Location":
                                    location_map.get(
                                        line[
                                            "location_id"
                                        ],
                                        (
                                            f"Location "
                                            f"{line['location_id']}"
                                        ),
                                    ),

                                "Quantity":
                                    line[
                                        "quantity"
                                    ],

                                "Recommended":
                                    line[
                                        "reorder_recommendation"
                                    ],

                                "MOQ":
                                    line[
                                        "minimum_order_qty"
                                    ],

                                "Unit Cost":
                                    (
                                        f"₦"
                                        f"{line['unit_cost']:,.2f}"
                                    ),
                            }
                        )

                    st.dataframe(
                        pd.DataFrame(
                            draft_line_rows
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )


                submit_comment = (
                    st.text_input(
                        "Submission comment",
                        placeholder=(
                            "Example: Reviewed and "
                            "ready for approval."
                        ),
                        key=(
                            f"submit_comment_"
                            f"{request_id}"
                        ),
                    )
                )


                if st.button(
                    "Submit for Approval",
                    key=(
                        f"submit_pr_"
                        f"{request_id}"
                    ),
                    use_container_width=True,
                ):

                    try:

                        result = (
                            submit_purchase_request(
                                purchase_request_id=(
                                    request_id
                                ),
                                user_id=(
                                    acting_user_id
                                ),
                                comment=(
                                    submit_comment.strip()
                                    if submit_comment
                                    else (
                                        "Submitted from "
                                        "dashboard"
                                    )
                                ),
                            )
                        )

                        st.success(
                            "Purchase request submitted "
                            "for approval."
                        )

                        st.json(
                            result
                        )

                        st.rerun()

                    except InventoryAPIError as exc:

                        st.error(
                            str(exc)
                        )

    else:

        st.info(
            "No draft purchase requests are "
            "waiting for submission."
        )


    st.divider()

    st.subheader(
        "Purchase Requests"
    )

    if purchase_requests:

        purchase_rows = []

        for request in purchase_requests:

            lines = request.get(
                "lines",
                [],
            )

            if not lines:

                purchase_rows.append(
                    {
                        "PR ID":
                            request[
                                "purchase_request_id"
                            ],

                        "Request Number":
                            request[
                                "request_number"
                            ],

                        "Status":
                            request[
                                "status"
                            ],

                        "Supplier ID":
                            request[
                                "supplier_id"
                            ],

                        "Requested By":
                            request[
                                "requested_by_user_id"
                            ],

                        "Product ID":
                            None,

                        "Location ID":
                            None,

                        "Quantity":
                            None,

                        "Unit Cost":
                            None,

                        "Created":
                            request[
                                "created_at"
                            ],
                    }
                )

                continue

            for line in lines:

                purchase_rows.append(
                    {
                        "PR ID":
                            request[
                                "purchase_request_id"
                            ],

                        "Request Number":
                            request[
                                "request_number"
                            ],

                        "Status":
                            request[
                                "status"
                            ],

                        "Supplier ID":
                            request[
                                "supplier_id"
                            ],

                        "Requested By":
                            request[
                                "requested_by_user_id"
                            ],

                        "Product ID":
                            line[
                                "product_id"
                            ],

                        "Location ID":
                            line[
                                "location_id"
                            ],

                        "Quantity":
                            line[
                                "quantity"
                            ],

                        "Unit Cost":
    (
        f"₦{line['unit_cost']:,.2f}"
        if line["unit_cost"]
        is not None
        else "-"
    ),

                        "Created":
                            request[
                                "created_at"
                            ],
                    }
                )

        purchase_df = (
            pd.DataFrame(
                purchase_rows
            )
        )

        pr_status_options = [
            "All"
        ] + sorted(
            purchase_df[
                "Status"
            ].unique().tolist()
        )

        selected_pr_status = (
            st.selectbox(
                "Purchase request status",
                pr_status_options,
            )
        )

        if selected_pr_status != "All":

            purchase_df = (
                purchase_df[
                    purchase_df[
                        "Status"
                    ]
                    == selected_pr_status
                ]
            )

        st.dataframe(
            purchase_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No purchase requests found."
        )

# =====================================================
# AI ASSISTANT TAB
# =====================================================

with assistant_tab:

    st.subheader(
        "🤖 Inventory AI Assistant"
    )

    st.caption(
        "Ask about live inventory, reorder "
        "recommendations, suppliers, policies "
        "or request human escalation."
    )

    st.info(
        f"Signed in as: {current_user['full_name']} "
        f"({current_user['role']})"
    )

    # -------------------------------------------------
    # INITIALIZE CHAT HISTORY
    # -------------------------------------------------

    if (
        "inventory_chat_history"
        not in st.session_state
    ):
        st.session_state[
            "inventory_chat_history"
        ] = []

    # -------------------------------------------------
    # DISPLAY PREVIOUS MESSAGES
    # -------------------------------------------------

    for message in st.session_state[
        "inventory_chat_history"
    ]:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

            if (
                message.get(
                    "tools_used"
                )
            ):

                with st.expander(
                    "Tools used"
                ):

                    st.write(
                        message[
                            "tools_used"
                        ]
                    )

    # -------------------------------------------------
    # CHAT INPUT
    # -------------------------------------------------

    user_prompt = st.chat_input(
        "Ask the Inventory Agent..."
    )

    if user_prompt:

        # ---------------------------------------------
        # STORE AND DISPLAY USER MESSAGE
        # ---------------------------------------------

        st.session_state[
            "inventory_chat_history"
        ].append(
            {
                "role":
                    "user",

                "content":
                    user_prompt,
            }
        )

        with st.chat_message(
            "user"
        ):
            st.markdown(
                user_prompt
            )

        # ---------------------------------------------
        # CALL FASTAPI AGENT
        # ---------------------------------------------

        with st.chat_message(
            "assistant"
        ):

            with st.spinner(
                "Checking the inventory system..."
            ):

                try:

                    agent_response = (
                        chat_with_agent(
                            message=user_prompt,
                            user_id=acting_user_id,
                        )
                    )

                    answer = (
                        agent_response[
                            "answer"
                        ]
                    )

                    tools_used = (
                        agent_response.get(
                            "tools_used",
                            [],
                        )
                    )

                    st.markdown(
                        answer
                    )

                    if tools_used:

                        with st.expander(
                            "Tools used"
                        ):

                            for tool in tools_used:
                                st.write(
                                    f"• {tool}"
                                )

                    st.session_state[
                        "inventory_chat_history"
                    ].append(
                        {
                            "role":
                                "assistant",

                            "content":
                                answer,

                            "tools_used":
                                tools_used,
                        }
                    )

                except InventoryAPIError as exc:

                    error_message = (
                        f"Unable to complete "
                        f"the request: {exc}"
                    )

                    st.error(
                        error_message
                    )

                    st.session_state[
                        "inventory_chat_history"
                    ].append(
                        {
                            "role":
                                "assistant",

                            "content":
                                error_message,

                            "tools_used":
                                [],
                        }
                    )

    # -------------------------------------------------
    # CLEAR CHAT
    # -------------------------------------------------

    if st.session_state[
        "inventory_chat_history"
    ]:

        if st.button(
            "Clear conversation",
            key="clear_agent_chat",
        ):

            st.session_state[
                "inventory_chat_history"
            ] = []

            st.rerun()


# =====================================================
# MANAGEMENT ACTIONS TAB
# =====================================================

with actions_tab:

    st.subheader(
        "✅ Management Actions"
    )

    st.caption(
        "All actions are submitted to FastAPI. "
        "Backend role and workflow rules remain "
        "authoritative."
    )

    st.info(
        f"Signed in as: {current_user['full_name']} "
        f"({current_user['role']})"
    )

    # =================================================
    # PURCHASE REQUEST APPROVALS
    # =================================================

    st.markdown(
        "### Pending Purchase Requests"
    )

    if pending_approvals:

        for pr in pending_approvals:

            with st.expander(
                f"{pr['request_number']} "
                f"— {pr['status']}"
            ):

                st.write(
                    f"**Requested By:** "
                    f"{user_name_map.get(pr['requested_by_user_id'], 'Unknown User')}"
                )

                st.write(
                    f"**Requested by User:** "
                    f"{pr['requested_by_user_id']}"
                )

                st.write(
                    f"**Supplier ID:** "
                    f"{pr['supplier_id']}"
                )

                st.write(
                    f"**Notes:** "
                    f"{pr.get('notes') or '-'}"
                )

                lines = pr.get(
                    "lines",
                    [],
                )

                if lines:
                    st.dataframe(
                        pd.DataFrame(lines),
                        use_container_width=True,
                        hide_index=True,
                    )

                decision_comment = (
                    st.text_area(
                        "Decision comment",
                        key=(
                            f"pr_comment_"
                            f"{pr['purchase_request_id']}"
                        ),
                    )
                )

                approve_col, reject_col = (
                    st.columns(2)
                )

                with approve_col:

                    if st.button(
                        "✅ Approve",
                        key=(
                            f"approve_pr_"
                            f"{pr['purchase_request_id']}"
                        ),
                        use_container_width=True,
                    ):

                        try:

                            result = (
                                approve_purchase_request(
                                    purchase_request_id=(
                                        pr[
                                            "purchase_request_id"
                                        ]
                                    ),
                                    user_id=acting_user_id,
                                    comment=(
                                        decision_comment
                                        or "Approved from dashboard"
                                    ),
                                )
                            )

                            st.success(
                                "Purchase request approved."
                            )

                            st.json(
                                result
                            )

                            st.rerun()

                        except InventoryAPIError as exc:

                            st.error(
                                str(exc)
                            )

                with reject_col:

                    if st.button(
                        "❌ Reject",
                        key=(
                            f"reject_pr_"
                            f"{pr['purchase_request_id']}"
                        ),
                        use_container_width=True,
                    ):

                        if (
                            not decision_comment
                            or len(
                                decision_comment.strip()
                            ) < 3
                        ):

                            st.warning(
                                "Enter a rejection "
                                "comment first."
                            )

                        else:

                            try:

                                result = (
                                    reject_purchase_request(
                                        purchase_request_id=(
                                            pr[
                                                "purchase_request_id"
                                            ]
                                        ),
                                        user_id=(
                                            acting_user_id
                                        ),
                                        comment=(
                                            decision_comment
                                        ),
                                    )
                                )

                                st.success(
                                    "Purchase request rejected."
                                )

                                st.json(
                                    result
                                )

                                st.rerun()

                            except InventoryAPIError as exc:

                                st.error(
                                    str(exc)
                                )

    else:

        st.success(
            "No purchase requests are "
            "waiting for approval."
        )

    st.divider()

    # =================================================
    # HUMAN HANDOFFS
    # =================================================

    st.markdown(
        "### Human Review Queue"
    )

    if open_handoffs:

        for handoff in open_handoffs:

            with st.expander(
                f"Handoff {handoff['handoff_id']} "
                f"— {handoff['reason_code']}"
            ):

                st.write(
                    handoff["summary"]
                )

                st.write(
                    f"**Related Entity:** "
                    f"{handoff.get('entity_type')} "
                    f"{handoff.get('entity_id')}"
                )

                st.write(
                    f"**Requested by User:** "
                    f"{handoff.get('requested_by_user_id')}"
                )

                resolution_note = (
                    st.text_area(
                        "Resolution note",
                        key=(
                            f"handoff_resolution_"
                            f"{handoff['handoff_id']}"
                        ),
                    )
                )

                if st.button(
                    "Resolve Handoff",
                    key=(
                        f"resolve_handoff_"
                        f"{handoff['handoff_id']}"
                    ),
                ):

                    if (
                        not resolution_note
                        or len(
                            resolution_note.strip()
                        ) < 3
                    ):

                        st.warning(
                            "Enter a resolution note."
                        )

                    else:

                        try:

                            resolve_handoff(
                                handoff_id=(
                                    handoff[
                                        "handoff_id"
                                    ]
                                ),
                                user_id=(
                                    acting_user_id
                                ),
                                resolution_note=(
                                    resolution_note
                                ),
                            )

                            st.success(
                                "Human handoff resolved."
                            )

                            st.rerun()

                        except InventoryAPIError as exc:

                            st.error(
                                str(exc)
                            )

    else:

        st.success(
            "No open human handoffs."
        )

    st.divider()

    # =================================================
    # OTHER OPEN ALERTS
    # =================================================

    st.markdown(
        "### Open Alert Resolution"
    )

    if open_alerts:

        for alert in open_alerts:

            # Handoff alerts are resolved through
            # the handoff workflow itself.
            if (
                alert["alert_type"]
                == "HUMAN_HANDOFF"
            ):
                continue

            with st.expander(
                f"Alert {alert['alert_id']} "
                f"— {alert['alert_type']}"
            ):

                st.write(
                    alert["message"]
                )

                alert_comment = (
                    st.text_input(
                        "Resolution comment",
                        key=(
                            f"alert_comment_"
                            f"{alert['alert_id']}"
                        ),
                    )
                )

                if st.button(
                    "Resolve Alert",
                    key=(
                        f"resolve_alert_"
                        f"{alert['alert_id']}"
                    ),
                ):

                    try:

                        resolve_alert(
                            alert_id=(
                                alert[
                                    "alert_id"
                                ]
                            ),
                            user_id=(
                                acting_user_id
                            ),
                            comment=(
                                alert_comment
                                or "Resolved from dashboard"
                            ),
                        )

                        st.success(
                            "Alert resolved."
                        )

                        st.rerun()

                    except InventoryAPIError as exc:

                        st.error(
                            str(exc)
                        )

    else:

        st.success(
            "No open alerts."
        )

# =====================================================
# STOCK MOVEMENTS TAB
# =====================================================

with movements_tab:

    st.subheader(
        "🔁 Record Stock Movement"
    )

    st.caption(
        "Stock changes are processed by the "
        "FastAPI transaction service. "
        "The dashboard cannot directly overwrite "
        "inventory quantities."
    )

    st.info(
        f"Signed in as: {current_user['full_name']} "
        f"({current_user['role']})"
    )

    # =================================================
    # EXISTING INVENTORY OPTIONS
    # =================================================

    inventory_options = {}

    for row in inventory_rows:

        label = (
            f"{row['Product']} | "
            f"{row['Location']} | "
            f"Available: {row['Available']}"
        )

        inventory_options[
            label
        ] = row[
            "Inventory ID"
        ]

    inventory_record_map = {
        record["inventory_id"]:
            record
        for record in inventory
    }

    # =================================================
    # MOVEMENT FORM
    # =================================================

    if inventory_options:

        with st.form(
            "stock_movement_form"
        ):

            selected_inventory_label = (
                st.selectbox(
                    "Inventory item",
                    options=list(
                        inventory_options.keys()
                    ),
                )
            )

            movement_type = (
                st.selectbox(
                    "Movement type",
                    options=[
                        "RECEIPT",
                        "ISSUE",
                        "ADJUSTMENT_IN",
                        "ADJUSTMENT_OUT",
                    ],
                )
            )

            quantity = st.number_input(
                "Quantity",
                min_value=1,
                step=1,
            )

            reason = st.text_area(
                "Reason",
                placeholder=(
                    "Example: Goods received "
                    "from supplier"
                ),
            )

            reference = st.text_input(
                "Reference (optional)",
                placeholder=(
                    "Example: GRN-1001"
                ),
            )

            submitted = st.form_submit_button(
                "Submit Stock Movement",
                use_container_width=True,
            )

        # =================================================
        # EXECUTE MOVEMENT
        # =================================================

        if submitted:

            if (
                not reason
                or len(
                    reason.strip()
                ) < 3
            ):

                st.warning(
                    "Enter a meaningful reason "
                    "for the stock movement."
                )

            else:

                inventory_id = (
                    inventory_options[
                        selected_inventory_label
                    ]
                )

                selected_inventory = (
                    inventory_record_map[
                        inventory_id
                    ]
                )

                try:

                    result = (
                        record_stock_movement(
                            product_id=(
                                selected_inventory[
                                    "product_id"
                                ]
                            ),
                            location_id=(
                                selected_inventory[
                                    "location_id"
                                ]
                            ),
                            movement_type=(
                                movement_type
                            ),
                            quantity=int(
                                quantity
                            ),
                            user_id=(
                                acting_user_id
                            ),
                            reason=(
                                reason.strip()
                            ),
                            reference=(
                                reference.strip()
                                if reference
                                else None
                            ),
                        )
                    )

                    st.success(
                        "Stock movement recorded."
                    )

                    st.json(
                        result
                    )

                    st.rerun()

                except InventoryAPIError as exc:

                    st.error(
                        str(exc)
                    )

    else:

        st.info(
            "No inventory records are "
            "available for movement."
        )

    st.divider()

    # =================================================
    # MOVEMENT HISTORY
    # =================================================

    st.subheader(
        "Stock Movement History"
    )

    if stock_movements:

        movement_rows = []

        for movement in stock_movements:

            product = product_map.get(
                movement["product_id"],
                {},
            )

            movement_rows.append(
                {
                    "Movement ID":
                        movement[
                            "movement_id"
                        ],

                    "Product":
                        product.get(
                            "name",
                            movement[
                                "product_id"
                            ],
                        ),

                    "Location":
    location_map.get(
        movement[
            "location_id"
        ],
        f"Location {movement['location_id']}",
    ),

                    "Type":
                        movement[
                            "movement_type"
                        ],

                    "Quantity":
                        movement[
                            "quantity"
                        ],

                    "Previous":
                        movement[
                            "previous_quantity"
                        ],

                    "New":
                        movement[
                            "new_quantity"
                        ],

                    "Performed By":
    user_name_map.get(
        movement[
            "performed_by_user_id"
        ],
        f"User {movement['performed_by_user_id']}",
    ),

                    "Reason":
                        movement[
                            "reason"
                        ],

                    "Reference":
                        movement.get(
                            "reference"
                        ),

                    "Created":
                        movement[
                            "created_at"
                        ],
                }
            )

        st.dataframe(
            pd.DataFrame(
                movement_rows
            ),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No stock movements recorded yet."
        )

        # =====================================================
# ACTIVITY / AUDIT LOG TAB
# =====================================================

with activity_tab:

    st.subheader(
        "📜 System Activity Log"
    )

    st.caption(
        "Traceable history of important inventory, "
        "procurement, approval and human-review actions."
    )

    if audit_logs:

        # =============================================
        # PREPARE AUDIT RECORDS
        # =============================================

        audit_rows = []

        for log in audit_logs:

            # Convert JSON text into a readable
            # Python dictionary.
            try:
                details_data = json.loads(
                    log["details"]
                )
            except (
                json.JSONDecodeError,
                TypeError,
            ):
                details_data = {
                    "details":
                        log["details"]
                }

            # Resolve user ID to readable name.
            user_name = user_name_map.get(
                log["user_id"],
                f"User {log['user_id']}",
            )

            # Make action names easier to read.
            action_label = (
                log["action"]
                .replace("_", " ")
                .title()
            )

            # Make entity names easier to read.
            entity_label = (
                log["entity_type"]
                .replace("_", " ")
                .title()
            )

            # Human-friendly timestamp.
            created_at = (
                log["created_at"]
                .replace("T", " ")
            )

            audit_rows.append(
                {
                    "Audit ID":
                        log["audit_id"],

                    "Time":
                        created_at,

                    "User":
                        user_name,

                    "Action":
                        action_label,

                    "Entity":
                        entity_label,

                    "Entity ID":
                        log["entity_id"],

                    "Details":
                        details_data,
                }
            )

        # Latest actions first.
        audit_rows = sorted(
            audit_rows,
            key=lambda row:
                row["Audit ID"],
            reverse=True,
        )

        # =============================================
        # AUDIT KPIs
        # =============================================

        st.markdown(
            "### Activity Overview"
        )

        audit_col1, audit_col2, audit_col3, audit_col4 = (
            st.columns(4)
        )

        with audit_col1:
            st.metric(
                "Recorded Actions",
                len(audit_rows),
            )

        with audit_col2:
            approval_count = sum(
                1
                for row in audit_rows
                if "Approved"
                in row["Action"]
            )

            st.metric(
                "Approvals",
                approval_count,
            )

        with audit_col3:
            movement_count = sum(
                1
                for row in audit_rows
                if (
                    row["Action"]
                    == "Stock Movement Recorded"
                )
            )

            st.metric(
                "Stock Movements",
                movement_count,
            )

        with audit_col4:
            handoff_count = sum(
                1
                for row in audit_rows
                if "Handoff"
                in row["Action"]
            )

            st.metric(
                "Handoff Actions",
                handoff_count,
            )

        st.divider()

        # =============================================
        # FILTERS
        # =============================================

        st.markdown(
            "### Filter Activity"
        )

        filter_col1, filter_col2, filter_col3 = (
            st.columns(3)
        )

        action_options = [
            "All"
        ] + sorted(
            {
                row["Action"]
                for row in audit_rows
            }
        )

        user_options = [
            "All"
        ] + sorted(
            {
                row["User"]
                for row in audit_rows
            }
        )

        entity_options = [
            "All"
        ] + sorted(
            {
                row["Entity"]
                for row in audit_rows
            }
        )

        with filter_col1:
            selected_action = (
                st.selectbox(
                    "Action",
                    action_options,
                    key="audit_action_filter",
                )
            )

        with filter_col2:
            selected_user_filter = (
                st.selectbox(
                    "User",
                    user_options,
                    key="audit_user_filter",
                )
            )

        with filter_col3:
            selected_entity = (
                st.selectbox(
                    "Entity",
                    entity_options,
                    key="audit_entity_filter",
                )
            )

        filtered_audit_rows = (
            audit_rows
        )

        if selected_action != "All":
            filtered_audit_rows = [
                row
                for row in filtered_audit_rows
                if (
                    row["Action"]
                    == selected_action
                )
            ]

        if selected_user_filter != "All":
            filtered_audit_rows = [
                row
                for row in filtered_audit_rows
                if (
                    row["User"]
                    == selected_user_filter
                )
            ]

        if selected_entity != "All":
            filtered_audit_rows = [
                row
                for row in filtered_audit_rows
                if (
                    row["Entity"]
                    == selected_entity
                )
            ]

        # =============================================
        # SUMMARY TABLE
        # =============================================

        table_rows = []

        for row in filtered_audit_rows:

            table_rows.append(
                {
                    "Audit ID":
                        row["Audit ID"],

                    "Time":
                        row["Time"],

                    "User":
                        row["User"],

                    "Action":
                        row["Action"],

                    "Entity":
                        row["Entity"],

                    "Entity ID":
                        row["Entity ID"],
                }
            )

        st.dataframe(
            pd.DataFrame(
                table_rows
            ),
            use_container_width=True,
            hide_index=True,
        )

        # =============================================
        # DETAILED ACTIVITY VIEW
        # =============================================

        st.markdown(
            "### Activity Details"
        )

        if filtered_audit_rows:

            for row in filtered_audit_rows:

                expander_title = (
                    f"#{row['Audit ID']} • "
                    f"{row['Action']} • "
                    f"{row['User']}"
                )

                with st.expander(
                    expander_title
                ):

                    detail_col1, detail_col2 = (
                        st.columns(2)
                    )

                    with detail_col1:

                        st.write(
                            f"**Time:** "
                            f"{row['Time']}"
                        )

                        st.write(
                            f"**User:** "
                            f"{row['User']}"
                        )

                        st.write(
                            f"**Action:** "
                            f"{row['Action']}"
                        )

                    with detail_col2:

                        st.write(
                            f"**Entity:** "
                            f"{row['Entity']}"
                        )

                        st.write(
                            f"**Entity ID:** "
                            f"{row['Entity ID']}"
                        )

                    st.markdown(
                        "**Recorded Details**"
                    )

                    st.json(
                        row["Details"]
                    )

        else:

            st.info(
                "No activity matches "
                "the selected filters."
            )

    else:

        st.info(
            "No audit activity has been "
            "recorded yet."
        )

# =====================================================
# FOOTER
# =====================================================

st.divider()

st.caption(
    "Virgocreativo Inventory Agent • "
    "Task 12 Demo Dashboard"
)