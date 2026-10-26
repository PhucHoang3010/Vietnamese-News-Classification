"""Kiểm tra môi trường chạy VnNews:  python kiem_tra_moi_truong.py
In ra phiên bản Python, đường dẫn đang dùng và thời gian nạp từng thư viện (để biết bước nào chậm hoặc thiếu)."""
import sys, time
print("Python:", sys.version.split()[0], "|", sys.executable, flush=True)
if ".venv" not in sys.executable.lower() and "venv" not in sys.executable.lower():
    print("  ⚠ Có vẻ bạn chưa dùng môi trường ảo (.venv). Hãy chạy:  .venv\\Scripts\\Activate.ps1", flush=True)
for m in ["numpy", "scipy", "pandas", "joblib", "sklearn", "flask"]:
    t = time.time()
    try:
        mod = __import__(m)
        print(f"  {m:8s} OK  {getattr(mod, '__version__', ''):10s} ({time.time() - t:.1f}s)", flush=True)
    except Exception as e:
        print(f"  {m:8s} LỖI: {e}   → chạy:  pip install -r requirements.txt", flush=True)
t = time.time()
try:
    import joblib
    from pathlib import Path
    joblib.load(Path(__file__).parent / "model.joblib")
    print(f"  model.joblib nạp được ({time.time() - t:.1f}s)", flush=True)
except Exception as e:
    print("  model.joblib LỖI:", repr(e)[:200], "\n  → chạy:  python train.py   rồi   python build_cache.py", flush=True)
print("Xong. Nếu mọi dòng đều OK thì chạy:  python app.py   (lần đầu chờ 1–3 phút, KHÔNG bấm Ctrl+C)")
