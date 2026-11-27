from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user
from ..services import like_pattern

router = APIRouter(prefix="/medicines", tags=["Справочник лекарств"])


def get_own_medicine(medicine_id: int, user: models.User, db: Session) -> models.Medicine:
    medicine = db.get(models.Medicine, medicine_id)
    if medicine is None or medicine.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Лекарство не найдено")
    return medicine


@router.get("", response_model=list[schemas.MedicineOut])
def list_medicines(q: str | None = None, user=Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(models.Medicine).where(models.Medicine.user_id == user.id)
    if q:
        stmt = stmt.where(models.Medicine.name.ilike(like_pattern(q), escape="\\"))
    return db.scalars(stmt.order_by(models.Medicine.name, models.Medicine.id)).all()


@router.post("", response_model=schemas.MedicineOut, status_code=status.HTTP_201_CREATED)
def create_medicine(data: schemas.MedicineIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    medicine = models.Medicine(user_id=user.id, **data.model_dump())
    db.add(medicine)
    db.commit()
    db.refresh(medicine)
    return medicine


@router.get("/{medicine_id}", response_model=schemas.MedicineOut)
def get_medicine(medicine_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return get_own_medicine(medicine_id, user, db)


@router.put("/{medicine_id}", response_model=schemas.MedicineOut)
def update_medicine(medicine_id: int, data: schemas.MedicineIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    medicine = get_own_medicine(medicine_id, user, db)
    for field, value in data.model_dump().items():
        setattr(medicine, field, value)
    db.commit()
    db.refresh(medicine)
    return medicine


@router.delete("/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medicine(medicine_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    medicine = get_own_medicine(medicine_id, user, db)
    if medicine.packages:
        raise HTTPException(status.HTTP_409_CONFLICT, "Нельзя удалить лекарство, пока у него есть упаковки")
    db.delete(medicine)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
