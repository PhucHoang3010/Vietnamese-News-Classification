"""Schema Pydantic cho request/response của API."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=60, pattern=r"^[a-zA-Z0-9._-]+$")
    full_name: str = Field(min_length=2, max_length=120)
    email: str | None = None
    role: str = Field(pattern=r"^(admin|hr|hiring_manager)$")
    department_id: int | None = None
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    role: str | None = Field(default=None, pattern=r"^(admin|hr|hiring_manager)$")
    department_id: int | None = None
    is_active: bool | None = None


class PasswordReset(BaseModel):
    new_password: str = Field(min_length=8)


class StageDecision(BaseModel):
    decision: str = Field(pattern=r"^(pass|fail|withdraw|no_show)$")
    score: float | None = Field(default=None, ge=1, le=5)
    feedback: str | None = Field(default=None, max_length=2000)
    reason: str | None = Field(default=None, max_length=500)
    interviewer: str | None = None
    force: bool = False  # vẫn lưu dù nhận xét bị gắn cờ thiên vị


class InsightReview(BaseModel):
    action: str = Field(pattern=r"^(approve|reject|reopen)$")
    note: str | None = None
    edited_content: dict | None = None


class WeeklyReportRequest(BaseModel):
    week_start: date


class RejectionInsightRequest(BaseModel):
    position_id: int | None = None
    department_id: int | None = None
