"""Kiểm thử tự động cho các chức năng mới (không cần mô hình lớn):  python -m unittest discover -s tests -v"""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import conformal as cf
import search_tools as st


def synthetic(n, K=5, seed=0, noise=1.0):
    """Điểm kiểu SVM: đáp án đúng có điểm cao hơn trung bình nhưng bị nhiễu nên có bài nhầm."""
    rng = np.random.default_rng(seed)
    y = rng.integers(0, K, n)
    D = rng.normal(0, noise, (n, K)); D[np.arange(n), y] += 1.6
    return D, y


class ConformalTests(unittest.TestCase):
    def test_quantile_edge_cases(self):
        self.assertEqual(cf.conformal_quantile([0.1, 0.2, 0.3], 0.5), 0.2)          # k = ceil(4*0.5) = 2
        self.assertEqual(cf.conformal_quantile([0.1, 0.2, 0.3], 0.01), float("inf"))  # quá ít mẫu: lấy mọi chuyên mục
        self.assertEqual(cf.conformal_quantile([], 0.1), float("inf"))

    def test_top1_always_in_set(self):
        D, y = synthetic(2000, seed=1); thr = cf.calibrate(D, y)
        for a in cf.ALPHAS:
            for mond in (True, False):
                m = cf.predict_sets(D, thr[str(a)], mondrian=mond)
                self.assertTrue(m[np.arange(len(D)), D.argmax(1)].all())

    def test_marginal_and_class_conditional_coverage(self):
        Dc, yc = synthetic(6000, seed=2); Dt, yt = synthetic(6000, seed=3)
        thr = cf.calibrate(Dc, yc)
        for a in cf.ALPHAS:
            marg = cf.evaluate(cf.predict_sets(Dt, thr[str(a)], mondrian=False), yt)
            self.assertGreaterEqual(marg["coverage"], 1 - a - 0.015, f"độ phủ chung alpha={a}")
            mon = cf.evaluate(cf.predict_sets(Dt, thr[str(a)], mondrian=True), yt)
            self.assertGreaterEqual(mon["worst_class_coverage"], 1 - a - 0.04, f"độ phủ theo từng chuyên mục alpha={a}")

    def test_smaller_alpha_gives_larger_sets(self):
        Dc, yc = synthetic(4000, seed=4); Dt, yt = synthetic(2000, seed=5); thr = cf.calibrate(Dc, yc)
        sizes = [cf.evaluate(cf.predict_sets(Dt, thr[str(a)]), yt)["avg_size"] for a in cf.ALPHAS]      # alpha giảm dần: 0,1 -> 0,05 -> 0,01
        self.assertTrue(sizes[0] <= sizes[1] <= sizes[2])

    def test_evaluate_hand_made(self):
        mask = np.array([[1, 0, 0], [1, 1, 0], [0, 1, 1], [0, 0, 1]], bool); y = np.array([0, 1, 0, 2])
        r = cf.evaluate(mask, y)
        self.assertAlmostEqual(r["coverage"], 3 / 4); self.assertAlmostEqual(r["avg_size"], 6 / 4); self.assertAlmostEqual(r["singleton_share"], 2 / 4)
        self.assertAlmostEqual(r["singleton_acc"], 1.0)


DOCS = [
    {"title": "Giá vàng tăng mạnh", "desc": "Vàng trong nước tăng", "content": "Giá vàng SJC tăng hơn 500 nghìn đồng mỗi lượng. Bitcoin cũng tăng.", "label": "Kinh doanh"},
    {"title": "Bóng đá Việt Nam thắng", "desc": "Đội tuyển thắng 2-0", "content": "Trận đấu bóng đá hấp dẫn, cầu thủ ghi hai bàn thắng.", "label": "Thể thao"},
    {"title": "Giá xăng giảm", "desc": "Xăng giảm giá", "content": "Giá xăng giảm nhẹ trong kỳ điều hành. Giá vàng đi ngang.", "label": "Kinh doanh"},
    {"title": "Bóng chuyền nữ", "desc": "Tuyển bóng chuyền", "content": "Bóng chuyền nữ Việt Nam giành huy chương.", "label": "Thể thao"},
]


class SearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.idx = st.BoolIndex(DOCS)

    def hits(self, q):
        return set(np.flatnonzero(self.idx.search(q)[0]).tolist())

    def test_fold(self):
        self.assertEqual(st.fold("Đại học Bách Khoa!"), "dai hoc bach khoa")

    def test_and_or_not(self):
        self.assertEqual(self.hits("vàng"), {0, 2})
        self.assertEqual(self.hits("vàng AND bitcoin"), {0})
        self.assertEqual(self.hits("vàng NOT bitcoin"), {2})
        self.assertEqual(self.hits("vàng -bitcoin"), {2})
        self.assertEqual(self.hits("xăng OR chuyền"), {2, 3})
        self.assertEqual(self.hits("giá AND (xăng OR bitcoin)"), {0, 2})

    def test_accent_insensitive(self):
        self.assertEqual(self.hits("gia vang"), self.hits("giá vàng"))

    def test_phrase_and_order(self):
        self.assertEqual(self.hits('"giá vàng"'), {0, 2})
        self.assertEqual(self.hits('"vàng giá"'), set())

    def test_wildcard(self):
        self.assertEqual(self.hits("bóng*"), {1, 3})

    def test_fields(self):
        self.assertEqual(self.hits('tieude:"giá vàng"'), {0})
        self.assertEqual(self.hits("tieude:xăng"), {2})
        self.assertEqual(self.hits("sapo:tuyển"), {1, 3})
        self.assertEqual(self.hits('chuyenmuc:"Thể thao"'), {1, 3})
        self.assertEqual(self.hits('chuyenmuc:"the thao" AND chuyền'), {3})
        self.assertEqual(self.hits("tieude:(xăng OR chuyền)"), {2, 3})

    def test_not_only(self):
        self.assertEqual(self.hits("NOT bóng"), {0, 2})

    def test_syntax_errors(self):
        for bad in ("(vàng", "vàng AND", "vàng)", ""):
            with self.assertRaises(st.QueryError):
                st.parse(bad)

    def test_detects_advanced(self):
        for q in ("a AND b", '"cụm từ"', "bóng*", "tieude:thuế", "-bitcoin vàng", "(a b)"):
            self.assertTrue(st.is_advanced(q), q)
        for q in ("giá vàng", "tỷ số 2:1", "xe điện - ưu đãi", "and or not"):
            self.assertFalse(st.is_advanced(q), q)

    def test_positive_terms_skip_negated(self):
        t = st.parse("vàng NOT bitcoin")
        self.assertEqual([x for x, _ in st.positive_terms(t)], ["vàng"])


if __name__ == "__main__":
    unittest.main()
