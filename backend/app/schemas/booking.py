from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.booking import BookingStatus


class BookingCreate(BaseModel):
    property_id: int
    message: str | None = Field(default=None, max_length=2000)
    scheduled_date: str | None = Field(default=None, max_length=32)
    tenant_profile: dict[str, Any] | None = None
    room_number: str | None = Field(default=None, max_length=80)
    lease_start: str | None = Field(default=None, max_length=32)
    lease_end: str | None = Field(default=None, max_length=32)


class BookingUpdate(BaseModel):
    status: BookingStatus | None = None
    deposit_status: str | None = None
    payment_transaction_id: str | None = None
    progress_key: str | None = None
    room_number: str | None = Field(default=None, max_length=80)
    lease_start: str | None = Field(default=None, max_length=32)
    lease_end: str | None = Field(default=None, max_length=32)
    contract_status: str | None = Field(default=None, max_length=32)
    admin_note: str | None = Field(default=None, max_length=1000)


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    property_id: int
    landlord_id: int
    status: BookingStatus
    message: str | None
    scheduled_date: str | None
    deposit_amount: int | None = None
    service_fee: int | None = None
    deposit_status: str | None = None
    payment_transaction_id: str | None = None
    tenant_profile: dict[str, Any] | None = None
    progress_steps: list[dict[str, Any]] | None = None
    room_number: str | None = None
    lease_start: str | None = None
    lease_end: str | None = None
    contract_status: str | None = None
    admin_note: str | None = None
    created_at: datetime
    updated_at: datetime
