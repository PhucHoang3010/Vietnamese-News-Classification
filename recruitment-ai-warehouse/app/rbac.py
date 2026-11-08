"""Phân quyền theo vai trò (RBAC) và che giấu dữ liệu nhạy cảm."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_access_token

ROLE_LABELS = {"admin": "Quản trị viên", "hr": "Nhân sự (HR)", "hiring_manager": "Quản lý tuyển dụng"}

PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "users:manage", "audit:read", "etl:run", "candidates:read_all", "pii:read", "ai:run", "ai:review",
        "ai:read_all", "reports:generate", "reports:approve", "fairness:read", "feedback:write", "positions:manage",
    },
    "hr": {
        "etl:run", "candidates:read_all", "pii:read", "ai:run", "ai:review", "ai:read_all", "reports:generate",
        "reports:approve", "fairness:read", "feedback:write", "positions:manage",
    },
    "hiring_manager": {"candidates:read_department", "feedback:write"},
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def has_perm(user: User, permission: str) -> bool:
    return permission in PERMISSIONS.get(user.role, set())


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Phiên đăng nhập không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except Exception as exc:  # noqa: BLE001
        raise credentials_error from exc
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_error
    return user


def require(permission: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if not has_perm(user, permission):
            raise HTTPException(status_code=403, detail="Bạn không có quyền thực hiện chức năng này")
        return user

    return checker


# --------------------------------------------------------------------------- #
# Che giấu dữ liệu cá nhân (data masking)
# --------------------------------------------------------------------------- #
def mask_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    local, domain = email.split("@", 1)
    return f"{local[:1]}***@{domain}"


def mask_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    return phone[:2] + "*" * (len(phone) - 4) + phone[-2:]


def initials(name: str | None) -> str:
    if not name:
        return "?"
    return ".".join(w[0].upper() for w in name.split() if w) + "."
