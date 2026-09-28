LIVE_OPERATIONAL_TOPICS = {
    "inventory_quantity",
    "reserved_quantity",
    "available_quantity",
    "stock_movement",
    "reorder_status",
    "reorder_quantity",
    "supplier_record",
    "purchase_request",
    "approval_status",
}


RAG_TOPICS = {
    "sop",
    "policy",
    "procedure",
    "product_note",
    "supplier_policy",
    "purchasing_procedure",
}


DIRECT_WRITE_FORBIDDEN_FIELDS = {
    "quantity_on_hand",
    "reserved_quantity",
    "audit_log",
    "approval_status",
}


REQUIRES_CLARIFICATION = {
    "ambiguous_product",
    "ambiguous_location",
}


HUMAN_HANDOFF_REASONS = {
    "authorization_failure",
    "conflicting_data",
    "unsupported_transaction",
    "high_risk_exception",
    "missing_required_data",
    "tool_failure",
}