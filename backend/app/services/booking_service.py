from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus
from app.models.notification import NotificationType
from app.models.property import Property
from app.schemas.booking import BookingCreate
from app.services.notification_service import NotificationService


ORDER_PROGRESS_LABELS = [
    ("submitted", "提交申请"),
    ("profile_review", "资料审核"),
    ("tenant_confirmed", "租客确认"),
    ("landlord_confirmed", "管理员确认"),
    ("contract_ready", "合同签署"),
    ("deposit_paid", "支付定金"),
    ("completed", "完成入住"),
]


def build_order_progress(active_key: str = "submitted") -> list[dict]:
    keys = [key for key, _ in ORDER_PROGRESS_LABELS]
    try:
        active_index = keys.index(active_key)
    except ValueError:
        active_index = 0
    return [
        {
            "key": key,
            "label": label,
            "done": index <= active_index,
            "active": index == active_index,
        }
        for index, (key, label) in enumerate(ORDER_PROGRESS_LABELS)
    ]


class BookingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_booking(
        self,
        tenant_id: int,
        property_id: int,
        landlord_id: int,
        booking_in: BookingCreate,
    ) -> Booking:

        existing = await self.session.execute(
            select(Booking).where(
                and_(
                    Booking.tenant_id == tenant_id,
                    Booking.property_id == property_id,
                    Booking.status == BookingStatus.pending,
                )
            )
        )
        if existing.scalars().first():
            raise ValueError("You already have a pending booking for this property")

        # Fetch property for deposit/fee calculation
        property_obj = await self.session.get(Property, property_id)
        deposit_amount = property_obj.deposit_amount if property_obj else 1000
        service_fee_rate = property_obj.service_fee_rate if property_obj else 0.10
        service_fee = int(float(property_obj.price_monthly) * service_fee_rate) if property_obj else 0

        booking = Booking(
            tenant_id=tenant_id,
            property_id=property_id,
            landlord_id=landlord_id,
            message=booking_in.message,
            scheduled_date=booking_in.scheduled_date,
            deposit_amount=deposit_amount,
            service_fee=service_fee,
            deposit_status="unpaid",
            tenant_profile=booking_in.tenant_profile or {},
            progress_steps=build_order_progress("submitted"),
            room_number=booking_in.room_number,
            lease_start=booking_in.lease_start,
            lease_end=booking_in.lease_end,
            contract_status="not_ready",
        )
        self.session.add(booking)
        await self.session.commit()
        await self.session.refresh(booking)

        # Unified notification: DB + push channels (WeChat + SMS + Email) for landlord
        notification_service = NotificationService(self.session)
        await notification_service.create_notification(
            user_id=landlord_id,
            type=NotificationType.booking_created,
            title="New booking request",
            content=f"A tenant has requested to view your property #{property_id}",
            channels=["wechat", "sms", "email"],
        )

        # Booking confirmation for tenant via WeChat template message (existing flow)
        try:
            from app.tasks.notification_tasks import send_booking_confirm_message

            booking_info = {
                "property_title": property_obj.title if property_obj else str(property_id),
                "booking_time": booking_in.scheduled_date or "TBD",
                "landlord_phone": "",
                "remark": "Please pay deposit to confirm booking.",
            }
            send_booking_confirm_message.delay(tenant_id, booking_info)
        except Exception:
            pass

        return booking

    async def update_status(self, booking_id: int, status: BookingStatus) -> Booking | None:
        booking = await self.session.get(Booking, booking_id)
        if not booking:
            return None

        booking.status = status
        await self.session.commit()
        await self.session.refresh(booking)

        notification_service = NotificationService(self.session)
        nt_map = {
            BookingStatus.approved: (
                NotificationType.booking_approved,
                "Booking approved",
                "Your booking has been approved",
                booking.tenant_id,
                ["wechat", "sms", "email"],
            ),
            BookingStatus.rejected: (
                NotificationType.booking_rejected,
                "Booking rejected",
                "Your booking has been rejected",
                booking.tenant_id,
                ["wechat", "sms", "email"],
            ),
            BookingStatus.cancelled: (
                NotificationType.booking_cancelled,
                "Booking cancelled",
                "A booking has been cancelled",
                booking.landlord_id,
                ["wechat", "sms", "email"],
            ),
            BookingStatus.completed: (
                NotificationType.booking_completed,
                "Booking completed",
                "The booking process has been completed",
                booking.tenant_id,
                ["wechat", "email"],
            ),
        }
        if status in nt_map:
            nt_type, title, content, notify_user, channels = nt_map[status]

            await notification_service.create_notification(
                user_id=notify_user,
                type=nt_type,
                title=title,
                content=content,
                channels=channels,
            )

            # For completed: also notify the landlord
            if status == BookingStatus.completed:
                await notification_service.create_notification(
                    user_id=booking.landlord_id,
                    type=NotificationType.booking_completed,
                    title="Booking completed",
                    content=f"Booking #{booking.id} has been completed",
                    channels=["wechat", "email"],
                )

        return booking

    async def update_progress(self, booking_id: int, update_in) -> Booking | None:
        booking = await self.session.get(Booking, booking_id)
        if not booking:
            return None

        if update_in.status is not None:
            booking.status = update_in.status
        if update_in.deposit_status is not None:
            booking.deposit_status = update_in.deposit_status
        if update_in.payment_transaction_id is not None:
            booking.payment_transaction_id = update_in.payment_transaction_id
        if update_in.progress_key:
            booking.progress_steps = build_order_progress(update_in.progress_key)
            if update_in.progress_key in {"profile_review", "tenant_confirmed", "landlord_confirmed", "contract_ready"}:
                booking.status = BookingStatus.approved
            if update_in.progress_key == "completed":
                booking.status = BookingStatus.completed
            if update_in.progress_key in {"contract_ready", "deposit_paid", "completed"}:
                booking.contract_status = "pending_signature" if update_in.progress_key == "contract_ready" else "signed"
        if update_in.room_number is not None:
            booking.room_number = update_in.room_number
        if update_in.lease_start is not None:
            booking.lease_start = update_in.lease_start
        if update_in.lease_end is not None:
            booking.lease_end = update_in.lease_end
        if update_in.contract_status is not None:
            booking.contract_status = update_in.contract_status
        if update_in.admin_note is not None:
            booking.admin_note = update_in.admin_note

        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def list_by_tenant(self, tenant_id: int) -> list[Booking]:
        stmt = (
            select(Booking)
            .where(Booking.tenant_id == tenant_id)
            .order_by(Booking.created_at.desc())
        )
        result = await self.session.scalars(stmt)
        return list(result)

    async def list_by_landlord(self, landlord_id: int) -> list[Booking]:
        stmt = (
            select(Booking)
            .where(Booking.landlord_id == landlord_id)
            .order_by(Booking.created_at.desc())
        )
        result = await self.session.scalars(stmt)
        return list(result)

    async def list_all(self) -> list[Booking]:
        stmt = select(Booking).order_by(Booking.created_at.desc())
        result = await self.session.scalars(stmt)
        return list(result)

    async def get(self, booking_id: int) -> Booking | None:
        return await self.session.get(Booking, booking_id)
