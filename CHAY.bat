@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === VnNews: tao moi truong (neu chua co) va chay website ===
if not exist ".venv\Scripts\python.exe" (
  echo Tao moi truong ao .venv ...
  python -m venv .venv
)
call ".venv\Scripts\activate.bat"
echo Cai thu vien (lan dau mat vai phut)...
python -m pip install -q -r requirements.txt
echo.
echo === Dang khoi dong. Lan dau co the mat 1-3 phut. KHONG bam Ctrl+C. ===
echo === Khi thay dong "Mo trinh duyet tai http://127.0.0.1:5000" thi mo trinh duyet. ===
python app.py
pause
