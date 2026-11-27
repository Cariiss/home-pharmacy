"""Бизнес-логика: расчёт статуса срока годности."""
from datetime import date

from . import models, schemas


def like_pattern(query: str) -> str:
    """Шаблон для ilike: % и _ в запросе ищутся как обычные символы."""
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def expiry_status(expiry_date: date, threshold_days: int, today: date | None = None) -> tuple[int, str]:
    today = today or date.today()
    days_left = (expiry_date - today).days
    if days_left < 0:
        return days_left, "expired"
    if days_left <= threshold_days:
        return days_left, "expiring"
    return days_left, "ok"


def package_to_out(package: models.Package, threshold_days: int) -> schemas.PackageOut:
    days_left, status = expiry_status(package.expiry_date, threshold_days)
    return schemas.PackageOut(
        id=package.id,
        medicine_id=package.medicine_id,
        medicine_name=package.medicine.name,
        expiry_date=package.expiry_date,
        quantity=package.quantity,
        location=package.location,
        days_left=days_left,
        status=status,
    )
