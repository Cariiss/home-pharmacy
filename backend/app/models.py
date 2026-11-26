from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    medicines: Mapped[list["Medicine"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    settings: Mapped["ReminderSettings"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    form: Mapped[str | None] = mapped_column(String(100))
    dosage: Mapped[str | None] = mapped_column(String(100))

    owner: Mapped[User] = relationship(back_populates="medicines")
    packages: Mapped[list["Package"]] = relationship(back_populates="medicine")


class Package(Base):
    __tablename__ = "packages"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_packages_quantity_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    medicine_id: Mapped[int] = mapped_column(ForeignKey("medicines.id", ondelete="RESTRICT"), index=True)
    expiry_date: Mapped[date] = mapped_column(Date)
    quantity: Mapped[int] = mapped_column(Integer)
    location: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    medicine: Mapped[Medicine] = relationship(back_populates="packages")


class ReminderSettings(Base):
    __tablename__ = "reminder_settings"
    __table_args__ = (CheckConstraint("threshold_days IN (7, 14, 30)", name="ck_threshold_days"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    threshold_days: Mapped[int] = mapped_column(Integer, default=30)
    notifications_enabled: Mapped[bool] = mapped_column(default=True)

    user: Mapped[User] = relationship(back_populates="settings")
