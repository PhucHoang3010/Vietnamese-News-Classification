"""Website tin tức VnNews — AI tự động phân loại chủ đề.   python app.py   →  http://127.0.0.1:5000"""
import csv, ipaddress, json, math, random, re, socket, unicodedata
import time
_T0 = time.time()
print("VnNews đang khởi động… Lần đầu (nhất là trên Windows) có thể mất 1–3 phút vì đang nạp thư viện. Vui lòng KHÔNG bấm Ctrl+C.", flush=True)
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import joblib
import numpy as np
import pandas as pd
from flask import Flask, abort, jsonify, redirect, render_template, request, url_for
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, confusion_matrix, f1_score

ROOT = Path(__file__).resolve().parent
PER_PAGE = 12

# ---------------------------------------------------------------- mô hình
model = joblib.load(ROOT / "model.joblib")
print(f"  ✓ đã nạp mô hình ({time.time() - _T0:.0f}s)", flush=True)
VEC, CLF = model.named_steps["tfidf"], model.named_steps["clf"]
FEATURES = np.array(VEC.get_feature_names_out())
CLASSES = list(model.classes_)
TEMP = 4.3          # hệ số nhiệt độ của softmax(TEMP × điểm SVM), chọn trên tập kiểm định (experiments/exp5_calibration.py): sai lệch hiệu chỉnh ECE trên tập kiểm thử giảm từ 7,6% xuống 3,2%

TOPICS = {  # tên: (slug, icon, màu)
    "Thời sự": ("thoi-su", "📰", "#111111"), "Thế giới": ("the-gioi", "🌍", "#111111"),
    "Kinh doanh": ("kinh-doanh", "💼", "#111111"), "Pháp luật": ("phap-luat", "⚖️", "#111111"),
    "Giáo dục": ("giao-duc", "🎓", "#111111"), "Sức khỏe": ("suc-khoe", "🩺", "#111111"),
    "Khoa học": ("khoa-hoc", "🔬", "#111111"), "Đời sống": ("doi-song", "🏡", "#111111"),
    "Giải trí": ("giai-tri", "🎬", "#111111"), "Thể thao": ("the-thao", "⚽", "#111111"), "Xe": ("xe", "🚗", "#111111"),
}
SLUG = {v[0]: k for k, v in TOPICS.items()}
SAMPLES = {
    "Giáo dục": "Bộ Giáo dục và Đào tạo công bố phương án tuyển sinh đại học năm nay. Thí sinh lớp 12 cần lưu ý thời gian đăng ký nguyện vọng, điểm chuẩn các trường và quy chế xét tuyển. Nhiều trường đại học cho biết sẽ tăng chỉ tiêu và mở thêm ngành mới.",
    "Giải trí": "Bộ phim mới của đạo diễn nổi tiếng ra rạp cuối tuần, thu hút đông đảo khán giả. Nam diễn viên chính gây ấn tượng mạnh với vai diễn đầy cảm xúc, trong khi ca sĩ trẻ cũng ra mắt MV mới đạt triệu lượt xem.",
    "Khoa học": "Apple vừa giới thiệu mẫu iPhone mới với chip xử lý nhanh hơn, camera cải tiến và nhiều tính năng trí tuệ nhân tạo. Người dùng smartphone có thể cập nhật hệ điều hành mới để trải nghiệm ứng dụng và công nghệ chuyển đổi số.",
    "Kinh doanh": "Ngân hàng Nhà nước điều chỉnh lãi suất điều hành, doanh nghiệp kỳ vọng chi phí vốn giảm. Thị trường chứng khoán tăng điểm, cổ phiếu ngân hàng dẫn dắt, nhà đầu tư quan tâm đến lợi nhuận quý và chính sách thuế.",
    "Pháp luật": "Tòa án nhân dân mở phiên xét xử bị cáo về tội lừa đảo chiếm đoạt tài sản. Cơ quan điều tra cho biết bị can đã bị khởi tố, viện kiểm sát đề nghị mức án phù hợp với hành vi vi phạm pháp luật.",
    "Sức khỏe": "Các bác sĩ khuyến cáo người dân tiêm vắc xin phòng bệnh và đi khám sức khỏe định kỳ. Bệnh viện tiếp nhận nhiều bệnh nhân mắc bệnh về hô hấp, điều trị ung thư cần phát hiện sớm để tăng hiệu quả.",
    "Thế giới": "Tổng thống Mỹ gặp lãnh đạo các nước châu Âu bàn về xung đột tại Ukraine và quan hệ với Trung Quốc. Liên Hợp Quốc kêu gọi các bên đối thoại, trong khi nhiều quốc gia công bố biện pháp trừng phạt mới.",
    "Thể thao": "Đội tuyển Việt Nam giành chiến thắng 2-0 trong trận chung kết, tiền đạo ghi hai bàn thắng đẹp mắt. Huấn luyện viên khen ngợi tinh thần thi đấu của các cầu thủ, bảng xếp hạng được cải thiện đáng kể.",
    "Thời sự": "Kỳ họp Quốc hội thảo luận dự thảo luật, đại biểu Quốc hội chất vấn các bộ trưởng. Chính phủ báo cáo công tác điều hành, Ủy ban Thường vụ Quốc hội cho ý kiến về nhân sự, Bộ Chính trị chỉ đạo các địa phương triển khai nghị quyết.",
    "Xe": "Hãng xe giới thiệu mẫu SUV điện mới với động cơ mạnh mẽ, quãng đường di chuyển hơn 500 km mỗi lần sạc. Giá xe dự kiến cạnh tranh, người mua ô tô quan tâm đến mức tiêu hao nhiên liệu và trang bị an toàn.",
    "Đời sống": "Nhiều gia đình chọn về quê đón Tết sớm, chợ hoa cuối năm đông đúc. Người dân chia sẻ cách chi tiêu tiết kiệm, nuôi dạy con cái và giữ gìn nếp sống hạnh phúc trong những ngày đầu xuân.",
}


def clean(t):
    t = unicodedata.normalize("NFC", str(t)).lower()
    t = re.sub(r"https?://\S+|\S+@\S+", " ", t); t = re.sub(r"\d+", " ", t)
    t = re.sub(r"[^\w\s]|_", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def analyze(text):
    x = clean(text)
    if len(x.split()) < 8:
        return None
    vec = VEC.transform([x]); s = CLF.decision_function(vec)[0]
    p = np.exp((s - s.max()) * TEMP); p /= p.sum(); order = np.argsort(-p)
    top = [{"label": CLASSES[i], "pct": round(float(p[i]) * 100, 1), "icon": TOPICS[CLASSES[i]][1], "color": TOPICS[CLASSES[i]][2],
            "slug": TOPICS[CLASSES[i]][0]} for i in order[:5]]
    k = int(order[0]); contrib = vec.multiply(CLF.coef_[k]).tocsr()
    idx = contrib.indices[np.argsort(-contrib.data)][:8] if contrib.nnz else []
    kws = [{"word": FEATURES[i], "weight": round(float(contrib[0, i]), 3)} for i in idx if contrib[0, i] > 0]
    gap = float(p[order[0]] - p[order[1]])
    return {"label": top[0]["label"], "icon": top[0]["icon"], "color": top[0]["color"], "slug": top[0]["slug"], "pct": top[0]["pct"],
            "confidence": "cao" if gap > 0.5 else "trung bình" if gap > 0.2 else "thấp", "top": top, "keywords": kws, "words": len(x.split())}


# ---------------------------------------------------------------- dữ liệu bài báo
if not (ROOT / "data/predictions.json").exists():
    import build_cache; build_cache.build()
PRED = json.loads((ROOT / "data/predictions.json").read_text(encoding="utf-8"))
DF = pd.read_csv(ROOT / "data/news_dataset.csv", usecols=["id", "title", "description", "content", "ground_truth"]).fillna("")
DF["id"] = DF.id.astype(int)
ART = {}
for r in DF.itertuples():
    pr = PRED[str(r.id)]
    desc = r.description.strip() or r.content[:200]
    ART[r.id] = {"id": r.id, "title": r.title.strip(), "desc": desc, "content": r.content, "truth": r.ground_truth, "label": pr["label"],
                 "pct": pr["pct"], "gap": pr["gap"], "test": pr["test"], "split": pr["split"], "slug": TOPICS[pr["label"]][0], "icon": TOPICS[pr["label"]][1],
                 "color": TOPICS[pr["label"]][2], "img": f"/img/{r.id}.svg", "minutes": max(1, round(len(r.content.split()) / 200))}
ORDER = list(ART)
random.Random(7).shuffle(ORDER)                       # thứ tự cố định nhưng trộn đều các chủ đề
BY_TOPIC = {t: [i for i in ORDER if ART[i]["label"] == t] for t in TOPICS}
# bài "nổi bật": độ tin cậy cao + mô tả đủ dài
for t in BY_TOPIC:
    BY_TOPIC[t].sort(key=lambda i: -(ART[i]["gap"] + (0.3 if len(ART[i]["desc"]) > 90 else 0)) )

# chỉ mục tìm kiếm / bài liên quan (tiêu đề + mô tả, nhẹ và nhanh)
IDS = list(ART)
IDX = {i: n for n, i in enumerate(IDS)}
SV = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1, max_df=0.5)
SX = SV.fit_transform([clean(ART[i]["title"] + " " + ART[i]["title"] + " " + ART[i]["desc"]) for i in IDS])
print(f"  ✓ đã dựng chỉ mục tìm kiếm ({time.time() - _T0:.0f}s)", flush=True)

# từ khóa đặc trưng từng chủ đề
KEYWORDS = {c: [FEATURES[j] for j in np.argsort(CLF.coef_[k])[-14:][::-1]] for k, c in enumerate(CLASSES)}

# thống kê trên tập kiểm thử
_t = [a for a in ART.values() if a["test"]]
_y, _p = [a["truth"] for a in _t], [a["label"] for a in _t]
REPORT = classification_report(_y, _p, output_dict=True, zero_division=0)
CM = confusion_matrix(_y, _p, labels=CLASSES)
STATS = {"n": len(ART), "n_test": len(_t), "acc": float(np.mean(np.array(_y) == np.array(_p))), "f1": float(f1_score(_y, _p, average="macro")),
         "counts": Counter(a["label"] for a in ART.values())}
STATS["n_err"] = int(np.sum(np.array(_y) != np.array(_p)))


def _cal(sel):
    return {"n": len(sel), "acc": round(100 * float(np.mean([a["label"] == a["truth"] for a in sel])), 1) if sel else 0.0}


# "mức nghiêng" của AI đáng tin đến đâu (đo trên tập kiểm thử): dùng để giải thích phần trăm hiển thị
STATS["cal_hi"] = _cal([a for a in _t if a["pct"] >= 95])
STATS["cal_lo"] = _cal([a for a in _t if a["pct"] < 50])
try:
    BENCH = list(csv.DictReader(open(ROOT / "outputs/so_sanh_mo_hinh.csv", encoding="utf-8")))
except Exception:
    BENCH = []

app = Flask(__name__)


@app.template_filter("vn")
def _vn(x):
    """Số có dấu chấm ngăn cách hàng nghìn kiểu Việt Nam: 5500 -> 5.500."""
    return f"{int(x):,}".replace(",", ".")
app.json.ensure_ascii = False
IMG_DIR = ROOT / "static" / "img"
NAV = [{"name": k, "slug": v[0], "icon": v[1], "color": v[2]} for k, v in TOPICS.items()]


# ---------------------------------------------------------------- ảnh minh họa (SVG đen-trắng, tạo theo chủ đề + id bài)
def _motif(label, r):
    """Hình minh họa đường nét cho từng chuyên mục, vẽ quanh tâm (320,200)."""
    K = 'stroke="#111" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"'
    if label == "Thể thao":
        pts = " ".join(f"{320 + 34 * math.cos(math.radians(a)):.1f},{200 + 34 * math.sin(math.radians(a)):.1f}" for a in range(-90, 270, 72))
        spokes = "".join(f'<line x1="{320 + 34 * math.cos(math.radians(a)):.1f}" y1="{200 + 34 * math.sin(math.radians(a)):.1f}" x2="{320 + 98 * math.cos(math.radians(a)):.1f}" y2="{200 + 98 * math.sin(math.radians(a)):.1f}" {K}/>' for a in range(-90, 270, 72))
        return f'<circle cx="320" cy="200" r="100" fill="#fff" {K}/><polygon points="{pts}" fill="#111"/>{spokes}<path d="M150 150 Q200 120 215 150 M135 200 Q185 175 205 205 M150 255 Q200 235 218 262" fill="none" {K}/>'
    if label == "Kinh doanh":
        bars = "".join(f'<rect x="{200 + i * 52}" y="{290 - h}" width="38" height="{h}" fill="{"#111" if i % 2 else "#fff"}" {K}/>' for i, h in enumerate([50, 85, 70, 125, 165]))
        return f'<line x1="180" y1="292" x2="470" y2="292" {K}/>{bars}<polyline points="205,205 258,170 310,185 362,130 420,95" fill="none" {K}/><polygon points="420,78 446,108 410,112" fill="#111"/>'
    if label == "Pháp luật":
        return f'<line x1="320" y1="95" x2="320" y2="300" {K}/><line x1="215" y1="125" x2="425" y2="125" {K}/><rect x="262" y="298" width="116" height="22" fill="#111"/><circle cx="320" cy="100" r="12" fill="#111"/><path d="M215 125 L180 210 H250 Z M425 125 L390 210 H460 Z" fill="#fff" {K}/><path d="M178 212 Q215 245 252 212 M388 212 Q425 245 462 212" fill="#111" {K}/>'
    if label == "Giáo dục":
        return f'<polygon points="320,120 460,175 320,230 180,175" fill="#111" {K}/><path d="M245 205 V265 Q320 305 395 265 V205" fill="#fff" {K}/><line x1="448" y1="182" x2="448" y2="262" {K}/><circle cx="448" cy="270" r="9" fill="#111"/>'
    if label == "Sức khỏe":
        return f'<circle cx="320" cy="170" r="92" fill="#fff" {K}/><rect x="300" y="115" width="40" height="110" fill="#111"/><rect x="265" y="150" width="110" height="40" fill="#111"/><polyline points="120,300 230,300 262,262 292,336 330,268 354,300 520,300" fill="none" {K}/>'
    if label == "Khoa học":
        el = "".join(f'<ellipse cx="320" cy="200" rx="130" ry="44" transform="rotate({a} 320 200)" fill="none" {K}/>' for a in (0, 60, 120))
        return f'{el}<circle cx="320" cy="200" r="22" fill="#111"/><circle cx="440" cy="200" r="10" fill="#111"/><circle cx="260" cy="304" r="10" fill="#111"/><circle cx="260" cy="96" r="10" fill="#111"/>'
    if label == "Đời sống":
        return f'<polygon points="320,100 460,215 180,215" fill="#111" {K}/><rect x="210" y="215" width="220" height="120" fill="#fff" {K}/><rect x="298" y="262" width="44" height="73" fill="#111"/><rect x="232" y="240" width="44" height="40" fill="#fff" {K}/><rect x="364" y="240" width="44" height="40" fill="#fff" {K}/><rect x="385" y="120" width="30" height="55" fill="#111"/>'
    if label == "Giải trí":
        stripes = "".join(f'<polygon points="{190 + i * 52},120 {222 + i * 52},120 {200 + i * 52},158 {168 + i * 52},158" fill="#111"/>' for i in range(5))
        return f'<rect x="185" y="165" width="270" height="150" fill="#fff" {K}/><g transform="rotate(-9 190 160)"><rect x="170" y="112" width="270" height="48" fill="#fff" {K}/>{stripes}</g><polygon points="290,205 290,275 355,240" fill="#111"/><polygon points="440,70 449,92 473,94 455,110 461,134 440,121 419,134 425,110 407,94 431,92" fill="#111"/>'
    if label == "Xe":
        return f'<path d="M185 255 Q185 220 220 218 L262 215 L290 168 H365 L400 215 L440 220 Q460 224 460 255 V275 H185 Z" fill="#fff" {K}/><polygon points="296,178 358,178 385,215 275,215" fill="#111"/><circle cx="262" cy="278" r="32" fill="#111" {K}/><circle cx="262" cy="278" r="12" fill="#fff"/><circle cx="385" cy="278" r="32" fill="#111" {K}/><circle cx="385" cy="278" r="12" fill="#fff"/><line x1="90" y1="205" x2="150" y2="205" {K}/><line x1="70" y1="235" x2="140" y2="235" {K}/>'
    if label == "Thế giới":
        mer = "".join(f'<ellipse cx="320" cy="200" rx="{rx}" ry="102" fill="none" {K}/>' for rx in (46, 82))
        lat = "".join(f'<line x1="{320 - w}" y1="{200 + y}" x2="{320 + w}" y2="{200 + y}" {K}/>' for y, w in ((-52, 88), (0, 102), (52, 88)))
        return f'<circle cx="320" cy="200" r="102" fill="#fff" {K}/>{mer}{lat}<path d="M285 150 Q310 130 335 150 Q340 175 315 185 Q290 175 285 150Z M345 225 Q372 215 382 245 Q365 268 345 255Z" fill="#111"/>'
    # Thời sự
    lines = "".join(f'<line x1="{x}" y1="{y}" x2="{x + 82}" y2="{y}" {K}/>' for x in (200, 330) for y in (190, 215, 240, 265, 290))
    return f'<rect x="170" y="85" width="300" height="240" fill="#fff" {K}/><rect x="200" y="108" width="240" height="46" fill="#111"/><rect x="200" y="166" width="108" height="8" fill="#111"/>{lines}'


def art_svg(label, seed):
    r = random.Random(seed)
    g1, g2 = r.choice([("#ececec", "#ffffff"), ("#dedede", "#f6f6f6"), ("#f2f2f2", "#d8d8d8"), ("#e6e6e6", "#fafafa")])
    kind = r.randrange(4)
    if kind == 0:
        pat = "".join(f'<circle cx="{x}" cy="{y}" r="{2.2 + (x + y) % 3}" fill="#111" opacity=".18"/>' for x in range(14, 640, 28) for y in range(14, 400, 28))
    elif kind == 1:
        pat = "".join(f'<line x1="{x}" y1="0" x2="{x - 200}" y2="400" stroke="#111" stroke-width="2" opacity=".12"/>' for x in range(0, 900, 26))
    elif kind == 2:
        pat = "".join(f'<line x1="{x}" y1="0" x2="{x}" y2="400" stroke="#111" opacity=".1"/>' for x in range(0, 640, 32)) + "".join(f'<line x1="0" y1="{y}" x2="640" y2="{y}" stroke="#111" opacity=".1"/>' for y in range(0, 400, 32))
    else:
        pat = "".join(f'<circle cx="{r.randint(0, 640)}" cy="{r.randint(0, 400)}" r="{r.randint(30, 120)}" fill="none" stroke="#111" stroke-width="2" opacity=".14"/>' for _ in range(9))
    dx, dy, rot, sc = r.randint(-26, 26), r.randint(-14, 14), r.randint(-6, 6), r.choice([0.92, 1.0, 1.08])
    blob = f'<circle cx="{r.randint(100, 540)}" cy="{r.randint(60, 340)}" r="{r.randint(110, 170)}" fill="#111" opacity=".07"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400" preserveAspectRatio="xMidYMid slice">'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{g1}"/><stop offset="1" stop-color="{g2}"/></linearGradient></defs>'
            f'<rect width="640" height="400" fill="url(#g)"/>{pat}{blob}'
            f'<g transform="translate({dx} {dy}) rotate({rot} 320 200) translate(320 200) scale({sc}) translate(-320 -200)">{_motif(label, r)}</g>'
            f'<rect x="1.5" y="1.5" width="637" height="397" fill="none" stroke="#111" stroke-width="3"/></svg>')


@app.get("/img/<int:aid>.svg")
def article_img(aid):
    a = ART.get(aid) or abort(404)
    resp = app.response_class(art_svg(a["label"], aid), mimetype="image/svg+xml")
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


def img_url(aid):
    for ext in ("jpg", "jpeg", "png", "webp"):      # nếu có ảnh thật static/img/<id>.jpg thì ưu tiên dùng
        if (IMG_DIR / f"{aid}.{ext}").exists():
            return f"/static/img/{aid}.{ext}"
    return f"/img/{aid}.svg"


for _a in ART.values():
    _a["img"] = img_url(_a["id"])


@app.context_processor
def inject():
    return {"NAV": NAV, "TOPICS": TOPICS, "STATS": STATS, "q": request.args.get("q", "")}


@app.template_filter("paras")
def paras(s):
    parts = [p.strip() for p in re.split(r"\n+", s) if p.strip()]
    if len(parts) > 1:
        return parts
    sents = [x for x in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ỹ])", s) if x.strip()]
    return [" ".join(sents[i:i + 3]) for i in range(0, len(sents), 3)]


def cards(ids): return [ART[i] for i in ids]


# ---------------------------------------------------------------- NLP khác ngoài phân loại: tóm tắt, từ khóa, gom cụm, gợi ý
from functools import lru_cache
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import normalize

_SENT = re.compile(r"(?<=[.!?…])\s+(?=[A-ZÀ-ỸĐ\"“‘(\[])|\n+")


_CREDIT = re.compile(r"\b[A-ZĐ]\.[A-ZĐ]\b|^\s*(Ảnh|Nguồn|Video|Clip|Đồ họa|Theo)\b|\bẢNH\b|ảnh:|Ảnh:|nguồn:|\[(video|clip|ảnh|photo)\]", re.I)


def split_sentences(text):
    """Tách câu, bỏ chú thích ảnh / nguồn và các đoạn dính nhau quá dài."""
    out = []
    for x in _SENT.split(text):
        x = (x or "").strip(); w = len(x.split())
        if 6 <= w <= 55 and not _CREDIT.search(x) and x[-1:] in ".!?…”\"":
            out.append(x)
    return out


def summarize(text, k=3, title=""):
    """Tóm tắt trích rút bằng TextRank: câu quan trọng = câu giống nhiều câu khác (PageRank trên đồ thị độ tương đồng TF-IDF),
    cộng điểm cho câu đầu bài và câu gần tiêu đề."""
    sents = split_sentences(text)[:80]
    n = len(sents)
    if n <= k:
        return sents, list(range(n)), sents
    M = VEC.transform([clean(x) for x in sents])
    S = (M @ M.T).toarray(); np.fill_diagonal(S, 0)
    rs = S.sum(1, keepdims=True); rs[rs == 0] = 1
    P = S / rs; r = np.full(n, 1 / n)
    for _ in range(50):
        r = 0.15 / n + 0.85 * (P.T @ r)
    r = r / (r.max() or 1)
    lead = 1 / np.sqrt(1 + np.arange(n))
    ts = (M @ VEC.transform([clean(title)]).T).toarray().ravel() if title else np.zeros(n)
    score = 0.6 * r + 0.25 * lead + 0.15 * (ts / (ts.max() or 1))
    pick = sorted(np.argsort(-score)[:k].tolist())
    return [sents[i] for i in pick], pick, sents


def keyphrases(text, n=8):
    x = VEC.transform([clean(text)]).tocsr()
    if not x.nnz:
        return []
    order = sorted(range(x.nnz), key=lambda j: -x.data[j] * (1.15 if " " in FEATURES[x.indices[j]] else 1))
    out = []
    for j in order:
        term = FEATURES[x.indices[j]]
        if len(term) < 3 or any(term in c or c in term for c in out):
            continue
        out.append(term)
        if len(out) >= n:
            break
    return out


@lru_cache(maxsize=2048)
def article_summary(aid, k=3):
    a = ART[aid]
    sm, _, _ = summarize(a["content"], k, a["title"])
    return sm


def _clusters():
    out = {}
    for t, ids in BY_TOPIC.items():
        rows = [IDX[i] for i in ids]; X = SX[rows]
        kk = max(8, round(len(ids) / 26))
        Z = normalize(TruncatedSVD(min(60, X.shape[1] - 1), random_state=42).fit_transform(X))
        km = KMeans(kk, n_init=5, random_state=42).fit(Z)
        sil = float(silhouette_score(Z, km.labels_))
        names = np.array(SV.get_feature_names_out())
        isbi = np.where(np.char.find(names.astype(str), " ") >= 0, 1.4, 1.0)
        gmean = np.asarray(X.mean(axis=0)).ravel()
        groups = []
        for c in range(kk):
            mem = np.where(km.labels_ == c)[0]
            if len(mem) < 3:
                continue
            cen = np.asarray(X[mem].mean(axis=0)).ravel() - gmean          # đặc trưng riêng của cụm so với cả chuyên mục
            terms = []
            for j in np.argsort(-cen * isbi)[:40]:
                if len(names[j]) < 4 or any(set(names[j].split()) & set(q.split()) for q in terms):
                    continue
                terms.append(names[j])
                if len(terms) == 3:
                    break
            rep = mem[np.argmax(Z[mem] @ km.cluster_centers_[c])]
            members = sorted(mem, key=lambda m: -(Z[m] @ km.cluster_centers_[c]))
            groups.append({"label": " · ".join(terms), "size": len(mem), "rep": ids[rep], "items": [ids[m] for m in members[:6]]})
        groups.sort(key=lambda g: -g["size"])
        out[t] = {"groups": groups, "sil": round(sil, 3), "k": len(groups)}
    return out


_CL = {}


def clusters():
    if not _CL:
        f = ROOT / "data" / "clusters.json"
        if f.exists():
            _CL.update(json.loads(f.read_text(encoding="utf-8")))
        else:
            _CL.update(_clusters())
            f.write_text(json.dumps(_CL, ensure_ascii=False), encoding="utf-8")
    return _CL


# ---------------------------------------------------------------- trang
@app.get("/")
def home():
    feat = {t: BY_TOPIC[t] for t in TOPICS}
    first_test = lambda t: next((i for i in feat[t] if ART[i]["test"]), feat[t][0])           # bài nổi bật lấy từ tập kiểm thử (AI chưa từng thấy)
    hero_ids = [first_test(t) for t in ("Thời sự", "Thể thao", "Kinh doanh", "Khoa học", "Sức khỏe")]
    latest = [i for i in ORDER if i not in hero_ids][:8]
    sections = [(t, cards(feat[t][1:5])) for t in ("Thời sự", "Kinh doanh", "Thể thao", "Giáo dục", "Sức khỏe", "Khoa học")]
    ok_ex = next(ART[i] for i in feat["Thế giới"] if ART[i]["test"] and ART[i]["label"] == ART[i]["truth"])
    wrong = sorted([a for a in ART.values() if a["test"] and a["label"] != a["truth"]], key=lambda a: a["pct"])
    bad_ex = wrong[len(wrong) // 2]                                                           # một bài AI sai điển hình (độ nghiêng trung vị)
    return render_template("home.html", hero=ART[hero_ids[0]], side=cards(hero_ids[1:]), latest=cards(latest), sections=sections, keywords=KEYWORDS, ok_ex=ok_ex, bad_ex=bad_ex, demo_text=(ok_ex["title"] + ". " + ok_ex["desc"] + " " + ok_ex["content"])[:900])


@app.get("/chu-de/<slug>")
def category(slug):
    name = SLUG.get(slug) or abort(404)
    all_ids = BY_TOPIC[name]
    loc = request.args.get("loc", "all")
    ids = {"test": [i for i in all_ids if ART[i]["test"]], "sai": [i for i in all_ids if ART[i]["label"] != ART[i]["truth"]]}.get(loc, all_ids)
    loc = loc if loc in ("test", "sai") else "all"
    counts = {"all": len(all_ids), "test": sum(ART[i]["test"] for i in all_ids), "sai": sum(ART[i]["label"] != ART[i]["truth"] for i in all_ids)}
    page = max(1, request.args.get("page", 1, type=int)); pages = max(1, math.ceil(len(ids) / PER_PAGE))
    return render_template("category.html", name=name, meta=TOPICS[name], items=cards(ids[(page - 1) * PER_PAGE: page * PER_PAGE]),
                           page=page, pages=pages, total=len(all_ids), shown=len(ids), loc=loc, counts=counts, keywords=KEYWORDS[name])


@app.get("/bai/<int:aid>")
def article(aid):
    a = ART.get(aid) or abort(404)
    res = analyze(a["title"] + ". " + a["desc"] + " " + a["content"])
    sim = (SX @ SX[IDX[aid]].T).toarray().ravel(); sim[IDX[aid]] = -1
    rel = [IDS[j] for j in np.argsort(-sim)[:4]]
    truth_rank = truth_pct = None
    if res:
        for n, t in enumerate(res["top"], 1):
            if t["label"] == a["truth"]:
                truth_rank, truth_pct = n, t["pct"]
    words = [k["word"] for k in (res["keywords"] if res else [])]
    why = [w for w in words if not (" " not in w and any(" " in o and w in o.split() for o in words))][:6]      # bỏ từ đơn đã nằm trong cụm 2 từ
    return render_template("article.html", a=a, res=res, related=cards(rel), summ=article_summary(aid, 3), kws=keyphrases(a["title"] + " " + a["content"], 6),
                           truth_rank=truth_rank, truth_pct=truth_pct, why=why)


@app.get("/tim-kiem")
def search():
    qq = request.args.get("q", "").strip(); topic = request.args.get("topic", "")
    results = []
    if qq:
        qv = SV.transform([clean(qq)]); sc = (SX @ qv.T).toarray().ravel()
        low = qq.lower()
        for n in np.argsort(-sc)[:200]:
            a = ART[IDS[n]]
            s = sc[n] + (0.5 if low in a["title"].lower() else 0)
            if s > 0.02 and (not topic or a["label"] == topic): results.append((s, a))
        results = [a for _, a in sorted(results, key=lambda x: -x[0])][:40]
    return render_template("search.html", qq=qq, results=results, topic=topic)


@app.get("/phan-loai")
def classify_page():
    return render_template("classify.html")


@app.get("/thong-ke")
def stats():
    per = [{"name": c, "p": REPORT[c]["precision"], "r": REPORT[c]["recall"], "f1": REPORT[c]["f1-score"], "n": int(REPORT[c]["support"])} for c in CLASSES if c in REPORT]
    wrong = [a for a in _t if a["label"] != a["truth"]]
    wrong.sort(key=lambda a: -a["gap"])
    return render_template("stats.html", wrong=wrong[:12], n_wrong=len(wrong), per=sorted(per, key=lambda x: -x["f1"]), cm=CM.tolist(), classes=CLASSES, maxcount=max(STATS["counts"].values()),
                           keywords=KEYWORDS, bench=BENCH)


@app.get("/gioi-thieu")
def about():
    return render_template("about.html", bench=BENCH)


# ---------------------------------------------------------------- API cho công cụ phân loại
class _Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.skip = 0; self.parts = []; self.title = ""; self._t = False
    def handle_starttag(self, tag, a):
        if tag in ("script", "style", "nav", "footer", "header", "aside", "noscript"): self.skip += 1
        if tag == "title": self._t = True
    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer", "header", "aside", "noscript") and self.skip: self.skip -= 1
        if tag == "title": self._t = False
    def handle_data(self, d):
        if self._t: self.title += d
        elif not self.skip and len(d.strip()) > 40: self.parts.append(d.strip())


def fetch_url(url):
    u = urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        raise ValueError("Link không hợp lệ (cần bắt đầu bằng http:// hoặc https://).")
    for info in socket.getaddrinfo(u.hostname, None):
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise ValueError("Không cho phép truy cập địa chỉ nội bộ.")
    raw = urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0 (VnNews)"}), timeout=10).read(2_000_000)
    p = _Text(); p.feed(raw.decode("utf-8", errors="ignore"))
    return p.title.strip(), "\n".join(p.parts)


@app.post("/api/predict")
def api_predict():
    res = analyze((request.get_json(silent=True) or {}).get("text", ""))
    if not res:
        return jsonify(error="Nội dung quá ngắn. Hãy nhập ít nhất một đoạn văn (khoảng 10 từ trở lên)."), 400
    return jsonify(res)


@app.post("/api/url")
def api_url():
    try:
        title, text = fetch_url((request.get_json(silent=True) or {}).get("url", "").strip())
    except Exception as e:
        return jsonify(error=f"Không đọc được link: {e}"), 400
    if len(text.split()) < 20:
        return jsonify(error="Không trích xuất được nội dung bài báo từ link này."), 400
    return jsonify(title=title, text=text[:6000])


@app.get("/api/samples")
def api_samples():
    return jsonify([{"label": k, "icon": TOPICS[k][1], "color": TOPICS[k][2], "text": v} for k, v in SAMPLES.items()])


@app.get("/api/random")
def api_random():
    a = ART[random.choice(IDS)]
    full = request.args.get("full")
    return jsonify(text=(a["content"] if full else a["title"] + ". " + a["desc"] + " " + a["content"])[: 8000 if full else 1500], title=a["title"], truth=a["truth"], id=a["id"], split=a["split"])


# ---------------------------------------------------------------- AI Lab: giải thích dự đoán (Explainable AI)
WORD = re.compile(r"[^\W\d_]+")
_URL = re.compile(r"https?://\S+|\S+@\S+")


def _chunks(text, n=3):
    paras = [p.strip() for p in re.split(r"\n+", text) if len(p.split()) >= 8]
    if len(paras) < 2:
        sents = [x for x in re.split(r"(?<=[.!?])\s+", text) if x.strip()]
        paras = [" ".join(sents[i:i + n]) for i in range(0, len(sents), n)]
    return [p for p in paras if len(p.split()) >= 8][:14]


def explain(text, mask=(), vs="all"):
    """Giải thích mô hình tuyến tính: đóng góp của từng từ = (trọng số lớp dự đoán − lớp đối chứng) × giá trị TF-IDF."""
    text = unicodedata.normalize("NFC", text)[:30000]
    scrub = _URL.sub(lambda m: " " * len(m.group()), text)
    spans = [(m.start(), m.end(), m.group().lower()) for m in WORD.finditer(scrub)]
    maskset = {w.lower() for w in mask}
    work = list(scrub)
    for st, en, tok in spans:
        if tok in maskset:
            work[st:en] = " " * (en - st)
    work = "".join(work)
    res = analyze(work)
    if not res:
        return None
    kept = [(i, tok) for i, (_, _, tok) in enumerate(spans) if tok not in maskset and len(tok) >= 2]
    feats = {}                                              # đặc trưng -> danh sách vị trí token
    for n, (i, tok) in enumerate(kept):
        feats.setdefault(tok, []).append((i,))
        if n + 1 < len(kept):
            feats.setdefault(tok + " " + kept[n + 1][1], []).append((i, kept[n + 1][0]))
    x = VEC.transform([clean(work)]).tocsr()
    k = CLASSES.index(res["label"])
    if vs in CLASSES and vs != res["label"]:
        ref = CLF.coef_[CLASSES.index(vs)]
    else:
        ref = (CLF.coef_.sum(axis=0) - CLF.coef_[k]) / (len(CLASSES) - 1)
    wdiff = CLF.coef_[k] - ref
    score = np.zeros(len(spans))
    for f, occ in feats.items():
        j = VEC.vocabulary_.get(f)
        if j is None:
            continue
        c = float(x[0, j]) * float(wdiff[j]) / len(occ)
        for pos in occ:
            for i in pos:
                score[i] += c / len(pos)
    toks = [{"s": st, "e": en, "w": round(float(score[i]), 4), "m": tok in maskset} for i, (st, en, tok) in enumerate(spans)]
    agg = {}
    for i, (_, _, tok) in enumerate(spans):
        agg[tok] = agg.get(tok, 0) + score[i]
    ranked = sorted(agg.items(), key=lambda kv: -kv[1])
    pos = [{"word": w, "w": round(v, 3)} for w, v in ranked[:10] if v > 0]
    neg = [{"word": w, "w": round(v, 3)} for w, v in ranked[::-1][:8] if v < 0]
    segs = []
    for ch in _chunks(work):
        r = analyze(ch)
        if r:
            segs.append({"text": ch[:110], "label": r["label"], "icon": r["icon"], "pct": r["pct"], "words": r["words"]})
    tw = sum(s["words"] for s in segs) or 1
    agree = sum(s["words"] for s in segs if s["label"] == res["label"]) / tw if segs else 1.0
    verdict = "Bài đơn chủ đề" if agree >= 0.75 else "Bài đa chủ đề / mơ hồ"
    return {"text": text, "tokens": toks, "result": res, "pos": pos, "neg": neg, "segments": segs, "agree": round(agree * 100), "verdict": verdict, "vs": vs}


@app.get("/giai-thich")
def lab():
    aid = request.args.get("id", type=int)
    pre = None
    if aid in ART:
        a = ART[aid]
        pre = {"id": aid, "title": a["title"], "text": a["title"] + ".\n" + a["desc"] + "\n" + a["content"]}
    return render_template("lab.html", pre=pre)


@app.post("/api/explain")
def api_explain():
    d = request.get_json(silent=True) or {}
    out = explain(d.get("text", ""), d.get("mask", []), d.get("vs", "all"))
    if not out:
        return jsonify(error="Nội dung quá ngắn. Hãy nhập ít nhất một đoạn văn (khoảng 10 từ trở lên)."), 400
    return jsonify(out)


# ---------------------------------------------------------------- chức năng mới: tóm tắt, sự kiện, bản tin, gợi ý
try:
    SUMEVAL = json.loads((ROOT / "outputs/summary_eval.json").read_text(encoding="utf-8"))
except Exception:
    SUMEVAL = {}


@app.get("/cong-cu")
def tools():
    return render_template("tools.html")


@app.get("/tom-tat")
def summarize_page():
    return render_template("summarize.html", ev=SUMEVAL)


@app.post("/api/summarize")
def api_summarize():
    d = request.get_json(silent=True) or {}
    text = (d.get("text") or "")[:20000]; k = min(6, max(1, int(d.get("k") or 3)))
    sents = split_sentences(text)
    if len(sents) < 3:
        return jsonify(error="Văn bản quá ngắn để tóm tắt. Hãy dán một bài báo đầy đủ (ít nhất vài câu)."), 400
    sm, pick, allsents = summarize(text, k, d.get("title", ""))
    win, wout = len(text.split()), sum(len(x.split()) for x in sm)
    return jsonify(summary=sm, sentences=[{"t": x, "picked": i in pick} for i, x in enumerate(allsents)], keywords=keyphrases(text, 8),
                   words_in=win, words_out=wout, ratio=round(100 * (1 - wout / max(win, 1))), saved=max(1, round((win - wout) / 200)))


@app.get("/su-kien")
def events():
    cl = clusters(); slug = request.args.get("c", "all")
    name = SLUG.get(slug)
    allg = sorted(((t, g) for t, c in cl.items() for g in c["groups"]), key=lambda x: -x[1]["size"])[:9]
    view = None
    if name:
        view = {"name": name, "meta": TOPICS[name], **cl[name]}
    return render_template("events.html", cl=cl, slug=slug, view=view, top=allg, ART=ART, avg_sil=round(sum(c["sil"] for c in cl.values()) / len(cl), 3))


@app.get("/ban-tin")
def digest():
    items = []
    for t in ("Thời sự", "Thế giới", "Kinh doanh", "Pháp luật", "Giáo dục", "Sức khỏe", "Khoa học", "Đời sống", "Giải trí", "Thể thao", "Xe"):
        a = ART[BY_TOPIC[t][0]]
        sm = article_summary(a["id"], 2)
        items.append({"a": a, "sum": sm, "kw": keyphrases(a["title"] + " " + a["content"], 4), "win": len(a["content"].split()), "wout": sum(len(x.split()) for x in sm)})
    return render_template("digest.html", items=items, win=sum(i["win"] for i in items), wout=sum(i["wout"] for i in items))


@app.get("/api/recommend")
def api_recommend():
    ids = [i for i in (request.args.get("ids", "").split(",")) if i.isdigit() and int(i) in IDX][-12:]
    if not ids:
        return jsonify(items=[], profile=[])
    rows = [IDX[int(i)] for i in ids]
    cen = np.asarray(SX[rows].mean(axis=0)).ravel()
    sim = SX @ cen; sim[rows] = -1
    top = np.argsort(-np.asarray(sim).ravel())[:6]
    cnt = Counter(ART[int(i)]["label"] for i in ids)
    prof = [{"label": k, "icon": TOPICS[k][1], "pct": round(100 * v / len(ids))} for k, v in cnt.most_common(4)]
    keep = ("id", "title", "desc", "label", "icon", "img", "minutes", "pct")
    return jsonify(items=[{k: ART[IDS[j]][k] for k in keep} for j in top], profile=prof)


# ---------------------------------------------------------------- Hỏi AI về tin tức: hỏi đáp CÓ DẪN NGUỒN (truy hồi + trích câu, không tự sinh nội dung)
import threading
QA = {"AX": None}
QA_READY = threading.Event()
_STOPQ = set("là gì nào sao thế bao nhiêu ai đâu khi không có được của và các những này đó thì mà ở tại cho với trong về như hay hoặc bị đã sẽ đang rất cũng còn hôm nay vậy ra làm".split())
QA_W_CONTENT, QA_W_TITLE = 0.7, 0.3                    # trọng số chỉ mục nội dung / tiêu đề+sapo (chọn bằng thí nghiệm experiments/exp8_qa.py)
QA_ABSTAIN, QA_MID, QA_HIGH = 0.10, 0.20, 0.30         # ngưỡng điểm của bài cao nhất: không trả lời / trung bình / cao (exp8: đúng bài ≈ 66–86% / 91% / 96%; ngưỡng 0,10: từ chối nhầm 3,8% câu hỏi thật, trả lời nhầm 14,2% câu ngẫu nhiên)
QA_EXAMPLES = ["Giá vàng trong nước biến động thế nào?", "Nga dùng UAV phá hủy pháo tự hành của Ukraine như thế nào?", "Mitsubishi Destinator ra mắt ở Việt Nam khi nào?",
               "Thông tư 29 về dạy thêm có hiệu lực khi nào?", "Nên ăn rau sống thế nào cho đúng?", "Xanh SM đạt giải thưởng gì?"]


def _build_qa_index():
    """Chỉ mục nội dung toàn bài cho hỏi đáp. Dựng ở luồng nền để website khởi động nhanh (mất vài chục giây lần đầu)."""
    try:
        QA["AX"] = VEC.transform([clean(ART[i]["title"] + " " + ART[i]["desc"] + " " + ART[i]["content"]) for i in IDS])
    finally:
        QA_READY.set()


threading.Thread(target=_build_qa_index, daemon=True).start()


def qa_answer(q, aid=None, ka=8, ks=3):
    """Trả lời câu hỏi bằng cách (1) tìm các bài liên quan, (2) chọn các CÂU giống câu hỏi nhất trong các bài đó và dẫn nguồn.
    Nếu aid được đưa ra thì chỉ tìm trong bài đó."""
    qfull = clean(q)
    if len(qfull.split()) < 2:
        raise ValueError("Hãy nhập câu hỏi dài hơn một chút (ít nhất 2 từ).")
    if not QA_READY.wait(240) or QA["AX"] is None:
        raise RuntimeError("Chỉ mục hỏi đáp chưa sẵn sàng, hãy thử lại sau vài giây.")
    t0 = time.time()                                    # chỉ đo thời gian trả lời, không tính thời gian chờ dựng chỉ mục lần đầu
    qc = " ".join(w for w in qfull.split() if w not in _STOPQ) or qfull
    qv = VEC.transform([qc])
    s = QA_W_CONTENT * (QA["AX"] @ qv.T).toarray().ravel() + QA_W_TITLE * (SX @ SV.transform([qc]).T).toarray().ravel()
    cand = [IDX[aid]] if aid is not None else [int(j) for j in np.argsort(-s)[:ka] if s[j] > 0]
    top_s = float(s[cand[0]]) if cand else 0.0
    smax = float(s.max()) or 1.0
    rows = []
    for j in cand:
        a = ART[IDS[j]]
        sents = split_sentences(a["desc"] + "\n" + a["content"])[:150]
        if not sents:
            continue
        c = (VEC.transform([clean(x) for x in sents]) @ qv.T).toarray().ravel()
        rel = min(1.0, float(s[j]) / smax)
        for n, (x, cc) in enumerate(zip(sents, c)):
            if cc > 0:
                rows.append((float(cc) * (0.75 + 0.25 * rel) + (0.01 if n < 2 else 0.0), float(cc), x, a["id"]))
    rows.sort(key=lambda r: -r[0])
    ans, seen, per = [], set(), Counter()
    for _, cc, x, i in rows:
        if x[:60] in seen or per[i] >= 2:
            continue
        seen.add(x[:60]); per[i] += 1
        a = ART[i]
        ans.append({"text": x, "score": round(cc, 3), "id": i, "title": a["title"], "label": a["label"], "icon": a["icon"]})
        if len(ans) >= ks:
            break
    if aid is not None:
        best = ans[0]["score"] if ans else 0.0
        conf = "cao" if best >= 0.35 else "trung bình" if best >= 0.2 else "thấp"
        abstain = best < 0.12
    else:
        conf = "cao" if top_s >= QA_HIGH else "trung bình" if top_s >= QA_MID else "thấp"
        abstain = top_s < QA_ABSTAIN or not ans
    # Chủ đề câu hỏi = chuyên mục AI đã xếp cho các bài tìm được (bỏ phiếu theo điểm liên quan); phân loại trực tiếp câu hỏi ngắn thì không đủ tin cậy
    vote = Counter()
    for j in cand[:5]:
        vote[ART[IDS[j]]["label"]] += float(s[j])
    cat = None
    if vote and sum(vote.values()) > 0:
        lab, w = vote.most_common(1)[0]
        cat = {"label": lab, "icon": TOPICS[lab][1], "share": round(100 * w / sum(vote.values()))}
    src = [ART[IDS[j]] for j in cand[:4]]
    return {"q": q, "scope": "bài" if aid is not None else "kho", "abstain": bool(abstain), "confidence": conf, "top_score": round(top_s, 3), "ms": round((time.time() - t0) * 1000),
            "cat": cat,
            "terms": [w for w in qc.split() if len(w) > 1], "answers": ans,
            "sources": [{"id": a["id"], "title": a["title"], "label": a["label"], "icon": a["icon"], "img": a["img"], "minutes": a["minutes"]} for a in src]}


@app.get("/hoi-ai")
def ask_page():
    return render_template("ask.html", examples=QA_EXAMPLES, q=request.args.get("q", "")[:300])


@app.post("/api/ask")
def api_ask():
    d = request.get_json(silent=True) or {}
    aid = d.get("aid")
    if aid is not None and (not isinstance(aid, int) or aid not in ART):
        return jsonify(error="Bài viết không tồn tại."), 400
    try:
        return jsonify(qa_answer(str(d.get("q", ""))[:300], aid))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except RuntimeError as e:
        return jsonify(error=str(e)), 503


# ---------------------------------------------------------------- kịch bản trình bày
@app.get("/trinh-bay")
def guide():
    return render_template("guide.html")


@app.get("/favicon.ico")
def favicon():
    return "", 204


def lan_ip():
    """Địa chỉ IP trong mạng nội bộ (để điện thoại cùng WiFi truy cập)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as so:
            so.connect(("10.255.255.255", 1))
            return so.getsockname()[0]
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    import os, sys
    lan = "--lan" in sys.argv or bool(os.environ.get("VNNEWS_LAN"))
    if lan:
        print(f"\n  Chế độ MẠNG NỘI BỘ — máy khác cùng WiFi mở được website tại: http://{lan_ip()}:5000\n")
    else:
        print("Mở trình duyệt tại http://127.0.0.1:5000   (thêm --lan để máy khác cùng WiFi cũng mở được)")
    app.run(host="0.0.0.0" if lan else "127.0.0.1", port=5000, debug=False, threaded=True)
