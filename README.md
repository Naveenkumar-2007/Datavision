# 🤖 AI Business Analyst - Complete System

Enterprise-grade AI Business Intelligence Platform powered by Groq and Advanced RAG.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file in project root:

```env
GROQ_API_KEY=your_groq_api_key_here
SENTENCE_MODEL=all-MiniLM-L6-v2
```

### 3. Start Backend API

```bash
uvicorn api.main:app --reload --port 8000
```

API will be available at: http://localhost:8000

### 4. Start Frontend UI

In a new terminal:

```bash
streamlit run ui/app.py
```

UI will be available at: http://localhost:8501

### 5. Run System Tests

In a new terminal:

```bash
python test_system.py
```

## 📁 Project Structure

```
ai_business_analyst/
├── config/
│   └── settings.py          # Configuration settings
├── core/
│   └── llm.py              # LLM & embeddings
├── ingestion/
│   ├── loader.py           # File loading
│   ├── processor.py        # Text processing
│   └── pipeline.py         # Ingestion pipeline
├── vector/
│   ├── embeddings.py       # Embedding generation
│   ├── store_faiss.py      # FAISS vector store
│   └── retriever.py        # Vector retrieval
├── graph/
│   ├── schema.py           # Schema detection
│   ├── builder.py          # Graph construction
│   └── query.py            # Graph queries
├── agents/
│   ├── state.py            # Agent state
│   ├── router.py           # Question routing
│   ├── nodes.py            # Agent nodes (RAG/Graph/Hybrid)
│   ├── workflow.py         # Main workflow
│   └── reports.py          # Report generation
├── memory/
│   └── history.py          # Chat history
├── api/
│   ├── main.py             # FastAPI app
│   ├── ingest_router.py    # File upload API
│   ├── query_router.py     # Query & dashboard API
│   └── report_router.py    # Report generation API
├── ui/
│   ├── app.py              # Streamlit main app
│   └── dashboard.py        # Dashboard components
├── storage/
│   ├── faiss/              # Vector store data
│   ├── graph/              # Knowledge graphs
│   ├── memory/             # Chat history
│   └── uploads/            # Uploaded files
├── requirements.txt         # Python dependencies
├── .env                    # Environment variables
├── test_system.py          # System tests
└── README.md               # This file
```

## 🎯 Features

✅ **Universal File Ingestion**
- PDF, Excel, CSV, JSON, TXT, Images
- Automatic schema detection
- Multi-company support

✅ **Vector Store (FAISS)**
- Semantic search with SentenceTransformers
- Fast retrieval for 1M+ documents
- Per-company data isolation

✅ **Knowledge Graph (GraphRAG)**
- Auto-detect customer, product, invoice, date
- NetworkX graph structure
- Graph-based analytics

✅ **Agentic AI System**
- Smart routing (RAG / Graph / Hybrid)
- Context-aware responses
- Multi-turn conversations

✅ **Business Analytics**
- Real-time dashboard
- Revenue trends
- Top customers & products
- Automated reports

✅ **REST API**
- FastAPI backend
- Full CRUD operations
- Swagger documentation

✅ **Web UI**
- Streamlit interface
- File upload
- Chat interface
- Interactive dashboard

## 📊 Usage

### Upload Data

1. Go to **"Upload Data"** tab
2. Select business files (CSV, Excel, PDF, etc.)
3. Click **"Process Files"**
4. Wait for processing to complete

**Example CSV format:**
```csv
customer,product,amount,date,invoice
Acme Corp,Laptop,45000,2024-12-01,INV-001
TechCo,Mouse,1500,2024-12-01,INV-002
Acme Corp,Keyboard,3000,2024-12-02,INV-003
```

### Ask Questions

**Factual Questions (RAG):**
- "What were sales this month?"
- "Show me customer information"
- "Summarize the uploaded report"

**Analytical Questions (Graph):**
- "Why did revenue drop last month?"
- "What are the trends in customer behavior?"
- "Which products correlate with high revenue?"

**Complex Questions (Hybrid):**
- "Compare Q1 and Q2 performance and explain differences"
- "Who are my best customers and what do they buy?"

### View Dashboard

Navigate to **"Dashboard"** tab to see:
- Total revenue, invoices, avg values
- Revenue over time (line chart)
- Top products (bar chart)
- Top customers (table)
- Recent transactions

### Generate Reports

Go to **"Reports"** tab:
- **Weekly Report**: Last 7 days analysis
- **Monthly Report**: Last 30 days with trends

## 🔧 API Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints

**1. Upload Files**
```http
POST /ingest/{company_id}
Content-Type: multipart/form-data

files: [file1, file2, ...]
```

**2. Ask Question**
```http
POST /query
Content-Type: application/json

{
  "question": "What is total revenue?",
  "company_id": "demo-company"
}
```

**3. Get Dashboard Data**
```http
GET /query/dashboard/{company_id}
```

**4. Generate Weekly Report**
```http
GET /report/{company_id}/weekly
```

**5. Generate Monthly Report**
```http
GET /report/{company_id}/monthly
```

### Swagger Docs
http://localhost:8000/docs

## 🧪 Testing

### Manual Testing

1. **Test File Upload:**
   - Upload a sample CSV file with business data
   - Check console for processing logs
   - Verify files appear in `storage/uploads/`

2. **Test Query:**
   - Ask: "What is total revenue?"
   - Should get answer based on uploaded data

3. **Test Dashboard:**
   - Open dashboard tab
   - Verify charts render correctly
   - Check metrics are accurate

### Automated Testing

```bash
python test_system.py
```

## 🐛 Troubleshooting

### API Not Connecting
```
Error: Cannot connect to API
```
**Solution:** Ensure backend is running:
```bash
uvicorn api.main:app --reload --port 8000
```

### No Data in Dashboard
```
Warning: No data available
```
**Solution:** 
1. Upload business files first
2. Ensure CSV/Excel has: customer, product, amount, date columns
3. Check `storage/uploads/` folder has files

### Import Errors
```
ModuleNotFoundError: No module named 'groq'
```
**Solution:**
```bash
pip install -r requirements.txt
```

### Groq API Error
```
Error: Unable to get response from AI model
```
**Solution:**
1. Check GROQ_API_KEY in `.env` file
2. Verify API key is valid
3. Check internet connection

### FAISS Index Error
```
Error: FAISS index corrupted
```
**Solution:** Delete and recreate:
```bash
rm -rf storage/faiss/*
# Re-upload files
```

## 📈 Performance Tips

**For Large Datasets:**
1. Use batch processing for embeddings
2. Consider FAISS IVF index for 1M+ documents
3. Implement pagination for dashboard queries

**For Better Accuracy:**
1. Upload clean, well-structured data
2. Use consistent column names
3. Include date information in YYYY-MM-DD format

**For Faster Responses:**
1. Limit graph snapshot to 500 nodes
2. Cache frequently asked questions
3. Use async processing for file uploads

## 🔜 Next Steps (After Evaluation)

### Phase 1: Authentication
- [ ] Add JWT token authentication
- [ ] Multi-user support
- [ ] API key management

### Phase 2: Pricing
- [ ] Stripe/Razorpay integration
- [ ] Usage tracking
- [ ] Subscription tiers

### Phase 3: Deployment
- [ ] Docker containerization
- [ ] AWS/GCP/Azure deployment
- [ ] CI/CD pipeline

### Phase 4: Advanced Features
- [ ] Email report automation
- [ ] Webhook integrations
- [ ] White-label customization
- [ ] Mobile app

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review code comments in source files
3. Test with sample data first

## 📄 License

Proprietary - All rights reserved

---

**Built with:** Python, FastAPI, Streamlit, Groq, FAISS, NetworkX, Sentence Transformers

**Version:** 1.0.0

**Last Updated:** December 2024
