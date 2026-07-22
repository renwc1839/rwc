from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db_session, require_admin
from app.models.booking import Booking
from app.models.property import Property
from app.models.user import User, UserRole
from app.schemas.user import UserRead
from app.services.audit_service import AuditService
from app.services.embedding_job_service import EmbeddingJobService
from app.services.property_service import PropertyService
from app.services.stats_service import StatsService
from app.services.user_service import UserService

router = APIRouter()


def mask_email(value: str | None) -> str | None:
    if not value or "@" not in value:
        return value
    name, domain = value.split("@", 1)
    return f"{name[:2] if len(name) > 1 else name[:1]}***@{domain}"


def mask_phone(value: str | None) -> str | None:
    if not value:
        return value
    if len(value) <= 4:
        return "***"
    return f"{value[:3]}****{value[-4:]}"


def role_label(role: UserRole | str) -> str:
    value = getattr(role, "value", role)
    labels = {
        "tenant": "租客",
        "landlord": "房源管理人员",
        "appointment_staff": "预约对接人员",
        "property_manager": "房源管理人员",
        "repair_worker": "维修工",
        "admin": "超级管理员",
    }
    return labels.get(str(value), str(value))


def enum_value(value) -> str:
    return getattr(value, "value", value)


def property_summary(prop: Property) -> dict:
    return {
        "id": prop.id,
        "title": prop.title,
        "address": prop.address,
        "district": prop.district,
        "price_monthly": float(prop.price_monthly),
        "status": enum_value(prop.status),
        "property_manager_id": prop.property_manager_id,
        "repair_worker_id": prop.repair_worker_id,
        "created_at": prop.created_at.isoformat(),
    }


def booking_summary(booking: Booking) -> dict:
    prop = booking.property
    return {
        "id": booking.id,
        "property_id": booking.property_id,
        "property_title": prop.title if prop else f"房源 #{booking.property_id}",
        "room_number": booking.room_number,
        "lease_start": booking.lease_start,
        "lease_end": booking.lease_end,
        "status": enum_value(booking.status),
        "contract_status": booking.contract_status,
        "deposit_status": booking.deposit_status,
        "scheduled_date": booking.scheduled_date,
        "created_at": booking.created_at.isoformat(),
    }


@router.get("/stats")
async def get_stats(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> dict:
    return await StatsService(session).get_stats()


@router.get("/logs")
async def list_audit_logs(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    action: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
) -> list[dict]:
    logs = await AuditService(session).list_logs(
        skip=skip, limit=limit, action=action, user_id=user_id,
    )
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


@router.get("/users", response_model=list[UserRead])
async def list_users(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    role: str | None = Query(default=None),
) -> list[UserRead]:
    user_role = None
    if role is not None:
        try:
            user_role = UserRole(role)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role filter",
            ) from exc
    return await UserService(session).list(skip=skip, limit=limit, role=user_role)


@router.get("/users/{user_id}/detail")
async def get_user_detail(
    user_id: int,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> dict:
    user = await UserService(session).get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    tenant_bookings = list(
        (
            await session.scalars(
                select(Booking)
                .options(selectinload(Booking.property))
                .where(Booking.tenant_id == user_id)
                .order_by(Booking.created_at.desc())
                .limit(20)
            )
        ).all()
    )
    handled_bookings = list(
        (
            await session.scalars(
                select(Booking)
                .options(selectinload(Booking.property))
                .where(Booking.landlord_id == user_id)
                .order_by(Booking.created_at.desc())
                .limit(20)
            )
        ).all()
    )
    managed_properties = list(
        (
            await session.scalars(
                select(Property)
                .where(
                    or_(
                        Property.property_manager_id == user_id,
                        Property.repair_worker_id == user_id,
                        (Property.property_manager_id.is_(None) & (Property.landlord_id == user_id)),
                    )
                )
                .order_by(Property.created_at.desc())
                .limit(20)
            )
        ).all()
    )

    from app.api.v1.routes.admin_portal import load_state

    state = load_state()
    username = user.username
    appointments = [
        item for item in state.get("appointments", [])
        if item.get("assignee") == username or item.get("customer") == username
    ][:20]
    repairs = [
        item for item in state.get("repairs", [])
        if item.get("assignee") == username or item.get("tenant") == username or item.get("owner") == username
    ][:20]
    work_orders = [
        item for item in state.get("workOrders", [])
        if item.get("owner") == username or item.get("customer") == username or item.get("related") in {r.get("id") for r in repairs}
    ][:20]
    messages = [
        item for item in state.get("messages", [])
        if item.get("assignee") == username or item.get("customer") == username or item.get("target") == username
    ][:20]

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": mask_email(user.email),
            "phone": mask_phone(user.phone),
            "role": enum_value(user.role),
            "role_label": role_label(user.role),
            "status": enum_value(user.status),
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        },
        "tenant_bookings": [booking_summary(item) for item in tenant_bookings],
        "handled_bookings": [booking_summary(item) for item in handled_bookings],
        "managed_properties": [property_summary(item) for item in managed_properties],
        "appointments": appointments,
        "repairs": repairs,
        "work_orders": work_orders,
        "messages": messages,
    }


@router.patch("/properties/{property_id}/status")
async def moderate_property(
    property_id: int,
    new_status: str = Query(...),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin),
) -> dict:
    valid_statuses = {"available", "rented", "maintenance", "offline"}
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )

    from app.schemas.property import PropertyUpdate

    property_obj = await PropertyService(session).update(
        property_id, PropertyUpdate(status=new_status)
    )
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    await AuditService(session).create_log(
        user_id=current_user.id,
        action="property_moderate",
        resource_type="property",
        resource_id=property_id,
        details={"new_status": new_status},
    )
    return {"detail": f"Property {property_id} status set to {new_status}"}


@router.patch("/users/{user_id}/role", response_model=UserRead)
async def update_user_role(
    user_id: int,
    new_role: str = Query(...),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin),
) -> UserRead:
    if new_role == "landlord":
        new_role = "property_manager"
    if new_role not in {"tenant", "appointment_staff", "property_manager", "repair_worker", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be: tenant, appointment_staff, property_manager, repair_worker, or admin",
        )

    from app.schemas.user import UserUpdate

    user = await UserService(session).update(user_id, UserUpdate(role=UserRole(new_role)))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await AuditService(session).create_log(
        user_id=current_user.id,
        action="user_role_change",
        resource_type="user",
        resource_id=user_id,
        details={"new_role": new_role},
    )
    return user


@router.get("/embeddings/stats")
async def get_embedding_stats(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> dict:
    return await EmbeddingJobService(session).get_stats()


@router.post("/embeddings/reindex")
async def trigger_reindex(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin),
    property_id: int | None = Query(default=None),
) -> dict:
    result = await EmbeddingJobService(session).trigger_reindex(property_id)
    await AuditService(session).create_log(
        user_id=current_user.id,
        action="embedding_reindex",
        details={"property_id": property_id},
    )
    return result
