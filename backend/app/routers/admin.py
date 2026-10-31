from typing import List
from fastapi import APIRouter, Depends, status

from app.core.deps import require_role
from app.models.users import User, UserRole
from app.schemas.auth import CreateStaffRequest, UserResponse
from app.services.auth_service import AuthService
from app.routers.auth import to_user_response

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/staff", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    req: CreateStaffRequest,
    current_admin: User = Depends(require_role("admin"))
):
    staff_user = await AuthService.create_staff(req)
    return to_user_response(staff_user)

@router.get("/staff", response_model=List[UserResponse])
async def list_staff(
    current_admin: User = Depends(require_role("admin"))
):
    staff_members = await User.find(User.role == UserRole.STAFF).to_list()
    return [to_user_response(u) for u in staff_members]
