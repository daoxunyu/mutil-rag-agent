"""学习日历 API — 日历事件 CRUD，数据存储在本地 JSON 文件中。"""

import json
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field

from app.schemas.common import ApiResponse

router = APIRouter(prefix="/calendar", tags=["calendar"])

CALENDAR_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "calendar.json")


def _load_events() -> list[dict[str, Any]]:
    try:
        os.makedirs(os.path.dirname(CALENDAR_FILE), exist_ok=True)
        with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_events(events: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(CALENDAR_FILE), exist_ok=True)
    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="事件标题")
    date: str = Field(..., description="日期 (YYYY-MM-DD)")
    time: str = Field(default="", description="时间 (如: 14:00-15:40)")
    event_type: str = Field(default="study", description="类型: study/exam/assignment/review/other")
    course_name: str = Field(default="", description="关联课程名称")
    description: str = Field(default="", max_length=1000, description="详细描述")
    duration_minutes: int = Field(default=45, ge=0, description="预计时长(分钟)")


@router.get("", summary="获取日历事件")
async def list_events(
    year: int = Query(default=0, description="年份筛选"),
    month: int = Query(default=0, description="月份筛选"),
) -> ApiResponse[dict]:
    events = _load_events()
    if year > 0 and month > 0:
        prefix = f"{year}-{month:02d}"
        events = [e for e in events if e.get("date", "").startswith(prefix)]
    return ApiResponse.success(data={"total": len(events), "events": events})


@router.post("", summary="添加日历事件")
async def create_event(event: EventCreate) -> ApiResponse[dict]:
    events = _load_events()
    import uuid
    new_event = event.model_dump()
    new_event["id"] = uuid.uuid4().hex[:8]
    new_event["created_at"] = datetime.now(timezone.utc).isoformat()
    events.append(new_event)
    _save_events(events)
    logger.info(f"[calendar] event created: {new_event['title']} on {new_event['date']}")
    return ApiResponse.success(data=new_event, message="事件已添加")


@router.delete("/{event_id}", summary="删除日历事件")
async def delete_event(event_id: str) -> ApiResponse[dict]:
    events = _load_events()
    for i, e in enumerate(events):
        if e.get("id") == event_id:
            deleted = events.pop(i)
            _save_events(events)
            return ApiResponse.success(data={"deleted_id": event_id}, message="事件已删除")
    raise HTTPException(404, f"事件不存在: {event_id}")
