# Tarang Receipt Intelligence — Production Deployment Guide

---

## 1. Production Architecture Overview

The platform is designed as a stateless microservice backed by local OCR inference, making it lightweight and suitable for deployment on a standard cloud virtual machine (e.g., AWS EC2 t3.medium or GCP e2-standard-2).

---

## 2. Linux Production Deployment (Ubuntu 22.04 / 24.04 LTS)

### 2.1 System Packages
```bash
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv tesseract-ocr libtesseract-dev git
```

### 2.2 Systemd Service for FastAPI
Create `/etc/systemd/system/tarang-api.service`:
```ini
[Unit]
Description=Tarang Receipt Intelligence FastAPI Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/Tarang-Receipt-Intelligence
ExecStart=/opt/Tarang-Receipt-Intelligence/.venv/bin/uvicorn app.api:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable tarang-api
sudo systemctl start tarang-api
```

---

## 3. Windows Server Deployment

1. Install Python 3.12 64-bit and Tesseract OCR 5.4.
2. In PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.api:app --host 0.0.0.0 --port 8000
```
3. Use Windows Task Scheduler or NSSM (Non-Sucking Service Manager) to run Uvicorn and Streamlit as background Windows services.
