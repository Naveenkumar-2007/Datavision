---
title: AI Business Analyst
emoji: 📊
colorFrom: orange
colorTo: red
sdk: docker
pinned: false
---

# AI Business Analyst - Enterprise Edition

An intelligent business analytics platform powered by AI.

## Features
- 🤖 AI-powered chat analyst with RAG & GraphRAG
- 📊 Interactive dashboards and visualizations
- 📈 Automated report generation
- 📁 File upload and analysis
- 🔔 Smart email notifications

## Tech Stack
- **Frontend**: React + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python
- **Database**: Supabase (PostgreSQL)
- **AI**: Groq (Llama models) + OpenAI
- **Email**: Resend

## Usage
1. Sign up / Log in
2. Upload your business data (CSV, Excel)
3. Ask questions to the AI analyst
4. Generate automated reports
5. View interactive dashboards

## Environment Variables Required
Configure these in Space Settings → Variables and secrets:
- SUPABASE_URL
- SUPABASE_KEY
- SUPABASE_JWT_SECRET
- DATABASE_URL
- GROQ_API_KEY
- OPENAI_API_KEY (optional)
- RESEND_API_KEY
- FRONTEND_URL
- CORS_ORIGINS
