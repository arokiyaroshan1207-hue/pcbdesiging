# AI-Powered PCB Defect Detection System

An industrial-grade computer vision application designed for automated Printed Circuit Board (PCB) quality assurance and defect inspection using YOLOv8, FastAPI, and React.

---

## 📌 Project Overview
- **Objective:** Automated defect detection on printed circuit boards via image upload or real-time webcam feed.
- **AI Core:** YOLOv8 deep learning model (`best.pt`) detecting 6 standard defect classes:
  - `0: open`
  - `1: short`
  - `2: mouse_bite`
  - `3: spur`
  - `4: spurious_copper`
  - `5: missing_hole`
- **Output:** Annotated defect bounding boxes, confidence metrics, defect frequency breakdown, inspection summaries, and downloadable PDF inspection reports.

---

## 🛠️ Architecture & Tech Stack

```
[ Frontend: React + Vite + Axios + React Webcam + Lucide Icons ]
                           │
                 REST API (HTTP/JSON + multipart)
                           ▼
[ Backend: FastAPI + Uvicorn + Pydantic + python-multipart ]
                           │
      ┌────────────────────┴────────────────────┐
      ▼                                         ▼
[ YOLOv8 Inference Engine ]           [ PDF Report Generator ]
(Ultralytics + PyTorch + OpenCV)             (ReportLab)
```

- **Frontend:** React 18, Vite, Axios, React Webcam, Lucide React icons, Vanilla CSS.
- **Backend:** FastAPI, Uvicorn, Pydantic, python-multipart, ReportLab.
- **AI & Vision:** Ultralytics YOLOv8, PyTorch, OpenCV, Pillow.

---

## 📁 Project Structure

```
PCB-DEFECT-DETECTION/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entrypoint, CORS & error handling
│   │   ├── routes/              # Detection, health, and report endpoints
│   │   ├── services/            # YOLOv8 inference & PDF generation services
│   │   └── schemas/             # Pydantic models for request/response validation
│   ├── models/                  # YOLOv8 weights (best.pt)
│   ├── sample_images/           # Sample test PCB images
│   ├── uploads/                 # Temporary input image storage
│   ├── results/                 # Annotated detection output images
│   └── requirements.txt         # Python dependencies
├── frontend/
│   ├── public/                  # Static assets & icons
│   ├── src/
│   │   ├── components/          # Reusable UI cards, uploaders, webcam modals
│   │   ├── pages/               # Dashboard, Inspection, Results, Reports
│   │   ├── services/            # Axios API client
│   │   └── styles/              # Design system tokens and styles
│   ├── package.json
│   ├── vite.config.js
│   └── .env                     # VITE_API_BASE_URL
├── .gitignore
└── README.md
```

---

## 🚀 Development Phases

- **Phase 1 (Completed):** Project structure initialization, environment audit, model weight & sample discovery.
- **Phase 2 (Completed):** FastAPI backend setup, CORS configuration, image validation service, detector service isolation, and `/api/health` endpoint.
- **Phase 3 (Completed):** YOLOv8 model loading, inference service, metadata class verification, and unit tests.
- **Phase 4 (Completed):** React frontend with Vite, design system tokens, and industrial inspection dashboard.
- **Phase 5 (Completed):** Image upload (drag & drop + webcam) and `/api/detect` integration.
- **Phase 6 (Completed):** Annotated image display, inspection metrics, and downloadable PDF reports.
- **Phase 7 (Completed):** End-to-end integration testing, validation, and documentation.

---

## 🌐 Production Deployment Guide

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "feat: complete PCB Defect Detection System with deployment configuration"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```

### 2. Deploy Backend on Render (Web Service)
1. In the [Render Dashboard](https://dashboard.render.com), click **New +** → **Web Service** and connect your GitHub repository.
2. Configure settings:
   - **Root Directory:** `backend`
   - **Environment:** `Python 3`
   - **Build Command:**
     ```bash
     pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
     ```
   - **Plan:** Free
3. Add **Environment Variables**:
   - `PYTHON_VERSION`: `3.11.9`
   - `ALLOWED_ORIGINS`: `https://<your-vercel-app-name>.vercel.app`
4. Deploy the service and copy your public Render URL (e.g., `https://pcb-defect-detection-api.onrender.com`).

### 3. Deploy Frontend on Vercel
1. In the [Vercel Dashboard](https://vercel.com/dashboard), click **Add New...** → **Project** and import your GitHub repository.
2. Configure settings:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
3. Add **Environment Variables**:
   - `VITE_API_BASE_URL`: `https://<your-render-service-name>.onrender.com/api`
4. Click **Deploy**. Vercel will build and host the responsive inspection dashboard at `https://<your-app>.vercel.app`.



