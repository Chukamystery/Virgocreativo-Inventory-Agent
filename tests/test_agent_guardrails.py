import pytest

from app.agent.agent_service import (
    is_explicit_handoff_request,
    is_policy_knowledge_question,
)
from app.agent.tool_definitions import (
    INVENTORY_AGENT_TOOLS,
)
from app.agent.tool_handlers import (
    execute_inventory_tool,
)


# =====================================================
# HELPER
# =====================================================

def get_agent_tool_names():
    """
    Return the names of every custom function
    currently exposed to the LLM.
    """

    return {
        tool["name"]
        for tool in INVENTORY_AGENT_TOOLS
        if tool.get("type") == "function"
    }


# =====================================================
# TEST 1
# APPROVAL TOOL MUST NOT BE EXPOSED
# =====================================================

def test_agent_cannot_directly_approve_purchase_requests():
    """
    The LLM must never receive a direct
    purchase-request approval tool.
    """

    tool_names = get_agent_tool_names()

    assert (
        "approve_purchase_request"
        not in tool_names
    )


# =====================================================
# TEST 2
# STOCK OVERWRITE TOOL MUST NOT EXIST
# =====================================================

def test_agent_cannot_directly_overwrite_inventory():
    """
    There must be no generic inventory
    update/set/overwrite tool exposed.
    """

    tool_names = get_agent_tool_names()

    forbidden_tools = {
        "update_inventory",
        "set_inventory",
        "overwrite_inventory",
        "set_stock_quantity",
        "update_stock_quantity",
        "patch_inventory",
    }

    assert tool_names.isdisjoint(
        forbidden_tools
    )


# =====================================================
# TEST 3
# PURCHASE-REQUEST REJECTION NOT EXPOSED
# =====================================================

def test_agent_cannot_directly_reject_purchase_requests():
    """
    Approval decisions remain human-controlled.
    """

    tool_names = get_agent_tool_names()

    assert (
        "reject_purchase_request"
        not in tool_names
    )


# =====================================================
# TEST 4
# HANDOFF TOOL IS EXPOSED
# =====================================================

def test_agent_can_create_human_handoff():
    """
    Human escalation is deliberately exposed
    because it is a controlled low-risk action.
    """

    tool_names = get_agent_tool_names()

    assert (
        "create_human_handoff"
        in tool_names
    )


# =====================================================
# TEST 5
# EXPECTED READ-ONLY TOOLS ARE AVAILABLE
# =====================================================

def test_expected_read_tools_are_available():
    """
    The LLM should still be able to read
    verified operational information.
    """

    tool_names = get_agent_tool_names()

    expected = {
        "find_products",
        "find_locations",
        "get_inventory_balance",
        "get_reorder_recommendation",
        "list_low_stock_items",
        "get_supplier_options",
    }

    assert expected.issubset(
        tool_names
    )


# =====================================================
# TEST 6
# UNKNOWN TOOL IS BLOCKED BY DISPATCHER
# =====================================================

def test_unknown_tool_is_blocked(
    db_session,
):
    """
    Even if the model somehow asks for a
    function that is not allowlisted, the
    backend dispatcher must reject it.
    """

    with pytest.raises(
        ValueError,
        match="Tool not allowed",
    ):
        execute_inventory_tool(
            db=db_session,
            tool_name="delete_all_inventory",
            arguments={},
            actor_user_id=1,
        )


# =====================================================
# TEST 7
# POLICY ROUTING
# =====================================================

def test_policy_question_is_detected():
    """
    SOP/policy questions should route to
    document retrieval instead of operational
    database tools.
    """

    assert (
        is_policy_knowledge_question(
            "What is our damaged goods procedure?"
        )
        is True
    )


# =====================================================
# TEST 8
# NORMAL INVENTORY QUESTION IS NOT POLICY
# =====================================================

def test_inventory_question_is_not_policy_question():
    """
    Live inventory questions must not be
    answered from RAG documents.
    """

    assert (
        is_policy_knowledge_question(
            "How many Wireless Mouse units "
            "are in Main Warehouse?"
        )
        is False
    )


# =====================================================
# TEST 9
# EXPLICIT HANDOFF ROUTING
# =====================================================

def test_explicit_handoff_request_is_detected():
    """
    Explicit escalation should deterministically
    enter the handoff path.
    """

    assert (
        is_explicit_handoff_request(
            "Escalate this to a human reviewer."
        )
        is True
    )


# =====================================================
# TEST 10
# NORMAL QUESTION DOES NOT FORCE HANDOFF
# =====================================================

def test_normal_question_does_not_force_handoff():
    """
    Ordinary operational questions should
    not automatically create handoffs.
    """

    assert (
        is_explicit_handoff_request(
            "What is the current stock level?"
        )
        is False
    )