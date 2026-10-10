"""Web phân loại tin tức tiếng Việt.   python app.py   →  http://127.0.0.1:5000"""
import csv, ipaddress, json, random, re, socket, unicodedata
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import joblib
import numpy as np
from flask import Flask, jsonify, render_template, request

ROOT = Path(__file__).resolve().parent
model = joblib.load(ROOT / "model.joblib")
VEC, CLF = model.named_steps["tfidf"], model.named_steps["clf"]
FEATURES = np.array(VEC.get_feature_names_out())
CLASSES = list(model.classes_)
app = Flask(__name__)
app.json.ensure_ascii = False

# Màu + biểu tượng cho từng chủ đề
TOPICS = {
    "Giáo dục": ("🎓", "#2563eb"), "Giải trí": ("🎬", "#db2777"), "Khoa học": ("🔬", "#7c3aed"),
    "Kinh doanh": ("💼", "#059669"), "Pháp luật": ("⚖️", "#b45309"), "Sức khỏe": ("🩺", "#dc2626"),
    "Thế giới": ("🌍", "#0891b2"), "Thể thao": ("⚽", "#16a34a"), "Thời sự": ("📰", "#475569"),
    "Xe": ("🚗", "#ea580c"), "Đời sống": ("🏡", "#c026d3"),
}
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
    vec = VEC.transform([x])
    s = CLF.decision_function(vec)[0]
    p = np.exp(s * 3); p /= p.sum()          # điểm tương đối (softmax), không phải xác suất hiệu chỉnh
    order = np.argsort(-p)
    top = [{"label": CLASSES[i], "pct": round(float(p[i]) * 100, 1), "icon": TOPICS[CLASSES[i]][0], "color": TOPICS[CLASSES[i]][1]} for i in order[:5]]
    k = int(order[0])
    contrib = vec.multiply(CLF.coef_[k]).tocsr()          # đóng góp của từng từ vào chủ đề dự đoán
    idx = contrib.indices[np.argsort(-contrib.data)][:8] if contrib.nnz else []
    kws = [{"word": FEATURES[i], "weight": round(float(contrib[0, i]), 3)} for i in idx if contrib[0, i] > 0]
    gap = float(p[order[0]] - p[order[1]])
    conf = "cao" if gap > 0.5 else "trung bình" if gap > 0.2 else "thấp"
    return {"label": top[0]["label"], "icon": top[0]["icon"], "color": top[0]["color"], "pct": top[0]["pct"],
            "confidence": conf, "top": top, "keywords": kws, "words": len(x.split())}


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
    for info in socket.getaddrinfo(u.hostname, None):          # chặn địa chỉ nội bộ
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise ValueError("Không cho phép truy cập địa chỉ nội bộ.")
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (NewsClassifier)"})
    raw = urlopen(req, timeout=10).read(2_000_000)
    html = raw.decode("utf-8", errors="ignore")
    p = _Text(); p.feed(html)
    return p.title.strip(), "\n".join(p.parts)


@app.get("/favicon.ico")
def favicon():
    return "", 204


@app.get("/")
def index():
    return render_template("index.html", topics=[{"name": k, "icon": v[0], "color": v[1]} for k, v in TOPICS.items()])


@app.post("/api/predict")
def api_predict():
    data = request.get_json(silent=True) or {}
    res = analyze(data.get("text", ""))
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
    return jsonify([{"label": k, "icon": TOPICS[k][0], "color": TOPICS[k][1], "text": v} for k, v in SAMPLES.items()])


@app.get("/api/random")
def api_random():
    path = ROOT.parent / "data" / "external" / "viet_online_news_test.csv"
    if not path.exists():
        return jsonify(error="Không tìm thấy data/external/viet_online_news_test.csv"), 404
    csv.field_size_limit(10**8)
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    r = random.choice(rows)
    text = (r["title"] + ". " + (r["description"] or "") + " " + (r["content"] or ""))[:1500]
    return jsonify(text=text, truth=r["ground_truth"])


@app.get("/api/info")
def api_info():
    out = ROOT / "outputs"
    info = {"classes": CLASSES, "features": int(len(FEATURES))}
    try:
        info["metrics"] = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
        rows = list(csv.DictReader(open(out / "bao_cao_phan_loai.csv", encoding="utf-8-sig")))
        info["per_class"] = [{"label": r[""], "f1": round(float(r["f1-score"]), 3), "precision": round(float(r["precision"]), 3),
                              "recall": round(float(r["recall"]), 3)} for r in rows if r[""] in TOPICS]
        info["bench"] = list(csv.DictReader(open(out / "so_sanh_mo_hinh.csv", encoding="utf-8")))
    except Exception:
        pass
    return jsonify(info)


if __name__ == "__main__":
    print("Mở trình duyệt tại http://127.0.0.1:5000")
    app.run(debug=False)
