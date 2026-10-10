"""Web demo phân loại tin tức:  python app.py  →  mở http://127.0.0.1:5000"""
import re, unicodedata
from pathlib import Path
import joblib
import numpy as np
from flask import Flask, jsonify, render_template_string, request

model = joblib.load(Path(__file__).parent / "model.joblib")
app = Flask(__name__)

def clean(t):
    t = unicodedata.normalize("NFC", str(t)).lower()
    t = re.sub(r"https?://\S+|\S+@\S+", " ", t); t = re.sub(r"\d+", " ", t)
    t = re.sub(r"[^\w\s]|_", " ", t)
    return re.sub(r"\s+", " ", t).strip()

PAGE = """<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Phân loại tin tức</title><style>
body{font-family:system-ui,sans-serif;background:#f1f5f9;margin:0;color:#0f172a}
main{max-width:760px;margin:32px auto;padding:0 16px}h1{font-size:26px}
textarea{width:100%;height:180px;padding:12px;border:1px solid #cbd5e1;border-radius:10px;font:15px/1.5 system-ui,sans-serif;box-sizing:border-box}
button{margin-top:10px;background:#2563eb;color:#fff;border:0;padding:10px 22px;border-radius:8px;font-size:15px;cursor:pointer}
.card{background:#fff;border-radius:12px;padding:18px;margin-top:18px;box-shadow:0 1px 3px #0001}
.top{font-size:24px;font-weight:700;color:#2563eb}.row{display:flex;align-items:center;gap:10px;margin:6px 0}
.row span:first-child{width:90px}.bar{flex:1;background:#e2e8f0;height:12px;border-radius:6px;overflow:hidden}
.bar i{display:block;height:100%;background:#3b82f6}small{color:#64748b}</style></head><body><main>
<h1>📰 Phân loại tin tức tiếng Việt</h1><small>TF-IDF + Linear SVM · 11 chủ đề</small>
<div class="card"><textarea id="t" placeholder="Dán nội dung bài báo vào đây..."></textarea>
<button onclick="go()">Phân loại</button></div><div id="out"></div></main><script>
async function go(){const r=await fetch('/api/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:document.getElementById('t').value})});
const d=await r.json();if(d.error){out.innerHTML='<div class="card">'+d.error+'</div>';return}
out.innerHTML='<div class="card"><small>Chủ đề dự đoán</small><div class="top">'+d.label+'</div>'+d.top.map(x=>'<div class="row"><span>'+x[0]+'</span><div class="bar"><i style="width:'+x[1]+'%"></i></div><span>'+x[1]+'%</span></div>').join('')+'</div>'}
</script></body></html>"""

@app.get("/")
def index(): return render_template_string(PAGE)

@app.post("/api/predict")
def predict():
    x = clean((request.get_json(silent=True) or {}).get("text", ""))
    if len(x) < 10: return jsonify(error="Vui lòng nhập nội dung dài hơn.")
    s = model.decision_function([x])[0]; p = np.exp(s * 3); p /= p.sum()   # điểm tương đối (softmax)
    top = sorted(zip(model.classes_, p), key=lambda a: -a[1])[:5]
    return jsonify(label=top[0][0], top=[[c, round(float(v) * 100, 1)] for c, v in top])

if __name__ == "__main__":
    app.run(debug=False)
