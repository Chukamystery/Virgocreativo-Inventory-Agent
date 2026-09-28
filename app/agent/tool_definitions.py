INVENTORY_AGENT_TOOLS = [

    # =================================================
    # FIND PRODUCTS
    # =================================================

    {
        "type": "function",
        "name": "find_products",
        "description": (
            "Search active inventory products by "
            "product name or SKU. Use this before "
            "other product-specific tools when the "
            "user provides a product name instead "
            "of a product ID."
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Product name, partial name, "
                        "or SKU to search for."
                    ),
                },
            },
            "required": [
                "query"
            ],
            "additionalProperties": False,
        },
    },

    # =================================================
    # FIND LOCATIONS
    # =================================================

    {
        "type": "function",
        "name": "find_locations",
        "description": (
            "Search active inventory locations by "
            "location name or location code. Use this "
            "when the user provides a location name "
            "instead of a location ID."
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Location name, partial name, "
                        "or location code."
                    ),
                },
            },
            "required": [
                "query"
            ],
            "additionalProperties": False,
        },
    },

    # =================================================
    # INVENTORY BALANCE
    # =================================================

    {
        "type": "function",
        "name": "get_inventory_balance",
        "description": (
            "Get the verified current inventory "
            "balance for one product at one location. "
            "Returns quantity on hand, reserved "
            "quantity and available quantity."
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": (
                        "Verified product ID."
                    ),
                },
                "location_id": {
                    "type": "integer",
                    "description": (
                        "Verified location ID."
                    ),
                },
            },
            "required": [
                "product_id",
                "location_id"
            ],
            "additionalProperties": False,
        },
    },

    # =================================================
    # REORDER RECOMMENDATION
    # =================================================

    {
        "type": "function",
        "name": "get_reorder_recommendation",
        "description": (
            "Calculate the verified reorder status "
            "and recommended reorder quantity for "
            "one product at one location using the "
            "backend inventory rules."
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": (
                        "Verified product ID."
                    ),
                },
                "location_id": {
                    "type": "integer",
                    "description": (
                        "Verified location ID."
                    ),
                },
            },
            "required": [
                "product_id",
                "location_id"
            ],
            "additionalProperties": False,
        },
    },

    # =================================================
    # LOW STOCK
    # =================================================

    {
        "type": "function",
        "name": "list_low_stock_items",
        "description": (
            "Return the verified list of inventory "
            "items that are currently at or below "
            "their reorder threshold."
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },

    # =================================================
    # SUPPLIER OPTIONS
    # =================================================

    {
        "type": "function",
        "name": "get_supplier_options",
        "description": (
            "Return verified supplier options and "
            "commercial terms for a product, including "
            "supplier SKU, unit cost, minimum order "
            "quantity, lead time and preferred status."
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": (
                        "Verified product ID."
                    ),
                },
            },
            "required": [
                "product_id"
            ],
            "additionalProperties": False,
        },
    },

    # =================================================
    # HUMAN HANDOFF
    # =================================================

    {
        "type": "function",
        "name": "create_human_handoff",
        "description": (
            "Create a human review request when the "
            "Inventory Agent cannot safely continue. "
            "Use this for conflicting data, ambiguous "
            "supplier decisions, unsupported actions, "
            "tool failures or high-risk exceptions."
        ),
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "reason_code": {
                    "type": "string",
                    "enum": [
                        "CONFLICTING_DATA",
                        "SUPPLIER_SELECTION",
                        "UNSUPPORTED_ACTION",
                        "TOOL_FAILURE",
                        "HIGH_RISK_EXCEPTION"
                    ],
                    "description": (
                        "Reason why human review "
                        "is required."
                    ),
                },
                "summary": {
                    "type": "string",
                    "description": (
                        "Short explanation of the "
                        "problem for the human reviewer."
                    ),
                },
                "entity_type": {
                    "type": [
                        "string",
                        "null"
                    ],
                    "description": (
                        "Related entity type, such as "
                        "product, inventory or "
                        "purchase_request, when known."
                    ),
                },
                "entity_id": {
                    "type": [
                        "integer",
                        "null"
                    ],
                    "description": (
                        "Related entity ID when known."
                    ),
                },
            },
            "required": [
                "reason_code",
                "summary",
                "entity_type",
                "entity_id"
            ],
            "additionalProperties": False,
        },
    },
]