"""课程管理 API — CRUD 操作，数据存储在本地 JSON 文件中。"""

import json
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from app.schemas.common import ApiResponse

router = APIRouter(prefix="/courses", tags=["courses"])

COURSES_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "courses.json")


def _load_courses() -> list[dict[str, Any]]:
    try:
        os.makedirs(os.path.dirname(COURSES_FILE), exist_ok=True)
        with open(COURSES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_courses(courses: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(COURSES_FILE), exist_ok=True)
    with open(COURSES_FILE, "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)


class CourseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="课程名称")
    college: str = Field(default="", description="所属学院")
    schedule: str = Field(default="", description="上课时间 (如: 周三 8:00-9:40)")
    category: str = Field(default="必修", description="课程类型: 必修/选修")
    credits: float = Field(default=3.0, gt=0, description="学分")
    instructor: str = Field(default="", description="授课教师")
    progress: int = Field(default=0, ge=0, le=100, description="学习进度百分比")
    assignments_done: int = Field(default=0, ge=0, description="已完成作业数")
    assignments_total: int = Field(default=0, ge=0, description="总作业数")
    gpa: float = Field(default=0, ge=0, le=5.0, description="该课程 GPA")


class CourseUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    college: str | None = None
    schedule: str | None = None
    category: str | None = None
    credits: float | None = Field(default=None, gt=0)
    instructor: str | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    assignments_done: int | None = Field(default=None, ge=0)
    assignments_total: int | None = Field(default=None, ge=0)
    gpa: float | None = Field(default=None, ge=0, le=5.0)


@router.get("", summary="获取课程列表")
async def list_courses() -> ApiResponse[dict]:
    courses = _load_courses()
    return ApiResponse.success(data={"total": len(courses), "courses": courses})


@router.post("", summary="添加课程")
async def create_course(course: CourseCreate) -> ApiResponse[dict]:
    courses = _load_courses()
    import uuid
    new_course = course.model_dump()
    new_course["id"] = uuid.uuid4().hex[:12]
    new_course["created_at"] = datetime.now(timezone.utc).isoformat()
    courses.append(new_course)
    _save_courses(courses)
    logger.info(f"[courses] created: {new_course['name']} (id={new_course['id']})")
    return ApiResponse.success(data=new_course, message="课程已添加")


@router.put("/{course_id}", summary="更新课程")
async def update_course(course_id: str, update: CourseUpdate) -> ApiResponse[dict]:
    courses = _load_courses()
    for c in courses:
        if c.get("id") == course_id:
            updates = update.model_dump(exclude_none=True)
            c.update(updates)
            c["updated_at"] = datetime.now(timezone.utc).isoformat()
            _save_courses(courses)
            logger.info(f"[courses] updated: {c.get('name')} (id={course_id})")
            return ApiResponse.success(data=c, message="课程已更新")
    raise HTTPException(404, f"课程不存在: {course_id}")


@router.delete("/{course_id}", summary="删除课程")
async def delete_course(course_id: str) -> ApiResponse[dict]:
    courses = _load_courses()
    for i, c in enumerate(courses):
        if c.get("id") == course_id:
            deleted = courses.pop(i)
            _save_courses(courses)
            logger.info(f"[courses] deleted: {deleted.get('name')} (id={course_id})")
            return ApiResponse.success(data={"deleted_id": course_id}, message="课程已删除")
    raise HTTPException(404, f"课程不存在: {course_id}")
