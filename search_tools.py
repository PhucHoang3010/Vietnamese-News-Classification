"""Công cụ tìm kiếm nâng cao cho VnNews.

1) BoolIndex: tìm theo toán tử Boolean (AND, OR, NOT), cụm từ trong ngoặc kép, ký tự đại diện (bóng*), ngoặc đơn
   và tìm theo trường (tieude: sapo: noidung: chuyenmuc:). Không phân biệt dấu tiếng Việt ("gia vang" tìm được "giá vàng").
   Ví dụ:   giá vàng AND (tăng OR giảm) NOT bitcoin      tieude:"thuế" noidung:ngân hàng      chuyenmuc:"Thể thao" bóng*
   Toán tử viết HOA; hai từ đứng cạnh nhau hiểu là AND; dấu - trước từ là NOT.
2) Semantic: tìm theo nghĩa bằng LSA (TF-IDF -> TruncatedSVD), dùng kèm điểm TF-IDF thường (xem experiments/exp10_search.py).
"""
import re
import unicodedata

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

FIELD_ALIASES = {"tieude": "title", "title": "title", "sapo": "desc", "mota": "desc", "noidung": "content", "content": "content",
                 "chuyenmuc": "label", "muc": "label"}
_FIELDS_RE = "(?:" + "|".join(FIELD_ALIASES) + ")"
_TOK = re.compile(r'\s*(?:(?P<lp>\()|(?P<rp>\))|"(?P<phrase>[^"]*)"|(?P<field>' + _FIELDS_RE + r'):(?=[^\s])|(?P<word>[^\s()"]+))', re.I)


class QueryError(ValueError):
    """Truy vấn sai cú pháp (thông báo bằng tiếng Việt, hiển thị cho người dùng)."""


def fold(s, star=False):
    """Chữ thường, bỏ dấu tiếng Việt, bỏ dấu câu; giữ chữ số (và dấu * nếu star=True, dùng cho ký tự đại diện trong truy vấn)."""
    s = unicodedata.normalize("NFD", str(s).lower().replace("đ", "d"))
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"[^\w\s*]|_" if star else r"[^\w\s]|_", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def is_advanced(q):
    """Truy vấn có dùng cú pháp nâng cao không (toán tử HOA, ngoặc kép, ngoặc đơn, trường:, từ*, -từ)."""
    return bool(re.search(r'\b(AND|OR|NOT)\b|["()]|\*|(^|\s)-\S|\b(?i:' + _FIELDS_RE + r'):\S', q))


def tokenize(q):
    out, pos = [], 0
    while pos < len(q):
        m = _TOK.match(q, pos)
        if not m:
            break
        pos = m.end()
        if m.group("lp"):
            out.append(("(", None))
        elif m.group("rp"):
            out.append((")", None))
        elif m.group("phrase") is not None:
            if fold(m.group("phrase")):
                out.append(("PHRASE", m.group("phrase")))
        elif m.group("field"):
            out.append(("FIELD", FIELD_ALIASES[m.group("field").lower()]))
        else:
            w = m.group("word")
            if w not in ("AND", "OR", "NOT") and not fold(w.lstrip("-"), star=True).strip("*"):
                continue                                              # chỉ toàn dấu câu (vd. "-" đứng riêng): bỏ qua
            if w in ("AND", "OR", "NOT"):
                out.append((w, None))
            elif w.startswith("-") and len(w) > 1:
                out.append(("NOT", None)); out.append(("WORD", w[1:]))
            else:
                out.append(("WORD", w))
    return out


def parse(q):
    """Phân tích cú pháp -> cây: ('and', [..]) | ('or', [..]) | ('not', x) | ('term', field|None, text, is_phrase)."""
    toks = tokenize(q); i = [0]

    def peek():
        return toks[i[0]][0] if i[0] < len(toks) else None

    def take():
        t = toks[i[0]]; i[0] += 1; return t

    def or_expr():
        parts = [and_expr()]
        while peek() == "OR":
            take(); parts.append(and_expr())
        return parts[0] if len(parts) == 1 else ("or", parts)

    def and_expr():
        parts = [not_expr()]
        while peek() not in (None, ")", "OR"):
            if peek() == "AND":
                take()
            parts.append(not_expr())
        return parts[0] if len(parts) == 1 else ("and", parts)

    def not_expr():
        if peek() == "NOT":
            take(); return ("not", not_expr())
        return atom(None)

    def with_field(e, field):
        """tieude:(a OR b) -> áp trường cho mọi từ bên trong chưa có trường."""
        if e[0] == "term":
            return ("term", e[1] or field, e[2], e[3])
        if e[0] == "not":
            return ("not", with_field(e[1], field))
        return (e[0], [with_field(x, field) for x in e[1]])

    def atom(field):
        t = peek()
        if t is None:
            raise QueryError("Truy vấn chưa đầy đủ (thiếu từ sau toán tử hoặc trường).")
        if t == "(":
            take(); e = or_expr()
            if peek() != ")":
                raise QueryError("Thiếu dấu ngoặc đóng “)”.")
            take(); return with_field(e, field) if field else e
        if t == "FIELD":
            return atom(take()[1])
        if t in ("WORD", "PHRASE"):
            _, txt = take(); return ("term", field, txt, t == "PHRASE")
        raise QueryError(f"Không hiểu vị trí của “{t}” trong truy vấn.")

    if not toks:
        raise QueryError("Hãy nhập từ khóa.")
    tree = or_expr()
    if i[0] != len(toks):
        raise QueryError("Dấu ngoặc đóng “)” thừa hoặc toán tử đặt sai chỗ.")
    return tree


def explain(tree):
    """Chuỗi mô tả truy vấn đã hiểu, để người dùng kiểm tra."""
    k = tree[0]
    if k == "term":
        _, f, t, ph = tree
        pre = {"title": "tiêu đề", "desc": "sapo", "content": "nội dung", "label": "chuyên mục"}.get(f)
        return (f"{pre}: " if pre else "") + (f"“{t}”" if ph else t)
    if k == "not":
        return "KHÔNG " + explain(tree[1])
    j = " VÀ " if k == "and" else " HOẶC "
    return "(" + j.join(explain(x) for x in tree[1]) + ")"


def positive_terms(tree, neg=False):
    """Các từ/cụm từ mang nghĩa 'có' (không nằm dưới NOT): dùng để xếp hạng và tô sáng."""
    k = tree[0]
    if k == "term":
        return [] if neg or tree[1] == "label" else [(tree[2], tree[3])]
    if k == "not":
        return positive_terms(tree[1], not neg)
    return [t for x in tree[1] for t in positive_terms(x, neg)]


class BoolIndex:
    """Chỉ mục ngược nhị phân theo từng trường (tiêu đề, sapo, nội dung) + chuyên mục."""
    FIELDS = ("title", "desc", "content")

    def __init__(self, docs):
        self.n = len(docs)
        self.text = {f: [" " + fold(d[f]) + " " for d in docs] for f in self.FIELDS}
        self.label = [fold(d["label"]) for d in docs]
        self.vocab, self.mat, self.terms = {}, {}, {}
        for f in self.FIELDS:
            cv = CountVectorizer(token_pattern=r"(?u)\b\w+\b", lowercase=False, binary=True, dtype=np.int8)
            self.mat[f] = cv.fit_transform(t.strip() for t in self.text[f]).tocsc()
            self.vocab[f] = cv.vocabulary_
            self.terms[f] = sorted(cv.vocabulary_)

    def _word(self, f, w):
        m = np.zeros(self.n, bool)
        if w.endswith("*") and len(w) > 2:                         # từ*: mọi từ bắt đầu bằng tiền tố
            p = w[:-1]
            for t in self.terms[f]:
                if t.startswith(p):
                    m[self.mat[f][:, self.vocab[f][t]].indices] = True
        else:
            j = self.vocab[f].get(w.strip("*"))
            if j is not None:
                m[self.mat[f][:, j].indices] = True
        return m

    def _term(self, f, text, phrase):
        q = fold(text, star=True)
        if not q:
            return np.zeros(self.n, bool)
        if f == "label":
            return np.fromiter((q == lb or (len(q) > 2 and q in lb) for lb in self.label), bool, self.n)
        fields = (f,) if f else self.FIELDS
        words = q.split()
        out = np.zeros(self.n, bool)
        for fl in fields:
            m = np.ones(self.n, bool)
            for w in words:
                m &= self._word(fl, w)
            if phrase and len(words) > 1 and "*" not in q:          # cụm từ: các từ phải đứng liền nhau
                key = " " + q + " "
                for i in np.flatnonzero(m):
                    m[i] = key in self.text[fl][i]
            out |= m
        return out

    def evaluate(self, tree):
        k = tree[0]
        if k == "term":
            return self._term(tree[1], tree[2], tree[3])
        if k == "not":
            return ~self.evaluate(tree[1])
        ms = [self.evaluate(x) for x in tree[1]]
        return np.logical_and.reduce(ms) if k == "and" else np.logical_or.reduce(ms)

    def search(self, q):
        tree = parse(q)
        return self.evaluate(tree), tree


class Semantic:
    """Tìm theo nghĩa: trộn điểm khớp từ khóa (TF-IDF) với độ gần nghĩa (LSA = TF-IDF -> TruncatedSVD).
    Thí nghiệm exp10: trộn 70% TF-IDF + 30% LSA (300 chiều) cho kết quả cùng chủ đề hơn TF-IDF thuần (P@10 +3,7 điểm),
    nhưng KHÔNG giúp tìm đúng một bài cụ thể (R@1 gần như không đổi)."""

    def __init__(self, texts, n_components=300, max_features=30000, alpha=0.7, seed=42):
        self.alpha = alpha
        self.tfidf = TfidfVectorizer(sublinear_tf=True, min_df=2, max_df=0.5, max_features=max_features)
        self.X = self.tfidf.fit_transform(texts)
        self.svd = TruncatedSVD(n_components=min(n_components, self.X.shape[1] - 1), random_state=seed, n_iter=5)
        self.Z = normalize(self.svd.fit_transform(self.X)).astype(np.float32)

    def scores(self, text, alpha=None):
        a = self.alpha if alpha is None else alpha
        q = self.tfidf.transform([text])
        kw = (self.X @ q.T).toarray().ravel()
        v = self.svd.transform(q); nv = np.linalg.norm(v)
        lsa = (self.Z @ (v[0] / nv).astype(np.float32)) if nv else np.zeros(self.Z.shape[0], np.float32)
        return a * kw + (1 - a) * lsa
