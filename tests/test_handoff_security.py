import pytest

from sqlalchemy import select

from app import models
from app.services.handoff_service import (
    create_handoff,
    get_handoffs,
    resolve_handoff,
)


# =====================================================
# TEST DATA
# =====================================================

@pytest.fixture()
def handoff_test_data(
    db_session,
):
    """
    Create users with different roles for
    testing human-handoff security.
    """

    staff_user = models.User(
        full_name="Test Inventory Staff",
        role="INVENTORY_STAFF",
        active=True,
    )

    procurement_user = models.User(
        full_name="Test Procurement Officer",
        role="PROCUREMENT_OFFICER",
        active=True,
    )

    manager_user = models.User(
        full_name="Test Inventory Manager",
        role="INVENTORY_MANAGER",
        active=True,
    )

    admin_user = models.User(
        full_name="Test Admin",
        role="ADMIN",
        active=True,
    )

    db_session.add_all(
        [
            staff_user,
            procurement_user,
            manager_user,
            admin_user,
        ]
    )

    db_session.commit()

    for user in [
        staff_user,
        procurement_user,
        manager_user,
        admin_user,
    ]:
        db_session.refresh(user)

    return {
        "staff":
            staff_user,

        "procurement":
            procurement_user,

        "manager":
            manager_user,

        "admin":
            admin_user,
    }


# =====================================================
# TEST 1
# CREATE HANDOFF
# =====================================================

def test_create_handoff(
    db_session,
    handoff_test_data,
):
    """
    Creating a valid handoff should create
    an OPEN persistent handoff record.
    """

    data = handoff_test_data

    result = create_handoff(
        db=db_session,
        reason_code="SUPPLIER_SELECTION",
        summary=(
            "Multiple suppliers require "
            "human review."
        ),
        entity_type="product",
        entity_id=2,
        requested_by_user_id=(
            data["procurement"].user_id
        ),
        context={
            "product":
                "Test Product",
        },
    )

    assert result["created"] is True

    handoff = result["handoff"]

    assert handoff.status == "OPEN"

    assert (
        handoff.reason_code
        == "SUPPLIER_SELECTION"
    )

    assert (
        handoff.requested_by_user_id
        == data["procurement"].user_id
    )

    assert handoff.assigned_to_user_id is None

    assert handoff.resolved_at is None


# =====================================================
# TEST 2
# DUPLICATE OPEN HANDOFF IS PREVENTED
# =====================================================

def test_duplicate_open_handoff_is_prevented(
    db_session,
    handoff_test_data,
):
    """
    The same OPEN handoff reason/entity
    should not create duplicate records.
    """

    data = handoff_test_data

    first_result = create_handoff(
        db=db_session,
        reason_code="SUPPLIER_SELECTION",
        summary="First supplier review request",
        entity_type="product",
        entity_id=2,
        requested_by_user_id=(
            data["procurement"].user_id
        ),
        context={
            "test":
                "first",
        },
    )

    second_result = create_handoff(
        db=db_session,
        reason_code="SUPPLIER_SELECTION",
        summary="Duplicate supplier review request",
        entity_type="product",
        entity_id=2,
        requested_by_user_id=(
            data["procurement"].user_id
        ),
        context={
            "test":
                "duplicate",
        },
    )

    assert first_result["created"] is True

    assert second_result["created"] is False

    assert (
        first_result[
            "handoff"
        ].handoff_id
        ==
        second_result[
            "handoff"
        ].handoff_id
    )

    handoffs = db_session.scalars(
        select(
            models.HumanHandoff
        )
    ).all()

    assert len(handoffs) == 1


# =====================================================
# TEST 3
# HANDOFF CREATES ALERT
# =====================================================

def test_handoff_creates_open_alert(
    db_session,
    handoff_test_data,
):
    """
    Every new human handoff should also
    create an OPEN HUMAN_HANDOFF alert.
    """

    data = handoff_test_data

    result = create_handoff(
        db=db_session,
        reason_code="UNSUPPORTED_ACTION",
        summary=(
            "Unsupported inventory operation "
            "requires review."
        ),
        entity_type="inventory",
        entity_id=10,
        requested_by_user_id=(
            data["procurement"].user_id
        ),
        context={
            "requested_action":
                "unsupported operation",
        },
    )

    handoff = result["handoff"]

    alert = db_session.scalar(
        select(
            models.Alert
        ).where(
            models.Alert.alert_type
            == "HUMAN_HANDOFF",

            models.Alert.entity_type
            == "human_handoff",

            models.Alert.entity_id
            == handoff.handoff_id,
        )
    )

    assert alert is not None

    assert alert.status == "OPEN"

    assert alert.severity == "WARNING"


# =====================================================
# TEST 4
# INVENTORY STAFF CANNOT RESOLVE
# =====================================================

def test_inventory_staff_cannot_resolve_handoff(
    db_session,
    handoff_test_data,
):
    """
    INVENTORY_STAFF is not allowed to
    resolve human handoffs.
    """

    data = handoff_test_data

    result = create_handoff(
        db=db_session,
        reason_code="CONFLICTING_DATA",
        summary=(
            "Conflicting inventory data "
            "requires human investigation."
        ),
        entity_type="inventory",
        entity_id=20,
        requested_by_user_id=(
            data["procurement"].user_id
        ),
    )

    handoff = result["handoff"]

    with pytest.raises(
        PermissionError
    ):
        resolve_handoff(
            db=db_session,
            handoff_id=handoff.handoff_id,
            performed_by_user_id=(
                data["staff"].user_id
            ),
            resolution_note=(
                "Unauthorized attempt"
            ),
        )

    db_session.rollback()

    db_session.refresh(handoff)

    assert handoff.status == "OPEN"

    assert handoff.assigned_to_user_id is None

    assert handoff.resolved_at is None


# =====================================================
# TEST 5
# MANAGER CAN RESOLVE
# =====================================================

def test_manager_can_resolve_handoff(
    db_session,
    handoff_test_data,
):
    """
    An Inventory Manager should be allowed
    to resolve an OPEN handoff.
    """

    data = handoff_test_data

    result = create_handoff(
        db=db_session,
        reason_code="TOOL_FAILURE",
        summary=(
            "Inventory tool failure requires "
            "human review."
        ),
        entity_type="inventory",
        entity_id=30,
        requested_by_user_id=(
            data["procurement"].user_id
        ),
    )

    handoff = result["handoff"]

    resolved = resolve_handoff(
        db=db_session,
        handoff_id=handoff.handoff_id,
        performed_by_user_id=(
            data["manager"].user_id
        ),
        resolution_note=(
            "Tool issue reviewed and resolved."
        ),
    )

    assert resolved.status == "RESOLVED"

    assert (
        resolved.assigned_to_user_id
        == data["manager"].user_id
    )

    assert (
        resolved.resolution_note
        == "Tool issue reviewed and resolved."
    )

    assert resolved.resolved_at is not None


# =====================================================
# TEST 6
# RESOLVING HANDOFF RESOLVES ALERT
# =====================================================

def test_resolving_handoff_resolves_alert(
    db_session,
    handoff_test_data,
):
    """
    Resolving a handoff should automatically
    resolve the linked HUMAN_HANDOFF alert.
    """

    data = handoff_test_data

    result = create_handoff(
        db=db_session,
        reason_code="HIGH_RISK_EXCEPTION",
        summary=(
            "High-risk exception requires "
            "manager review."
        ),
        entity_type="purchase_request",
        entity_id=50,
        requested_by_user_id=(
            data["procurement"].user_id
        ),
    )

    handoff = result["handoff"]

    alert = db_session.scalar(
        select(
            models.Alert
        ).where(
            models.Alert.alert_type
            == "HUMAN_HANDOFF",

            models.Alert.entity_type
            == "human_handoff",

            models.Alert.entity_id
            == handoff.handoff_id,
        )
    )

    assert alert is not None
    assert alert.status == "OPEN"

    resolve_handoff(
        db=db_session,
        handoff_id=handoff.handoff_id,
        performed_by_user_id=(
            data["manager"].user_id
        ),
        resolution_note=(
            "Human review completed."
        ),
    )

    db_session.refresh(alert)

    assert alert.status == "RESOLVED"

    assert (
        alert.resolved_by_user_id
        == data["manager"].user_id
    )

    assert alert.resolved_at is not None


# =====================================================
# TEST 7
# HANDOFF CREATION + RESOLUTION CREATE AUDIT LOGS
# =====================================================

def test_handoff_workflow_creates_audit_logs(
    db_session,
    handoff_test_data,
):
    """
    Both handoff creation and resolution
    must leave audit evidence.
    """

    data = handoff_test_data

    result = create_handoff(
        db=db_session,
        reason_code="UNSUPPORTED_ACTION",
        summary=(
            "Unsupported action sent for "
            "human review."
        ),
        entity_type="product",
        entity_id=99,
        requested_by_user_id=(
            data["procurement"].user_id
        ),
    )

    handoff = result["handoff"]

    resolve_handoff(
        db=db_session,
        handoff_id=handoff.handoff_id,
        performed_by_user_id=(
            data["manager"].user_id
        ),
        resolution_note=(
            "Case reviewed by manager."
        ),
    )

    audit_logs = db_session.scalars(
        select(
            models.AuditLog
        ).where(
            models.AuditLog.entity_type
            == "human_handoff",

            models.AuditLog.entity_id
            == handoff.handoff_id,
        )
    ).all()

    assert len(audit_logs) == 2

    actions = {
        log.action
        for log in audit_logs
    }

    assert (
        "HUMAN_HANDOFF_CREATED"
        in actions
    )

    assert (
        "HUMAN_HANDOFF_RESOLVED"
        in actions
    )

    create_log = next(
        log
        for log in audit_logs
        if log.action
        == "HUMAN_HANDOFF_CREATED"
    )

    resolve_log = next(
        log
        for log in audit_logs
        if log.action
        == "HUMAN_HANDOFF_RESOLVED"
    )

    assert (
        create_log.user_id
        == data["procurement"].user_id
    )

    assert (
        resolve_log.user_id
        == data["manager"].user_id
    )


# =====================================================
# TEST 8
# GET OPEN HANDOFFS
# =====================================================

def test_get_open_handoffs(
    db_session,
    handoff_test_data,
):
    """
    get_handoffs(status='OPEN') should return
    only unresolved cases.
    """

    data = handoff_test_data

    first = create_handoff(
        db=db_session,
        reason_code="TOOL_FAILURE",
        summary="First open handoff",
        entity_type="inventory",
        entity_id=101,
        requested_by_user_id=(
            data["procurement"].user_id
        ),
    )

    second = create_handoff(
        db=db_session,
        reason_code="CONFLICTING_DATA",
        summary="Second handoff",
        entity_type="inventory",
        entity_id=102,
        requested_by_user_id=(
            data["procurement"].user_id
        ),
    )

    resolve_handoff(
        db=db_session,
        handoff_id=(
            second["handoff"].handoff_id
        ),
        performed_by_user_id=(
            data["manager"].user_id
        ),
        resolution_note=(
            "Second case resolved."
        ),
    )

    open_handoffs = get_handoffs(
        db=db_session,
        status="OPEN",
    )

    assert len(open_handoffs) == 1

    assert (
        open_handoffs[0].handoff_id
        == first["handoff"].handoff_id
    )

    assert (
        open_handoffs[0].status
        == "OPEN"
    )