from fastapi import APIRouter, Depends

from app import clock
from app.models import Owner
from app.routers.auth import current_owner
from app.schemas import DashboardOut

# Every route here requires the owner session.
router = APIRouter(prefix="/owner", tags=["owner"], dependencies=[Depends(current_owner)])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(owner: Owner = Depends(current_owner)):
    # Key numbers and charts arrive in slice 6.
    return DashboardOut(date=clock.now().date().isoformat(), owner_name=owner.full_name)
