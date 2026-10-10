"""Website tin tức VnNews — AI tự động phân loại chủ đề.   python app.py   →  http://127.0.0.1:5000"""
import csv, ipaddress, json, math, random, re, socket, unicodedata
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
VEC, CLF = model.named_steps["tfidf"], model.named_steps["clf"]
FEATURES = np.array(VEC.get_feature_names_out())
CLASSES = list(model.classes_)

TOPICS = {  # tên: (slug, icon, màu)
    "Thời sự": ("thoi-su", "📰", "#475569"), "Thế giới": ("the-gioi", "🌍", "#0891b2"),
    "Kinh doanh": ("kinh-doanh", "💼", "#059669"), "Pháp luật": ("phap-luat", "⚖️", "#b45309"),
    "Giáo dục": ("giao-duc", "🎓", "#2563eb"), "Sức khỏe": ("suc-khoe", "🩺", "#dc2626"),
    "Khoa học": ("khoa-hoc", "🔬", "#7c3aed"), "Đời sống": ("doi-song", "🏡", "#c026d3"),
    "Giải trí": ("giai-tri", "🎬", "#db2777"), "Thể thao": ("the-thao", "⚽", "#16a34a"), "Xe": ("xe", "🚗", "#ea580c"),
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
    p = np.exp(s * 3); p /= p.sum(); order = np.argsort(-p)
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
                 "pct": pr["pct"], "gap": pr["gap"], "test": pr["test"], "slug": TOPICS[pr["label"]][0], "icon": TOPICS[pr["label"]][1],
                 "color": TOPICS[pr["label"]][2], "minutes": max(1, round(len(r.content.split()) / 200))}
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

# từ khóa đặc trưng từng chủ đề
KEYWORDS = {c: [FEATURES[j] for j in np.argsort(CLF.coef_[k])[-14:][::-1]] for k, c in enumerate(CLASSES)}

# thống kê trên tập kiểm thử
_t = [a for a in ART.values() if a["test"]]
_y, _p = [a["truth"] for a in _t], [a["label"] for a in _t]
REPORT = classification_report(_y, _p, output_dict=True, zero_division=0)
CM = confusion_matrix(_y, _p, labels=CLASSES)
STATS = {"n": len(ART), "n_test": len(_t), "acc": float(np.mean(np.array(_y) == np.array(_p))), "f1": float(f1_score(_y, _p, average="macro")),
         "counts": Counter(a["label"] for a in ART.values())}
try:
    BENCH = list(csv.DictReader(open(ROOT / "outputs/so_sanh_mo_hinh.csv", encoding="utf-8")))
except Exception:
    BENCH = []

app = Flask(__name__)
app.json.ensure_ascii = False
NAV = [{"name": k, "slug": v[0], "icon": v[1], "color": v[2]} for k, v in TOPICS.items()]


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


# ---------------------------------------------------------------- trang
@app.get("/")
def home():
    feat = {t: BY_TOPIC[t] for t in TOPICS}
    hero_ids = [feat[t][0] for t in ("Thời sự", "Thể thao", "Kinh doanh", "Khoa học", "Sức khỏe")]
    latest = [i for i in ORDER if i not in hero_ids][:8]
    sections = [(t, cards(feat[t][1:5])) for t in ("Thời sự", "Kinh doanh", "Thể thao", "Giáo dục", "Sức khỏe", "Khoa học")]
    return render_template("home.html", hero=ART[hero_ids[0]], side=cards(hero_ids[1:]), latest=cards(latest), sections=sections, keywords=KEYWORDS)


@app.get("/chu-de/<slug>")
def category(slug):
    name = SLUG.get(slug) or abort(404)
    ids = BY_TOPIC[name]; page = max(1, request.args.get("page", 1, type=int)); pages = math.ceil(len(ids) / PER_PAGE)
    return render_template("category.html", name=name, meta=TOPICS[name], items=cards(ids[(page - 1) * PER_PAGE: page * PER_PAGE]),
                           page=page, pages=pages, total=len(ids), keywords=KEYWORDS[name])


@app.get("/bai/<int:aid>")
def article(aid):
    a = ART.get(aid) or abort(404)
    res = analyze(a["title"] + ". " + a["desc"] + " " + a["content"])
    sim = (SX @ SX[IDX[aid]].T).toarray().ravel(); sim[IDX[aid]] = -1
    rel = [IDS[j] for j in np.argsort(-sim)[:4]]
    return render_template("article.html", a=a, res=res, related=cards(rel))


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
    return render_template("stats.html", per=sorted(per, key=lambda x: -x["f1"]), cm=CM.tolist(), classes=CLASSES, maxcount=max(STATS["counts"].values()),
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
    return jsonify(text=(a["title"] + ". " + a["desc"] + " " + a["content"])[:1500], truth=a["truth"])


@app.get("/favicon.ico")
def favicon():
    return "", 204


if __name__ == "__main__":
    print("Mở trình duyệt tại http://127.0.0.1:5000")
    app.run(debug=False)
