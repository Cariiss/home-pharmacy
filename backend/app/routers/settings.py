from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..security import get_current_user

router = APIRouter(prefix="/settings", tags=["Настройки уведомлений"])


@router.get("", response_model=schemas.SettingsOut)
def get_settings(user=Depends(get_current_user)):
    return user.settings


@router.put("", response_model=schemas.SettingsOut)
def update_settings(data: schemas.SettingsIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    user.settings.threshold_days = data.threshold_days
    user.settings.notifications_enabled = data.notifications_enabled
    db.commit()
    return user.settings
