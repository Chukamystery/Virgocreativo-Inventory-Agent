import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.services.alert_service import (
    create_open_alert,
    resolve_matching_alerts,
)


HANDOFF_RESOLUTION_ROLES = {
    "INVENTORY_MANAGER",
    "ADMIN",
}


ALLOWED_HANDOFF_REASONS = {
    "AUTHORIZATION_FAILURE",
    "CONFLICTING_DATA",
    "SUPPLIER_SELECTION",
    "UNSUPPORTED_ACTION",
    "TOOL_FAILURE",
    "HIGH_RISK_EXCEPTION",
}


def _find_existing_open_handoff(
    db: Session,
    reason_code: str,
    entity_type: str | None,
    entity_id: int | None,
):
    statement = select(
        models.HumanHandoff
    ).where(
        models.HumanHandoff.reason_code
        == reason_code,

        models.HumanHandoff.status
        == "OPEN",
    )

    if entity_type is None:
        statement = statement.where(
            models.HumanHandoff.entity_type.is_(None)
        )
    else:
        statement = statement.where(
            models.HumanHandoff.entity_type
            == entity_type
        )

    if entity_id is None:
        statement = statement.where(
            models.HumanHandoff.entity_id.is_(None)
        )
    else:
        statement = statement.where(
            models.HumanHandoff.entity_id
            == entity_id
        )

    return db.scalar(
        statement
    )


def create_handoff(
    db: Session,
    reason_code: str,
    summary: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    requested_by_user_id: int | None = None,
    context: dict | None = None,
):
    """
    Create a human handoff.

    Duplicate OPEN handoffs for the same
    reason/entity are not created.
    """

    if reason_code not in ALLOWED_HANDOFF_REASONS:
        raise ValueError(
            "Unsupported handoff reason"
        )

    if requested_by_user_id is not None:

        user = db.get(
            models.User,
            requested_by_user_id,
        )

        if user is None or not user.active:
            raise ValueError(
                "Requesting user not found or inactive"
            )

    existing = _find_existing_open_handoff(
        db=db,
        reason_code=reason_code,
        entity_type=entity_type,
        entity_id=entity_id,
    )

    if existing is not None:
        return {
            "handoff": existing,
            "created": False,
        }

    handoff = models.HumanHandoff(
        reason_code=reason_code,
        summary=summary,
        entity_type=entity_type,
        entity_id=entity_id,
        requested_by_user_id=(
            requested_by_user_id
        ),
        status="OPEN",
        context_json=(
            json.dumps(context)
            if context is not None
            else None
        ),
    )

    try:
        db.add(
            handoff
        )

        db.flush()

        create_open_alert(
            db=db,
            alert_type="HUMAN_HANDOFF",
            severity="WARNING",
            message=(
                f"Human review required: {summary}"
            ),
            entity_type="human_handoff",
            entity_id=handoff.handoff_id,
            commit=False,
        )

        audit = models.AuditLog(
            user_id=requested_by_user_id,
            action="HUMAN_HANDOFF_CREATED",
            entity_type="human_handoff",
            entity_id=handoff.handoff_id,
            details=json.dumps(
                {
                    "reason_code":
                        reason_code,

                    "summary":
                        summary,

                    "related_entity_type":
                        entity_type,

                    "related_entity_id":
                        entity_id,
                }
            ),
        )

        db.add(
            audit
        )

        db.commit()

        db.refresh(
            handoff
        )

        return {
            "handoff": handoff,
            "created": True,
        }

    except Exception:
        db.rollback()
        raise


def get_handoffs(
    db: Session,
    status: str | None = None,
):
    statement = select(
        models.HumanHandoff
    )

    if status:
        statement = statement.where(
            models.HumanHandoff.status
            == status
        )

    statement = statement.order_by(
        models.HumanHandoff.handoff_id.desc()
    )

    return db.scalars(
        statement
    ).all()


def resolve_handoff(
    db: Session,
    handoff_id: int,
    performed_by_user_id: int,
    resolution_note: str,
):
    user = db.get(
        models.User,
        performed_by_user_id,
    )

    if user is None or not user.active:
        raise PermissionError(
            "User not found or inactive"
        )

    if user.role not in HANDOFF_RESOLUTION_ROLES:
        raise PermissionError(
            "User role is not allowed "
            "to resolve human handoffs"
        )

    handoff = db.get(
        models.HumanHandoff,
        handoff_id,
    )

    if handoff is None:
        raise ValueError(
            "Human handoff not found"
        )

    if handoff.status != "OPEN":
        raise ValueError(
            "Only an OPEN handoff "
            "can be resolved"
        )

    try:
        handoff.status = "RESOLVED"

        handoff.assigned_to_user_id = (
            performed_by_user_id
        )

        handoff.resolution_note = (
            resolution_note
        )

        handoff.resolved_at = (
            datetime.utcnow()
        )

        resolve_matching_alerts(
            db=db,
            alert_type="HUMAN_HANDOFF",
            entity_type="human_handoff",
            entity_id=handoff.handoff_id,
            resolved_by_user_id=(
                performed_by_user_id
            ),
            resolution_note=(
                "Related human handoff resolved."
            ),
            commit=False,
        )

        audit = models.AuditLog(
            user_id=performed_by_user_id,
            action="HUMAN_HANDOFF_RESOLVED",
            entity_type="human_handoff",
            entity_id=handoff.handoff_id,
            details=json.dumps(
                {
                    "reason_code":
                        handoff.reason_code,

                    "resolution_note":
                        resolution_note,
                }
            ),
        )

        db.add(
            audit
        )

        db.commit()

        db.refresh(
            handoff
        )

        return handoff

    except Exception:
        db.rollback()
        raise