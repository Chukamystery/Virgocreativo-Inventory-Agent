from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# =====================================================
# CURRENT LOGGED-IN USER
# =====================================================

@router.get("/me")
def get_my_profile(
    current_user: User = Depends(
        get_current_user
    ),
):
    return {
        "user_id":
            current_user.user_id,

        "full_name":
            current_user.full_name,

        "role":
            current_user.role,

        "business_role":
            current_user.business_role,

        "active":
            current_user.active,

        "auth_user_id":
            current_user.auth_user_id,
    }


# =====================================================
# ACTIVE BUSINESS USERS
# =====================================================

@router.get("/users")
def list_active_users(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Return active Inventory Agent users.

    This allows the dashboard to display
    real employee names instead of labels
    such as 'User 5'.
    """

    statement = (
        select(User)
        .where(
            User.active.is_(True)
        )
        .order_by(
            User.user_id
        )
    )

    users = db.scalars(
        statement
    ).all()

    return [
        {
            "user_id":
                user.user_id,

            "full_name":
                user.full_name,

            "role":
                user.role,

            "business_role":
                user.business_role,
        }
        for user in users
    ]