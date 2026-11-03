"""Bình luận của bạn đọc dưới mỗi bài báo.

Lưu trong SQLite (data/comments.db, tệp này nằm trong .gitignore nên mỗi máy có bộ bình luận riêng).
Website không có tài khoản: mỗi trình duyệt tự sinh một mã ngẫu nhiên (localStorage) và gửi kèm mỗi yêu cầu trong tiêu đề X-Reader-Id.
Máy chủ chỉ giữ BẢN BĂM của mã này, dùng để biết "bình luận này của mình" và "mình đã thích chưa"; mã gốc không được lưu hay trả về.

Chức năng: đăng, trả lời (một cấp), thích, xóa bình luận của chính mình (xóa luôn các trả lời bên dưới),
sắp xếp mới nhất / nhiều lượt thích, phân trang.
Chống lạm dụng ở mức đơn giản: giới hạn độ dài, giới hạn tốc độ (theo trình duyệt và theo địa chỉ IP), không nhận bình luận trùng.
Nội dung được lưu nguyên văn; trình duyệt luôn hiển thị nó như chữ thường (static/comments.js thoát ký tự HTML), nên không chèn được mã.
Giới hạn: không có kiểm duyệt nội dung và không có quản trị viên; chủ website xóa bình luận bằng cách sửa tệp data/comments.db.
"""
import hashlib
import re
import sqlite3
import threading
import time
import unicodedata
from collections import defaultdict, deque
from contextlib import closing
from pathlib import Path

from flask import Blueprint, jsonify, request

MAX_NAME, MAX_BODY, MIN_BODY = 30, 1000, 2
PAGE = 10                  # số bình luận gốc mỗi lần tải
MIN_GAP = 5                # giây tối thiểu giữa hai bình luận của cùng một trình duyệt
MAX_PER_HOUR = 20          # bình luận tối đa mỗi giờ cho một trình duyệt
MAX_PER_HOUR_IP = 60       # ... và cho một địa chỉ IP
DUP_WINDOW = 300           # giây: cùng nội dung, cùng bài, cùng trình duyệt thì coi là gửi trùng
UNAVAILABLE = "Chưa ghi được bình luận trên máy này (không mở được tệp data/comments.db)."

_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f​-‏‪-‮⁠﻿]")   # ký tự điều khiển, ký tự vô hình, đảo chiều chữ
_TOKEN = re.compile(r"[A-Za-z0-9_-]{16,80}")

SCHEMA = """
CREATE TABLE IF NOT EXISTS comments(
  id     INTEGER PRIMARY KEY AUTOINCREMENT,
  aid    INTEGER NOT NULL,            -- số thứ tự bài báo
  parent INTEGER,                     -- NULL: bình luận gốc; ngược lại là id bình luận gốc (chỉ một cấp trả lời)
  name   TEXT NOT NULL,
  body   TEXT NOT NULL,
  uid    TEXT NOT NULL,               -- bản băm mã trình duyệt
  ts     INTEGER NOT NULL             -- giây (UNIX)
);
CREATE INDEX IF NOT EXISTS ix_comments_aid ON comments(aid, parent, ts);
CREATE INDEX IF NOT EXISTS ix_comments_parent ON comments(parent);
CREATE TABLE IF NOT EXISTS likes(
  cid INTEGER NOT NULL,
  uid TEXT NOT NULL,
  PRIMARY KEY(cid, uid)
);
"""


class CommentError(Exception):
    """Lỗi người dùng gây ra; thông báo bằng tiếng Việt, hiển thị thẳng cho họ. status là mã HTTP."""

    def __init__(self, msg, status=400):
        super().__init__(msg)
        self.status = status


def clean_name(s):
    s = unicodedata.normalize("NFC", _CTRL.sub("", str(s or "")))
    return re.sub(r"\s+", " ", s).strip()[:MAX_NAME] or "Bạn đọc"


def clean_body(s):
    s = unicodedata.normalize("NFC", _CTRL.sub("", str(s or ""))).replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r" ?\n ?", "\n", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def reader_hash(token, required=True):
    """Bản băm của mã trình duyệt. required=False: mã sai/thiếu thì trả None (khi chỉ xem)."""
    if not isinstance(token, str) or not _TOKEN.fullmatch(token):
        if required:
            raise CommentError("Trình duyệt chưa có mã bạn đọc (có thể đang chặn localStorage). Hãy bật lưu dữ liệu trang web rồi tải lại.", 400)
        return None
    return hashlib.sha256(("vnnews-comments:" + token).encode()).hexdigest()


class CommentStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._posts = defaultdict(deque)        # uid -> [(ts, aid, body)], dùng để giới hạn tốc độ và phát hiện trùng
        self._ips = defaultdict(deque)          # ip -> [ts]
        self._counts = {}                       # aid -> số bình luận (giữ trong bộ nhớ để thẻ bài hiện số rất nhanh)
        self._ensure()
        with closing(self._conn()) as c, c:
            c.executescript(SCHEMA)             # tệp có sẵn từ trước: chắc chắn đủ bảng
            self._counts.update((aid, n) for aid, n in c.execute("SELECT aid, COUNT(*) FROM comments GROUP BY aid"))

    def _ensure(self):
        """Tệp có thể bị xóa khi website đang chạy (để làm sạch bình luận): khi đó tạo lại bảng và xóa các bộ đếm trong bộ nhớ."""
        if self.path.exists():
            return
        with self._lock:
            if self.path.exists():
                return
            self._counts.clear(); self._posts.clear(); self._ips.clear()
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(self.path, timeout=10)) as c, c:
                c.executescript(SCHEMA)

    def _conn(self):
        self._ensure()
        c = sqlite3.connect(self.path, timeout=10)
        c.row_factory = sqlite3.Row
        return c

    # ------------------------------------------------------------------ đọc
    def count(self, aid):
        self._ensure()
        return self._counts.get(aid, 0)

    def counts(self):
        self._ensure()
        return dict(self._counts)

    @staticmethod
    def _public(r, uid):
        return {"id": r["id"], "aid": r["aid"], "parent": r["parent"], "name": r["name"], "body": r["body"], "ts": r["ts"],
                "likes": r["nl"], "liked": bool(r["liked"]), "mine": uid is not None and r["uid"] == uid, "replies": []}

    _SEL = ("SELECT c.id, c.aid, c.parent, c.name, c.body, c.ts, c.uid, "
            "(SELECT COUNT(*) FROM likes l WHERE l.cid = c.id) AS nl, "
            "EXISTS(SELECT 1 FROM likes m WHERE m.cid = c.id AND m.uid = ?) AS liked FROM comments c ")

    def list(self, aid, token=None, sort="moi", offset=0, limit=PAGE):
        """Bình luận gốc của một bài (kèm các trả lời). sort: 'moi' (mới nhất trước) hoặc 'thich' (nhiều lượt thích trước)."""
        uid = reader_hash(token, required=False)
        order = "nl DESC, c.ts DESC, c.id DESC" if sort == "thich" else "c.ts DESC, c.id DESC"
        with closing(self._conn()) as c:
            tops = c.execute(self._SEL + f"WHERE c.aid = ? AND c.parent IS NULL ORDER BY {order} LIMIT ? OFFSET ?",
                             (uid or "", aid, limit + 1, max(0, offset))).fetchall()
            more, tops = len(tops) > limit, tops[:limit]
            items = {r["id"]: self._public(r, uid) for r in tops}
            if items:
                marks = ",".join("?" * len(items))
                for r in c.execute(self._SEL + f"WHERE c.parent IN ({marks}) ORDER BY c.ts ASC, c.id ASC", (uid or "", *items)):
                    items[r["parent"]]["replies"].append(self._public(r, uid))
        return {"aid": aid, "total": self.count(aid), "items": [items[r["id"]] for r in tops], "more": more}

    def get(self, cid, token=None):
        uid = reader_hash(token, required=False)
        with closing(self._conn()) as c:
            r = c.execute(self._SEL + "WHERE c.id = ?", (uid or "", cid)).fetchone()
        return self._public(r, uid) if r else None

    def latest(self, n=5):
        """Các bình luận mới nhất trên toàn website (cho khối “Ý kiến bạn đọc”)."""
        with closing(self._conn()) as c:
            return [dict(r) for r in c.execute("SELECT id, aid, name, body, ts FROM comments ORDER BY ts DESC, id DESC LIMIT ?", (n,))]

    # ------------------------------------------------------------------ ghi
    def _throttle(self, uid, ip, now, aid, body):
        q = self._posts[uid]
        while q and now - q[0][0] > 3600:
            q.popleft()
        if q and now - q[-1][0] < MIN_GAP:
            raise CommentError("Bạn gửi hơi nhanh, hãy đợi vài giây rồi gửi tiếp.", 429)
        if len(q) >= MAX_PER_HOUR:
            raise CommentError("Bạn đã gửi khá nhiều bình luận trong một giờ qua, hãy quay lại sau.", 429)
        if any(a == aid and b == body and now - t < DUP_WINDOW for t, a, b in q):
            raise CommentError("Bạn vừa gửi đúng bình luận này rồi.", 409)
        if ip:
            qi = self._ips[ip]
            while qi and now - qi[0] > 3600:
                qi.popleft()
            if len(qi) >= MAX_PER_HOUR_IP:
                raise CommentError("Địa chỉ mạng của bạn đã gửi quá nhiều bình luận trong một giờ, hãy quay lại sau.", 429)
        if len(self._posts) > 5000:             # dọn bộ nhớ: bỏ những người đã im quá một giờ
            for k in [k for k, v in self._posts.items() if not v or now - v[-1][0] > 3600]:
                del self._posts[k]
            for k in [k for k, v in self._ips.items() if not v or now - v[-1] > 3600]:
                del self._ips[k]

    def add(self, aid, body, name=None, token=None, parent=None, ip="", now=None):
        """Đăng một bình luận (hoặc trả lời, nếu có parent). Trả về bình luận vừa tạo."""
        now = int(time.time() if now is None else now)
        uid = reader_hash(token)
        body, name = clean_body(body), clean_name(name)
        if len(body) < MIN_BODY:
            raise CommentError(f"Bình luận quá ngắn (ít nhất {MIN_BODY} ký tự).")
        if len(body) > MAX_BODY:
            raise CommentError(f"Bình luận dài tối đa {MAX_BODY} ký tự (hiện {len(body)}).")
        with self._lock:
            self._throttle(uid, ip, now, aid, body)
            with closing(self._conn()) as c, c:
                if parent is not None:
                    p = c.execute("SELECT id, aid, parent FROM comments WHERE id = ?", (parent,)).fetchone()
                    if not p or p["aid"] != aid:
                        raise CommentError("Bình luận bạn định trả lời không còn nữa.", 404)
                    parent = p["parent"] or p["id"]          # trả lời một trả lời -> gắn vào bình luận gốc (chỉ một cấp)
                cid = c.execute("INSERT INTO comments(aid, parent, name, body, uid, ts) VALUES (?,?,?,?,?,?)", (aid, parent, name, body, uid, now)).lastrowid
            self._counts[aid] = self._counts.get(aid, 0) + 1
            self._posts[uid].append((now, aid, body))
            if ip:
                self._ips[ip].append(now)
        return self.get(cid, token)

    def like(self, cid, token):
        """Bấm thích / bỏ thích (mỗi trình duyệt thích một bình luận tối đa một lần)."""
        uid = reader_hash(token)
        with self._lock, closing(self._conn()) as c, c:
            if not c.execute("SELECT 1 FROM comments WHERE id = ?", (cid,)).fetchone():
                raise CommentError("Bình luận không còn nữa.", 404)
            had = c.execute("SELECT 1 FROM likes WHERE cid = ? AND uid = ?", (cid, uid)).fetchone() is not None
            if had:
                c.execute("DELETE FROM likes WHERE cid = ? AND uid = ?", (cid, uid))
            else:
                c.execute("INSERT INTO likes(cid, uid) VALUES (?, ?)", (cid, uid))
            n = c.execute("SELECT COUNT(*) FROM likes WHERE cid = ?", (cid,)).fetchone()[0]
        return {"likes": n, "liked": not had}

    def delete(self, cid, token):
        """Xóa bình luận của chính mình; bình luận gốc bị xóa thì các trả lời bên dưới cũng bị xóa."""
        uid = reader_hash(token)
        with self._lock, closing(self._conn()) as c, c:
            r = c.execute("SELECT id, aid, uid FROM comments WHERE id = ?", (cid,)).fetchone()
            if not r:
                raise CommentError("Bình luận không còn nữa.", 404)
            if r["uid"] != uid:
                raise CommentError("Bạn chỉ xóa được bình luận do chính mình viết (trên trình duyệt này).", 403)
            ids = [cid] + [x[0] for x in c.execute("SELECT id FROM comments WHERE parent = ?", (cid,))]
            marks = ",".join("?" * len(ids))
            c.execute(f"DELETE FROM likes WHERE cid IN ({marks})", ids)
            c.execute(f"DELETE FROM comments WHERE id IN ({marks})", ids)
            left = self._counts.get(r["aid"], 0) - len(ids)
            if left > 0:
                self._counts[r["aid"]] = left
            else:
                self._counts.pop(r["aid"], None)
        return {"removed": len(ids), "total": self.count(r["aid"])}


def make_blueprint(store, valid_aid):
    """Các đường dẫn /api/comments. store có thể là None (không mở được tệp): khi đó mọi yêu cầu trả 503 kèm lời giải thích."""
    bp = Blueprint("comments", __name__)
    reader = lambda: request.headers.get("X-Reader-Id", "")

    def guard(fn):
        def run(*a, **k):
            if store is None:
                return jsonify(error=UNAVAILABLE), 503
            try:
                return fn(*a, **k)
            except CommentError as e:
                return jsonify(error=str(e)), e.status
            except sqlite3.Error:
                return jsonify(error=UNAVAILABLE), 503
        run.__name__ = fn.__name__
        return run

    def body_json():
        d = request.get_json(silent=True)
        return d if isinstance(d, dict) else {}

    def as_int(v):
        return v if isinstance(v, int) and not isinstance(v, bool) else None

    @bp.get("/api/comments")
    @guard
    def api_list():
        aid = request.args.get("aid", type=int)
        if aid is None or not valid_aid(aid):
            return jsonify(error="Bài viết không tồn tại."), 404
        sort = "thich" if request.args.get("sort") == "thich" else "moi"
        res = store.list(aid, reader(), sort, request.args.get("offset", 0, type=int) or 0)
        res["now"] = int(time.time())
        resp = jsonify(res)
        resp.headers["Cache-Control"] = "no-store"
        return resp

    @bp.post("/api/comments")
    @guard
    def api_add():
        d = body_json()
        aid, parent = as_int(d.get("aid")), d.get("parent")
        if aid is None or not valid_aid(aid):
            return jsonify(error="Bài viết không tồn tại."), 404
        if parent is not None and as_int(parent) is None:
            return jsonify(error="Bình luận cần trả lời không hợp lệ."), 400
        c = store.add(aid, d.get("body"), d.get("name"), reader(), parent, request.remote_addr or "")
        return jsonify(comment=c, total=store.count(aid), now=int(time.time())), 201

    @bp.post("/api/comments/<int:cid>/like")
    @guard
    def api_like(cid):
        return jsonify(store.like(cid, reader()))

    @bp.post("/api/comments/<int:cid>/delete")
    @guard
    def api_delete(cid):
        return jsonify(store.delete(cid, reader()))

    return bp
