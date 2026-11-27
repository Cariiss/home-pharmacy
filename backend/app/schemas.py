from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        # bcrypt учитывает только первые 72 байта; русская буква занимает 2 байта
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Пароль слишком длинный (не больше 72 байт)")
        return value


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr


class MedicineIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    form: str | None = Field(default=None, max_length=100)
    dosage: str | None = Field(default=None, max_length=100)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Название не может быть пустым")
        return value

    @field_validator("form", "dosage")
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class MedicineOut(MedicineIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PackageIn(BaseModel):
    medicine_id: int
    expiry_date: date
    quantity: int = Field(gt=0, le=10000)
    location: str | None = Field(default=None, max_length=100)


class PackageUpdate(BaseModel):
    expiry_date: date | None = None
    quantity: int | None = Field(default=None, gt=0, le=10000)
    location: str | None = Field(default=None, max_length=100)

    @field_validator("expiry_date", "quantity")
    @classmethod
    def required_not_null(cls, value):
        if value is None:
            raise ValueError("Поле нельзя очистить")
        return value


ExpiryStatus = Literal["ok", "expiring", "expired"]


class PackageOut(BaseModel):
    id: int
    medicine_id: int
    medicine_name: str
    expiry_date: date
    quantity: int
    location: str | None
    days_left: int
    status: ExpiryStatus


class SettingsIn(BaseModel):
    threshold_days: Literal[7, 14, 30]
    notifications_enabled: bool = True


class SettingsOut(SettingsIn):
    model_config = ConfigDict(from_attributes=True)
