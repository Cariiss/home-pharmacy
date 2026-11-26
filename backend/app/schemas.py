from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


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


class MedicineOut(MedicineIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PackageIn(BaseModel):
    medicine_id: int
    expiry_date: date
    quantity: int = Field(gt=0)
    location: str | None = Field(default=None, max_length=100)


class PackageUpdate(BaseModel):
    expiry_date: date | None = None
    quantity: int | None = Field(default=None, gt=0)
    location: str | None = Field(default=None, max_length=100)



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
