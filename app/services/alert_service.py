from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.services.reorder_service import (
    get_low_stock_items,
)


ALERT_RESOLUTION_ROLES = {
    "PROCUREMENT_OFFICER",
    "INVENTORY_MANAGER",
    "ADMIN",
}


def _get_open_alert(
    db: Session,
    alert_type: str,
    entity_type: str | None,
    entity_id: int | None,
):
    statement = select(
        models.Alert
    ).where(
        models.Alert.alert_type
        == alert_type,

        models.Alert.status
        == "OPEN",
    )

    if entity_type is None:
        statement = statement.where(
            models.Alert.entity_type.is_(None)
        )
    else:
        statement = statement.where(
            models.Alert.entity_type
            == entity_type
        )

    if entity_id is None:
        statement = statement.where(
            models.Alert.entity_id.is_(None)
        )
    else:
        statement = statement.where(
            models.Alert.entity_id
            == entity_id
        )

    return db.scalar(
        statement
    )


def create_open_alert(
    db: Session,
    alert_type: str,
    severity: str,
    message: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    commit: bool = False,
):
    """
    Create an OPEN alert unless one already
    exists for the same type/entity.

    This prevents duplicate alert noise.
    """

    existing = _get_open_alert(
        db=db,
        alert_type=alert_type,
        entity_type=entity_type,
        entity_id=entity_id,
    )

    if existing is not None:
        return {
            "alert": existing,
            "created": False,
        }

    alert = models.Alert(
        alert_type=alert_type,
        severity=severity,
        message=message,
        entity_type=entity_type,
        entity_id=entity_id,
        status="OPEN",
    )

    db.add(
        alert
    )

    db.flush()

    if commit:
        db.commit()

        db.refresh(
            alert
        )

    return {
        "alert": alert,
        "created": True,
    }


def resolve_matching_alerts(
    db: Session,
    alert_type: str,
    entity_type: str,
    entity_id: int,
    resolved_by_user_id: int | None = None,
    resolution_note: str | None = None,
    commit: bool = False,
):
    alerts = db.scalars(
        select(
            models.Alert
        )
        .where(
            models.Alert.alert_type
            == alert_type,

            models.Alert.entity_type
            == entity_type,

            models.Alert.entity_id
            == entity_id,

            models.Alert.status
            == "OPEN",
        )
    ).all()

    for alert in alerts:
        alert.status = "RESOLVED"

        alert.resolved_by_user_id = (
            resolved_by_user_id
        )

        alert.resolution_note = (
            resolution_note
        )

        alert.resolved_at = (
            datetime.utcnow()
        )

    if commit:
        db.commit()

    return len(alerts)


def get_alerts(
    db: Session,
    status: str | None = None,
    alert_type: str | None = None,
):
    statement = select(
        models.Alert
    )

    if status:
        statement = statement.where(
            models.Alert.status
            == status
        )

    if alert_type:
        statement = statement.where(
            models.Alert.alert_type
            == alert_type
        )

    statement = statement.order_by(
        models.Alert.alert_id.desc()
    )

    return db.scalars(
        statement
    ).all()


def resolve_alert(
    db: Session,
    alert_id: int,
    performed_by_user_id: int,
    comment: str | None = None,
):
    user = db.get(
        models.User,
        performed_by_user_id,
    )

    if user is None or not user.active:
        raise PermissionError(
            "User not found or inactive"
        )

    if user.role not in ALERT_RESOLUTION_ROLES:
        raise PermissionError(
            "User role is not allowed "
            "to resolve alerts"
        )

    alert = db.get(
        models.Alert,
        alert_id,
    )

    if alert is None:
        raise ValueError(
            "Alert not found"
        )

    if alert.status != "OPEN":
        raise ValueError(
            "Only an OPEN alert can be resolved"
        )

    try:
        alert.status = "RESOLVED"

        alert.resolved_by_user_id = (
            performed_by_user_id
        )

        alert.resolution_note = (
            comment
        )

        alert.resolved_at = (
            datetime.utcnow()
        )

        audit = models.AuditLog(
            user_id=performed_by_user_id,
            action="ALERT_RESOLVED",
            entity_type="alert",
            entity_id=alert.alert_id,
            details=(
                f"Alert {alert.alert_id} resolved. "
                f"Type={alert.alert_type}"
            ),
        )

        db.add(
            audit
        )

        db.commit()

        db.refresh(
            alert
        )

        return alert

    except Exception:
        db.rollback()
        raise


def sync_low_stock_alerts(
    db: Session,
):
    """
    Create alerts for currently low-stock items.

    Existing OPEN alerts are reused rather than
    duplicated.

    Alerts for inventory records that are no
    longer low-stock are automatically resolved.
    """

    low_stock_items = (
        get_low_stock_items(
            db
        )
    )

    current_low_stock_ids = set()

    created_count = 0

    already_open_count = 0

    for item in low_stock_items:

        inventory_id = item[
            "inventory_id"
        ]

        current_low_stock_ids.add(
            inventory_id
        )

        message = (
            f"{item['product_name']} at "
            f"{item['location_name']} is low stock. "
            f"Available={item['available_quantity']}, "
            f"reorder point={item['reorder_point']}."
        )

        result = create_open_alert(
            db=db,
            alert_type="LOW_STOCK",
            severity="WARNING",
            message=message,
            entity_type="inventory",
            entity_id=inventory_id,
            commit=False,
        )

        if result["created"]:
            created_count += 1
        else:
            already_open_count += 1

    open_low_stock_alerts = db.scalars(
        select(
            models.Alert
        )
        .where(
            models.Alert.alert_type
            == "LOW_STOCK",

            models.Alert.status
            == "OPEN",
        )
    ).all()

    auto_resolved_count = 0

    for alert in open_low_stock_alerts:

        if (
            alert.entity_type == "inventory"
            and alert.entity_id
            not in current_low_stock_ids
        ):
            alert.status = "RESOLVED"

            alert.resolution_note = (
                "Automatically resolved because "
                "the inventory record is no longer "
                "below its reorder threshold."
            )

            alert.resolved_at = (
                datetime.utcnow()
            )

            auto_resolved_count += 1

    db.commit()

    return {
        "low_stock_items":
            len(low_stock_items),

        "alerts_created":
            created_count,

        "already_open":
            already_open_count,

        "auto_resolved":
            auto_resolved_count,
    }