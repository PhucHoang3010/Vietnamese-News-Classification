"""Client gọi FastAPI backend từ giao diện Streamlit."""
from __future__ import annotations

import os

import httpx
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/") + "/api"
TIMEOUT = httpx.Timeout(120.0, connect=30.0)  # máy chủ miễn phí có thể "ngủ" và cần ~1 phút để thức dậy


class ApiError(Exception):
    def __init__(self, status: int, detail):
        self.status = status
        self.detail = detail
        message = detail.get("message") if isinstance(detail, dict) else detail
        super().__init__(str(message))


def _headers() -> dict:
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def request(method: str, path: str, raw: bool = False, **kwargs):
    try:
        response = httpx.request(method, API_BASE + path, headers=_headers(), timeout=TIMEOUT, **kwargs)
    except httpx.HTTPError as exc:
        raise ApiError(0, f"Không kết nối được máy chủ API ({API_BASE}). Vui lòng thử lại sau ít phút.") from exc
    if response.status_code == 401 and st.session_state.get("token"):
        st.session_state.clear()
        raise ApiError(401, "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.")
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        if isinstance(detail, list):  # lỗi validate của FastAPI
            detail = "; ".join(f"{'.'.join(str(x) for x in d.get('loc', [])[1:])}: {d.get('msg')}" for d in detail)
        raise ApiError(response.status_code, detail)
    return response if raw else response.json()


def get(path: str, **kwargs):
    return request("GET", path, **kwargs)


def post(path: str, **kwargs):
    return request("POST", path, **kwargs)


def patch(path: str, **kwargs):
    return request("PATCH", path, **kwargs)


def login(username: str, password: str) -> dict:
    data = request("POST", "/auth/login", data={"username": username, "password": password})
    st.session_state["token"] = data["access_token"]
    st.session_state["user"] = data["user"]
    return data["user"]


@st.cache_data(ttl=300, show_spinner=False)
def _meta(token: str) -> dict:
    response = httpx.get(API_BASE + "/meta", headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def meta() -> dict:
    return _meta(st.session_state.get("token", ""))
