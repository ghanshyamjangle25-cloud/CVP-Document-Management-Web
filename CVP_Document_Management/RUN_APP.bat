@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
echo.
echo Other computers on the same network can open:  http://%COMPUTERNAME%:8501
echo.
python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
pause
