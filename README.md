---
title: DataVision AI
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

<div align="center">
  <img src="frontend/public/datavision-logo.png" alt="DataVision logo" width="96" />
  <h1>DataVision AI</h1>
  <p><strong>Autonomous analytics, business intelligence, AutoML, computer vision, and team collaboration in one platform.</strong></p>
  <p>
    <a href="https://datavision-ai-datavision.hf.space">Live application</a> ·
    <a href="frontend/public/DataVision_AI_Product_User_Guide.pdf">Product user guide (PDF)</a>
  </p>
</div>

## What DataVision provides

- Interactive dashboards with slicers, KPI cards, business charts, AI explanations, exports, and themes.
- AI Analyst for grounded questions about uploaded datasets.
- AutoML, predictions, forecasts, reports, vector search, and data pipelines.
- Computer Vision for detection, classification, segmentation, pose estimation, and OCR.
- Persistent collaboration with channels, replies, reactions, pinning, and message deletion.
- Developer API keys, webhooks, usage reporting, and embed tools.

## Run locally

Requirements: Python 3.11+, Node.js 20+, and PostgreSQL for persistent production data.

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py

# Frontend (in a second terminal)
cd frontend
npm install
npm run dev
```

The frontend opens at `http://localhost:5173`.

## Configuration

Create `backend/.env` with your production settings. Do not commit secrets.

```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/datavision
GROQ_API_KEY=your_key
JWT_SECRET=a_long_random_secret
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173
```

## Deployment

Pushes to `main` run the GitHub Actions workflows in `.github/workflows/`. Configure these GitHub secrets before deployment:

- `HF_TOKEN` (Hugging Face write token)
- Optional `HF_SPACE` (defaults to `datavision-ai/Datavision`)

Set `DATABASE_URL`, `GROQ_API_KEY`, and `JWT_SECRET` in your Hugging Face Space settings. See [HUGGINGFACE_DEPLOYMENT.md](HUGGINGFACE_DEPLOYMENT.md) for the checklist.

## User guide

The updated guide is available here: [DataVision AI Product User Guide](frontend/public/DataVision_AI_Product_User_Guide.pdf).

## Validation

```bash
cd frontend
npm run build
```

```bash
cd backend
python -m py_compile main.py api/v1/endpoints/collaboration.py
```
