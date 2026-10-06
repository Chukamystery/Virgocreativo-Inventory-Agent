import logging


# =====================================================
# TEST 1
# UNAUTHENTICATED USER IS BLOCKED
# =====================================================

def test_unauthenticated_agent_request_returns_401(
    client,
):
    """
    The AI Agent must not be usable without
    authentication.
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

    assert response.status_code == 401

    assert response.json() == {
        "detail":
            "Authentication required."
    }


# =====================================================
# TEST 2
# BODY USER ID CANNOT SPOOF IDENTITY
# =====================================================

def test_agent_uses_authenticated_user_not_body_user_id(
    authenticated_client,
    authenticated_user,
    monkeypatch,
):
    """
    A caller must not be able to impersonate
    another user by changing user_id in the
    request body.
    """

    captured = {}

    def fake_successful_agent(
        db,
        user_message,
        user_id,
    ):
        captured["user_id"] = user_id

        return {
            "answer":
                "Authenticated response.",

            "tools_used":
                [],

            "model":
                "test-model",

            "prompt_version":
                "1.0.0",
        }

    monkeypatch.setattr(
        "app.routers.agent.run_inventory_agent",
        fake_successful_agent,
    )

    response = authenticated_client.post(
        "/agent/chat",
        json={
            "message":
                "Show me current inventory.",

            # Deliberately claim to be another user.
            "user_id":
                999999,
        },
    )

    assert response.status_code == 200

    # The backend must ignore the claimed ID
    # and use the authenticated account.
    assert (
        captured["user_id"]
        == authenticated_user.user_id
    )

    assert (
        captured["user_id"]
        != 999999
    )


# =====================================================
# TEST 3
# MISSING USER ID STILL FAILS SCHEMA VALIDATION
# =====================================================

def test_missing_user_id_returns_validation_error(
    authenticated_client,
):
    """
    user_id is still part of the current
    request schema for compatibility.

    Authentication must succeed first so the
    request can reach Pydantic validation.
    """

    response = authenticated_client.post(
        "/agent/chat",
        json={
            "message":
                "Show me current inventory."
        },
    )

    assert response.status_code == 422


# =====================================================
# TEST 4
# INVALID USER ID STILL FAILS SCHEMA VALIDATION
# =====================================================

def test_invalid_user_id_returns_validation_error(
    authenticated_client,
):
    """
    The compatibility user_id field must still
    satisfy its current validation rules.
    """

    response = authenticated_client.post(
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
    authenticated_client,
    authenticated_user,
    monkeypatch,
):
    """
    Unexpected backend errors should produce
    a generic 500 response.

    Sensitive/internal exception text must
    never be returned to the caller.
    """

    def fake_agent_failure(
        db,
        user_message,
        user_id,
    ):
        assert (
            user_id
            == authenticated_user.user_id
        )

        raise RuntimeError(
            "SECRET_DATABASE_PASSWORD=abc123"
        )

    monkeypatch.setattr(
        "app.routers.agent.run_inventory_agent",
        fake_agent_failure,
    )

    response = authenticated_client.post(
        "/agent/chat",
        json={
            "message":
                "Test internal failure.",

            "user_id":
                999999,
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
# VALID AUTHENTICATED AGENT RESPONSE
# =====================================================

def test_valid_agent_response_structure(
    authenticated_client,
    authenticated_user,
    monkeypatch,
):
    """
    Mock the actual LLM so this test does not
    consume OpenAI API credits.
    """

    def fake_successful_agent(
        db,
        user_message,
        user_id,
    ):
        assert (
            user_id
            == authenticated_user.user_id
        )

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

    response = authenticated_client.post(
        "/agent/chat",
        json={
            "message":
                "How much inventory do we have?",

            # Deliberately not the real ID.
            "user_id":
                999999,
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

    assert (
        body["model"]
        == "test-model"
    )

    assert (
        body["prompt_version"]
        == "1.0.0"
    )


# =====================================================
# TEST 7
# INTERNAL FAILURE IS LOGGED
# =====================================================

def test_internal_failure_is_logged(
    authenticated_client,
    authenticated_user,
    monkeypatch,
    caplog,
):
    """
    Internal failures should be logged for
    developers while remaining hidden from
    the API caller.
    """

    def fake_agent_failure(
        db,
        user_message,
        user_id,
    ):
        assert (
            user_id
            == authenticated_user.user_id
        )

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
        response = authenticated_client.post(
            "/agent/chat",
            json={
                "message":
                    "Trigger logging test.",

                "user_id":
                    999999,
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