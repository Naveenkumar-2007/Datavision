"""
🧠 DATAVISION PRODUCT KNOWLEDGE BASE
====================================

This module contains comprehensive product knowledge that enables
the AI to understand and guide users through DataVision features.

Used by the LLM to:
1. Answer "how to" questions about the product
2. Guide users to the right features
3. Provide step-by-step instructions
4. Explain what DataVision is and its capabilities
"""


DATAVISION_PRODUCT_KNOWLEDGE = """
## 🚀 DataVision AI - Complete Product Knowledge Base

### WHAT IS DATAVISION?

**DataVision AI** is an enterprise-grade, AI-powered data analytics and machine learning platform that enables users to:
- Upload and analyze data without coding
- Train production-quality machine learning models in minutes
- Get AI-powered insights from business data
- Create automated reports and visualizations
- Make predictions using trained models

**Key Differentiators:**
- 🧠 **No-Code ML**: Train models without programming
- ⚡ **Fast Training**: From data to production model in 30 seconds to 10 minutes
- 🎯 **Multi-Mode AI**: Traditional ML, NLP (Natural Language Processing), and Deep Learning
- 📊 **Smart Analytics**: AI-generated charts and insights
- 🔒 **Per-User Isolation**: Each user's data and models are completely private

### ML MODES EXPLAINED:

1. **Traditional ML** 🤖
   - Best for: Structured/tabular data (sales, customers, transactions)
   - Algorithms: Random Forest, XGBoost, LightGBM, SVM, Neural Networks
   - Use when: Your data has clear columns like "price", "age", "category"

2. **NLP (Natural Language Processing)** 📝
   - Best for: Text data (reviews, emails, documents, social media)
   - Algorithms: TF-IDF, Word2Vec, BERT, Sentiment Analysis
   - Use when: You want to analyze or classify text content

3. **Deep Learning** 🧠
   - Best for: Complex patterns, large datasets, sequential data
   - Architectures: MLP, RNN, LSTM, GRU, Transformers
   - Use when: You have 10,000+ rows or need maximum accuracy

### CORE FEATURES:

1. **DATA HUB** (Upload & Manage Data) 📂
   - Upload CSV, Excel (.xlsx, .xls), JSON files (max 50MB)
   - View data preview with first 100 rows
   - See column statistics and data types
   - Check data quality scores (A-F grades)
   - Auto-detect date, numeric, and categorical columns
   - **Navigation**: Click "Data Hub" in the sidebar

2. **ANALYST CHAT** (AI-Powered Data Q&A) 💬
   - Ask questions in natural language
   - Get charts, insights, and analysis automatically
   - Three analysis modes:
     - ⚡ Speed Mode: Fast answers, simple queries
     - 🎯 Balanced Mode: Best accuracy/speed trade-off (DEFAULT)
     - 🔬 Precision Mode: Most accurate, complex analysis
   - Example questions:
     - "What are my total sales by region?"
     - "Show me a trend of revenue over time"
     - "Which products have the highest margins?"
   - **Navigation**: Click "Chat" in the sidebar

3. **AUTOML** (Train Machine Learning Models) 🤖
   - Upload data → Select target column → Click Train
   - Automatically tests 20+ algorithms and picks the best
   - Three ML modes:
     - **Traditional ML**: For tabular/structured data
     - **NLP**: For text classification/analysis
     - **Deep Learning**: For complex patterns and large data
   - Two training speeds:
     - **Fast Mode**: 7 algorithms, ~30-60 seconds
     - **Ultra Mode**: 20+ algorithms, ~2-10 minutes (maximum accuracy)
   - Supported tasks:
     - **Classification**: Predict categories (Yes/No, A/B/C, spam/not spam)
     - **Regression**: Predict numbers (price, sales, scores)
   - **Navigation**: Click "ML Predictions" in the sidebar

4. **ML PREDICTIONS** (Use Trained Models) 🔮
   - View all your trained models with metrics
   - **Playground**: Make single predictions by entering values
   - **Batch Predictions**: Upload new data for bulk predictions
   - Export predictions as CSV
   - View feature importance and model insights
   - Compare models from different training runs
   - **Navigation**: Click "ML Predictions" in the sidebar

5. **CLUSTERING** (Unsupervised Learning) 🎯
   - Find natural groups in your data
   - Perfect for customer segmentation
   - Algorithms available:
     - K-Means (most common, fast)
     - DBSCAN (density-based, finds outliers)
     - Hierarchical (creates tree of clusters)
     - GMM (Gaussian Mixture, soft clustering)
     - Spectral (graph-based)
   - Auto-detects optimal number of clusters
   - **Navigation**: Click "Clustering" in the sidebar

6. **DASHBOARD** (AI-Generated Visualizations) 📊
   - Automatic chart recommendations based on your data
   - Interactive visualizations (hover, zoom, filter)
   - KPI cards showing key metrics
   - Export as PNG, PDF, or PPTX
   - **Navigation**: Click "Dashboard" in the sidebar

7. **REPORTS** (Automated Reports) 📋
   - Generate PDF/Markdown reports automatically
   - Report types:
     - Executive Summary
     - Data Quality Report
     - ML Model Performance Report
     - Full Analysis Report
   - Schedule automated reports (daily/weekly)
   - **Navigation**: Click "Reports" in the sidebar

8. **FORECASTING** (Time Series Predictions) 📈
   - Predict future values (sales, demand, prices)
   - Automatic trend detection
   - Seasonality analysis
   - Multiple algorithms: ARIMA, Prophet, LSTM
   - Confidence intervals for predictions

### COMMON USER QUESTIONS AND ANSWERS:

**Q: "What is DataVision?"**
A: DataVision AI is a no-code data analytics and machine learning platform. You can upload data, train ML models, make predictions, create visualizations, and generate reports - all without writing code. It supports Traditional ML, NLP, and Deep Learning.

**Q: "How do I upload data?"**
A: Go to **Data Hub** → Click the upload area or drag & drop your CSV/Excel/JSON file. Files are automatically processed and you'll see a preview immediately.

**Q: "How do I train a machine learning model?"**
A: 
1. Go to **ML Predictions** (click in sidebar)
2. Select your uploaded file
3. Choose the column you want to predict (target)
4. Select ML mode (Traditional/NLP/Deep Learning)
5. Click **"Train Model"**
6. Wait for training to complete (30 seconds - 10 minutes)
7. View results: accuracy, charts, feature importance

**Q: "What file formats are supported?"**
A: CSV (.csv), Excel (.xlsx, .xls), and JSON files up to 50MB.

**Q: "How do I make predictions with my trained model?"**
A: 
1. Go to **ML Predictions** (click in sidebar)
2. Click the **Playground** tab
3. Enter values for each feature
4. Click **Predict** to get the result
5. For bulk predictions, use the **Batch** tab and upload a CSV

**Q: "How do I segment customers?"**
A: 
1. Go to **Clustering** (click in sidebar)
2. Select your customer data file
3. Choose an algorithm (K-Means recommended)
4. Click **Run Clustering**
5. View the segments and insights
6. Download the results with cluster labels

**Q: "How do I export results?"**
A: Click the **Download** button on any chart or report. Available formats: CSV, PNG, PDF, PPTX.

**Q: "What's the difference between Fast and Ultra training mode?"**
A: 
- **Fast Mode**: Tests 7 top algorithms quickly (~30-60 seconds). Good for quick experiments.
- **Ultra Mode**: Tests 20+ algorithms with hyperparameter tuning (~2-10 minutes). Best for production models with maximum accuracy.

**Q: "When should I use NLP mode?"**
A: Use NLP mode when your data contains text you want to analyze or classify. Examples:
- Sentiment analysis of reviews
- Email/ticket classification
- Spam detection
- Document categorization

**Q: "When should I use Deep Learning mode?"**
A: Use Deep Learning when:
- You have 10,000+ rows of data
- Traditional ML accuracy is not satisfactory
- Your data has complex patterns
- You're working with sequential or time-series data

**Q: "Why is my model accuracy low?"**
A: Common reasons and solutions:
1. **Not enough data**: Aim for 500+ rows, ideally 5000+
2. **Missing values in target**: Clean your data before training
3. **Too many categories**: Consider grouping similar categories
4. **Irrelevant features**: Remove columns that don't relate to the prediction
5. **Class imbalance**: Use Ultra mode which handles imbalanced data better

**Q: "How do I ask better questions in Chat?"**
A: Be specific! Instead of "show me data", try:
- "What are total sales by region?"
- "Show monthly revenue trend for 2024"
- "Which products have the highest profit margin?"
- "Compare sales between Q1 and Q2"
- "What is the average order value by customer segment?"

**Q: "How do I improve model accuracy?"**
A: 
1. Use **Ultra Mode** for more thorough training
2. Try **Deep Learning** mode for complex patterns
3. Clean your data (remove duplicates, handle missing values)
4. Train on more data (more rows = better learning)
5. Check **Feature Importance** and remove irrelevant columns
6. Use **Multi-Mode** training to combine Traditional ML + NLP + Deep Learning

### ML METRICS EXPLAINED:

- **Accuracy**: Percentage of correct predictions (higher is better)
- **Precision**: Of positive predictions, how many were correct?
- **Recall**: Of actual positives, how many did we catch?
- **F1 Score**: Balance between precision and recall
- **AUC-ROC**: Model's ability to distinguish between classes
- **R² Score**: For regression - how well model explains variance
- **MAE/RMSE**: For regression - average prediction error

### WHAT I CAN HELP WITH:

1. **DATA ANALYSIS** - When you ask about your uploaded data
   - "What are the top 10 customers by revenue?"
   - "Show me trends over time"
   - "Calculate average order value"
   - "What's the distribution of sales by region?"

2. **PRODUCT GUIDANCE** - When you ask how to use features
   - "How do I train a model?"
   - "Where do I upload files?"
   - "How to export predictions?"
   - "What's the difference between ML modes?"

3. **ML RECOMMENDATIONS** - When you need ML advice
   - "Should I use classification or regression?"
   - "What algorithm is best for my data?"
   - "How can I improve accuracy?"
   - "When should I use Deep Learning?"

4. **TECHNICAL SUPPORT** - When you have issues
   - "Why is training taking so long?"
   - "Why can't I see my charts?"
   - "How do I fix low accuracy?"
"""


def get_product_knowledge() -> str:
    """Get the product knowledge base string."""
    return DATAVISION_PRODUCT_KNOWLEDGE


def is_product_question(query: str) -> bool:
    """
    Detect if the query is asking about DataVision features
    rather than about the user's data.
    """
    product_keywords = [
        # What is questions
        "what is datavision", "what is this", "what does this do",
        "what can you do", "what are your capabilities", "what features",
        "tell me about datavision", "explain datavision", "describe datavision",
        
        # How-to questions
        "how do i", "how to", "how can i",
        "where do i", "where is", "where can i",
        "what is the", "what's the",
        
        # Feature names
        "data hub", "datahub", "automl", "auto ml", "auto-ml",
        "predictions", "prediction page", "clustering",
        "dashboard", "reports", "settings", "playground",
        "ml predictions", "deep learning", "nlp", "traditional ml",
        
        # Actions
        "upload", "train", "predict", "export", "download",
        "segment", "cluster", "analyze", "forecast",
        
        # Navigation
        "find", "access", "navigate", "go to", "open",
        
        # Help
        "help", "tutorial", "guide", "instructions",
        "documentation", "docs", "getting started",
        
        # Product-specific
        "datavision", "this app", "this tool", "the system",
        "your feature", "your product", "this platform",
        "this application", "your capabilities",
        
        # ML concepts (when asking generally, not about their data)
        "what is classification", "what is regression",
        "what is machine learning", "what is deep learning",
        "what is nlp", "what is clustering",
        "difference between", "when should i use",
        "how does ml work", "what algorithm",
        "improve accuracy", "fix accuracy", "better model"
    ]
    
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in product_keywords)


def get_relevant_product_help(query: str) -> str:
    """
    Get specific product help based on the query topic.
    Returns a focused response rather than the full knowledge base.
    """
    query_lower = query.lower()
    
    # What is DataVision
    if any(phrase in query_lower for phrase in ["what is datavision", "what is this", "tell me about datavision", 
                                                   "what can you do", "what does this do", "your capabilities"]):
        return """
🚀 **What is DataVision AI?**

DataVision is an enterprise-grade, AI-powered data analytics and machine learning platform that enables you to:

- 📂 **Upload Data**: CSV, Excel, JSON files up to 50MB
- 💬 **Ask Questions**: Natural language queries about your data
- 🤖 **Train ML Models**: No-code machine learning (Traditional ML, NLP, Deep Learning)
- 🔮 **Make Predictions**: Use trained models on new data
- 📊 **Create Charts**: AI-generated visualizations
- 📋 **Generate Reports**: Automated PDF/Markdown reports
- 🎯 **Cluster Data**: Customer segmentation and grouping

**Getting Started:**
1. Upload your data in **Data Hub**
2. Ask questions in **Chat** or train a model in **ML Predictions**
3. View insights in **Dashboard**
"""
    
    # Upload/Data questions
    if any(word in query_lower for word in ["upload", "file", "data hub", "import"]):
        return """
📂 **Uploading Data:**
1. Go to **Data Hub** (click in sidebar)
2. Drag & drop your file or click to browse
3. Supported formats: CSV, Excel (.xlsx, .xls), JSON
4. Max file size: 50MB
5. Data is automatically processed and previewed
"""
    
    # Training questions
    if any(word in query_lower for word in ["train", "automl", "machine learning"]):
        return """
🤖 **Training ML Models:**
1. Go to **ML Predictions** (click in sidebar)
2. Select your uploaded file
3. Choose the target column (what to predict)
4. Select ML mode:
   - **Traditional ML**: Best for tabular data
   - **NLP**: Best for text data
   - **Deep Learning**: Best for complex patterns
5. Click **Train Model**
6. Wait for training (30s - 10min)

**Tips:**
- Use **Ultra Mode** for maximum accuracy
- Ensure target column has no missing values
- Aim for 500+ rows of data
"""

    # NLP questions
    if any(word in query_lower for word in ["nlp", "text", "natural language", "sentiment"]):
        return """
📝 **NLP (Natural Language Processing):**

Use NLP mode when your data contains text you want to analyze or classify:
- **Sentiment Analysis**: Analyze customer reviews, feedback
- **Text Classification**: Categorize emails, tickets, documents
- **Spam Detection**: Identify spam vs legitimate content

**How to use:**
1. Go to **ML Predictions**
2. Select file with text column
3. Choose **NLP** mode
4. Select your text column
5. Train the model

**Algorithms**: TF-IDF, Word2Vec, BERT, FastText, and more
"""

    # Deep Learning questions
    if any(word in query_lower for word in ["deep learning", "neural network", "lstm", "rnn", "ann"]):
        return """
🧠 **Deep Learning:**

Use Deep Learning for complex patterns and large datasets:
- Best when you have **10,000+ rows**
- Captures non-linear relationships
- Great for sequential/time-series data

**Available Architectures:**
- MLP (Multi-Layer Perceptron)
- RNN (Recurrent Neural Network)
- LSTM (Long Short-Term Memory)
- GRU (Gated Recurrent Unit)
- Transformers

**How to use:**
1. Go to **ML Predictions**
2. Select file
3. Choose **Deep Learning** mode
4. Select architecture (or use Auto)
5. Train the model
"""
    
    # Prediction questions
    if any(word in query_lower for word in ["predict", "inference", "playground"]):
        return """
🔮 **Making Predictions:**
1. Go to **ML Predictions** (click in sidebar)
2. Click the **Playground** tab
3. Enter values for each feature
4. Click **Predict** to get the result

**For Batch Predictions:**
1. Click the **Batch** tab
2. Upload a CSV with new data
3. Download predictions with results
"""
    
    # Clustering questions
    if any(word in query_lower for word in ["cluster", "segment", "group", "unsupervised"]):
        return """
🎯 **Clustering / Segmentation:**
1. Go to **Clustering** (click in sidebar)
2. Select your data file
3. Choose algorithm:
   - **K-Means**: Most common, fast
   - **DBSCAN**: Finds outliers
   - **Hierarchical**: Creates tree structure
   - **GMM**: Soft clustering
4. Click **Run Clustering**
5. View segments and download results

**Best for:** Customer segmentation, product grouping, pattern discovery
"""
    
    # Chart/Dashboard questions
    if any(word in query_lower for word in ["chart", "graph", "visual", "dashboard"]):
        return """
📊 **Creating Visualizations:**
1. Go to **Dashboard** for AI-generated charts
2. Or ask me in Chat: "Show me a bar chart of sales by region"
3. Click **Download** on any chart to export as PNG

**Chart Types:** Bar, Line, Pie, Scatter, Heatmap, Box Plot, and more
"""
    
    # Export questions
    if any(word in query_lower for word in ["export", "download", "save"]):
        return """
📥 **Exporting Data:**
- **Charts**: Click Download button → PNG or PDF
- **Predictions**: ML Predictions page → Download CSV
- **Reports**: Reports page → Generate → Download PDF
- **Raw Data**: Data Hub → Export button
"""
    
    # Accuracy questions
    if any(word in query_lower for word in ["accuracy", "improve", "better model", "low score"]):
        return """
📈 **Improving Model Accuracy:**

1. **More Data**: Aim for 500+ rows, ideally 5000+
2. **Clean Data**: Remove duplicates, handle missing values
3. **Ultra Mode**: Tests 20+ algorithms for best results
4. **Deep Learning**: Try for complex patterns
5. **Multi-Mode**: Combine Traditional + NLP + Deep Learning
6. **Feature Engineering**: Remove irrelevant columns

**Common Issues:**
- Target column has missing values
- Too many categories (try grouping)
- Data is too imbalanced (one class dominates)
"""
    
    # Default - return full knowledge
    return DATAVISION_PRODUCT_KNOWLEDGE
