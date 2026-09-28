import json

from fastapi.encoders import jsonable_encoder
from openai import OpenAI
from sqlalchemy.orm import Session

from app import models
from app.agent.tool_definitions import (
    INVENTORY_AGENT_TOOLS,
)
from app.agent.tool_handlers import (
    execute_inventory_tool,
)
from app.config import settings
from app.prompts.inventory_agent import (
    INVENTORY_AGENT_PROMPT_VERSION,
    INVENTORY_AGENT_SYSTEM_PROMPT,
)


client = OpenAI(
    api_key=settings.openai_api_key
)


MAX_TOOL_ROUNDS = 8


# =====================================================
# POLICY / SOP ROUTING
# =====================================================

POLICY_KNOWLEDGE_TERMS = {
    "policy",
    "policies",
    "procedure",
    "procedures",
    "sop",
    "guideline",
    "guidelines",
    "damaged",
    "damage",
    "receiving procedure",
    "receiving process",
    "emergency procurement",
    "emergency purchase",
    "supplier policy",
    "purchasing procedure",
    "procurement procedure",
    "approval procedure",
}


def is_policy_knowledge_question(
    user_message: str,
) -> bool:
    message = user_message.lower()

    return any(
        term in message
        for term in POLICY_KNOWLEDGE_TERMS
    )


# =====================================================
# HUMAN HANDOFF ROUTING
# =====================================================

HANDOFF_TERMS = {
    "escalate",
    "escalation",
    "human review",
    "human reviewer",
    "handoff",
    "hand off",
    "send to a human",
    "refer to a human",
}


def is_explicit_handoff_request(
    user_message: str,
) -> bool:
    """
    Detect an explicit request to escalate
    a case to a human.

    This is deterministic so the model cannot
    merely say 'please escalate' without actually
    creating a handoff record.
    """

    message = user_message.lower()

    return any(
        term in message
        for term in HANDOFF_TERMS
    )


def get_function_tool(
    tool_name: str,
):
    """
    Retrieve exactly one approved function
    definition from the agent allowlist.
    """

    for tool in INVENTORY_AGENT_TOOLS:

        if (
            tool.get("type") == "function"
            and tool.get("name") == tool_name
        ):
            return tool

    raise RuntimeError(
        f"Required agent tool not configured: "
        f"{tool_name}"
    )


# =====================================================
# FILE SEARCH TOOL
# =====================================================

def build_file_search_tool():

    if not settings.openai_vector_store_id:
        raise RuntimeError(
            "Policy knowledge was requested, "
            "but no vector store is configured."
        )

    return {
        "type": "file_search",
        "vector_store_ids": [
            settings.openai_vector_store_id
        ],
        "max_num_results": 5,
    }


# =====================================================
# MAIN INVENTORY AGENT
# =====================================================

def run_inventory_agent(
    db: Session,
    user_message: str,
    user_id: int,
):
    """
    Inventory Agent orchestration.

    Explicit escalation:
        force Human Handoff tool.

    Policy / SOP questions:
        file search.

    Structured operational questions:
        approved database-backed tools.

    A valid active demo user must exist
    before processing begins.
    """

    # =================================================
    # VERIFY ACTING USER
    # =================================================

    user = db.get(
        models.User,
        user_id,
    )

    if user is None or not user.active:
        raise PermissionError(
            "Chat user not found or inactive"
        )

    input_items = [
        {
            "role": "user",
            "content": user_message,
        }
    ]

    tools_used = []

    # =================================================
    # EXPLICIT HUMAN HANDOFF
    # =================================================

    if is_explicit_handoff_request(
        user_message
    ):

        handoff_tool = get_function_tool(
            "create_human_handoff"
        )

        # ---------------------------------------------
        # FORCE THE HANDOFF TOOL CALL
        # ---------------------------------------------

        response = client.responses.create(
            model=settings.openai_model,

            instructions=(
                INVENTORY_AGENT_SYSTEM_PROMPT
                + """

The user has explicitly requested human
escalation.

You MUST create a human handoff.

Choose the most appropriate allowed
reason_code.

Summarize the issue clearly for the human
reviewer.

Do not claim the issue has been resolved.

Do not approve a purchase request, modify
inventory, or bypass authorization.
"""
            ),

            input=input_items,

            tools=[
                handoff_tool
            ],

            tool_choice={
                "type": "function",
                "name": "create_human_handoff",
            },
        )

        input_items.extend(
            response.output
        )

        function_calls = [
            item
            for item in response.output
            if getattr(
                item,
                "type",
                None,
            )
            == "function_call"
        ]

        if not function_calls:
            raise RuntimeError(
                "Explicit handoff was requested, "
                "but the handoff tool was not called."
            )

        for tool_call in function_calls:

            try:
                arguments = json.loads(
                    tool_call.arguments
                )

                result = execute_inventory_tool(
                    db=db,
                    tool_name=tool_call.name,
                    arguments=arguments,
                    actor_user_id=user_id,
                )

                tools_used.append(
                    tool_call.name
                )

                tool_output = {
                    "success": True,
                    "result": result,
                }

            except Exception as exc:

                tool_output = {
                    "success": False,
                    "error": str(exc),
                }

            safe_tool_output = (
                jsonable_encoder(
                    tool_output
                )
            )

            input_items.append(
                {
                    "type":
                        "function_call_output",

                    "call_id":
                        tool_call.call_id,

                    "output":
                        json.dumps(
                            safe_tool_output
                        ),
                }
            )

        # ---------------------------------------------
        # GET FINAL USER-FACING RESPONSE
        # ---------------------------------------------

        final_response = (
            client.responses.create(
                model=settings.openai_model,

                instructions=(
                    INVENTORY_AGENT_SYSTEM_PROMPT
                    + """

A human handoff tool has already been
executed.

Explain the result to the user.

If the tool returned a handoff ID, include it.

Do not say the issue was resolved.

Do not call another tool.
"""
                ),

                input=input_items,

                tools=[
                    handoff_tool
                ],

                tool_choice="none",
            )
        )

        return {
            "answer":
                final_response.output_text,

            "tools_used":
                tools_used,

            "model":
                settings.openai_model,

            "prompt_version":
                INVENTORY_AGENT_PROMPT_VERSION,
        }

    # =================================================
    # POLICY / SOP QUESTION
    # =================================================

    policy_question = (
        is_policy_knowledge_question(
            user_message
        )
    )

    if policy_question:

        file_search_tool = (
            build_file_search_tool()
        )

        response = client.responses.create(
            model=settings.openai_model,

            instructions=(
                INVENTORY_AGENT_SYSTEM_PROMPT
                + """

For this request, you MUST use file search
before answering.

Answer only from the retrieved approved
policy/SOP knowledge.

If the retrieved files do not contain enough
information, say that the procedure could not
be verified from the available documents.

Do not invent company policy.
"""
            ),

            input=input_items,

            tools=[
                file_search_tool
            ],

            tool_choice="required",

            include=[
                "file_search_call.results"
            ],
        )

        output_types = [
            getattr(
                item,
                "type",
                None,
            )
            for item in response.output
        ]

        if (
            "file_search_call"
            in output_types
        ):
            tools_used.append(
                "file_search"
            )

        if (
            "file_search"
            not in tools_used
        ):
            raise RuntimeError(
                "Policy question was detected, "
                "but file search was not executed."
            )

        return {
            "answer":
                response.output_text,

            "tools_used":
                tools_used,

            "model":
                settings.openai_model,

            "prompt_version":
                INVENTORY_AGENT_PROMPT_VERSION,
        }

    # =================================================
    # STRUCTURED OPERATIONAL QUESTION
    # =================================================

    for _ in range(
        MAX_TOOL_ROUNDS
    ):

        response = client.responses.create(
            model=settings.openai_model,

            instructions=(
                INVENTORY_AGENT_SYSTEM_PROMPT
                + """

For this request, use only the supplied
structured operational tools.

Do not use document knowledge as the source
for live inventory, supplier records,
reorder calculations, transaction status,
or other operational facts.
"""
            ),

            input=input_items,

            tools=INVENTORY_AGENT_TOOLS,

            tool_choice="auto",
        )

        input_items.extend(
            response.output
        )

        function_calls = [
            item
            for item in response.output
            if getattr(
                item,
                "type",
                None,
            )
            == "function_call"
        ]

        # =============================================
        # NO TOOL CALLS = FINAL ANSWER
        # =============================================

        if not function_calls:

            return {
                "answer":
                    response.output_text,

                "tools_used":
                    tools_used,

                "model":
                    settings.openai_model,

                "prompt_version":
                    INVENTORY_AGENT_PROMPT_VERSION,
            }

        # =============================================
        # EXECUTE CUSTOM TOOLS
        # =============================================

        for tool_call in function_calls:

            tool_name = (
                tool_call.name
            )

            try:
                arguments = json.loads(
                    tool_call.arguments
                )

                result = (
                    execute_inventory_tool(
                        db=db,
                        tool_name=tool_name,
                        arguments=arguments,
                        actor_user_id=user_id,
                    )
                )

                tools_used.append(
                    tool_name
                )

                tool_output = {
                    "success": True,
                    "result": result,
                }

            except Exception as exc:

                tool_output = {
                    "success": False,
                    "error": str(exc),
                }

            safe_tool_output = (
                jsonable_encoder(
                    tool_output
                )
            )

            input_items.append(
                {
                    "type":
                        "function_call_output",

                    "call_id":
                        tool_call.call_id,

                    "output":
                        json.dumps(
                            safe_tool_output
                        ),
                }
            )

    raise RuntimeError(
        "Agent exceeded maximum tool-call rounds"
    )