# 🔍 HOW TO CHECK BACKEND CONSOLE LOGS

## Quick Guide - 3 Steps

### Step 1: Open Terminal in VS Code

**Look at the BOTTOM of your VS Code window**. You should see tabs like:
- PROBLEMS
- OUTPUT  
- DEBUG CONSOLE
- **TERMINAL** ← Click this one!

**Keyboard Shortcut**: Press `Ctrl + J` to open/close the bottom panel

---

### Step 2: Find the Running Backend

In the TERMINAL tab, you might see multiple terminals. Look for one that shows:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

This is your backend server running!

---

### Step 3: Trigger the Logs

Now go to your browser and:
1. **Delete** the current data file in Data Hub
2. **Upload** `test_data_sales_comprehensive.csv` again
3. **Switch back to VS Code terminal** immediately

You'll see logs appear like:
```
📂 [SCHEMA API] Looking for files in: C:\Users\navee\...
📄 [SCHEMA API] Loading file: test_data_sales_comprehensive.csv
✅ [SCHEMA API] Loaded 100 rows from test_data_sales_comprehensive.csv
📊 [SCHEMA API] Column data types:
   - Order_ID: object
   - Customer_Name: object
   - Quantity: int64           ← IMPORTANT!
   - Unit_Price: float64       ← IMPORTANT!
   - Total_Amount: float64     ← IMPORTANT!
```

---

## Alternative: Check Logs Without Terminal

If you still can't find the terminal, I can read it for you! Just:

1. Go to Data Hub in browser
2. Delete current file
3. Upload the sales CSV again
4. Wait 10 seconds
5. Tell me "done uploading"

Then I'll read the backend logs and tell you what they say!

---

## Screenshot Guide

**Where to look in VS Code:**

```
┌─────────────────────────────────────────────────┐
│  VS CODE - YOUR FILES AREA                      │
│  (code editor in the middle)                    │
│                                                  │
├─────────────────────────────────────────────────┤
│  ← CLICK HERE TO OPEN                           │
│  ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓                                │
├─────────────────────────────────────────────────┤
│ PROBLEMS | OUTPUT | DEBUG | TERMINAL ← CLICK!  │
├─────────────────────────────────────────────────┤
│                                                  │
│  Your terminal output will show here            │
│  📂 [SCHEMA API] Looking for files...           │
│  ✅ [SCHEMA API] Loaded 100 rows...             │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## Can't Find It? Try This:

### Option A: Use Keyboard
1. Press `Ctrl + J` → Opens bottom panel
2. Click "TERMINAL" tab
3. You should see the backend running!

### Option B: Menu Bar
1. Click **View** menu (top of VS Code)
2. Click **Terminal**
3. Bottom panel opens with terminal

### Option C: Let Me Help
Just tell me **"I can't find it"** and I'll:
1. Read the logs for you directly
2. Show you exactly what's happening
3. Fix any issues without you needing the terminal

---

## What to Send Me

Once you can see the terminal, just:
1. Upload the sales data
2. Copy ALL the text that appears
3. Paste it here

Or just take a screenshot and send it!

🎯 **The logs will tell us exactly why metrics aren't being detected!**
