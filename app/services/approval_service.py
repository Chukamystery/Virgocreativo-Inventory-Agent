from app.services.alert_service import (
    create_open_alert,
    resolve_matching_alerts,
)

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models


ALLOWED_SUBMIT_ROLES = {
    "PROCUREMENT_OFFICER",
    "INVENTORY_MANAGER",
    "ADMIN",
}


ALLOWED_APPROVAL_ROLES = {
    "INVENTORY_MANAGER",
    "ADMIN",
}


def _get_active_user(
    db: Session,
    user_id: int,
):
    user = db.get(
        models.User,
        user_id,
    )

    if user is None:
        raise PermissionError(
            "User not found"
        )

    if not user.active:
        raise PermissionError(
            "User is inactive"
        )

    return user


def _get_purchase_request(
    db: Session,
    purchase_request_id: int,
):
    purchase_request = db.get(
        models.PurchaseRequest,
        purchase_request_id,
    )

    if purchase_request is None:
        raise ValueError(
            "Purchase request not found"
        )

    return purchase_request


def _create_audit_log(
    db: Session,
    user_id: int,
    action: str,
    purchase_request_id: int,
    details: dict,
):
    audit = models.AuditLog(
        user_id=user_id,
        action=action,
        entity_type="purchase_request",
        entity_id=purchase_request_id,
        details=json.dumps(
            details
        ),
    )

    db.add(
        audit
    )


def submit_purchase_request(
    db: Session,
    purchase_request_id: int,
    performed_by_user_id: int,
    comment: str | None = None,
):
    """
    Move a purchase request:

    DRAFT -> PENDING_APPROVAL
    """

    user = _get_active_user(
        db,
        performed_by_user_id,
    )

    purchase_request = (
        _get_purchase_request(
            db,
            purchase_request_id,
        )
    )

    if user.role not in ALLOWED_SUBMIT_ROLES:
        raise PermissionError(
            "User role is not allowed to submit "
            "purchase requests"
        )

    if purchase_request.status != "DRAFT":
        raise ValueError(
            "Only a DRAFT purchase request "
            "can be submitted"
        )

    previous_status = (
        purchase_request.status
    )

    new_status = "PENDING_APPROVAL"

    try:
        purchase_request.status = (
            new_status
        )

        approval = (
            models.PurchaseRequestApproval(
                purchase_request_id=(
                    purchase_request_id
                ),
                action="SUBMITTED",
                performed_by_user_id=(
                    performed_by_user_id
                ),
                previous_status=(
                    previous_status
                ),
                new_status=new_status,
                comment=comment,
            )
        )

        db.add(
            approval
        )

        db.flush()

        _create_audit_log(
            db=db,
            user_id=performed_by_user_id,
            action=(
                "PURCHASE_REQUEST_SUBMITTED"
            ),
            purchase_request_id=(
                purchase_request_id
            ),
            details={
                "request_number":
                    purchase_request.request_number,

                "previous_status":
                    previous_status,

                "new_status":
                    new_status,

                "performed_by_user_id":
                    performed_by_user_id,
            },
        )

        create_open_alert(
                  db=db,
            alert_type="PENDING_APPROVAL",
            severity="WARNING",
            message=(
                "Purchase request "
                f"{purchase_request.request_number} "
                "requires approval."
            ),
            entity_type="purchase_request",
            entity_id=purchase_request_id,
            commit=False,
         )
        

        db.commit()

        db.refresh(
            purchase_request
        )

        db.refresh(
            approval
        )

        return {
            "purchase_request":
                purchase_request,

            "approval":
                approval,
        }

    except Exception:
        db.rollback()
        raise


def approve_purchase_request(
    db: Session,
    purchase_request_id: int,
    performed_by_user_id: int,
    comment: str | None = None,
):
    """
    Move a purchase request:

    PENDING_APPROVAL -> APPROVED
    """

    user = _get_active_user(
        db,
        performed_by_user_id,
    )

    purchase_request = (
        _get_purchase_request(
            db,
            purchase_request_id,
        )
    )

    if user.role not in ALLOWED_APPROVAL_ROLES:
        raise PermissionError(
            "User role is not allowed to approve "
            "purchase requests"
        )

    if (
        purchase_request.requested_by_user_id
        == performed_by_user_id
    ):
        raise PermissionError(
            "The purchase request creator cannot "
            "approve their own request"
        )

    if (
        purchase_request.status
        != "PENDING_APPROVAL"
    ):
        raise ValueError(
            "Only a PENDING_APPROVAL purchase "
            "request can be approved"
        )

    previous_status = (
        purchase_request.status
    )

    new_status = "APPROVED"

    try:
        purchase_request.status = (
            new_status
        )

        approval = (
            models.PurchaseRequestApproval(
                purchase_request_id=(
                    purchase_request_id
                ),
                action="APPROVED",
                performed_by_user_id=(
                    performed_by_user_id
                ),
                previous_status=(
                    previous_status
                ),
                new_status=new_status,
                comment=comment,
            )
        )

        db.add(
            approval
        )

        db.flush()

        _create_audit_log(
            db=db,
            user_id=performed_by_user_id,
            action=(
                "PURCHASE_REQUEST_APPROVED"
            ),
            purchase_request_id=(
                purchase_request_id
            ),
            details={
                "request_number":
                    purchase_request.request_number,

                "previous_status":
                    previous_status,

                "new_status":
                    new_status,

                "performed_by_user_id":
                    performed_by_user_id,
            },
        )

        resolve_matching_alerts(
            db=db,
            alert_type="PENDING_APPROVAL",
            entity_type="purchase_request",
            entity_id=purchase_request_id,
            resolved_by_user_id=(
                performed_by_user_id
            ),
            resolution_note=(
                "Purchase request approved."
            ),
            commit=False,
        
        )

        db.commit()

        db.refresh(
            purchase_request
        )

        db.refresh(
            approval
        )

        return {
            "purchase_request":
                purchase_request,

            "approval":
                approval,
        }

    except Exception:
        db.rollback()
        raise


def reject_purchase_request(
    db: Session,
    purchase_request_id: int,
    performed_by_user_id: int,
    comment: str | None = None,
):
    """
    Move a purchase request:

    PENDING_APPROVAL -> REJECTED
    """

    user = _get_active_user(
        db,
        performed_by_user_id,
    )

    purchase_request = (
        _get_purchase_request(
            db,
            purchase_request_id,
        )
    )

    if user.role not in ALLOWED_APPROVAL_ROLES:
        raise PermissionError(
            "User role is not allowed to reject "
            "purchase requests"
        )

    if (
        purchase_request.requested_by_user_id
        == performed_by_user_id
    ):
        raise PermissionError(
            "The purchase request creator cannot "
            "reject their own request"
        )

    if (
        purchase_request.status
        != "PENDING_APPROVAL"
    ):
        raise ValueError(
            "Only a PENDING_APPROVAL purchase "
            "request can be rejected"
        )

    if (
        comment is None
        or len(comment.strip()) < 3
    ):
        raise ValueError(
            "A rejection comment is required"
        )

    previous_status = (
        purchase_request.status
    )

    new_status = "REJECTED"

    try:
        purchase_request.status = (
            new_status
        )

        approval = (
            models.PurchaseRequestApproval(
                purchase_request_id=(
                    purchase_request_id
                ),
                action="REJECTED",
                performed_by_user_id=(
                    performed_by_user_id
                ),
                previous_status=(
                    previous_status
                ),
                new_status=new_status,
                comment=comment,
            )
        )

        db.add(
            approval
        )

        db.flush()

        _create_audit_log(
            db=db,
            user_id=performed_by_user_id,
            action=(
                "PURCHASE_REQUEST_REJECTED"
            ),
            purchase_request_id=(
                purchase_request_id
            ),
            details={
                "request_number":
                    purchase_request.request_number,

                "previous_status":
                    previous_status,

                "new_status":
                    new_status,

                "performed_by_user_id":
                    performed_by_user_id,

                "comment":
                    comment,
            },
            )


        resolve_matching_alerts(
            db=db,
            alert_type="PENDING_APPROVAL",
            entity_type="purchase_request",
            entity_id=purchase_request_id,
            resolved_by_user_id=(
                performed_by_user_id
            ),
            resolution_note=(
                "Purchase request rejected."
            ),
            commit=False,
        
        )

        db.commit()

        db.refresh(
            purchase_request
        )

        db.refresh(
            approval
        )

        return {
            "purchase_request":
                purchase_request,

            "approval":
                approval,
        }

    except Exception:
        db.rollback()
        raise


def get_approval_history(
    db: Session,
    purchase_request_id: int,
):
    """
    Return the complete approval history
    for one purchase request.
    """

    _get_purchase_request(
        db,
        purchase_request_id,
    )

    return db.scalars(
        select(
            models.PurchaseRequestApproval
        )
        .where(
            models.PurchaseRequestApproval
            .purchase_request_id
            == purchase_request_id
        )
        .order_by(
            models.PurchaseRequestApproval
            .approval_id
        )
    ).all()