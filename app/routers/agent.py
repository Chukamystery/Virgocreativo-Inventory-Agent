from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.logging_config import (
    get_logger,
)

from sqlalchemy.orm import Session

from app import schemas
from app.agent.agent_service import (
    run_inventory_agent,
)
from app.database import get_db


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
    db: Session = Depends(get_db),
):
    """
    Send a message to the Inventory Agent.

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
            user_id=request.user_id,
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