"""Kiểm thử chức năng bình luận (comments.py): lưu trữ, trả lời, thích, xóa, giới hạn tốc độ, kiểm tra đầu vào và API.

Chạy:  python -m unittest discover -s tests -v
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import comments as cm
from flask import Flask

A, B = "a" * 32, "b" * 32          # hai "trình duyệt" khác nhau
T0 = 1_700_000_000


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "sub" / "c.db"
        self.s = cm.CommentStore(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def post(self, body="Bài viết hay", token=A, aid=1, t=T0, **k):
        return self.s.add(aid, body, k.pop("name", "Minh"), token, now=t, **k)

    def test_add_and_list_newest_first(self):
        a = self.post("một", t=T0)
        b = self.post("hai", t=T0 + 10)
        res = self.s.list(1, A)
        self.assertEqual([c["body"] for c in res["items"]], ["hai", "một"])
        self.assertEqual(res["total"], 2)
        self.assertTrue(res["items"][0]["mine"])
        self.assertFalse(self.s.list(1, B)["items"][0]["mine"])
        self.assertEqual(a["name"], "Minh")
        self.assertEqual(b["likes"], 0)

    def test_comments_are_per_article(self):
        self.post("bài 1", aid=1)
        self.post("bài 2", aid=2, t=T0 + 10)
        self.assertEqual([c["body"] for c in self.s.list(2, A)["items"]], ["bài 2"])
        self.assertEqual(self.s.count(1), 1)
        self.assertEqual(self.s.count(3), 0)

    def test_reader_hash_is_not_exposed(self):
        c = self.post()
        self.assertNotIn("uid", c)
        self.assertNotIn(A, repr(self.s.list(1, A)))

    def test_reply_nests_and_flattens_to_one_level(self):
        top = self.post("gốc")
        r1 = self.post("trả lời 1", token=B, parent=top["id"], t=T0 + 10)
        r2 = self.post("trả lời của trả lời", token=A, parent=r1["id"], t=T0 + 20)
        self.assertEqual(r1["parent"], top["id"])
        self.assertEqual(r2["parent"], top["id"])                           # không có cấp thứ ba
        res = self.s.list(1, A)
        self.assertEqual(len(res["items"]), 1)
        self.assertEqual([r["body"] for r in res["items"][0]["replies"]], ["trả lời 1", "trả lời của trả lời"])   # cũ trước, mới sau
        self.assertEqual(res["total"], 3)

    def test_reply_to_missing_or_other_article(self):
        top = self.post("gốc", aid=1)
        with self.assertRaises(cm.CommentError) as e:
            self.post("trả lời sai bài", aid=2, parent=top["id"], t=T0 + 10)   # bình luận gốc thuộc bài khác
        self.assertEqual(e.exception.status, 404)
        with self.assertRaises(cm.CommentError) as e:
            self.post("trả lời bình luận không có", parent=9999, t=T0 + 20)
        self.assertEqual(e.exception.status, 404)
        self.assertEqual(self.s.count(1), 1)                                  # hai lần lỗi không để lại gì

    def test_like_toggle_and_liked_flag(self):
        c = self.post()
        self.assertEqual(self.s.like(c["id"], B), {"likes": 1, "liked": True})
        self.assertEqual(self.s.like(c["id"], A), {"likes": 2, "liked": True})
        self.assertTrue(self.s.list(1, B)["items"][0]["liked"])
        self.assertEqual(self.s.list(1, B)["items"][0]["likes"], 2)
        self.assertEqual(self.s.like(c["id"], B), {"likes": 1, "liked": False})      # bấm lần nữa = bỏ thích
        self.assertFalse(self.s.list(1, B)["items"][0]["liked"])
        with self.assertRaises(cm.CommentError):
            self.s.like(424242, A)

    def test_sort_by_likes_then_newest(self):
        a = self.post("cũ nhiều thích", t=T0)
        b = self.post("mới ít thích", t=T0 + 10)
        self.s.like(a["id"], A)
        self.s.like(a["id"], B)
        self.s.like(b["id"], A)
        self.assertEqual([c["body"] for c in self.s.list(1, A, sort="thich")["items"]], ["cũ nhiều thích", "mới ít thích"])
        self.assertEqual([c["body"] for c in self.s.list(1, A, sort="moi")["items"]], ["mới ít thích", "cũ nhiều thích"])

    def test_delete_only_by_owner_and_cascades(self):
        top = self.post("gốc", token=A)
        rep = self.post("trả lời", token=B, parent=top["id"], t=T0 + 10)
        self.s.like(top["id"], B)
        with self.assertRaises(cm.CommentError) as e:
            self.s.delete(top["id"], B)                                       # B không phải chủ bình luận gốc
        self.assertEqual(e.exception.status, 403)
        out = self.s.delete(top["id"], A)
        self.assertEqual(out, {"removed": 2, "total": 0})                   # trả lời bị xóa theo
        self.assertEqual(self.s.list(1, A)["items"], [])
        self.assertIsNone(self.s.get(rep["id"], B))
        self.assertEqual(self.s.count(1), 0)
        with self.assertRaises(cm.CommentError) as e:
            self.s.delete(top["id"], A)
        self.assertEqual(e.exception.status, 404)

    def test_delete_own_reply_keeps_parent(self):
        top = self.post("gốc", token=A)
        rep = self.post("trả lời", token=B, parent=top["id"], t=T0 + 10)
        self.assertEqual(self.s.delete(rep["id"], B), {"removed": 1, "total": 1})
        self.assertEqual(self.s.list(1, A)["items"][0]["replies"], [])

    def test_pagination(self):
        for i in range(25):
            self.post(f"bình luận {i:02d}", t=T0 + i * 10, token=("t%02d" % i) * 8)
        p1 = self.s.list(1, A, limit=10)
        p3 = self.s.list(1, A, offset=20, limit=10)
        self.assertEqual(len(p1["items"]), 10)
        self.assertTrue(p1["more"])
        self.assertEqual(p1["items"][0]["body"], "bình luận 24")
        self.assertEqual(len(p3["items"]), 5)
        self.assertFalse(p3["more"])
        self.assertEqual(p1["total"], 25)

    def test_validation(self):
        bad = [("", "quá ngắn"), (" \n ", "quá ngắn"), ("a", "quá ngắn"), ("x" * (cm.MAX_BODY + 1), "tối đa")]
        for i, (body, word) in enumerate(bad):
            with self.assertRaises(cm.CommentError, msg=body[:10]) as e:
                self.post(body, t=T0 + i * 100)
            self.assertIn(word, str(e.exception))
        self.assertEqual(self.s.count(1), 0)
        self.assertEqual(len(self.post("x" * cm.MAX_BODY, t=T0 + 999)["body"]), cm.MAX_BODY)

    def test_token_required(self):
        for tok in (None, "", "ngắn", "có dấu và khoảng trắng " * 3, "a" * 200):
            with self.assertRaises(cm.CommentError, msg=str(tok)[:10]):
                self.s.add(1, "nội dung", "x", tok, now=T0)

    def test_clean_text(self):
        c = self.post("  xin   chào\r\n\r\n\r\n\r\nbạn​ đọc\x00  ", name="  ‮An \t  Nhiên " + "x" * 50)
        self.assertEqual(c["body"], "xin chào\n\nbạn đọc")
        self.assertEqual(c["name"], ("An Nhiên " + "x" * 50)[:cm.MAX_NAME].strip())
        self.assertEqual(self.post("nội dung khác", name="   ", t=T0 + 100)["name"], "Bạn đọc")

    def test_html_is_stored_verbatim(self):
        """Máy chủ không biến đổi HTML; việc thoát ký tự do trình duyệt làm (static/comments.js, kiểm bằng Playwright)."""
        payload = '<img src=x onerror="alert(1)"> & <script>1</script>'
        self.assertEqual(self.post(payload)["body"], payload)

    def test_rate_limit_gap_hour_and_duplicates(self):
        self.post("một", t=T0)
        with self.assertRaises(cm.CommentError) as e:
            self.post("hai", t=T0 + cm.MIN_GAP - 1)
        self.assertEqual(e.exception.status, 429)
        self.post("hai", t=T0 + cm.MIN_GAP)                                   # đủ giãn cách thì được
        with self.assertRaises(cm.CommentError) as e:
            self.post("hai", t=T0 + cm.MIN_GAP * 3)                           # gửi trùng nội dung
        self.assertEqual(e.exception.status, 409)
        self.post("hai", token=B, t=T0 + cm.MIN_GAP * 3)                      # người khác gửi cùng nội dung thì không sao
        t = T0 + 100
        n = 0
        with self.assertRaises(cm.CommentError) as e:
            for n in range(cm.MAX_PER_HOUR + 2):
                self.post(f"loạt {n}", t=t + n * (cm.MIN_GAP + 1))
        self.assertEqual(e.exception.status, 429)
        self.assertLessEqual(self.s.count(1), cm.MAX_PER_HOUR + 2)
        self.post("sau một giờ", t=T0 + 4 * 3600)                             # qua một giờ thì được gửi lại

    def test_ip_limit(self):
        for i in range(cm.MAX_PER_HOUR_IP):
            self.s.add(1, f"từ ip {i}", "x", ("k%03d" % i) * 6, ip="10.0.0.1", now=T0 + i)
        with self.assertRaises(cm.CommentError) as e:
            self.s.add(1, "vượt mức", "x", "z" * 32, ip="10.0.0.1", now=T0 + 100)
        self.assertEqual(e.exception.status, 429)
        self.s.add(1, "ip khác", "x", "z" * 32, ip="10.0.0.2", now=T0 + 100)

    def test_persistence_and_counts(self):
        self.post("còn mãi", aid=7)
        self.post("bài khác", aid=9, t=T0 + 10)
        again = cm.CommentStore(self.path)
        self.assertEqual(again.counts(), {7: 1, 9: 1})
        self.assertEqual(again.list(7, A)["items"][0]["body"], "còn mãi")
        self.assertTrue(again.list(7, A)["items"][0]["mine"])

    def test_file_deleted_while_running(self):
        """Xóa data/comments.db khi website đang chạy để làm sạch bình luận: không được lỗi, bộ đếm về 0, đăng tiếp được."""
        self.post("sắp bị xóa", aid=4)
        self.assertEqual(self.s.count(4), 1)
        self.path.unlink()
        self.assertEqual(self.s.count(4), 0)
        self.assertEqual(self.s.list(4, A)["items"], [])
        self.assertEqual(self.s.latest(5), [])
        self.post("sau khi làm sạch", aid=4, t=T0 + 100)
        self.assertEqual(self.s.count(4), 1)
        self.assertEqual(cm.CommentStore(self.path).count(4), 1)

    def test_latest(self):
        self.post("cũ", aid=1, t=T0)
        self.post("mới", aid=2, t=T0 + 50, token=B)
        self.assertEqual([x["body"] for x in self.s.latest(5)], ["mới", "cũ"])
        self.assertEqual(self.s.latest(1)[0]["aid"], 2)
        self.assertNotIn("uid", self.s.latest(1)[0])


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = cm.CommentStore(Path(self.tmp.name) / "c.db")
        app = Flask(__name__)
        app.register_blueprint(cm.make_blueprint(self.store, lambda aid: aid in (1, 2)))
        self.c = app.test_client()
        self.h = {"X-Reader-Id": A}
        down = Flask(__name__)
        down.register_blueprint(cm.make_blueprint(None, lambda aid: True))
        self.down = down.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def test_post_then_list(self):
        r = self.c.post("/api/comments", json={"aid": 1, "body": "Xin chào", "name": "Lan"}, headers=self.h)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json()["total"], 1)
        got = self.c.get("/api/comments?aid=1", headers=self.h).get_json()
        self.assertEqual(got["items"][0]["body"], "Xin chào")
        self.assertTrue(got["items"][0]["mine"])
        self.assertIn("now", got)
        other = self.c.get("/api/comments?aid=1", headers={"X-Reader-Id": B}).get_json()
        self.assertFalse(other["items"][0]["mine"])
        anon = self.c.get("/api/comments?aid=1").get_json()                    # xem không cần mã
        self.assertFalse(anon["items"][0]["mine"])

    def test_errors(self):
        post = lambda j, h=None: self.c.post("/api/comments", json=j, headers=self.h if h is None else h)
        self.assertEqual(post({"aid": 99, "body": "xin chào"}).status_code, 404)
        self.assertEqual(post({"aid": "1", "body": "xin chào"}).status_code, 404)
        self.assertEqual(post({"aid": True, "body": "xin chào"}).status_code, 404)
        self.assertEqual(post({"aid": 1, "body": "xin chào", "parent": "x"}).status_code, 400)
        self.assertEqual(post({"aid": 1, "body": "xin chào"}, h={}).status_code, 400)       # thiếu mã bạn đọc
        self.assertEqual(post({"aid": 1, "body": ""}).status_code, 400)
        self.assertEqual(self.c.post("/api/comments", data="không phải json", headers=self.h).status_code, 404)
        self.assertEqual(self.c.get("/api/comments?aid=abc").status_code, 404)
        self.assertEqual(self.c.get("/api/comments").status_code, 404)
        msg = post({"aid": 1, "body": ""}).get_json()["error"]
        self.assertIn("quá ngắn", msg)

    def test_like_and_delete(self):
        cid = self.c.post("/api/comments", json={"aid": 1, "body": "để thích"}, headers=self.h).get_json()["comment"]["id"]
        hb = {"X-Reader-Id": B}
        self.assertEqual(self.c.post(f"/api/comments/{cid}/like", headers=hb).get_json(), {"likes": 1, "liked": True})
        self.assertEqual(self.c.post(f"/api/comments/{cid}/delete", headers=hb).status_code, 403)
        self.assertEqual(self.c.post(f"/api/comments/{cid}/like", headers={}).status_code, 400)
        self.assertEqual(self.c.post(f"/api/comments/{cid}/delete", headers=self.h).get_json(), {"removed": 1, "total": 0})
        self.assertEqual(self.c.post(f"/api/comments/{cid}/like", headers=hb).status_code, 404)

    def test_html_roundtrip_is_json_text(self):
        payload = "<script>alert(1)</script>"
        self.c.post("/api/comments", json={"aid": 1, "body": payload, "name": "<b>x</b>"}, headers=self.h)
        item = self.c.get("/api/comments?aid=1").get_json()["items"][0]
        self.assertEqual((item["body"], item["name"]), (payload, "<b>x</b>"))
        self.assertTrue(self.c.get("/api/comments?aid=1").headers["Content-Type"].startswith("application/json"))
        self.assertEqual(self.c.get("/api/comments?aid=1").headers["Cache-Control"], "no-store")

    def test_sort_and_offset_parameters(self):
        for i in range(12):
            self.store.add(1, f"nội dung số {i:02d}", "x", ("r%02d" % i) * 8, now=T0 + i * 10)
        a = self.c.get("/api/comments?aid=1&sort=thich&offset=0").get_json()
        b = self.c.get("/api/comments?aid=1&offset=10&sort=nonsense").get_json()
        self.assertEqual((len(a["items"]), a["more"]), (10, True))
        self.assertEqual((len(b["items"]), b["more"]), (2, False))
        self.assertEqual(self.c.get("/api/comments?aid=1&offset=-5").status_code, 200)

    def test_unavailable_store(self):
        self.assertEqual(self.down.get("/api/comments?aid=1").status_code, 503)
        self.assertEqual(self.down.post("/api/comments", json={"aid": 1, "body": "xin chào"}, headers=self.h).status_code, 503)
        self.assertIn("comments.db", self.down.get("/api/comments?aid=1").get_json()["error"])


if __name__ == "__main__":
    unittest.main()
