"""同学协作 API — 学习小组和讨论，数据存储在本地 JSON 文件中。"""

import json
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from app.schemas.common import ApiResponse

router = APIRouter(prefix="/collaboration", tags=["collaboration"])

COLLAB_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "collaboration.json")


def _load_data() -> dict[str, Any]:
    try:
        os.makedirs(os.path.dirname(COLLAB_FILE), exist_ok=True)
        with open(COLLAB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"groups": [], "discussions": []}


def _save_data(data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(COLLAB_FILE), exist_ok=True)
    with open(COLLAB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="小组名称")
    topic: str = Field(default="", description="学习主题")
    course: str = Field(default="", description="关联课程")


class DiscussionCreate(BaseModel):
    group_id: str = Field(default="", description="关联小组 ID")
    author: str = Field(default="匿名", description="发帖人")
    content: str = Field(..., min_length=1, max_length=2000, description="讨论内容")
    topic_tag: str = Field(default="", description="话题标签")


@router.get("/groups", summary="获取学习小组列表")
async def list_groups() -> ApiResponse[dict]:
    data = _load_data()
    return ApiResponse.success(data={"groups": data.get("groups", [])})


@router.post("/groups", summary="创建学习小组")
async def create_group(group: GroupCreate) -> ApiResponse[dict]:
    data = _load_data()
    import uuid
    new_group = group.model_dump()
    new_group["id"] = uuid.uuid4().hex[:8]
    new_group["member_count"] = 1
    new_group["created_at"] = datetime.now(timezone.utc).isoformat()
    data.setdefault("groups", []).append(new_group)
    _save_data(data)
    return ApiResponse.success(data=new_group, message="小组已创建")


@router.get("/discussions", summary="获取讨论列表")
async def list_discussions() -> ApiResponse[dict]:
    data = _load_data()
    return ApiResponse.success(data={"discussions": data.get("discussions", [])})


@router.post("/discussions", summary="发起讨论")
async def create_discussion(disc: DiscussionCreate) -> ApiResponse[dict]:
    data = _load_data()
    import uuid
    new_disc = disc.model_dump()
    new_disc["id"] = uuid.uuid4().hex[:8]
    new_disc["created_at"] = datetime.now(timezone.utc).isoformat()
    new_disc["replies"] = 0
    new_disc["likes"] = 0
    data.setdefault("discussions", []).insert(0, new_disc)
    _save_data(data)
    return ApiResponse.success(data=new_disc, message="讨论已发布")
