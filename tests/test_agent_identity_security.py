import pytest

from sqlalchemy import select

from app import models
from app.agent.agent_service import (
    run_inventory_agent,
)
from app.agent.tool_handlers import (
    execute_inventory_tool,
)


@pytest.fixture()
def agent_identity_users(
    db_session,
):
    """
    Create one active user and one inactive
    user in the isolated test database.
    """

    active_user = models.User(
        full_name="Active Procurement User",
        role="PROCUREMENT_OFFICER",
        active=True,
    )

    inactive_user = models.User(
        full_name="Inactive Procurement User",
        role="PROCUREMENT_OFFICER",
        active=False,
    )

    db_session.add_all(
        [
            active_user,
            inactive_user,
        ]
    )

    db_session.commit()

    db_session.refresh(active_user)
    db_session.refresh(inactive_user)

    return {
        "active":
            active_user,

        "inactive":
            inactive_user,
    }


# =====================================================
# TEST 1
# UNKNOWN CHAT USER IS BLOCKED
# =====================================================

def test_unknown_chat_user_is_blocked(
    db_session,
):
    """
    User validation happens before the LLM
    is called.

    Therefore an unknown user should fail
    immediately.
    """

    with pytest.raises(
        PermissionError,
        match="Chat user not found or inactive",
    ):
        run_inventory_agent(
            db=db_session,
            user_message=(
                "How many items are in stock?"
            ),
            user_id=999999,
        )


# =====================================================
# TEST 2
# INACTIVE CHAT USER IS BLOCKED
# =====================================================

def test_inactive_chat_user_is_blocked(
    db_session,
    agent_identity_users,
):
    """
    An existing but inactive user must not
    be allowed to use the Inventory Agent.
    """

    inactive_user = (
        agent_identity_users["inactive"]
    )

    with pytest.raises(
        PermissionError,
        match="Chat user not found or inactive",
    ):
        run_inventory_agent(
            db=db_session,
            user_message=(
                "Show me the current inventory."
            ),
            user_id=inactive_user.user_id,
        )


# =====================================================
# TEST 3
# HANDOFF REQUIRES AN ACTOR
# =====================================================

def test_handoff_tool_requires_actor_user(
    db_session,
):
    """
    The AI cannot create an auditable
    handoff without an acting user.
    """

    with pytest.raises(
        ValueError,
        match="verified acting user",
    ):
        execute_inventory_tool(
            db=db_session,
            tool_name="create_human_handoff",
            arguments={
                "reason_code":
                    "UNSUPPORTED_ACTION",

                "summary":
                    "Unsupported action requires review.",

                "entity_type":
                    "inventory",

                "entity_id":
                    1,
            },
            actor_user_id=None,
        )


# =====================================================
# TEST 4
# VERIFIED USER CAN CREATE HANDOFF
# =====================================================

def test_verified_actor_is_recorded_on_handoff(
    db_session,
    agent_identity_users,
):
    """
    A valid actor should be written into
    the HumanHandoff record.
    """

    active_user = (
        agent_identity_users["active"]
    )

    result = execute_inventory_tool(
        db=db_session,
        tool_name="create_human_handoff",
        arguments={
            "reason_code":
                "UNSUPPORTED_ACTION",

            "summary":
                "Unsupported inventory operation "
                "requires human review.",

            "entity_type":
                "inventory",

            "entity_id":
                123,
        },
        actor_user_id=(
            active_user.user_id
        ),
    )

    assert result["created"] is True

    assert result["status"] == "OPEN"

    assert (
        result["requested_by_user_id"]
        == active_user.user_id
    )

    handoff = db_session.get(
        models.HumanHandoff,
        result["handoff_id"],
    )

    assert handoff is not None

    assert (
        handoff.requested_by_user_id
        == active_user.user_id
    )


# =====================================================
# TEST 5
# HANDOFF AUDIT USES SAME ACTOR
# =====================================================

def test_agent_handoff_audit_uses_verified_actor(
    db_session,
    agent_identity_users,
):
    """
    The handoff and its audit entry must
    identify the same user.
    """

    active_user = (
        agent_identity_users["active"]
    )

    result = execute_inventory_tool(
        db=db_session,
        tool_name="create_human_handoff",
        arguments={
            "reason_code":
                "TOOL_FAILURE",

            "summary":
                "A tool failure requires "
                "human investigation.",

            "entity_type":
                "inventory",

            "entity_id":
                456,
        },
        actor_user_id=(
            active_user.user_id
        ),
    )

    handoff_id = result[
        "handoff_id"
    ]

    audit = db_session.scalar(
        select(
            models.AuditLog
        ).where(
            models.AuditLog.action
            == "HUMAN_HANDOFF_CREATED",

            models.AuditLog.entity_type
            == "human_handoff",

            models.AuditLog.entity_id
            == handoff_id,
        )
    )

    assert audit is not None

    assert (
        audit.user_id
        == active_user.user_id
    )