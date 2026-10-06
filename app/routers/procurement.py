from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app import schemas
from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.services.approval_service import (
    approve_purchase_request,
    get_approval_history,
    reject_purchase_request,
    submit_purchase_request,
)
from app.services.procurement_service import (
    get_purchase_request_lines,
    get_purchase_requests,
    prepare_purchase_request,
)


router = APIRouter(
    prefix="/purchase-requests",
    tags=["Procurement"],
    dependencies=[
        Depends(get_current_user)
    ],
)


# =====================================================
# PREPARE DRAFT
# =====================================================

@router.post(
    "/prepare",
    status_code=status.HTTP_201_CREATED,
)
def prepare_request(
    request: schemas.PreparePurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = prepare_purchase_request(
            db=db,
            product_id=request.product_id,
            location_id=request.location_id,
            requested_by_user_id=current_user.user_id,
            notes=request.notes,
        )

        header = result["purchase_request"]
        lines = result["lines"]
        supplier = result["supplier"]

        return {
            "purchase_request_id":
                header.purchase_request_id,

            "request_number":
                header.request_number,

            "status":
                header.status,

            "supplier": {
                "supplier_id":
                    supplier["supplier_id"],

                "supplier_name":
                    supplier["supplier_name"],
            },

            "requested_by_user_id":
                header.requested_by_user_id,

            "notes":
                header.notes,

            "lines": [
                {
                    "purchase_request_line_id":
                        line.purchase_request_line_id,

                    "product_id":
                        line.product_id,

                    "location_id":
                        line.location_id,

                    "quantity":
                        line.quantity,

                    "unit_cost":
                        line.unit_cost,

                    "reorder_recommendation":
                        line.reorder_recommendation,

                    "minimum_order_qty":
                        line.minimum_order_qty,
                }
                for line in lines
            ],
        }

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


# =====================================================
# LIST PURCHASE REQUESTS
# =====================================================

@router.get("")
def list_purchase_requests(
    db: Session = Depends(get_db),
):
    headers = get_purchase_requests(
        db
    )

    results = []

    for header in headers:

        lines = get_purchase_request_lines(
            db,
            header.purchase_request_id,
        )

        results.append(
            {
                "purchase_request_id":
                    header.purchase_request_id,

                "request_number":
                    header.request_number,

                "status":
                    header.status,

                "supplier_id":
                    header.supplier_id,

                "requested_by_user_id":
                    header.requested_by_user_id,

                "notes":
                    header.notes,

                "created_at":
                    header.created_at,

                "lines": [
                    {
                        "purchase_request_line_id":
                            line.purchase_request_line_id,

                        "product_id":
                            line.product_id,

                        "location_id":
                            line.location_id,

                        "quantity":
                            line.quantity,

                        "unit_cost":
                            line.unit_cost,

                        "reorder_recommendation":
                            line.reorder_recommendation,

                        "minimum_order_qty":
                            line.minimum_order_qty,
                    }
                    for line in lines
                ],
            }
        )

    return results


# =====================================================
# SUBMIT
# =====================================================

@router.post(
    "/{purchase_request_id}/submit",
    response_model=(
        schemas.PurchaseRequestTransitionResponse
    ),
)
def submit_request(
    purchase_request_id: int,
    request: schemas.PurchaseRequestActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = submit_purchase_request(
            db=db,
            purchase_request_id=purchase_request_id,
            performed_by_user_id=current_user.user_id,
            comment=request.comment,
        )

        header = result["purchase_request"]
        approval = result["approval"]

        return {
            "purchase_request_id":
                header.purchase_request_id,

            "request_number":
                header.request_number,

            "status":
                header.status,

            "action":
                approval.action,

            "approval_id":
                approval.approval_id,

            "performed_by_user_id":
                approval.performed_by_user_id,

            "comment":
                approval.comment,
        }

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
# =====================================================
# APPROVE
# =====================================================

@router.post(
    "/{purchase_request_id}/approve",
    response_model=(
        schemas.PurchaseRequestTransitionResponse
    ),
)
def approve_request(
    purchase_request_id: int,
    request: schemas.PurchaseRequestActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = approve_purchase_request(
            db=db,
            purchase_request_id=purchase_request_id,
            performed_by_user_id=current_user.user_id,
            comment=request.comment,
        )

        header = result["purchase_request"]
        approval = result["approval"]

        return {
            "purchase_request_id":
                header.purchase_request_id,

            "request_number":
                header.request_number,

            "status":
                header.status,

            "action":
                approval.action,

            "approval_id":
                approval.approval_id,

            "performed_by_user_id":
                approval.performed_by_user_id,

            "comment":
                approval.comment,
        }

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

# =====================================================
# REJECT
# =====================================================

@router.post(
    "/{purchase_request_id}/reject",
    response_model=(
        schemas.PurchaseRequestTransitionResponse
    ),
)
def reject_request(
    purchase_request_id: int,
    request: schemas.PurchaseRequestActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = reject_purchase_request(
            db=db,
            purchase_request_id=purchase_request_id,
            performed_by_user_id=current_user.user_id,
            comment=request.comment,
        )

        header = result["purchase_request"]
        approval = result["approval"]

        return {
            "purchase_request_id":
                header.purchase_request_id,

            "request_number":
                header.request_number,

            "status":
                header.status,

            "action":
                approval.action,

            "approval_id":
                approval.approval_id,

            "performed_by_user_id":
                approval.performed_by_user_id,

            "comment":
                approval.comment,
        }

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


# =====================================================
# APPROVAL HISTORY
# =====================================================

@router.get(
    "/{purchase_request_id}/approval-history",
    response_model=list[
        schemas.PurchaseRequestApprovalRead
    ],
)
def approval_history(
    purchase_request_id: int,
    db: Session = Depends(get_db),
):
    try:
        return get_approval_history(
            db,
            purchase_request_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )