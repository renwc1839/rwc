from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import require_admin

router = APIRouter()

DATA_FILE = Path(__file__).resolve().parents[4] / "data" / "admin_portal_state.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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
        "arbitrations": [
            {"caseNo": "AR-1001", "type": "押金纠纷", "parties": "李同学 / UK Living", "amount": "£1,200", "evidence": "照片 8 张、合同 1 份", "status": "待仲裁", "result": ""},
            {"caseNo": "PN-0039", "type": "违规处罚", "parties": "房东 NY Homes", "amount": "虚假房源", "evidence": "房源截图、核验记录", "status": "待处理", "result": ""},
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
        "accounts": [
            {"id": "A-001", "name": "superadmin", "role": "超级管理员", "phone": "138****0000", "twoFactor": True, "status": "启用"},
            {"id": "A-002", "name": "ops_london", "role": "城市运营", "phone": "139****1201", "twoFactor": True, "status": "启用"},
        ],
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
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


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


class ComplaintCreate(BaseModel):
    category: str
    title: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=5, max_length=2000)
    complainantName: str = Field(min_length=1, max_length=80)
    contact: str = Field(min_length=3, max_length=80)
    city: str = Field(min_length=1, max_length=80)
    property: str | None = None


class StatusUpdate(BaseModel):
    status: str
    result: str | None = None


class AppointmentAssign(BaseModel):
    assignee: str = Field(min_length=1, max_length=80)


class RuleUpdate(BaseModel):
    rules: dict[str, Any]


class RuleChangeRequest(BaseModel):
    scope: str = Field(min_length=1, max_length=80)
    reason: str = Field(min_length=5, max_length=1000)


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
    state["arbitrations"].insert(
        0,
        {
            "caseNo": complaint_id,
            "type": "投诉处理",
            "parties": f"{payload.complainantName} / 平台",
            "amount": payload.category,
            "evidence": payload.title,
            "status": "待处理",
            "result": "",
        },
    )
    append_log(state, "投诉提交", complaint_id, f"{payload.complainantName} 提交投诉：{payload.title}", operator="customer")
    save_state(state)
    return complaint


@router.get("/overview")
async def get_overview(_: object = Depends(require_admin)) -> dict[str, Any]:
    state = load_state()
    pending_complaints = [c for c in state["complaints"] if c["status"] != "已完结"]
    pending_arbitrations = [a for a in state["arbitrations"] if a["status"] in {"待仲裁", "待处理"}]
    urgent_warnings = [w for w in state["warnings"] if w["level"] == "紧急" and w["status"] != "已处理"]
    return {
        "metrics": [
            {"label": "今日预约数", "value": len(state["appointments"]), "hint": "来自预约调度", "danger": False},
            {"label": "今日带看数", "value": 18, "hint": "示例统计", "danger": False},
            {"label": "今日签约数", "value": 7, "hint": "转化稳定", "danger": False},
            {"label": "待处理投诉", "value": len(pending_complaints), "hint": "来自投诉入口", "danger": True},
            {"label": "待仲裁纠纷", "value": len(pending_arbitrations), "hint": "来自仲裁中心", "danger": True},
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
            for arbitration in state["arbitrations"]:
                if arbitration["caseNo"] == complaint_id:
                    arbitration["status"] = payload.status
                    arbitration["result"] = payload.result or arbitration.get("result", "")
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
    allowed = {"properties": "id", "exceptions": "id", "arbitrations": "caseNo", "warnings": "id", "staff": "id", "accounts": "id"}
    if collection not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported collection")
    state = load_state()
    key = allowed[collection]
    for item in state[collection]:
        if item[key] == item_id:
            item["status"] = payload.status
            if payload.result is not None:
                item["result"] = payload.result
            append_log(state, "状态更新", item_id, f"{collection} 状态更新为 {payload.status}")
            save_state(state)
            return item
    raise HTTPException(status_code=404, detail="Item not found")


@router.put("/rules")
async def update_rules(payload: RuleUpdate, _: object = Depends(require_admin)) -> dict[str, Any]:
    state = load_state()
    protected_penalty = deepcopy(state["rules"].get("penalty", seed_state()["rules"]["penalty"]))
    next_rules = deepcopy(payload.rules)
    next_rules["penalty"] = protected_penalty
    state["rules"] = next_rules
    append_log(state, "规则发布", "rules", "管理员发布了新的运营规则配置；处罚治理策略保持锁定")
    save_state(state)
    return state["rules"]


@router.post("/rules/change-requests", status_code=status.HTTP_201_CREATED)
async def create_rule_change_request(
    payload: RuleChangeRequest,
    _: object = Depends(require_admin),
) -> dict[str, Any]:
    state = load_state()
    request_id = f"RC-{len(state.setdefault('ruleChangeRequests', [])) + 1001}"
    item = {
        "id": request_id,
        "scope": payload.scope,
        "reason": payload.reason,
        "status": "待评审",
        "createdAt": now(),
    }
    state["ruleChangeRequests"].insert(0, item)
    append_log(state, "规则变更申请", request_id, f"{payload.scope}：{payload.reason}")
    save_state(state)
    return item
