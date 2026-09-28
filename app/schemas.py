from datetime import datetime
from typing import Literal
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# ==========================================
# PRODUCT SCHEMAS
# ==========================================

class ProductBase(BaseModel):
    sku: str
    name: str
    category: str
    unit_of_measure: str

    reorder_point: int = Field(
        ge=0
    )

    target_stock: int = Field(
        ge=0
    )

    active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    unit_of_measure: str | None = None

    reorder_point: int | None = Field(
        default=None,
        ge=0
    )

    target_stock: int | None = Field(
        default=None,
        ge=0
    )

    active: bool | None = None


class ProductRead(ProductBase):
    product_id: int

    model_config = ConfigDict(
        from_attributes=True
    )


# ==========================================
# INVENTORY SCHEMA
# ==========================================

class InventoryRead(BaseModel):
    inventory_id: int
    product_id: int
    location_id: int
    quantity_on_hand: int
    reserved_quantity: int

    model_config = ConfigDict(
        from_attributes=True
    )


# ==========================================
# STOCK MOVEMENT SCHEMAS
# ==========================================

class StockMovementCreate(BaseModel):
    product_id: int = Field(
        gt=0
    )

    location_id: int = Field(
        gt=0
    )

    movement_type: Literal[
        "RECEIPT",
        "ISSUE",
        "ADJUSTMENT_IN",
        "ADJUSTMENT_OUT"
    ]

    quantity: int = Field(
        gt=0
    )

    performed_by_user_id: int = Field(
        gt=0
    )

    reason: str = Field(
        min_length=3,
        max_length=250
    )

    reference: str | None = Field(
        default=None,
        max_length=100
    )


class StockMovementRead(BaseModel):
    movement_id: int
    product_id: int
    location_id: int
    movement_type: str
    quantity: int

    previous_quantity: int
    new_quantity: int

    performed_by_user_id: int

    reason: str

    reference: str | None

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


# ==========================================
# AUDIT LOG SCHEMA
# ==========================================

class AuditLogRead(BaseModel):
    audit_id: int

    user_id: int

    action: str

    entity_type: str

    entity_id: int

    details: str

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )

class ReorderRecommendationRead(BaseModel):
    inventory_id: int

    product_id: int
    sku: str
    product_name: str

    location_id: int
    location_name: str

    quantity_on_hand: int
    reserved_quantity: int
    available_quantity: int

    reorder_point: int
    target_stock: int

    is_low_stock: bool

    recommended_reorder_quantity: int


class ReorderSummaryRead(BaseModel):
    low_stock_count: int

    items: list[ReorderRecommendationRead]


class AgentChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
    )

    user_id: int = Field(
        gt=0
    )


class AgentChatResponse(BaseModel):
    answer: str

    tools_used: list[str]

    model: str

    prompt_version: str


class SupplierOptionRead(BaseModel):
    supplier_id: int
    supplier_code: str
    supplier_name: str
    supplier_sku: str
    unit_cost: Decimal
    minimum_order_qty: int
    lead_time_days: int
    currency: str
    preferred: bool


class PreparePurchaseRequest(BaseModel):
    product_id: int = Field(gt=0)

    location_id: int = Field(gt=0)

    requested_by_user_id: int = Field(gt=0)

    notes: str | None = Field(
        default=None,
        max_length=300,
    )


class PurchaseRequestLineRead(BaseModel):
    purchase_request_line_id: int

    product_id: int

    location_id: int

    quantity: int

    unit_cost: Decimal

    reorder_recommendation: int

    minimum_order_qty: int

    model_config = ConfigDict(
        from_attributes=True
    )


class PurchaseRequestRead(BaseModel):
    purchase_request_id: int

    request_number: str

    requested_by_user_id: int

    supplier_id: int

    status: str

    notes: str | None

    created_at: datetime

    lines: list[PurchaseRequestLineRead]



class PurchaseRequestActionRequest(BaseModel):
    performed_by_user_id: int = Field(
        gt=0
    )

    comment: str | None = Field(
        default=None,
        max_length=300,
    )


class PurchaseRequestApprovalRead(BaseModel):
    approval_id: int
    purchase_request_id: int
    action: str
    performed_by_user_id: int
    previous_status: str
    new_status: str
    comment: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class PurchaseRequestTransitionResponse(BaseModel):
    purchase_request_id: int
    request_number: str
    status: str
    action: str
    approval_id: int
    performed_by_user_id: int
    comment: str | None

class AlertRead(BaseModel):
    alert_id: int
    alert_type: str
    severity: str
    message: str
    entity_type: str | None
    entity_id: int | None
    status: str
    resolved_by_user_id: int | None
    resolution_note: str | None
    created_at: datetime
    resolved_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True
    )


class AlertResolveRequest(BaseModel):
    performed_by_user_id: int = Field(
        gt=0
    )

    comment: str | None = Field(
        default=None,
        max_length=500,
    )

class HumanHandoffCreate(BaseModel):
    reason_code: Literal[
        "AUTHORIZATION_FAILURE",
        "CONFLICTING_DATA",
        "SUPPLIER_SELECTION",
        "UNSUPPORTED_ACTION",
        "TOOL_FAILURE",
        "HIGH_RISK_EXCEPTION",
    ]

    summary: str = Field(
        min_length=5,
        max_length=500,
    )

    entity_type: str | None = Field(
        default=None,
        max_length=50,
    )

    entity_id: int | None = Field(
        default=None,
        gt=0,
    )

    requested_by_user_id: int | None = Field(
        default=None,
        gt=0,
    )

    context: dict | None = None


class HumanHandoffResolveRequest(BaseModel):
    performed_by_user_id: int = Field(
        gt=0
    )

    resolution_note: str = Field(
        min_length=3,
        max_length=500,
    )


class HumanHandoffRead(BaseModel):
    handoff_id: int
    reason_code: str
    summary: str
    entity_type: str | None
    entity_id: int | None
    requested_by_user_id: int | None
    assigned_to_user_id: int | None
    status: str
    context_json: str | None
    resolution_note: str | None
    created_at: datetime
    resolved_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True
    )

class LocationLookupRead(BaseModel):
    location_id: int
    code: str
    name: str
    location_type: str
    active: bool

    model_config = ConfigDict(
        from_attributes=True
    )


class SupplierLookupRead(BaseModel):
    supplier_id: int
    supplier_code: str
    name: str
    email: str | None
    phone: str | None
    lead_time_days: int
    currency: str
    active: bool

    model_config = ConfigDict(
        from_attributes=True
    )