"""Đăng nhập, thông tin tài khoản, quản lý người dùng, nhật ký hệ thống."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog, Department, User
from app.rbac import PERMISSIONS, get_current_user, require
from app.schemas import PasswordChange, PasswordReset, Token, UserCreate, UserUpdate
from app.security import create_access_token, hash_password, verify_password
from app.serializers import iso, user_out
from app.services.audit import log_action
from app.utils import now_vn

router = APIRouter(tags=["Xác thực & người dùng"])


@router.post("/auth/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == form.username.strip().lower()))
    if user is None or not verify_password(form.password, user.hashed_password):
        log_action(db, None, "auth:login_failed", "user", None, username=form.username)
        db.commit()
        raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Tài khoản đã bị khoá")
    user.last_login_at = now_vn()
    log_action(db, user, "auth:login", "user", user.id)
    db.commit()
    return Token(access_token=create_access_token(user.id, user.role),
                 user={**user_out(user), "permissions": sorted(PERMISSIONS.get(user.role, set()))})


@router.get("/auth/me")
def me(user: User = Depends(get_current_user)):
    return {**user_out(user), "permissions": sorted(PERMISSIONS.get(user.role, set()))}


@router.post("/auth/change-password")
def change_password(body: PasswordChange, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(body.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không đúng")
    user.hashed_password = hash_password(body.new_password)
    log_action(db, user, "auth:change_password", "user", user.id)
    db.commit()
    return {"ok": True}


@router.get("/users")
def list_users(db: Session = Depends(get_db), _: User = Depends(require("users:manage"))):
    return [user_out(u) for u in db.scalars(select(User).order_by(User.role, User.username))]


@router.post("/users", status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db), admin: User = Depends(require("users:manage"))):
    username = body.username.strip().lower()
    if db.scalar(select(User).where(User.username == username)):
        raise HTTPException(status_code=409, detail="Tên đăng nhập đã tồn tại")
    if body.role == "hiring_manager" and not body.department_id:
        raise HTTPException(status_code=400, detail="Quản lý tuyển dụng phải thuộc một phòng ban")
    if body.department_id and db.get(Department, body.department_id) is None:
        raise HTTPException(status_code=400, detail="Phòng ban không tồn tại")
    user = User(username=username, full_name=body.full_name, email=body.email, role=body.role,
                department_id=body.department_id, hashed_password=hash_password(body.password))
    db.add(user)
    db.flush()
    log_action(db, admin, "user:create", "user", user.id, username=username, role=body.role)
    db.commit()
    db.refresh(user)
    return user_out(user)


@router.patch("/users/{user_id}")
def update_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db),
                admin: User = Depends(require("users:manage"))):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    changes = body.model_dump(exclude_unset=True)
    if user.id == admin.id and (changes.get("is_active") is False or changes.get("role", "admin") != "admin"):
        raise HTTPException(status_code=400, detail="Không thể tự khoá hoặc hạ quyền tài khoản của chính mình")
    for key, value in changes.items():
        setattr(user, key, value)
    if user.role == "hiring_manager" and not user.department_id:
        raise HTTPException(status_code=400, detail="Quản lý tuyển dụng phải thuộc một phòng ban")
    log_action(db, admin, "user:update", "user", user.id, **{k: str(v) for k, v in changes.items()})
    db.commit()
    db.refresh(user)
    return user_out(user)


@router.post("/users/{user_id}/reset-password")
def reset_password(user_id: int, body: PasswordReset, db: Session = Depends(get_db),
                   admin: User = Depends(require("users:manage"))):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    user.hashed_password = hash_password(body.new_password)
    log_action(db, admin, "user:reset_password", "user", user.id)
    db.commit()
    return {"ok": True}


@router.get("/audit-logs")
def audit_logs(limit: int = 200, db: Session = Depends(get_db), _: User = Depends(require("audit:read"))):
    rows = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(min(limit, 1000)))
    return [{"id": r.id, "created_at": iso(r.created_at), "user": r.user.username if r.user else None,
             "action": r.action, "entity_type": r.entity_type, "entity_id": r.entity_id, "detail": r.detail}
            for r in rows]
