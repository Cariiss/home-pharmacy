from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user
from ..services import package_to_out
from .medicines import get_own_medicine

router = APIRouter(prefix="/packages", tags=["Упаковки"])


def get_own_package(package_id: int, user: models.User, db: Session) -> models.Package:
    package = db.get(models.Package, package_id)
    if package is None or package.medicine.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Упаковка не найдена")
    return package


@router.get("", response_model=list[schemas.PackageOut])
def list_packages(
    q: str | None = None,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(models.Package)
        .join(models.Medicine)
        .where(models.Medicine.user_id == user.id)
        .order_by(models.Package.expiry_date)
    )
    if q:
        stmt = stmt.where(models.Medicine.name.ilike(f"%{q}%"))
    threshold = user.settings.threshold_days
    result = [package_to_out(p, threshold) for p in db.scalars(stmt).all()]
    return result


@router.post("", response_model=schemas.PackageOut, status_code=status.HTTP_201_CREATED)
def create_package(data: schemas.PackageIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    get_own_medicine(data.medicine_id, user, db)
    package = models.Package(**data.model_dump())
    db.add(package)
    db.commit()
    db.refresh(package)
    return package_to_out(package, user.settings.threshold_days)


@router.get("/{package_id}", response_model=schemas.PackageOut)
def get_package(package_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return package_to_out(get_own_package(package_id, user, db), user.settings.threshold_days)


@router.put("/{package_id}", response_model=schemas.PackageOut)
def update_package(package_id: int, data: schemas.PackageUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    package = get_own_package(package_id, user, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(package, field, value)
    db.commit()
    db.refresh(package)
    return package_to_out(package, user.settings.threshold_days)


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package(package_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(get_own_package(package_id, user, db))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
