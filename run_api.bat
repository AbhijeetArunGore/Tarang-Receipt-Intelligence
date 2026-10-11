@echo off
echo Starting Tarang Receipt Intelligence FastAPI Server on http://localhost:8000
python -m uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
