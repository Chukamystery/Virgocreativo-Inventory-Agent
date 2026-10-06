from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.models import User


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.get("/me")
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return {
        "user_id": current_user.user_id,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "active": current_user.active,
        "auth_user_id": current_user.auth_user_id,
    }