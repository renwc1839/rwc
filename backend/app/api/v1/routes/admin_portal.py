from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, require_admin, require_workspace_user
from app.models.user import User

router = APIRouter()

DATA_FILE = Path(__file__).resolve().parents[4] / "data" / "admin_portal_state.json"

REPAIR_STEP_LABELS = ["待处理", "已派单", "维修中", "已完成"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def repair_progress_steps(status_value: str) -> list[dict[str, Any]]:
    try:
        active_index = REPAIR_STEP_LABELS.index(status_value)
    except ValueError:
        active_index = 0
    return [
        {
            "key": label,
            "label": label,
            "done": index <= active_index,
            "active": index == active_index,
        }
        for index, label in enumerate(REPAIR_STEP_LABELS)
    ]


def default_permission_catalog() -> list[dict[str, Any]]:
    return [
        {"key": "admin.all", "name": "最高管理员权限", "group": "系统权限", "desc": "角色、人员、工单、房源和审计全部可管"},
        {"key": "admin.role.assign", "name": "分配后台角色", "group": "权限管理", "desc": "给人员设置角色模板"},
        {"key": "admin.feature.toggle", "name": "单独功能开关", "group": "权限管理", "desc": "按账号勾选或关闭单项功能"},
        {"key": "schedule.view", "name": "查看排班日期", "group": "人员排班", "desc": "查看人员日期、班次和在岗状态"},
        {"key": "schedule.conflict", "name": "查看人员冲突", "group": "人员排班", "desc": "查看撞单、跨城和超负载提醒"},
        {"key": "workorder.all", "name": "总工单查看", "group": "工单管理", "desc": "查看全部投诉、维修、带看反馈工单"},
        {"key": "repair.assign", "name": "维修联系分配", "group": "预约对接", "desc": "分配维修联系人和处理进度"},
        {"key": "appointment.list", "name": "客户预约列表", "group": "预约对接", "desc": "查看客户预约并推进确认"},
        {"key": "feedback.work", "name": "工作反馈界面", "group": "预约对接", "desc": "填写带看、维修、客户沟通反馈"},
        {"key": "property.publish", "name": "发布房源", "group": "房源管理", "desc": "进入房源发布流程"},
        {"key": "property.manage", "name": "房源信息管理", "group": "房源管理", "desc": "维护房源状态、图片和运营信息"},
        {"key": "repair.progress", "name": "维修项目进度监督", "group": "工单管理", "desc": "监督维修项目派单、维修中、完成情况"},
        {"key": "repair.work", "name": "维修工处理界面", "group": "维修执行", "desc": "查看分配给自己的维修项目并推进节点进度"},
        {"key": "audit.logs", "name": "操作日志审计", "group": "系统权限", "desc": "查看不可删除的后台操作记录"},
    ]


def all_permission_keys() -> list[str]:
    return [item["key"] for item in default_permission_catalog()]


def default_role_profiles() -> list[dict[str, Any]]:
    return [
        {
            "key": "super_admin",
            "name": "超级管理员",
            "desc": "最高权限，负责角色、排班、人员冲突、总工单和维修监督。",
            "permissions": all_permission_keys(),
            "locked": True,
        },
        {
            "key": "appointment_staff",
            "name": "预约对接人员",
            "desc": "类似客服，负责客户预约、维修联系分配和工作反馈。",
            "permissions": ["repair.assign", "appointment.list", "feedback.work", "workorder.all", "repair.progress"],
            "locked": False,
        },
        {
            "key": "property_manager",
            "name": "房源管理人员",
            "desc": "负责房源发布、房源信息维护和房源状态运营。",
            "permissions": ["property.publish", "property.manage"],
            "locked": False,
        },
        {
            "key": "repair_worker",
            "name": "维修工",
            "desc": "负责接收管理员分配的维修项目，按节点更新到场、维修中、完成和凭证记录。",
            "permissions": ["repair.work", "repair.progress"],
            "locked": False,
        },
    ]


def default_accounts() -> list[dict[str, Any]]:
    return [
        {
            "id": "A-001",
            "name": "superadmin",
            "login": "superadmin",
            "trialPassword": "Admin@123456",
            "roleKey": "super_admin",
            "role": "超级管理员",
            "phone": "138****0000",
            "twoFactor": True,
            "status": "启用",
            "permissions": all_permission_keys(),
        },
        {
            "id": "A-002",
            "name": "appointment_staff",
            "login": "appointment_staff",
            "trialPassword": "Staff@123456",
            "roleKey": "appointment_staff",
            "role": "预约对接人员",
            "phone": "139****1201",
            "twoFactor": True,
            "status": "启用",
            "permissions": ["repair.assign", "appointment.list", "feedback.work", "workorder.all", "repair.progress"],
        },
        {
            "id": "A-003",
            "name": "property_manager",
            "login": "property_manager",
            "trialPassword": "Property@123456",
            "roleKey": "property_manager",
            "role": "房源管理人员",
            "phone": "137****3208",
            "twoFactor": True,
            "status": "启用",
            "permissions": ["property.publish", "property.manage"],
        },
        {
            "id": "A-004",
            "name": "repair_worker",
            "login": "repair_worker",
            "trialPassword": "Repair@123456",
            "roleKey": "repair_worker",
            "role": "维修工",
            "phone": "136****4500",
            "twoFactor": True,
            "status": "启用",
            "permissions": ["repair.work", "repair.progress"],
        },
    ]


def default_schedules() -> list[dict[str, Any]]:
    return [
        {"id": "SCH-001", "date": "2026-07-13", "name": "Anna", "role": "预约对接人员", "city": "伦敦", "shift": "09:00-18:00", "workOrders": 14, "conflict": "预约撞单 2 笔", "status": "冲突"},
        {"id": "SCH-002", "date": "2026-07-13", "name": "Mike", "role": "预约对接人员", "city": "纽约", "shift": "10:00-19:00", "workOrders": 7, "conflict": "无", "status": "正常"},
        {"id": "SCH-003", "date": "2026-07-13", "name": "Sofia", "role": "房源管理人员", "city": "悉尼", "shift": "休息日", "workOrders": 0, "conflict": "休息日被分配带看", "status": "冲突"},
    ]


def default_work_feedbacks() -> list[dict[str, Any]]:
    return [
        {"id": "FB-001", "staff": "Anna", "related": "BK-10291", "type": "客户预约", "content": "客户希望改到明天下午带看，等待二次确认。", "createdAt": "2026-07-13 10:20", "status": "待跟进"},
        {"id": "FB-002", "staff": "Mike", "related": "RP-5002", "type": "维修联系", "content": "已联系维修方，预计今日 17:00 前上门。", "createdAt": "2026-07-13 11:05", "status": "处理中"},
    ]


def merge_default_rows(state: dict[str, Any], key: str, id_key: str = "id") -> bool:
    defaults = seed_state()[key]
    rows = state.setdefault(key, [])
    existing_ids = {row.get(id_key) for row in rows}
    changed = False
    for item in defaults:
        if item.get(id_key) not in existing_ids:
            rows.append(item)
            changed = True
    return changed


def role_name_by_key(role_key: str) -> str:
    for role in default_role_profiles():
        if role["key"] == role_key:
            return role["name"]
    return role_key


def default_permissions_for_role(role_key: str) -> list[str]:
    for role in default_role_profiles():
        if role["key"] == role_key:
            return list(role["permissions"])
    return []


def seed_state() -> dict[str, Any]:
    timestamp = now()
    return {
        "appointments": [
            {
                "id": "BK-10291",
                "customer": "李同学",
                "phone": "138****2001",
                "property": "伦敦一区学生公寓 A-1208",
                "time": "2026-07-07 14:00",
                "city": "伦敦",
                "assignee": "Anna",
                "status": "待分配",
                "priority": "普通",
                "created": timestamp,
            },
            {
                "id": "BK-10292",
                "customer": "王同学",
                "phone": "186****1102",
                "property": "纽约曼哈顿 Studio",
                "time": "2026-07-07 16:30",
                "city": "纽约",
                "assignee": "Mike",
                "status": "待确认",
                "priority": "重要",
                "created": timestamp,
            },
            {
                "id": "BK-10293",
                "customer": "Chen",
                "phone": "+44 **** 8821",
                "property": "悉尼 CBD 两室",
                "time": "2026-07-08 11:00",
                "city": "悉尼",
                "assignee": "Sofia",
                "status": "已确认",
                "priority": "普通",
                "created": timestamp,
            },
        ],
        "properties": [
            {
                "id": "P-1001",
                "title": "伦敦一区学生公寓 A-1208",
                "city": "伦敦",
                "landlord": "UK Living",
                "status": "已预约",
                "lockedUntil": "2026-07-08 14:00",
                "conflicts": 2,
            },
            {
                "id": "P-1002",
                "title": "纽约曼哈顿 Studio",
                "city": "纽约",
                "landlord": "NY Homes",
                "status": "可租",
                "lockedUntil": "-",
                "conflicts": 0,
            },
            {
                "id": "P-1003",
                "title": "悉尼 CBD 两室",
                "city": "悉尼",
                "landlord": "AU Stay",
                "status": "已签约",
                "lockedUntil": "-",
                "conflicts": 0,
            },
        ],
        "staff": [
            {"id": "S-001", "name": "Anna", "city": "伦敦", "online": True, "workTime": "09:00-18:00", "load": 88, "pending": 14, "status": "在岗"},
            {"id": "S-002", "name": "Mike", "city": "纽约", "online": True, "workTime": "10:00-19:00", "load": 46, "pending": 7, "status": "在岗"},
            {"id": "S-003", "name": "Sofia", "city": "悉尼", "online": False, "workTime": "休息日", "load": 0, "pending": 0, "status": "休息"},
        ],
        "exceptions": [
            {"id": "EX-001", "type": "超时未确认", "target": "预约单 BK-10291", "owner": "Anna", "elapsed": "2h 35m", "level": "重要", "status": "待处理"},
            {"id": "EX-002", "type": "客户投诉未处理", "target": "投诉 CP-0082", "owner": "客服组", "elapsed": "9h 20m", "level": "紧急", "status": "待处理"},
        ],
        "complaints": [
            {
                "id": "CP-0082",
                "category": "服务问题",
                "title": "带看顾问迟到且未提前说明",
                "description": "预约 10:00 带看，顾问迟到 35 分钟，客户希望平台介入处理。",
                "complainantName": "王同学",
                "contact": "186****1102",
                "city": "纽约",
                "property": "纽约曼哈顿 Studio",
                "status": "待处理",
                "priority": "重要",
                "createdAt": timestamp,
                "result": "",
            }
        ],
        "workOrders": [
            {
                "id": "WO-2101",
                "type": "投诉核实",
                "title": "核实 CP-0082 顾问迟到情况",
                "owner": "客服组",
                "related": "CP-0082",
                "deadline": "今日 18:00",
                "priority": "重要",
                "status": "待处理",
                "result": "",
            },
            {
                "id": "WO-2102",
                "type": "带看反馈",
                "title": "补录 BK-10293 带看结果",
                "owner": "Sofia",
                "related": "BK-10293",
                "deadline": "今日 20:00",
                "priority": "一般",
                "status": "处理中",
                "result": "",
            },
            {
                "id": "WO-5002",
                "type": "维修报修",
                "title": "厨房水槽漏水",
                "owner": "维修组",
                "related": "RP-5002",
                "deadline": "48 小时内",
                "priority": "重要",
                "status": "已派单",
                "result": "",
            },
        ],
        "repairs": [
            {
                "id": "RP-5001",
                "property": "朝阳区阳光花园 3-1502",
                "tenant": "刘先生",
                "category": "家电",
                "desc": "主卧空调不制冷，需维修",
                "date": "2026-06-27",
                "status": "待处理",
                "owner": "维修组",
                "assignee": "",
                "progressSteps": repair_progress_steps("待处理"),
                "reason": "",
                "materials": "",
                "evidenceImages": [],
                "updateLogs": [],
                "result": "",
            },
            {
                "id": "RP-5002",
                "property": "海淀区融科A座",
                "tenant": "李明",
                "category": "水电",
                "desc": "厨房水槽漏水",
                "date": "2026-06-25",
                "status": "已派单",
                "owner": "维修组",
                "assignee": "repair_worker",
                "progressSteps": repair_progress_steps("已派单"),
                "reason": "",
                "materials": "",
                "evidenceImages": [],
                "updateLogs": [],
                "result": "",
            },
            {
                "id": "RP-5003",
                "property": "西城区学区房",
                "tenant": "王芳",
                "category": "家电",
                "desc": "热水器无法正常加热",
                "date": "2026-06-22",
                "status": "维修中",
                "owner": "维修组",
                "assignee": "repair_worker",
                "progressSteps": repair_progress_steps("维修中"),
                "reason": "",
                "materials": "",
                "evidenceImages": [],
                "updateLogs": [],
                "result": "",
            },
        ],
        "messages": [
            {
                "id": "MSG-7001",
                "channel": "投诉",
                "sender": "王同学",
                "target": "客服组",
                "summary": "带看顾问迟到且未提前说明",
                "related": "CP-0082",
                "createdAt": timestamp,
                "status": "未读",
            },
            {
                "id": "MSG-7002",
                "channel": "预约",
                "sender": "系统",
                "target": "Anna",
                "summary": "BK-10291 超过 2 小时未确认",
                "related": "BK-10291",
                "createdAt": timestamp,
                "status": "未读",
            },
        ],
        "financeItems": [
            {
                "id": "FIN-3301",
                "type": "押金退款",
                "customer": "李同学",
                "property": "伦敦一区学生公寓 A-1208",
                "amount": "£1,200",
                "evidence": "退租确认单、房屋照片",
                "owner": "财务组",
                "status": "待审核",
                "result": "",
            },
            {
                "id": "FIN-3302",
                "type": "费用扣款",
                "customer": "王同学",
                "property": "纽约曼哈顿 Studio",
                "amount": "$80",
                "evidence": "清洁费用凭证",
                "owner": "财务组",
                "status": "待处理",
                "result": "",
            },
        ],
        "warnings": [
            {"id": "W-001", "type": "业务异常", "content": "多伦多预约量较 7 日均值下降 38%", "level": "重要", "created": timestamp, "status": "待处理"},
            {"id": "W-002", "type": "房源异常", "content": "伦敦一区 A-1208 出现多笔冲突预约", "level": "紧急", "created": timestamp, "status": "待处理"},
        ],
        "rules": {
            "booking": {"advanceHours": 4, "maxActive": 3, "lockHours": 24, "cancelFee": True},
            "deposit": {"ratio": "押一付一", "refundDays": 3, "deductions": ["清洁费", "维修费"]},
            "ai": {"price": 80, "distance": 70, "room": 65, "area": 55, "facility": 60, "score": 75, "resultCount": 10, "coldStart": "hot-city"},
            "penalty": {"tenantNoShow": "第 1 次警告，第 2 次扣 10% 押金，第 3 次封号 7 天", "fakeProperty": "第 1 次下架整改，第 2 次罚款，第 3 次终止合作", "complaintLimit": 3, "levels": ["一般", "较重", "严重"]},
            "notification": {"scene": "new-booking", "channels": ["短信", "站内信"], "targets": ["客户", "对接人"], "template": "您好，您有新的预约：{booking_time}，房源：{property_title}。"},
        },
        "ruleChangeRequests": [],
        "permissionCatalog": default_permission_catalog(),
        "roleProfiles": default_role_profiles(),
        "schedules": default_schedules(),
        "workFeedbacks": default_work_feedbacks(),
        "reports": [],
        "exportRequests": [],
        "actionHistory": [],
        "chatThreads": [],
        "chatReadReceipts": {},
        "accounts": default_accounts(),
        "settings": {"platformName": "AI 全球公寓租赁", "servicePhone": "+86 400-888-0000", "cities": ["伦敦", "纽约", "悉尼"]},
        "logs": [
            {"operator": "system", "time": timestamp, "type": "系统初始化", "target": "Admin Portal", "content": "创建第一版可用数据", "ip": "127.0.0.1"}
        ],
    }


def load_state() -> dict[str, Any]:
    if not DATA_FILE.exists():
        state = seed_state()
        save_state(state)
        return state
    state = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    defaults = seed_state()
    changed = False
    for key in (
        "workOrders",
        "repairs",
        "messages",
        "financeItems",
        "permissionCatalog",
        "roleProfiles",
        "schedules",
        "workFeedbacks",
        "reports",
        "exportRequests",
        "actionHistory",
        "chatThreads",
        "chatReadReceipts",
        "accounts",
    ):
        if key not in state:
            state[key] = defaults[key]
            changed = True
    for key in ("permissionCatalog", "roleProfiles", "schedules", "workFeedbacks", "accounts"):
        if merge_default_rows(state, key):
            changed = True
    accounts = state.setdefault("accounts", [])
    for default_account in default_accounts():
        account = next((item for item in accounts if item.get("id") == default_account["id"]), None)
        if account is None:
            accounts.append(default_account)
            changed = True
            continue
        if not account.get("login") or account.get("name") in {"ops_london"}:
            account.update(default_account)
            changed = True
    valid_permissions = set(all_permission_keys())
    role_permission_map = {role["key"]: list(role["permissions"]) for role in state.get("roleProfiles", [])}
    for account in state.get("accounts", []):
        role_key = account.get("roleKey")
        if not role_key:
            role_key = "super_admin" if account.get("name") == "superadmin" else "appointment_staff"
            account["roleKey"] = role_key
            changed = True
        role_name = role_name_by_key(role_key)
        if account.get("role") != role_name:
            account["role"] = role_name
            changed = True
        if account.get("id") == "A-001":
            account["roleKey"] = "super_admin"
            account["role"] = "超级管理员"
            account["permissions"] = all_permission_keys()
            account["status"] = "启用"
            account.setdefault("login", "superadmin")
            account.setdefault("trialPassword", "Admin@123456")
            changed = True
            continue
        if "permissions" not in account:
            account["permissions"] = role_permission_map.get(role_key, default_permissions_for_role(role_key))
            changed = True
        clean_permissions = [item for item in account.get("permissions", []) if item in valid_permissions]
        if clean_permissions != account.get("permissions"):
            account["permissions"] = clean_permissions
            changed = True
    existing_repair_work_orders = {item.get("related") for item in state.get("workOrders", []) if item.get("type") == "维修报修"}
    for repair in state.get("repairs", []):
        if "assignee" not in repair:
            repair["assignee"] = "repair_worker" if repair.get("status") in {"已派单", "维修中"} else ""
            changed = True
        steps = repair_progress_steps(repair.get("status", "待处理"))
        if repair.get("progressSteps") != steps:
            repair["progressSteps"] = steps
            changed = True
        for field, default_value in (
            ("reason", ""),
            ("materials", ""),
            ("evidenceImages", []),
            ("updateLogs", []),
        ):
            if field not in repair:
                repair[field] = list(default_value) if isinstance(default_value, list) else default_value
                changed = True
        if repair["id"] not in existing_repair_work_orders:
            state.setdefault("workOrders", []).append(repair_to_work_order(repair))
            changed = True
    if "arbitrations" in state:
        state.pop("arbitrations", None)
        changed = True
    if changed:
        save_state(state)
    return state


def save_state(state: dict[str, Any]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def append_log(state: dict[str, Any], action: str, target: str, content: str, operator: str = "superadmin") -> None:
    state.setdefault("logs", []).insert(
        0,
        {
            "operator": operator,
            "time": now(),
            "type": action,
            "target": target,
            "content": content,
            "ip": "127.0.0.1",
        },
    )


ROLE_LABELS = {
    "admin": "超级管理员",
    "super_admin": "超级管理员",
    "appointment_staff": "预约对接人员",
    "property_manager": "房源管理人员",
    "landlord": "房源管理人员",
    "repair_worker": "维修工",
    "tenant": "租客",
    "customer": "租客",
}


def normalize_role(role: str | None) -> str:
    if role in {"super_admin"}:
        return "admin"
    if role in {"landlord"}:
        return "property_manager"
    return role or "staff"


def chat_key(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-") or "contact"


def conversation_id_for(current_key: str, contact_key: str, scope: str = "direct") -> str:
    participants = sorted([current_key, contact_key])
    return f"{scope}:{participants[0]}:{participants[1]}"


def current_contact(current_user: User) -> dict[str, Any]:
    role = normalize_role(getattr(current_user.role, "value", current_user.role))
    return {
        "key": f"staff:{current_user.username}",
        "name": current_user.username,
        "role": role,
        "roleLabel": ROLE_LABELS.get(role, role),
        "scope": "当前账号",
    }


def account_contacts(state: dict[str, Any]) -> list[dict[str, Any]]:
    contacts: list[dict[str, Any]] = []
    for account in state.get("accounts", []):
        login = account.get("login") or account.get("name")
        if not login:
            continue
        role = normalize_role(account.get("roleKey"))
        contacts.append(
            {
                "key": f"staff:{login}",
                "name": account.get("name") or login,
                "login": login,
                "role": role,
                "roleLabel": ROLE_LABELS.get(role, account.get("role") or role),
                "scope": "后台人员",
            }
        )
    return contacts


def tenant_contacts_from_messages(state: dict[str, Any]) -> list[dict[str, Any]]:
    contacts: dict[str, dict[str, Any]] = {}
    for message in state.get("messages", []):
        sender = message.get("sender")
        if not sender or sender == "系统":
            continue
        key = f"tenant:{chat_key(sender)}"
        contacts[key] = {
            "key": key,
            "name": sender,
            "role": "tenant",
            "roleLabel": "租客",
            "scope": message.get("channel") or "客户咨询",
            "related": message.get("related") or message.get("id"),
        }
    return list(contacts.values())


def tenant_contacts_from_repairs(state: dict[str, Any], username: str | None = None) -> list[dict[str, Any]]:
    contacts: dict[str, dict[str, Any]] = {}
    for repair in state.get("repairs", []):
        if username and repair.get("assignee") != username and repair.get("owner") != username:
            continue
        tenant = repair.get("tenant")
        if not tenant:
            continue
        key = f"tenant:{chat_key(tenant)}"
        contacts[key] = {
            "key": key,
            "name": tenant,
            "role": "tenant",
            "roleLabel": "租客",
            "scope": f"维修对象 {repair.get('id')}",
            "related": repair.get("id"),
        }
    return list(contacts.values())


def allowed_chat_contacts(state: dict[str, Any], current_user: User) -> list[dict[str, Any]]:
    me = current_contact(current_user)
    role = me["role"]
    username = current_user.username
    staff = [item for item in account_contacts(state) if item["key"] != me["key"]]
    admins = [item for item in staff if item["role"] == "admin"]

    if role == "admin":
        return [item for item in staff if item["role"] != "tenant"]
    if role == "appointment_staff":
        return admins + tenant_contacts_from_messages(state)
    if role == "repair_worker":
        arrangers = [item for item in staff if item["role"] in {"admin", "appointment_staff"}]
        return arrangers + tenant_contacts_from_repairs(state, username)
    if role == "property_manager":
        return admins
    return []


def seed_conversation_messages(state: dict[str, Any], contact: dict[str, Any]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    if contact.get("role") != "tenant":
        return messages
    for message in state.get("messages", []):
        if chat_key(message.get("sender", "")) == contact["key"].replace("tenant:", ""):
            messages.append(
                {
                    "id": f"seed-{message.get('id')}",
                    "senderKey": contact["key"],
                    "senderName": contact["name"],
                    "content": message.get("summary", ""),
                    "createdAt": message.get("createdAt") or now(),
                    "readBy": [] if message.get("status") == "未读" else ["*"],
                    "system": False,
                }
            )
    for repair in state.get("repairs", []):
        if chat_key(repair.get("tenant", "")) == contact["key"].replace("tenant:", ""):
            messages.append(
                {
                    "id": f"seed-{repair.get('id')}",
                    "senderKey": contact["key"],
                    "senderName": contact["name"],
                    "content": f"报修：{repair.get('desc', '')}",
                    "createdAt": repair.get("date") or now(),
                    "readBy": ["*"],
                    "system": False,
                }
            )
    return sorted(messages, key=lambda item: item.get("createdAt", ""))


def build_chat_conversation(state: dict[str, Any], current_user: User, contact: dict[str, Any]) -> dict[str, Any]:
    me = current_contact(current_user)
    conversation_id = conversation_id_for(me["key"], contact["key"])
    stored = next(
        (item for item in state.setdefault("chatThreads", []) if item.get("id") == conversation_id),
        None,
    )
    stored_messages = list(stored.get("messages", [])) if stored else []
    seeded = seed_conversation_messages(state, contact)
    seen = {item.get("id") for item in stored_messages}
    messages = [item for item in seeded if item.get("id") not in seen] + stored_messages
    messages = sorted(messages, key=lambda item: item.get("createdAt", ""))
    read_receipts = state.setdefault("chatReadReceipts", {})
    enriched_messages: list[dict[str, Any]] = []
    for raw_message in messages:
        message = dict(raw_message)
        read_by = set(message.get("readBy") or [])
        read_by.update(read_receipts.get(message.get("id"), []))
        message["readBy"] = list(read_by)
        message["unread"] = (
            message.get("senderKey") != me["key"]
            and me["key"] not in read_by
            and "*" not in read_by
        )
        enriched_messages.append(message)
    unread_count = sum(1 for message in enriched_messages if message.get("unread"))
    return {
        "id": conversation_id,
        "contact": {**contact, "conversationId": conversation_id, "unreadCount": unread_count},
        "participants": [me, contact],
        "messages": enriched_messages,
        "lastMessage": enriched_messages[-1] if enriched_messages else None,
        "unreadCount": unread_count,
    }


def chat_state_for_user(state: dict[str, Any], current_user: User) -> dict[str, Any]:
    contacts = allowed_chat_contacts(state, current_user)
    conversations = [build_chat_conversation(state, current_user, contact) for contact in contacts]
    contacts = [conversation["contact"] for conversation in conversations]
    unread_total = sum(conversation.get("unreadCount", 0) for conversation in conversations)
    return {"me": current_contact(current_user), "contacts": contacts, "conversations": conversations, "unreadTotal": unread_total}


class ComplaintCreate(BaseModel):
    category: str
    title: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=5, max_length=2000)
    complainantName: str = Field(min_length=1, max_length=80)
    contact: str = Field(min_length=3, max_length=80)
    city: str = Field(min_length=1, max_length=80)
    property: str | None = None


class CustomerContactCreate(BaseModel):
    sender: str = Field(min_length=1, max_length=80)
    contact: str = Field(min_length=3, max_length=80)
    summary: str = Field(min_length=3, max_length=500)
    property: str | None = None
    propertyId: int | None = None
    channel: str = Field(default="房源咨询", max_length=40)


class MessageHandleUpdate(BaseModel):
    action: str = Field(pattern="^(claim|reply|resolve)$")
    reply: str | None = Field(default=None, max_length=800)
    assignee: str | None = Field(default=None, max_length=80)


class ChatMessageCreate(BaseModel):
    conversationId: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=1, max_length=1000)


class StatusUpdate(BaseModel):
    status: str
    result: str | None = None


class AccountPermissionUpdate(BaseModel):
    roleKey: str | None = None
    permissions: list[str] | None = None
    status: str | None = None


class RolePermissionUpdate(BaseModel):
    permissions: list[str] = Field(default_factory=list)


class AppointmentAssign(BaseModel):
    assignee: str = Field(min_length=1, max_length=80)


class RepairCreate(BaseModel):
    property: str = Field(min_length=1, max_length=160)
    tenant: str = Field(min_length=1, max_length=80)
    category: str = Field(min_length=1, max_length=40)
    desc: str = Field(min_length=3, max_length=800)


class RepairUpdate(BaseModel):
    status: str | None = None
    assignee: str | None = None
    result: str | None = None
    reason: str | None = None
    materials: str | None = None
    evidenceImages: list[dict[str, Any]] = Field(default_factory=list)


class PortalActionCreate(BaseModel):
    action: str = Field(min_length=1, max_length=80)
    target: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=500)


@router.get("/public/options")
async def get_public_options() -> dict[str, Any]:
    state = load_state()
    return {
        "categories": ["房源问题", "服务问题", "押金问题", "合同问题", "其他"],
        "cities": state["settings"].get("cities", []),
    }


@router.post("/complaints", status_code=status.HTTP_201_CREATED)
async def create_complaint(payload: ComplaintCreate) -> dict[str, Any]:
    state = load_state()
    complaint_id = f"CP-{len(state['complaints']) + 1001}"
    complaint = {
        "id": complaint_id,
        "category": payload.category,
        "title": payload.title,
        "description": payload.description,
        "complainantName": payload.complainantName,
        "contact": payload.contact,
        "city": payload.city,
        "property": payload.property or "",
        "status": "待处理",
        "priority": "重要" if payload.category in {"押金问题", "服务问题"} else "一般",
        "createdAt": now(),
        "result": "",
    }
    state["complaints"].insert(0, complaint)
    state.setdefault("workOrders", []).insert(
        0,
        {
            "id": f"WO-{len(state.get('workOrders', [])) + 2101}",
            "type": "投诉核实",
            "title": payload.title,
            "owner": "客服组",
            "related": complaint_id,
            "deadline": "24 小时内",
            "priority": complaint["priority"],
            "status": "待处理",
            "result": "",
        },
    )
    state.setdefault("messages", []).insert(
        0,
        {
            "id": f"MSG-{len(state.get('messages', [])) + 7001}",
            "channel": "投诉",
            "sender": payload.complainantName,
            "target": "客服组",
            "summary": payload.title,
            "related": complaint_id,
            "createdAt": now(),
            "status": "未读",
        },
    )
    append_log(state, "投诉提交", complaint_id, f"{payload.complainantName} 提交投诉：{payload.title}", operator="customer")
    save_state(state)
    return complaint


@router.post("/messages", status_code=status.HTTP_201_CREATED)
async def create_customer_message(payload: CustomerContactCreate) -> dict[str, Any]:
    state = load_state()
    message_id = f"MSG-{len(state.get('messages', [])) + 7001}"
    related = f"PROP-{payload.propertyId}" if payload.propertyId else ""
    summary_parts = [payload.summary]
    if payload.property:
        summary_parts.append(f"关联房源：{payload.property}")
    summary_parts.append(f"联系方式：{payload.contact}")
    message = {
        "id": message_id,
        "channel": payload.channel or "房源咨询",
        "sender": payload.sender,
        "target": "预约对接组",
        "summary": "；".join(summary_parts),
        "related": related,
        "createdAt": now(),
        "status": "未读",
    }
    state.setdefault("messages", []).insert(0, message)
    state.setdefault("workOrders", []).insert(
        0,
        {
            "id": f"WO-{len(state.get('workOrders', [])) + 2101}",
            "type": "客户咨询",
            "title": payload.summary,
            "owner": "预约对接组",
            "related": message_id,
            "deadline": "2 小时内",
            "priority": "一般",
            "status": "待处理",
            "result": "",
        },
    )
    append_log(state, "客户咨询", message_id, f"{payload.sender} 咨询：{payload.summary}", operator="customer")
    save_state(state)
    return message


def repair_to_work_order(repair: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"WO-{repair['id'].replace('RP-', '')}",
        "type": "维修报修",
        "title": repair["desc"],
        "owner": repair.get("assignee") or repair.get("owner") or "维修组",
        "related": repair["id"],
        "deadline": "48 小时内",
        "priority": "重要" if repair.get("category") in {"水电", "家电"} else "一般",
        "status": repair["status"],
        "result": repair.get("result", ""),
    }


@router.get("/repairs")
async def list_repairs(current_user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    repairs = load_state().get("repairs", [])
    if current_user.role.value == "repair_worker":
        return [item for item in repairs if item.get("assignee") == current_user.username]
    return repairs


@router.post("/repairs", status_code=status.HTTP_201_CREATED)
async def create_repair(payload: RepairCreate) -> dict[str, Any]:
    state = load_state()
    repair_id = f"RP-{len(state.setdefault('repairs', [])) + 5001}"
    repair = {
        "id": repair_id,
        "property": payload.property,
        "tenant": payload.tenant,
        "category": payload.category,
        "desc": payload.desc,
        "date": now()[:10],
        "status": "待处理",
        "owner": "维修组",
        "assignee": "",
        "progressSteps": repair_progress_steps("待处理"),
        "reason": "",
        "materials": "",
        "evidenceImages": [],
        "updateLogs": [],
        "result": "",
    }
    state["repairs"].insert(0, repair)
    state.setdefault("workOrders", []).insert(0, repair_to_work_order(repair))
    state.setdefault("messages", []).insert(
        0,
        {
            "id": f"MSG-{len(state.get('messages', [])) + 7001}",
            "channel": "报修",
            "sender": payload.tenant,
            "target": "维修组",
            "summary": payload.desc,
            "related": repair_id,
            "createdAt": now(),
            "status": "未读",
        },
    )
    append_log(state, "报修提交", repair_id, f"{payload.tenant} 提交报修：{payload.desc}", operator="tenant")
    save_state(state)
    return repair


@router.patch("/repairs/{repair_id}")
async def update_repair(repair_id: str, payload: RepairUpdate) -> dict[str, Any]:
    state = load_state()
    for repair in state.get("repairs", []):
        if repair["id"] == repair_id:
            if payload.status is not None:
                repair["status"] = payload.status
                repair["progressSteps"] = repair_progress_steps(payload.status)
            if payload.assignee is not None:
                repair["assignee"] = payload.assignee
                repair["owner"] = payload.assignee or "维修组"
            if payload.result is not None:
                repair["result"] = payload.result
            if payload.reason is not None:
                repair["reason"] = payload.reason
            if payload.materials is not None:
                repair["materials"] = payload.materials
            if payload.evidenceImages:
                repair["evidenceImages"] = payload.evidenceImages
            if payload.reason is not None or payload.materials is not None or payload.evidenceImages:
                repair.setdefault("updateLogs", []).insert(
                    0,
                    {
                        "time": now(),
                        "status": repair.get("status"),
                        "assignee": repair.get("assignee") or "",
                        "reason": payload.reason or "",
                        "materials": payload.materials or "",
                        "result": payload.result or "",
                        "images": payload.evidenceImages,
                    },
                )
            for work_order in state.get("workOrders", []):
                if work_order.get("related") == repair_id:
                    if payload.status is not None:
                        work_order["status"] = payload.status
                    if payload.assignee is not None:
                        work_order["owner"] = payload.assignee or "维修组"
                    if payload.result is not None:
                        work_order["result"] = payload.result
            append_log(state, "维修工单更新", repair_id, f"状态更新为 {repair['status']}；维修工：{repair.get('assignee') or '-'}；原因：{payload.reason or '-'}；材料：{payload.materials or '-'}；处理记录：{payload.result or '-'}")
            save_state(state)
            return repair
    raise HTTPException(status_code=404, detail="Repair not found")


@router.get("/overview")
async def get_overview(_: object = Depends(require_admin)) -> dict[str, Any]:
    state = load_state()
    pending_complaints = [c for c in state["complaints"] if c["status"] != "已完结"]
    pending_work_orders = [w for w in state.get("workOrders", []) if w["status"] != "已完结"]
    pending_finance = [f for f in state.get("financeItems", []) if f["status"] not in {"已退款", "已扣款", "已完结"}]
    urgent_warnings = [w for w in state["warnings"] if w["level"] == "紧急" and w["status"] != "已处理"]
    return {
        "metrics": [
            {"label": "今日预约数", "value": len(state["appointments"]), "hint": "来自预约调度", "danger": False},
            {"label": "今日带看数", "value": 18, "hint": "示例统计", "danger": False},
            {"label": "今日签约数", "value": 7, "hint": "转化稳定", "danger": False},
            {"label": "待处理投诉", "value": len(pending_complaints), "hint": "来自投诉入口", "danger": True},
            {"label": "待办工单", "value": len(pending_work_orders), "hint": "投诉、维修、带看反馈", "danger": True},
            {"label": "押金财务待处理", "value": len(pending_finance), "hint": "退款、扣款、凭证记录", "danger": True},
            {"label": "紧急预警", "value": len(urgent_warnings), "hint": "来自预警中心", "danger": True},
        ],
        "cityRanks": [
            {"city": "伦敦", "count": 86, "percent": 100},
            {"city": "纽约", "count": 73, "percent": 85},
            {"city": "悉尼", "count": 55, "percent": 64},
            {"city": "多伦多", "count": 38, "percent": 44},
            {"city": "新加坡", "count": 25, "percent": 29},
        ],
        "trend": [
            {"day": "D-6", "booking": 62, "sign": 26},
            {"day": "D-5", "booking": 84, "sign": 34},
            {"day": "D-4", "booking": 70, "sign": 28},
            {"day": "D-3", "booking": 96, "sign": 42},
            {"day": "D-2", "booking": 76, "sign": 30},
            {"day": "D-1", "booking": 90, "sign": 38},
            {"day": "今日", "booking": 68, "sign": 32},
        ],
    }


@router.get("/state")
async def get_admin_portal_state(_: object = Depends(require_admin)) -> dict[str, Any]:
    return load_state()


@router.get("/workspace-state")
async def get_workspace_state(current_user: User = Depends(require_workspace_user)) -> dict[str, Any]:
    state = load_state()
    role = getattr(current_user.role, "value", current_user.role)

    if role in {"admin", "landlord"}:
        return state

    payload: dict[str, Any] = {
        "messages": [],
        "workOrders": [],
        "accounts": state.get("accounts", []),
        "repairs": [],
        "schedules": [],
        "logs": [],
        "financeItems": [],
        "permissionCatalog": [],
        "roleProfiles": [],
    }

    if role == "appointment_staff":
        payload["messages"] = state.get("messages", [])
        payload["workOrders"] = state.get("workOrders", [])
        payload["repairs"] = state.get("repairs", [])
        payload["schedules"] = [
            item for item in state.get("schedules", [])
            if item.get("role") == "预约对接人员" or item.get("name") == current_user.username
        ]
    elif role == "repair_worker":
        payload["repairs"] = [
            item for item in state.get("repairs", [])
            if item.get("assignee") == current_user.username or item.get("owner") == current_user.username
        ]
        related_repairs = {item.get("id") for item in payload["repairs"]}
        payload["workOrders"] = [
            item for item in state.get("workOrders", [])
            if item.get("related") in related_repairs or item.get("owner") == current_user.username
        ]
    elif role == "property_manager":
        payload["workOrders"] = [
            item for item in state.get("workOrders", [])
            if item.get("type") in {"房源审核", "房源运营"}
        ]

    return payload


@router.get("/chat")
async def get_chat_state(current_user: User = Depends(require_workspace_user)) -> dict[str, Any]:
    state = load_state()
    chat_state = chat_state_for_user(state, current_user)
    if "chatThreads" not in state:
        state["chatThreads"] = []
        save_state(state)
    return chat_state


@router.post("/chat/messages", status_code=status.HTTP_201_CREATED)
async def send_chat_message(
    payload: ChatMessageCreate,
    current_user: User = Depends(require_workspace_user),
) -> dict[str, Any]:
    state = load_state()
    chat_state = chat_state_for_user(state, current_user)
    conversation = next(
        (item for item in chat_state["conversations"] if item["id"] == payload.conversationId),
        None,
    )
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chat target is not allowed for this role")

    me = chat_state["me"]
    contact = conversation["contact"]
    threads = state.setdefault("chatThreads", [])
    thread = next((item for item in threads if item.get("id") == payload.conversationId), None)
    if thread is None:
        thread = {
            "id": payload.conversationId,
            "participants": [me["key"], contact["key"]],
            "messages": [],
        }
        threads.append(thread)

    message = {
        "id": f"CHAT-{sum(len(item.get('messages', [])) for item in threads) + 1:05d}",
        "senderKey": me["key"],
        "senderName": me["name"],
        "senderRole": me["roleLabel"],
        "content": payload.content.strip(),
        "createdAt": now(),
        "readBy": [me["key"]],
        "system": False,
    }
    thread.setdefault("messages", []).append(message)
    append_log(state, "聊天消息", payload.conversationId, f"{me['name']} 发送消息给 {contact['name']}", operator=me["name"])
    save_state(state)

    refreshed = chat_state_for_user(state, current_user)
    return next(item for item in refreshed["conversations"] if item["id"] == payload.conversationId)


@router.patch("/chat/{conversation_id}/read")
async def mark_chat_read(
    conversation_id: str,
    current_user: User = Depends(require_workspace_user),
) -> dict[str, Any]:
    state = load_state()
    chat_state = chat_state_for_user(state, current_user)
    conversation = next(
        (item for item in chat_state["conversations"] if item["id"] == conversation_id),
        None,
    )
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chat target is not allowed for this role")

    me = chat_state["me"]
    receipts = state.setdefault("chatReadReceipts", {})
    for message in conversation.get("messages", []):
        if message.get("senderKey") == me["key"]:
            continue
        message_id = message.get("id")
        if not message_id:
            continue
        readers = set(receipts.get(message_id, []))
        readers.add(me["key"])
        receipts[message_id] = list(readers)

    for thread in state.setdefault("chatThreads", []):
        if thread.get("id") != conversation_id:
            continue
        for message in thread.get("messages", []):
            if message.get("senderKey") == me["key"]:
                continue
            read_by = set(message.get("readBy") or [])
            read_by.add(me["key"])
            message["readBy"] = list(read_by)

    save_state(state)
    refreshed = chat_state_for_user(state, current_user)
    return next(item for item in refreshed["conversations"] if item["id"] == conversation_id)


@router.post("/actions", status_code=status.HTTP_201_CREATED)
async def create_portal_action(
    payload: PortalActionCreate,
    current_user: object = Depends(require_workspace_user),
) -> dict[str, Any]:
    state = load_state()
    timestamp = now()
    action = {
        "id": f"ACT-{len(state.setdefault('actionHistory', [])) + 1:04d}",
        "action": payload.action,
        "target": payload.target,
        "content": payload.content,
        "createdAt": timestamp,
        "operator": getattr(current_user, "username", "workspace"),
        "status": "已记录",
    }

    if payload.action == "report.generate":
        report = {
            "id": f"RPT-{len(state.setdefault('reports', [])) + 1:04d}",
            "name": "运营综合报表",
            "source": "真实预约、投诉、工单、房源状态",
            "bookings": len(state.get("appointments", [])),
            "complaints": len(state.get("complaints", [])),
            "workOrders": len(state.get("workOrders", [])),
            "properties": len(state.get("properties", [])),
            "createdAt": timestamp,
            "status": "已生成",
        }
        state["reports"].insert(0, report)
        action["status"] = "已生成报表"
    elif payload.action == "report.export":
        export_request = {
            "id": f"EXP-{len(state.setdefault('exportRequests', [])) + 1:04d}",
            "name": "运营数据导出",
            "scope": "预约、投诉、工单、财务、房源",
            "applicant": "superadmin",
            "createdAt": timestamp,
            "status": "待审批",
        }
        state["exportRequests"].insert(0, export_request)
        action["status"] = "已提交导出审批"
    elif payload.action == "exception.remind":
        for exception in state.get("exceptions", []):
            if exception.get("id") == payload.target:
                exception["status"] = "处理中"
                exception["result"] = payload.content
                state.setdefault("messages", []).insert(
                    0,
                    {
                        "id": f"MSG-{len(state.get('messages', [])) + 7001}",
                        "channel": "督办",
                        "sender": getattr(current_user, "username", "workspace"),
                        "target": exception.get("owner", "对接人"),
                        "summary": payload.content,
                        "related": payload.target,
                        "createdAt": timestamp,
                        "status": "未读",
                    },
                )
                action["status"] = "已催办"
                break

    state["actionHistory"].insert(0, action)
    append_log(state, "运营动作", payload.target, payload.content, operator=getattr(current_user, "username", "workspace"))
    save_state(state)
    return action


@router.patch("/messages/{message_id}/handle")
async def handle_message(
    message_id: str,
    payload: MessageHandleUpdate,
    current_user: User = Depends(require_workspace_user),
) -> dict[str, Any]:
    role = getattr(current_user.role, "value", current_user.role)
    if role not in {"admin", "landlord", "appointment_staff"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Message handling role required")

    state = load_state()
    timestamp = now()
    operator = current_user.username

    for message in state.get("messages", []):
        if message.get("id") != message_id:
            continue

        work_order = next(
            (
                item for item in state.get("workOrders", [])
                if item.get("related") in {message_id, message.get("related")}
            ),
            None,
        )

        assignee = payload.assignee or message.get("assignee") or operator
        message["assignee"] = assignee
        message["handledAt"] = timestamp

        if payload.action == "claim":
            message["status"] = "处理中"
            message["result"] = f"{assignee} 已认领，待回复客户"
            if work_order:
                work_order["owner"] = assignee
                work_order["status"] = "处理中"
                work_order["result"] = "消息已认领，等待客户沟通反馈"
            log_content = f"{operator} 认领消息 {message_id}"
        elif payload.action == "reply":
            if not payload.reply or not payload.reply.strip():
                raise HTTPException(status_code=400, detail="Reply content required")
            reply = {
                "operator": operator,
                "content": payload.reply.strip(),
                "createdAt": timestamp,
            }
            message.setdefault("replies", []).insert(0, reply)
            message["status"] = "已回复"
            message["result"] = payload.reply.strip()
            if work_order:
                work_order["owner"] = assignee
                work_order["status"] = "处理中"
                work_order["result"] = payload.reply.strip()
            log_content = f"{operator} 回复消息 {message_id}：{payload.reply.strip()}"
        else:
            result = payload.reply.strip() if payload.reply else "客户咨询已处理完结"
            message["status"] = "已处理"
            message["result"] = result
            message["resolvedAt"] = timestamp
            if work_order:
                work_order["owner"] = assignee
                work_order["status"] = "已完结"
                work_order["result"] = result
            log_content = f"{operator} 结案消息 {message_id}：{result}"

        append_log(state, "消息处理", message_id, log_content, operator=operator)
        save_state(state)
        return {"message": message, "workOrder": work_order}

    raise HTTPException(status_code=404, detail="Message not found")


@router.patch("/accounts/{account_id}")
async def update_account_permissions(
    account_id: str,
    payload: AccountPermissionUpdate,
    _: object = Depends(require_admin),
) -> dict[str, Any]:
    state = load_state()
    valid_roles = {role["key"] for role in state.get("roleProfiles", [])}
    valid_permissions = set(all_permission_keys())
    for account in state.get("accounts", []):
        if account["id"] != account_id:
            continue
        if account_id == "A-001":
            account["roleKey"] = "super_admin"
            account["role"] = "超级管理员"
            account["permissions"] = all_permission_keys()
            account["status"] = "启用"
            append_log(state, "账号权限更新", account_id, "超级管理员账号保持最高权限，不允许降权")
            save_state(state)
            return account
        if payload.roleKey is not None:
            if payload.roleKey not in valid_roles:
                raise HTTPException(status_code=400, detail="Unsupported role")
            account["roleKey"] = payload.roleKey
            account["role"] = role_name_by_key(payload.roleKey)
            if payload.permissions is None:
                account["permissions"] = default_permissions_for_role(payload.roleKey)
        if payload.permissions is not None:
            account["permissions"] = [item for item in payload.permissions if item in valid_permissions]
        if payload.status is not None:
            account["status"] = payload.status
        append_log(state, "账号权限更新", account_id, f"{account['name']} 更新为 {account['role']}")
        save_state(state)
        return account
    raise HTTPException(status_code=404, detail="Account not found")


@router.patch("/roles/{role_key}")
async def update_role_permissions(
    role_key: str,
    payload: RolePermissionUpdate,
    _: object = Depends(require_admin),
) -> dict[str, Any]:
    state = load_state()
    valid_permissions = set(all_permission_keys())
    for role in state.get("roleProfiles", []):
        if role["key"] != role_key:
            continue
        if role.get("locked"):
            role["permissions"] = all_permission_keys()
            append_log(state, "角色权限更新", role_key, "超级管理员角色保持最高权限，不允许降权")
            save_state(state)
            return role
        role["permissions"] = [item for item in payload.permissions if item in valid_permissions]
        append_log(state, "角色权限更新", role_key, f"{role['name']} 权限已更新")
        save_state(state)
        return role
    raise HTTPException(status_code=404, detail="Role not found")


@router.patch("/complaints/{complaint_id}")
async def update_complaint(
    complaint_id: str,
    payload: StatusUpdate,
    _: object = Depends(require_admin),
) -> dict[str, Any]:
    state = load_state()
    for complaint in state["complaints"]:
        if complaint["id"] == complaint_id:
            complaint["status"] = payload.status
            if payload.result is not None:
                complaint["result"] = payload.result
            append_log(state, "投诉处理", complaint_id, f"状态更新为 {payload.status}；处理结果：{payload.result or '-'}")
            save_state(state)
            return complaint
    raise HTTPException(status_code=404, detail="Complaint not found")


@router.patch("/appointments/{appointment_id}/assign")
async def assign_appointment(
    appointment_id: str,
    payload: AppointmentAssign,
    _: object = Depends(require_admin),
) -> dict[str, Any]:
    state = load_state()
    for appointment in state["appointments"]:
        if appointment["id"] == appointment_id:
            appointment["assignee"] = payload.assignee
            appointment["status"] = "待确认"
            append_log(state, "预约分配", appointment_id, f"分配给 {payload.assignee}")
            save_state(state)
            return appointment
    raise HTTPException(status_code=404, detail="Appointment not found")


@router.patch("/items/{collection}/{item_id}")
async def update_item_status(
    collection: str,
    item_id: str,
    payload: StatusUpdate,
    _: object = Depends(require_admin),
) -> dict[str, Any]:
    allowed = {
        "properties": "id",
        "appointments": "id",
        "exceptions": "id",
        "warnings": "id",
        "staff": "id",
        "accounts": "id",
        "workOrders": "id",
        "messages": "id",
        "financeItems": "id",
    }
    if collection not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported collection")
    state = load_state()
    key = allowed[collection]
    for item in state[collection]:
        if item[key] == item_id:
            item["status"] = payload.status
            if payload.result is not None:
                item["result"] = payload.result
            if collection == "workOrders" and item.get("type") == "维修报修":
                for repair in state.get("repairs", []):
                    if repair["id"] == item.get("related"):
                        repair["status"] = payload.status
                        if payload.result is not None:
                            repair["result"] = payload.result
            append_log(state, "状态更新", item_id, f"{collection} 状态更新为 {payload.status}")
            save_state(state)
            return item
    raise HTTPException(status_code=404, detail="Item not found")

