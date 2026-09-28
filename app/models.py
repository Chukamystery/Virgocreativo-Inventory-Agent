from datetime import datetime

from sqlalchemy import DateTime, Text
from sqlalchemy.sql import func

from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    DateTime,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "role IN "
            "('INVENTORY_STAFF', "
            "'INVENTORY_MANAGER', "
            "'PROCUREMENT_OFFICER', "
            "'ADMIN')",
            name="ck_user_valid_role"
        ),
    )


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    sku: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    unit_of_measure: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    reorder_point: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    target_stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "reorder_point >= 0",
            name="ck_product_reorder_nonnegative"
        ),
        CheckConstraint(
            "target_stock >= reorder_point",
            name="ck_product_target_valid"
        ),
    )


class Location(Base):
    __tablename__ = "locations"

    location_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    code: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False
    )

    location_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )


class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    supplier_code: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    phone: Mapped[str] = mapped_column(
        String(40),
        nullable=False
    )

    lead_time_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "lead_time_days >= 0",
            name="ck_supplier_lead_time_nonnegative"
        ),
    )


class ProductSupplier(Base):
    __tablename__ = "product_suppliers"

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.product_id"),
        primary_key=True
    )

    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.supplier_id"),
        primary_key=True
    )

    supplier_sku: Mapped[str] = mapped_column(
        String(80),
        nullable=False
    )

    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    minimum_order_qty: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    preferred: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "unit_cost >= 0",
            name="ck_supplier_cost_nonnegative"
        ),
        CheckConstraint(
            "minimum_order_qty > 0",
            name="ck_supplier_moq_positive"
        ),
    )


class Inventory(Base):
    __tablename__ = "inventory"

    inventory_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.product_id"),
        nullable=False
    )

    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.location_id"),
        nullable=False
    )

    quantity_on_hand: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    reserved_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "location_id",
            name="uq_inventory_product_location"
        ),
        CheckConstraint(
            "quantity_on_hand >= 0",
            name="ck_inventory_nonnegative"
        ),
        CheckConstraint(
            "reserved_quantity >= 0",
            name="ck_reserved_nonnegative"
        ),
        CheckConstraint(
            "reserved_quantity <= quantity_on_hand",
            name="ck_reserved_not_above_on_hand"
        ),
    )

class StockMovement(Base):
    __tablename__ = "stock_movements"

    movement_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.product_id"),
        nullable=False,
        index=True
    )

    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.location_id"),
        nullable=False,
        index=True
    )

    movement_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    previous_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    new_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    performed_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"),
        nullable=False
    )

    reason: Mapped[str] = mapped_column(
        String(250),
        nullable=False
    )

    reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "movement_type IN "
            "('RECEIPT', 'ISSUE', "
            "'ADJUSTMENT_IN', 'ADJUSTMENT_OUT')",
            name="ck_stock_movement_type"
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_stock_movement_quantity_positive"
        ),
        CheckConstraint(
            "previous_quantity >= 0",
            name="ck_movement_previous_nonnegative"
        ),
        CheckConstraint(
            "new_quantity >= 0",
            name="ck_movement_new_nonnegative"
        ),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"),
        nullable=False
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    entity_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    details: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        nullable=False
    )


class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    purchase_request_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    request_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    requested_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"),
        nullable=False
    )

    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.supplier_id"),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="DRAFT"
    )

    notes: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('DRAFT', 'PENDING_APPROVAL', "
            "'APPROVED', 'REJECTED')",
            name="ck_purchase_request_status"
        ),
    )


class PurchaseRequestLine(Base):
    __tablename__ = "purchase_request_lines"

    purchase_request_line_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    purchase_request_id: Mapped[int] = mapped_column(
        ForeignKey(
            "purchase_requests.purchase_request_id"
        ),
        nullable=False,
        index=True
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.product_id"),
        nullable=False
    )

    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.location_id"),
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    reorder_recommendation: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    minimum_order_qty: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_pr_line_quantity_positive"
        ),
        CheckConstraint(
            "unit_cost >= 0",
            name="ck_pr_line_cost_nonnegative"
        ),
    )

class PurchaseRequestApproval(Base):
    __tablename__ = "purchase_request_approvals"

    approval_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    purchase_request_id: Mapped[int] = mapped_column(
        ForeignKey(
            "purchase_requests.purchase_request_id"
        ),
        nullable=False,
        index=True
    )

    action: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    performed_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"),
        nullable=False
    )

    previous_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    new_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    comment: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "action IN "
            "('SUBMITTED', 'APPROVED', 'REJECTED')",
            name="ck_pr_approval_action"
        ),
    )

class Alert(Base):
    __tablename__ = "alerts"

    alert_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    alert_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        index=True
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="WARNING"
    )

    message: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    entity_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    entity_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="OPEN",
        index=True
    )

    resolved_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id"),
        nullable=True
    )

    resolution_note: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        nullable=False
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    __table_args__ = (
        CheckConstraint(
            "severity IN ('INFO', 'WARNING', 'CRITICAL')",
            name="ck_alert_severity"
        ),
        CheckConstraint(
            "status IN ('OPEN', 'RESOLVED')",
            name="ck_alert_status"
        ),
    )

class HumanHandoff(Base):
    __tablename__ = "human_handoffs"

    handoff_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    reason_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    summary: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    entity_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    entity_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    requested_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id"),
        nullable=True
    )

    assigned_to_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id"),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="OPEN",
        index=True
    )

    context_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    resolution_note: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        nullable=False
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    __table_args__ = (
        CheckConstraint(
            "reason_code IN ("
            "'AUTHORIZATION_FAILURE', "
            "'CONFLICTING_DATA', "
            "'SUPPLIER_SELECTION', "
            "'UNSUPPORTED_ACTION', "
            "'TOOL_FAILURE', "
            "'HIGH_RISK_EXCEPTION'"
            ")",
            name="ck_handoff_reason"
        ),
        CheckConstraint(
            "status IN ('OPEN', 'RESOLVED')",
            name="ck_handoff_status"
        ),
    )