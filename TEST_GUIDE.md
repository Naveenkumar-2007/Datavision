# 📊 Test Dataset Guide - Chart Generation Predictions

## 📁 Dataset 1: HR Comprehensive (`test_data_hr_comprehensive.csv`)

### Dataset Details
- **Rows**: 50 employees
- **Departments**: 5 (Engineering, Marketing, Sales, HR, Finance)
- **Metrics**: 7 (Salary, Performance_Rating, Years_Experience, Age, Project_Count, Training_Hours, Satisfaction_Score)
- **Dimensions**: 4 (Department, Position, Name, Employee_ID)
- **Time Column**: 1 (Hire_Date from 2009-2022)

### Expected Charts (15-18 total)

#### ✅ **NEW Advanced Charts** (All 4 will appear!)

1. **BOX PLOT** (Score: ~95) 🎯
   - **Title**: "Salary Distribution by Department"
   - **What it shows**: Min, Q1, Median, Q3, Max salary for each department
   - **Why**: Perfect data - categorical (Department) + numeric (Salary) with good variance

2. **CORRELATION MATRIX** (Score: ~90) 🎯
   - **Title**: "Metric Correlations"
   - **What it shows**: Correlations between Salary, Performance, Experience, Age, Projects, Training, Satisfaction
   - **Why**: 7 numeric columns = ideal for correlation analysis

3. **SANKEY DIAGRAM** (Score: ~85) 🎯
   - **Title**: "Department → Position Flow"
   - **What it shows**: How employees flow from departments to specific positions
   - **Why**: 2+ categorical dimensions (Department, Position)

4. **CALENDAR HEATMAP** (Score: ~80) 🎯
   - **Title**: "Hire Date Activity Calendar"
   - **What it shows**: Hiring activity by date (darker = more hires)
   - **Why**: Has datetime column (Hire_Date) + can aggregate by date

#### 📈 **Overview Page Charts** (~8 charts)
- Donut chart (Department distribution)
- Funnel chart (Position levels)
- Gauge chart (Avg Performance Rating)
- Progress bars (Department sizes)
- Data quality cards
- Metric cards (Salary, Performance, etc.)
- Sparklines (Trend over hire dates)

#### 📊 **Dashboard Page Charts** (~12-15 charts)
- Area chart (Salary trends)
- Horizontal bar (Top departments by headcount)
- Vertical bar (Salary comparison)
- Radar chart (Department metrics)
- Scatter plot (Salary vs Experience)
- Line chart (Hires over time)
- Stats card (Salary statistics)
- Top5 lists (Top performers)
- Summary cards
- **+ The 4 new advanced charts!**

---

## 📁 Dataset 2: Sales Comprehensive (`test_data_sales_comprehensive.csv`)

### Dataset Details
- **Rows**: 100 orders
- **Customers**: 20 unique
- **Products**: 40+ unique
- **Metrics**: 9 (Quantity, Unit_Price, Total_Amount, Discount_Percent, Shipping_Cost, Profit_Margin, Customer_Rating, Processing_Days)
- **Dimensions**: 7 (Customer_Name, Customer_Segment, Product_Category, Product_Name, Region, Sales_Channel)
- **Time Column**: Order_Date (Jan-May 2024)

### Expected Charts (18-20 total - Maximum variety!)

#### ✅ **NEW Advanced Charts** (All 4 GUARANTEED!)

1. **BOX PLOT** (Score: ~98) 🎯🎯
   - **Title**: "Total Amount Distribution by Product Category"
   - **What it shows**: Order value distribution across Electronics, Software, Office Supplies
   - **Why**: Perfect - 3 categories + high variance in amounts

2. **CORRELATION MATRIX** (Score: ~100) 🎯🎯🎯
   - **Title**: "Metric Correlations"
   - **What it shows**: Relationships between Quantity, Price, Amount, Discount, Shipping, Profit, Rating, Processing
   - **Why**: 9 numeric columns = MAXIMUM score!

3. **SANKEY DIAGRAM** (Score: ~95) 🎯🎯
   - **Title**: "Customer Segment → Product Category → Sales Channel Flow"
   - **What it shows**: Purchase journey flows
   - **Why**: 7 categorical dimensions = excellent flow visualization

4. **CALENDAR HEATMAP** (Score: ~90) 🎯🎯
   - **Title**: "Order Activity Calendar"
   - **What it shows**: Daily order intensity over 5 months
   - **Why**: 100 rows across 5 months = perfect temporal pattern

#### 📈 **Overview Page Charts** (~10 charts)
- Donut (Category breakdown)
- Funnel (Sales channel conversion)
- Gauge (Avg customer rating)
- Progress bars (Regional performance)
- Data quality
- Metric cards (Revenue, Orders, etc.)
- Sparklines (Revenue trends)
- Top performers list

#### 📊 **Dashboard Page Charts** (~15-18 charts)
- Area chart (Revenue over time)
- Horizontal bars (Top products)
- Vertical bars (Channel comparison)
- Radar chart (Regional metrics)
- Scatter plot (Quantity vs Profit)
- Line chart (Orders trend)
- Waterfall (Revenue build-up)
- Treemap (Product mix)
- Stacked bar (Segment by category)
- Bullet chart (Performance targets)
- Stats cards (Amount, Profit statistics)
- Top5 lists (Customers, Products)
- Heatmap (Region × Category)
- Bubble chart (Multi-dimensional)
- Distribution bars
- **+ The 4 new advanced charts!**

---

## 🎯 **Which Dataset Shows More Charts?**

### 🏆 **Winner: Sales Dataset (18-20 charts)**

**Why?**
- ✅ More rows (100 vs 50) = Better statistical power
- ✅ More dimensions (7 vs 4) = More chart variety
- ✅ More metrics (9 vs 7) = Better correlations
- ✅ Longer time range (5 months vs 14 years sparse) = Better temporal patterns
- ✅ More categories (3 product types, 4 segments, 4 regions) = More combinations

**Chart Count Breakdown:**
- Overview: ~10 charts
- Dashboard: ~15 charts
- **Total: ~25 charts** (including both pages)

---

## 📋 **How to Test**

### Step 1: Upload Dataset
```
1. Go to Data Hub
2. Click "Upload Files"
3. Select test_data_sales_comprehensive.csv (recommended first)
4. Wait for processing
```

### Step 2: View Overview Page
```
Navigate to Overview → You'll see:
- 4 KPI cards at top
- 8-10 visualization charts
- Look for the NEW charts with special styling
```

### Step 3: View Dashboard Page
```
Navigate to Dashboard → You'll see:
- 4 KPI cards
- 15-18 visualization widgets
- Interactive filters at top
- ALL 4 new chart types should appear!
```

### Step 4: Check Console
```
Open browser console (F12) → Check for:
- Chart fitness scores logged
- "NEW ADVANCED CHART TYPES" in output
- No errors in rendering
```

---

## 🔍 **Identifying the New Charts**

### Box Plot
- **Look for**: Horizontal bars with whiskers (min-max) and colored boxes (Q1-Q3)
- **Title contains**: "Distribution by..."
- **Layout**: Stacked horizontal rows

### Sankey Diagram
- **Look for**: Flowing horizontal bars between source → target
- **Title contains**: "→" arrow or  "Flow"
- **Layout**: Source names on left, target names on right

### Calendar Heatmap
- **Look for**: 7-column grid (like a calendar week)
- **Title contains**: "Activity Calendar" or "Heatmap"
- **Layout**: Small squares with dates inside

### Correlation Matrix
- **Look for**: Square grid with correlation values (-1 to +1)
- **Title**: "Metric Correlations"
- **Colors**: Red (negative) ↔ Gray (neutral) ↔ Green (positive)
- **Layout**: N×N grid where N = number of metrics

---

## 💡 **Pro Tips**

1. **Sales dataset shows MORE charts** because it has better data variety
2. **Look for scores in browser console** - backend logs fitness scores
3. **Try filtering** on Dashboard - charts update dynamically!
4. **Check both light and dark mode** - all charts are theme-aware
5. **Hover over charts** for tooltips with exact values

---

## 📊 **Expected Total Chart Count**

| Page | HR Dataset | Sales Dataset |
|------|-----------|---------------|
| Overview | 8-10 | 10-12 |
| Dashboard | 12-14 | 15-18 |
| **Total** | **20-24** | **25-30** |

🎯 **Use Sales dataset for maximum chart variety!**
