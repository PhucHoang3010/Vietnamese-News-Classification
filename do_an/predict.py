"""Dự đoán chủ đề bài báo.
  python do_an/predict.py "Đội tuyển Việt Nam thắng 2-0 ..."
  python do_an/predict.py            (nhập nhiều dòng, kết thúc bằng Enter trống)
"""
import re, sys, unicodedata
from pathlib import Path
import joblib

def clean(t):
    t = unicodedata.normalize("NFC", str(t)).lower()
    t = re.sub(r"https?://\S+|\S+@\S+", " ", t); t = re.sub(r"\d+", " ", t)
    t = re.sub(r"[^\w\s]|_", " ", t)
    return re.sub(r"\s+", " ", t).strip()

model = joblib.load(Path(__file__).parent / "model.joblib")
text = " ".join(sys.argv[1:]) or "\n".join(iter(input, ""))
x = clean(text)
scores = model.decision_function([x])[0]
top = sorted(zip(model.classes_, scores), key=lambda s: -s[1])[:3]
print("Chủ đề dự đoán:", top[0][0])
for c, s in top: print(f"  {c:<12} {s:+.3f}")
