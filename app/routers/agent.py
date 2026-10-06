from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app import schemas
from app.agent.agent_service import (
    run_inventory_agent,
)
from app.auth import get_current_user
from app.database import get_db
from app.logging_config import (
    get_logger,
)
from app.models import User


logger = get_logger(
    __name__
)

router = APIRouter(
    prefix="/agent",
    tags=["Inventory Agent"],
)


@router.post(
    "/chat",
    response_model=schemas.AgentChatResponse,
)
def chat_with_inventory_agent(
    request: schemas.AgentChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a message to the Inventory Agent.

    The authenticated user's identity is used.
    Any user_id supplied by the client is ignored.

    Error handling rules:

    PermissionError
        -> 403 Forbidden

    ValueError
        -> 400 Bad Request

    Unexpected/internal errors
        -> 500 with a generic message

    Internal exception details are deliberately
    not returned to the API caller.
    """

    try:
        return run_inventory_agent(
            db=db,
            user_message=request.message,
            user_id=current_user.user_id,
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception:
        logger.exception(
            "Unexpected Inventory Agent failure"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Inventory Agent encountered "
                "an internal error."
            ),
        )