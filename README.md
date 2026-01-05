---
title: AI Business Analyst
sdk: docker
app_port: 7860
---

<div align="center">
  <h1>📊 DataVision AI</h1>
  <h3>The Autonomous AI Business Analyst</h3>
  <p>
    Turn raw data into executive insights in seconds.
    <br />
    <strong>AutoML • Predictive Analytics • Intelligent Reporting</strong>
  </p>
</div>

---

## 🚀 Overview

**DataVision AI** is a production-grade autonomous data analysis platform designed to replace manual data crunching. It combines state-of-the-art **AutoML** (Automated Machine Learning) with a premium React frontend to deliver a seamless "Business Analyst in a Box" experience.

### Key Features

*   **🧠 Silicon Valley Grade AutoML**: Automatically selects, trains, and tunes the best models (XGBoost, CatBoost, LightGBM, Random Forest) for your data.
*   **📊 Intelligent Dashboards**: Interactive, animated visualizations that reveal trends, outliers, and correlations automatically.
*   **🔮 Predictive Engine**: Forecast future metrics with confidence intervals and "What-If" scenario planning.
*   **📝 Automated Reporting**: Multi-page PDF/Markdown reports (Executive Summary, Anomaly Detection) generated on demand.
*   **💎 Premium UI/UX**: Dark mode by default, skeleton loaders, and smooth transitions for a top-tier user experience.

---

## 🛠️ Tech Stack

### Backend (Python/FastAPI)
*   **Framework**: FastAPI (Async high-performance API)
*   **ML Core**: Scikit-Learn, XGBoost, LightGBM, CatBoost
*   **Data Processing**: Pandas, NumPy
*   **AI/LLM**: Integration with Groq/OpenAI for natural language insights

### Frontend (TypeScript/React)
*   **Framework**: React 18, Vite
*   **Styling**: Tailwind CSS (Premium Teal/Amber Theme)
*   **Animations**: Framer Motion
*   **State**: React Query, Context API

---

## 🚦 Getting Started

### Prerequisites
*   Docker & Docker Compose (Recommended)
*   OR Python 3.11+ and Node.js 20+

### Option 1: Docker (Fastest)

Run the entire stack with a single command:

```bash
docker-compose up --build
```

Access the app at `http://localhost:5173`.

### Option 2: Manual Setup

#### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

#### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing

We include a comprehensive smoke test suite to verify the critical path (Upload -> Train -> Predict -> Report).

```bash
# Run backend smoke tests
cd backend
python smoke_test.py
```

---

## 🔑 Configuration

Create a `.env` file in the root directory (see `.env.example`):

```env
GROQ_API_KEY=your_key_here
SUPABASE_URL=your_url
SUPABASE_ANON_KEY=your_key
```

---

## 📄 License

MIT License. Built with ❤️ by the DataVision Team.
