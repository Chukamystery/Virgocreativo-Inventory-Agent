import pytest

from sqlalchemy import select

from app import models
from app.services.approval_service import (
    approve_purchase_request,
    get_approval_history,
    reject_purchase_request,
    submit_purchase_request,
)


# =====================================================
# TEST DATA
# =====================================================

@pytest.fixture()
def approval_test_data(
    db_session,
):
    """
    Create users, supplier, and purchase
    requests inside the isolated test DB.
    """

    procurement_user = models.User(
        full_name="Test Procurement Officer",
        role="PROCUREMENT_OFFICER",
        active=True,
    )

    inventory_staff = models.User(
        full_name="Test Inventory Staff",
        role="INVENTORY_STAFF",
        active=True,
    )

    manager = models.User(
        full_name="Test Inventory Manager",
        role="INVENTORY_MANAGER",
        active=True,
    )

    manager_creator = models.User(
        full_name="Test Manager Creator",
        role="INVENTORY_MANAGER",
        active=True,
    )

    admin = models.User(
        full_name="Test Admin",
        role="ADMIN",
        active=True,
    )

    supplier = models.Supplier(
        supplier_code="TEST-SUP-001",
        name="Test Supplier",
        email="supplier@test.example",
        phone="08000000000",
        lead_time_days=5,
        currency="NGN",
        active=True,
    )

    db_session.add_all(
        [
            procurement_user,
            inventory_staff,
            manager,
            manager_creator,
            admin,
            supplier,
        ]
    )

    db_session.commit()

    for record in [
        procurement_user,
        inventory_staff,
        manager,
        manager_creator,
        admin,
        supplier,
    ]:
        db_session.refresh(record)

    procurement_pr = models.PurchaseRequest(
        request_number="TEST-PR-001",
        requested_by_user_id=(
            procurement_user.user_id
        ),
        supplier_id=supplier.supplier_id,
        status="DRAFT",
        notes="Approval workflow test",
    )

    manager_pr = models.PurchaseRequest(
        request_number="TEST-PR-002",
        requested_by_user_id=(
            manager_creator.user_id
        ),
        supplier_id=supplier.supplier_id,
        status="DRAFT",
        notes="Self approval security test",
    )

    rejection_pr = models.PurchaseRequest(
        request_number="TEST-PR-003",
        requested_by_user_id=(
            procurement_user.user_id
        ),
        supplier_id=supplier.supplier_id,
        status="DRAFT",
        notes="Rejection workflow test",
    )

    db_session.add_all(
        [
            procurement_pr,
            manager_pr,
            rejection_pr,
        ]
    )

    db_session.commit()

    db_session.refresh(
        procurement_pr
    )

    db_session.refresh(
        manager_pr
    )

    db_session.refresh(
        rejection_pr
    )

    return {
        "procurement_user":
            procurement_user,

        "inventory_staff":
            inventory_staff,

        "manager":
            manager,

        "manager_creator":
            manager_creator,

        "admin":
            admin,

        "supplier":
            supplier,

        "procurement_pr":
            procurement_pr,

        "manager_pr":
            manager_pr,

        "rejection_pr":
            rejection_pr,
    }


# =====================================================
# TEST 1
# DRAFT -> PENDING_APPROVAL
# =====================================================

def test_procurement_officer_can_submit_draft(
    db_session,
    approval_test_data,
):
    data = approval_test_data

    pr = data[
        "procurement_pr"
    ]

    result = submit_purchase_request(
        db=db_session,
        purchase_request_id=(
            pr.purchase_request_id
        ),
        performed_by_user_id=(
            data[
                "procurement_user"
            ].user_id
        ),
        comment="Ready for manager review",
    )

    assert result["purchase_request"].status == (
        "PENDING_APPROVAL"
    )

    db_session.refresh(pr)

    assert pr.status == (
        "PENDING_APPROVAL"
    )

    history = get_approval_history(
        db=db_session,
        purchase_request_id=(
            pr.purchase_request_id
        ),
    )

    assert len(history) == 1

    assert history[0].action == (
        "SUBMITTED"
    )

    assert history[0].previous_status == (
        "DRAFT"
    )

    assert history[0].new_status == (
        "PENDING_APPROVAL"
    )


# =====================================================
# TEST 2
# INVENTORY_STAFF CANNOT APPROVE
# =====================================================

def test_inventory_staff_cannot_approve_pr(
    db_session,
    approval_test_data,
):
    data = approval_test_data

    pr = data[
        "procurement_pr"
    ]

    submit_purchase_request(
        db=db_session,
        purchase_request_id=(
            pr.purchase_request_id
        ),
        performed_by_user_id=(
            data[
                "procurement_user"
            ].user_id
        ),
        comment="Submit for approval",
    )

    with pytest.raises(
        PermissionError
    ):
        approve_purchase_request(
            db=db_session,
            purchase_request_id=(
                pr.purchase_request_id
            ),
            performed_by_user_id=(
                data[
                    "inventory_staff"
                ].user_id
            ),
            comment=(
                "Unauthorized approval attempt"
            ),
        )

    db_session.rollback()

    db_session.refresh(pr)

    assert pr.status == (
        "PENDING_APPROVAL"
    )


# =====================================================
# TEST 3
# CREATOR CANNOT APPROVE OWN PR
# =====================================================

def test_creator_cannot_approve_own_pr(
    db_session,
    approval_test_data,
):
    data = approval_test_data

    pr = data[
        "manager_pr"
    ]

    submit_purchase_request(
        db=db_session,
        purchase_request_id=(
            pr.purchase_request_id
        ),
        performed_by_user_id=(
            data[
                "manager_creator"
            ].user_id
        ),
        comment="Submitting my request",
    )

    with pytest.raises(
        PermissionError
    ):
        approve_purchase_request(
            db=db_session,
            purchase_request_id=(
                pr.purchase_request_id
            ),
            performed_by_user_id=(
                data[
                    "manager_creator"
                ].user_id
            ),
            comment=(
                "Attempting self approval"
            ),
        )

    db_session.rollback()

    db_session.refresh(pr)

    assert pr.status == (
        "PENDING_APPROVAL"
    )


# =====================================================
# TEST 4
# DIFFERENT MANAGER CAN APPROVE
# =====================================================

def test_different_manager_can_approve_pending_pr(
    db_session,
    approval_test_data,
):
    data = approval_test_data

    pr = data[
        "procurement_pr"
    ]

    submit_purchase_request(
        db=db_session,
        purchase_request_id=(
            pr.purchase_request_id
        ),
        performed_by_user_id=(
            data[
                "procurement_user"
            ].user_id
        ),
        comment="Ready for review",
    )

    result = approve_purchase_request(
        db=db_session,
        purchase_request_id=(
            pr.purchase_request_id
        ),
        performed_by_user_id=(
            data[
                "manager"
            ].user_id
        ),
        comment=(
            "Approved for replenishment"
        ),
    )

    assert result["purchase_request"].status == (
    "APPROVED"
)

    db_session.refresh(pr)

    assert pr.status == (
        "APPROVED"
    )

    history = get_approval_history(
        db=db_session,
        purchase_request_id=(
            pr.purchase_request_id
        ),
    )

    assert len(history) == 2

    assert history[0].action == (
        "SUBMITTED"
    )

    assert history[1].action == (
        "APPROVED"
    )

    assert history[1].previous_status == (
        "PENDING_APPROVAL"
    )

    assert history[1].new_status == (
        "APPROVED"
    )

    assert (
        history[
            1
        ].performed_by_user_id
        == data["manager"].user_id
    )


# =====================================================
# TEST 5
# APPROVED PR CANNOT BE APPROVED AGAIN
# =====================================================

def test_approved_pr_cannot_be_approved_again(
    db_session,
    approval_test_data,
):
    data = approval_test_data

    pr = data[
        "procurement_pr"
    ]

    submit_purchase_request(
        db=db_session,
        purchase_request_id=(
            pr.purchase_request_id
        ),
        performed_by_user_id=(
            data[
                "procurement_user"
            ].user_id
        ),
        comment="Submit",
    )

    approve_purchase_request(
        db=db_session,
        purchase_request_id=(
            pr.purchase_request_id
        ),
        performed_by_user_id=(
            data[
                "manager"
            ].user_id
        ),
        comment="First approval",
    )

    with pytest.raises(
        ValueError
    ):
        approve_purchase_request(
            db=db_session,
            purchase_request_id=(
                pr.purchase_request_id
            ),
            performed_by_user_id=(
                data[
                    "admin"
                ].user_id
            ),
            comment="Second approval attempt",
        )

    db_session.rollback()

    db_session.refresh(pr)

    assert pr.status == (
        "APPROVED"
    )

    history = get_approval_history(
        db=db_session,
        purchase_request_id=(
            pr.purchase_request_id
        ),
    )

    actions = [
        record.action
        for record in history
    ]

    assert actions == [
        "SUBMITTED",
        "APPROVED",
    ]


# =====================================================
# TEST 6
# VALID REJECTION
# =====================================================

def test_manager_can_reject_pending_pr(
    db_session,
    approval_test_data,
):
    data = approval_test_data

    pr = data[
        "rejection_pr"
    ]

    submit_purchase_request(
        db=db_session,
        purchase_request_id=(
            pr.purchase_request_id
        ),
        performed_by_user_id=(
            data[
                "procurement_user"
            ].user_id
        ),
        comment="Requesting approval",
    )

    result = reject_purchase_request(
        db=db_session,
        purchase_request_id=(
            pr.purchase_request_id
        ),
        performed_by_user_id=(
            data[
                "manager"
            ].user_id
        ),
        comment=(
            "Reorder request requires "
            "additional review"
        ),
    )

    assert result["purchase_request"].status == (
        "REJECTED"
    )
    db_session.refresh(pr)

    assert pr.status == (
        "REJECTED"
    )

    history = get_approval_history(
        db=db_session,
        purchase_request_id=(
            pr.purchase_request_id
        ),
    )

    assert len(history) == 2

    assert history[0].action == (
        "SUBMITTED"
    )

    assert history[1].action == (
        "REJECTED"
    )

    assert history[1].previous_status == (
        "PENDING_APPROVAL"
    )

    assert history[1].new_status == (
        "REJECTED"
    )


# =====================================================
# TEST 7
# APPROVAL WORKFLOW CREATES AUDIT LOGS
# =====================================================

def test_approval_workflow_creates_audit_logs(
    db_session,
    approval_test_data,
):
    data = approval_test_data

    pr = data[
        "procurement_pr"
    ]

    submit_purchase_request(
        db=db_session,
        purchase_request_id=(
            pr.purchase_request_id
        ),
        performed_by_user_id=(
            data[
                "procurement_user"
            ].user_id
        ),
        comment="Audit submission",
    )

    approve_purchase_request(
        db=db_session,
        purchase_request_id=(
            pr.purchase_request_id
        ),
        performed_by_user_id=(
            data[
                "manager"
            ].user_id
        ),
        comment="Audit approval",
    )

    audit_logs = db_session.scalars(
        select(
            models.AuditLog
        ).where(
            models.AuditLog.entity_type
            == "purchase_request",

            models.AuditLog.entity_id
            == pr.purchase_request_id,
        )
    ).all()

    assert len(audit_logs) == 2

    actions = {
        log.action
        for log in audit_logs
    }

    assert (
        "PURCHASE_REQUEST_SUBMITTED"
        in actions
    )

    assert (
        "PURCHASE_REQUEST_APPROVED"
        in actions
    )


# =====================================================
# TEST 8
# PENDING APPROVAL ALERT IS RESOLVED
# =====================================================

def test_approval_resolves_pending_alert(
    db_session,
    approval_test_data,
):
    data = approval_test_data

    pr = data[
        "procurement_pr"
    ]

    submit_purchase_request(
        db=db_session,
        purchase_request_id=(
            pr.purchase_request_id
        ),
        performed_by_user_id=(
            data[
                "procurement_user"
            ].user_id
        ),
        comment="Create approval alert",
    )

    alert = db_session.scalar(
        select(
            models.Alert
        ).where(
            models.Alert.alert_type
            == "PENDING_APPROVAL",

            models.Alert.entity_type
            == "purchase_request",

            models.Alert.entity_id
            == pr.purchase_request_id,
        )
    )

    assert alert is not None
    assert alert.status == "OPEN"

    approve_purchase_request(
        db=db_session,
        purchase_request_id=(
            pr.purchase_request_id
        ),
        performed_by_user_id=(
            data[
                "manager"
            ].user_id
        ),
        comment="Approve and close alert",
    )

    db_session.refresh(alert)

    assert alert.status == (
        "RESOLVED"
    )

    assert (
        alert.resolved_by_user_id
        == data["manager"].user_id
    )

    assert alert.resolved_at is not None