from app import models


# =====================================================
# TEST 1
# UNKNOWN USER RETURNS 403
# =====================================================

def test_unknown_agent_user_returns_403(
    client,
):
    """
    Unknown users should be rejected before
    the LLM is called.
    """

    response = client.post(
        "/agent/chat",
        json={
            "message":
                "Show me current inventory.",

            "user_id":
                999999,
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail":
            "Chat user not found or inactive"
    }


# =====================================================
# TEST 2
# INACTIVE USER RETURNS 403
# =====================================================

def test_inactive_agent_user_returns_403(
    client,
    test_database,
):
    """
    An inactive user should receive a
    controlled authorization response.
    """

    SessionLocal = (
        test_database[
            "session_factory"
        ]
    )

    db = SessionLocal()

    user = models.User(
        full_name="Inactive API User",
        role="PROCUREMENT_OFFICER",
        active=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    user_id = user.user_id

    db.close()

    response = client.post(
        "/agent/chat",
        json={
            "message":
                "Show me current inventory.",

            "user_id":
                user_id,
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail":
            "Chat user not found or inactive"
    }


# =====================================================
# TEST 3
# MISSING USER ID RETURNS 422
# =====================================================

def test_missing_user_id_returns_validation_error(
    client,
):
    """
    AgentChatRequest requires user_id.

    FastAPI/Pydantic should reject malformed
    requests before they reach the agent.
    """

    response = client.post(
        "/agent/chat",
        json={
            "message":
                "Show me current inventory."
        },
    )

    assert response.status_code == 422


# =====================================================
# TEST 4
# INVALID USER ID VALUE RETURNS 422
# =====================================================

def test_invalid_user_id_returns_validation_error(
    client,
):
    """
    user_id must be greater than zero.
    """

    response = client.post(
        "/agent/chat",
        json={
            "message":
                "Show me inventory.",

            "user_id":
                0,
        },
    )

    assert response.status_code == 422


# =====================================================
# TEST 5
# INTERNAL ERROR DOES NOT LEAK DETAILS
# =====================================================

def test_internal_agent_error_is_sanitized(
    client,
    test_database,
    monkeypatch,
):
    """
    Unexpected backend errors should produce
    a generic 500 response.

    Sensitive/internal exception text must
    not be returned to the caller.
    """

    SessionLocal = (
        test_database[
            "session_factory"
        ]
    )

    db = SessionLocal()

    user = models.User(
        full_name="Active API User",
        role="PROCUREMENT_OFFICER",
        active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    user_id = user.user_id

    db.close()

    def fake_agent_failure(
        db,
        user_message,
        user_id,
    ):
        raise RuntimeError(
            "SECRET_DATABASE_PASSWORD=abc123"
        )

    monkeypatch.setattr(
        "app.routers.agent.run_inventory_agent",
        fake_agent_failure,
    )

    response = client.post(
        "/agent/chat",
        json={
            "message":
                "Test internal failure.",

            "user_id":
                user_id,
        },
    )

    assert response.status_code == 500

    body = response.json()

    assert body == {
        "detail":
            "Inventory Agent encountered "
            "an internal error."
    }

    assert (
        "SECRET_DATABASE_PASSWORD"
        not in response.text
    )

    assert "abc123" not in response.text


# =====================================================
# TEST 6
# VALID AGENT RESPONSE FORMAT
# =====================================================

def test_valid_agent_response_structure(
    client,
    test_database,
    monkeypatch,
):
    """
    Mock the actual LLM so this test does not
    consume OpenAI API credits.
    """

    SessionLocal = (
        test_database[
            "session_factory"
        ]
    )

    db = SessionLocal()

    user = models.User(
        full_name="Valid API User",
        role="PROCUREMENT_OFFICER",
        active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    user_id = user.user_id

    db.close()

    def fake_successful_agent(
        db,
        user_message,
        user_id,
    ):
        return {
            "answer":
                "Verified inventory response.",

            "tools_used":
                [
                    "get_inventory_balance"
                ],

            "model":
                "test-model",

            "prompt_version":
                "1.0.0",
        }

    monkeypatch.setattr(
        "app.routers.agent.run_inventory_agent",
        fake_successful_agent,
    )

    response = client.post(
        "/agent/chat",
        json={
            "message":
                "How much inventory do we have?",

            "user_id":
                user_id,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["answer"]
        == "Verified inventory response."
    )

    assert body["tools_used"] == [
        "get_inventory_balance"
    ]

    assert body["model"] == "test-model"

    assert (
        body["prompt_version"]
        == "1.0.0"
    )

def test_internal_failure_is_logged(
    client,
    test_database,
    monkeypatch,
    caplog,
):
    """
    Internal failures should be logged for
    developers while remaining hidden from
    the API caller.
    """

    import logging

    SessionLocal = (
        test_database[
            "session_factory"
        ]
    )

    db = SessionLocal()

    user = models.User(
        full_name="Logging Test User",
        role="PROCUREMENT_OFFICER",
        active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    user_id = user.user_id

    db.close()

    def fake_agent_failure(
        db,
        user_message,
        user_id,
    ):
        raise RuntimeError(
            "Simulated internal database failure"
        )

    monkeypatch.setattr(
        "app.routers.agent.run_inventory_agent",
        fake_agent_failure,
    )

    with caplog.at_level(
        logging.ERROR
    ):
        response = client.post(
            "/agent/chat",
            json={
                "message":
                    "Trigger logging test.",

                "user_id":
                    user_id,
            },
        )

    assert response.status_code == 500

    assert response.json() == {
        "detail":
            "Inventory Agent encountered "
            "an internal error."
    }

    assert (
        "Unexpected Inventory Agent failure"
        in caplog.text
    )

    assert (
        "Simulated internal database failure"
        in caplog.text
    )