import enum

from sqlalchemy import Enum, ForeignKey, Integer, JSON, String, Text as SAText
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.mixins import TimestampMixin
from app.db.session import Base


class BookingStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"
    completed = "completed"


class Booking(TimestampMixin, Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), index=True
    )
    landlord_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status"),
        default=BookingStatus.pending,
        nullable=False,
    )
    message: Mapped[str | None] = mapped_column(SAText)
    scheduled_date: Mapped[str | None] = mapped_column(String(32))

    deposit_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    service_fee: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deposit_status: Mapped[str] = mapped_column(String(20), default="unpaid")
    payment_transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tenant_profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    progress_steps: Mapped[list | None] = mapped_column(JSON, nullable=True)
    room_number: Mapped[str | None] = mapped_column(String(80), nullable=True)
    lease_start: Mapped[str | None] = mapped_column(String(32), nullable=True)
    lease_end: Mapped[str | None] = mapped_column(String(32), nullable=True)
    contract_status: Mapped[str] = mapped_column(String(32), default="not_ready")
    admin_note: Mapped[str | None] = mapped_column(SAText)

    tenant: Mapped["User"] = relationship(foreign_keys=[tenant_id])
    property: Mapped["Property"] = relationship()
    landlord: Mapped["User"] = relationship(foreign_keys=[landlord_id])
