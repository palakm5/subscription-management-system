from typing import Dict, Any, Optional
from datetime import date
from fastapi import APIRouter, Depends

from app.core.deps import require_role
from app.models.users import User
from app.services.billing_service import BillingService

router = APIRouter(prefix="/billing", tags=["billing"])

@router.post("/run")
async def run_billing(
    current_user: User = Depends(require_role("admin"))
):
    result = await BillingService.run_billing_job()
    return result.to_dict()
