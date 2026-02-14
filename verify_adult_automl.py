"""
==========================================================================
 ADULT.CSV - AutoML vs Manual Verification
 Exact replication of DataVision AutoML pipeline
 Dataset: adult.csv (32561 rows, 15 columns, target: income)
==========================================================================
 
 RUN:  python verify_adult_automl.py
 
 Then compare the output metrics with your AutoML results.
==========================================================================
"""

import numpy as np
import pandas as pd
import pickle
import warnings
import os
from datetime import datetime

warnings.filterwarnings('ignore')

# ──────────────────────────────────────────────────────────────
# STEP 1: LOAD DATA
# ──────────────────────────────────────────────────────────────
print("=" * 60)
print("  STEP 1: LOADING DATASET")
print("=" * 60)

# Try multiple paths
dataset_paths = [
    r"backend\storage\users\d4f48123-b254-47f8-a335-6d142b3f1a72\files\adult.csv",
    r"adult.csv",
    r"backend\uploads\adult.csv",
]

df = None
for p in dataset_paths:
    if os.path.exists(p):
        df = pd.read_csv(p)
        print(f"  Loaded from: {p}")
        break

if df is None:
    print("  ❌ adult.csv not found! Place it in same folder or update path above.")
    exit(1)

print(f"  Shape: {df.shape[0]} rows × {df.shape[1]} columns")
print(f"  Columns: {list(df.columns)}")

# Target
target_col = 'income'
print(f"  Target: {target_col}")
print(f"  Target distribution: {df[target_col].value_counts().to_dict()}")

# ──────────────────────────────────────────────────────────────
# STEP 2: DATA CLEANING (ProductionDataCleaner.clean)
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  STEP 2: DATA CLEANING [Same as AutoML Phase 1]")
print("=" * 60)

from sklearn.preprocessing import LabelEncoder, RobustScaler
from sklearn.feature_selection import VarianceThreshold
from sklearn.model_selection import train_test_split
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.impute import KNNImputer
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    classification_report, confusion_matrix
)

original_shape = df.shape
df = df.copy()

# STEP 0: Remove useless columns (IDs, URLs, indices)
useless_patterns = [
    'unnamed', 'index', '_id', 'id_', 'guid', 'uuid', 'url', 'link', 'href',
    'path', 'filepath', 'file_path', 'image_url', 'img_url', 'photo_url'
]
useless_cols = []
for col in df.columns:
    col_lower = col.lower().strip()
    if any(pat in col_lower for pat in useless_patterns):
        useless_cols.append(col)
    elif df[col].dtype == 'object':
        unique_ratio = df[col].nunique() / len(df) if len(df) > 0 else 0
        if unique_ratio > 0.9:
            sample_vals = df[col].dropna().head(5).astype(str)
            if any('http' in str(v).lower() or 'www.' in str(v).lower() for v in sample_vals):
                useless_cols.append(col)
            elif sample_vals.str.match(r'^\d+$').all():
                useless_cols.append(col)

if target_col in useless_cols:
    useless_cols.remove(target_col)
if useless_cols:
    print(f"  🗑️  Removing useless columns: {useless_cols}")
    df = df.drop(columns=useless_cols, errors='ignore')

# Step 1: Remove duplicates
n_dups = df.duplicated().sum()
if n_dups > 0:
    df = df.drop_duplicates()
    print(f"  ✅ Removed {n_dups} duplicate rows")
else:
    print(f"  ✅ No duplicate rows")

# Step 2: Strip whitespace from all string columns
for col in df.columns:
    if df[col].dtype == object:
        try:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace(['nan', 'NaN', 'None', 'null', ''], np.nan)
        except:
            pass
print(f"  ✅ Stripped whitespace and cleaned strings")

# Step 3: Smart type conversion (detect hidden numerics in strings)
def parse_value_with_units(val):
    if pd.isna(val):
        return np.nan
    val = str(val).strip().lower()
    if val in ['varies with device', 'varies', 'free', 'nan', '', 'n/a']:
        return np.nan
    val = val.replace('$', '').replace('€', '').replace('£', '')
    val = val.replace('+', '').replace('%', '').replace(',', '')
    multiplier = 1
    if val.endswith('m'):
        val = val[:-1]; multiplier = 1e6
    elif val.endswith('k'):
        val = val[:-1]; multiplier = 1e3
    elif val.endswith('b'):
        val = val[:-1]; multiplier = 1e9
    try:
        return float(val) * multiplier
    except:
        return np.nan

converted_count = 0
for col in df.columns:
    if df[col].dtype != object:
        continue
    sample = df[col].dropna().head(100)
    if len(sample) == 0:
        continue
    parsed_sample = [parse_value_with_units(v) for v in sample]
    valid_count = sum(1 for v in parsed_sample if pd.notna(v))
    if valid_count / len(sample) > 0.6:
        df[col] = df[col].apply(parse_value_with_units)
        converted_count += 1
        print(f"  ✅ Auto-converted '{col}' to numeric")
if converted_count == 0:
    print(f"  ✅ No hidden numeric columns found")

# Step 4: Handle missing values
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
if target_col in numeric_cols:
    numeric_cols = [c for c in numeric_cols if c != target_col]

categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
if target_col in categorical_cols:
    categorical_cols = [c for c in categorical_cols if c != target_col]

# KNN imputation for numeric
missing_numeric = [c for c in numeric_cols if df[c].isna().any()]
if missing_numeric:
    try:
        imputer = KNNImputer(n_neighbors=5, weights='distance')
        df[numeric_cols] = imputer.fit_transform(df[numeric_cols])
        print(f"  ✅ KNN imputed {len(missing_numeric)} numeric columns")
    except:
        for col in missing_numeric:
            fill_val = df[col].median()
            df[col] = df[col].fillna(fill_val if pd.notna(fill_val) else 0)
        print(f"  ✅ Median imputed {len(missing_numeric)} numeric columns")
else:
    print(f"  ✅ No missing numeric values")

# Fill categorical with mode
for col in categorical_cols:
    if df[col].isna().sum() > 0:
        mode_vals = df[col].mode()
        fill_val = mode_vals.iloc[0] if len(mode_vals) > 0 else '_MISSING_'
        df[col] = df[col].fillna(fill_val)

missing_total = df.isna().sum().sum()
print(f"  ✅ Handled missing values (remaining: {missing_total})")

# Step 5: Handle infinite values
for col in numeric_cols:
    try:
        inf_count = np.isinf(df[col]).sum()
        if inf_count > 0:
            median_val = df[col].replace([np.inf, -np.inf], np.nan).median()
            df[col] = df[col].replace([np.inf, -np.inf], median_val if pd.notna(median_val) else 0)
    except:
        pass
print(f"  ✅ Handled infinite values")

# Step 6: Remove constant columns
constant_cols = []
for col in df.columns:
    if col == target_col:
        continue
    try:
        if df[col].nunique() <= 1:
            constant_cols.append(col)
    except:
        pass
if constant_cols:
    df = df.drop(columns=constant_cols)
    print(f"  ✅ Removed {len(constant_cols)} constant columns: {constant_cols}")
else:
    print(f"  ✅ No constant columns")

# Step 7: IsolationForest outlier detection
numeric_cols = [c for c in numeric_cols if c in df.columns]
if len(numeric_cols) > 0 and len(df) >= 100:
    try:
        data = df[numeric_cols].fillna(0).values
        iso = IsolationForest(contamination=0.05, random_state=42, n_jobs=-1)
        outlier_labels = iso.fit_predict(data)
        n_outliers = (outlier_labels == -1).sum()
        if n_outliers > 0 and n_outliers < len(df) * 0.3:
            print(f"  ✅ IsolationForest detected {n_outliers} outliers ({n_outliers/len(df)*100:.1f}%)")
    except:
        pass

# Step 8: IQR-based outlier capping
for col in df.select_dtypes(include=[np.number]).columns:
    if col == target_col:
        continue
    try:
        Q1 = df[col].quantile(0.01)
        Q3 = df[col].quantile(0.99)
        iqr_q1 = df[col].quantile(0.25)
        iqr_q3 = df[col].quantile(0.75)
        iqr = iqr_q3 - iqr_q1
        iqr_lower = iqr_q1 - 3 * iqr
        iqr_upper = iqr_q3 + 3 * iqr
        final_lower = max(Q1, iqr_lower) if pd.notna(iqr_lower) else Q1
        final_upper = min(Q3, iqr_upper) if pd.notna(iqr_upper) else Q3
        df[col] = df[col].clip(lower=final_lower, upper=final_upper)
    except:
        pass
print(f"  ✅ Capped outliers using Percentile + IQR method")

# Step 9: Final cleanup
for col in df.select_dtypes(include=[np.number]).columns:
    if col != target_col and df[col].isna().any():
        df[col] = df[col].fillna(0)

print(f"  📊 Result: {original_shape} → {df.shape}")

# Drop NaN targets
target_nan = df[target_col].isna().sum()
if target_nan > 0:
    df = df.dropna(subset=[target_col])
    print(f"  ⚠️  Dropped {target_nan} rows with missing target")

# ──────────────────────────────────────────────────────────────
# STEP 3: DETECT TASK TYPE & ENCODE TARGET
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  STEP 3: TASK DETECTION & TARGET ENCODING")
print("=" * 60)

y_temp = df[target_col]
if y_temp.dtype == 'object' or (y_temp.dtype in ['int64', 'float64'] and y_temp.nunique() <= 20):
    task_type = 'classification'
else:
    task_type = 'regression'

print(f"  🔍 Task Type: {task_type}")

# Encode target for classification (CRITICAL - same as automl_engine line ~3322)
target_encoder = None
if task_type == 'classification':
    target_encoder = LabelEncoder()
    df[target_col] = target_encoder.fit_transform(df[target_col].astype(str))
    n_classes = len(target_encoder.classes_)
    print(f"  🏷️  Target encoded: {list(target_encoder.classes_)} → {list(range(n_classes))}")

# ──────────────────────────────────────────────────────────────
# STEP 4: FEATURE ENGINEERING (ProductionFeatureEngineer.fit_transform)
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  STEP 4: FEATURE ENGINEERING [Same as AutoML Phase 2]")
print("=" * 60)

df_feat = df.copy()

# Separate target
y = df_feat[target_col].values
original_columns = [c for c in df_feat.columns if c != target_col]
df_feat = df_feat.drop(columns=[target_col])

feature_parts = []
feature_names = []
encoders = {}
transformers = {}

# ───── Detect column types ─────
numeric_cols = []
categorical_cols = []
text_cols = []
datetime_cols = []

for col in df_feat.columns:
    if pd.api.types.is_datetime64_any_dtype(df_feat[col]):
        datetime_cols.append(col)
        continue
    if pd.api.types.is_numeric_dtype(df_feat[col]):
        try:
            _ = df_feat[col].astype(float).values
            numeric_cols.append(col)
        except:
            categorical_cols.append(col)
        continue

    # Object/string columns
    try:
        series = df_feat[col].astype(str)
        nunique = series.nunique()
        avg_len = series.str.len().mean()
        unique_ratio = nunique / len(df_feat) if len(df_feat) > 0 else 0

        # Date check
        col_lower = col.lower()
        is_date_like = any(kw in col_lower for kw in ['date', 'time', 'year', 'month', 'day', 'created', 'updated'])
        if is_date_like:
            try:
                parsed = pd.to_datetime(df_feat[col], errors='coerce')
                if parsed.notna().sum() > len(df_feat) * 0.5:
                    datetime_cols.append(col)
                    continue
            except:
                pass

        # Text detection
        text_keywords = ['description', 'text', 'comment', 'review', 'content', 'body', 'message',
                        'title', 'summary', 'feedback', 'note', 'detail', 'caption', 'headline',
                        'tweet', 'sentence', 'post', 'question', 'answer', 'query', 'phrase']
        has_text_name = any(word in col_lower for word in text_keywords)
        sample_text = df_feat[col].dropna().head(10).astype(str)
        has_sentence_pattern = any(' ' in str(t) and len(str(t)) > 10 for t in sample_text)

        is_real_text = (
            (avg_len > 20 and unique_ratio > 0.3) or
            (avg_len > 30 and unique_ratio > 0.1) or
            (avg_len > 50) or
            (has_text_name and avg_len > 10) or
            (has_sentence_pattern and avg_len > 15)
        )
        if is_real_text:
            text_cols.append(col)
            print(f"  [TEXT] Detected: {col} (avg_len={avg_len:.1f}, unique_ratio={unique_ratio:.2f})")
        else:
            categorical_cols.append(col)
    except:
        categorical_cols.append(col)

print(f"  📊 Columns: {len(numeric_cols)} numeric, {len(categorical_cols)} categorical, {len(text_cols)} text, {len(datetime_cols)} datetime")
print(f"     Numeric: {numeric_cols}")
print(f"     Categorical: {categorical_cols}")
print(f"     Text: {text_cols}")

# ───── NUMERIC FEATURES ─────
if numeric_cols:
    numeric_data = df_feat[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

    # Log transform skewed features
    log_transformed = []
    for col in numeric_cols:
        col_data = numeric_data[col]
        if col_data.min() >= 0:
            skewness = col_data.skew()
            if abs(skewness) > 2:
                numeric_data[col] = np.log1p(col_data)
                log_transformed.append(col)
    if log_transformed:
        print(f"  ✅ Log-transformed {len(log_transformed)} skewed features: {log_transformed}")

    numeric_values = numeric_data.values
    scaler = RobustScaler()
    numeric_scaled = scaler.fit_transform(numeric_values)
    numeric_scaled = np.nan_to_num(numeric_scaled, nan=0.0, posinf=0.0, neginf=0.0)

    transformers['numeric_scaler'] = scaler
    transformers['numeric_cols'] = numeric_cols
    feature_parts.append(numeric_scaled)
    feature_names.extend(numeric_cols)
    print(f"  ✅ Numeric: {len(numeric_cols)} features (scaled)")

    # Polynomial features (squares + interactions for top 4 features)
    if 2 <= len(numeric_cols) <= 10:
        interactions = []
        interaction_names = []
        for i in range(min(len(numeric_cols), 4)):
            squared = numeric_scaled[:, i] ** 2
            interactions.append(squared.reshape(-1, 1))
            interaction_names.append(f"{numeric_cols[i]}^2")
        for i in range(min(len(numeric_cols), 4)):
            for j in range(i+1, min(len(numeric_cols), 4)):
                interaction = numeric_scaled[:, i] * numeric_scaled[:, j]
                interactions.append(interaction.reshape(-1, 1))
                interaction_names.append(f"{numeric_cols[i]}*{numeric_cols[j]}")
        if interactions:
            feature_parts.append(np.hstack(interactions))
            feature_names.extend(interaction_names)
            print(f"  ✅ Polynomial: {len(interactions)} features (squares + interactions)")

# ───── CATEGORICAL FEATURES ─────
for col in categorical_cols:
    try:
        series = df_feat[col].fillna('_MISSING_').astype(str).str.strip()
        nunique = series.nunique()

        if nunique <= 2:
            # Binary - label encode
            le = LabelEncoder()
            encoded = le.fit_transform(series)
            feature_parts.append(encoded.reshape(-1, 1).astype(float))
            feature_names.append(f"{col}_binary")
            encoders[col] = le
            print(f"  ✅ Binary '{col}': label encoded ({list(le.classes_)})")
        elif nunique <= 10:
            # One-hot encoding
            dummies = pd.get_dummies(series, prefix=col, drop_first=False)
            if dummies.shape[1] > 0:
                feature_parts.append(dummies.values.astype(float))
                feature_names.extend(dummies.columns.tolist())
                print(f"  ✅ Categorical '{col}': {dummies.shape[1]} one-hot features")
        else:
            # High cardinality - label + frequency encoding
            le = LabelEncoder()
            encoded = le.fit_transform(series)
            feature_parts.append(encoded.reshape(-1, 1).astype(float))
            feature_names.append(f"{col}_encoded")
            encoders[col] = le

            freq_map = series.value_counts(normalize=True).to_dict()
            freq_encoded = series.map(freq_map).values.astype(float)
            feature_parts.append(freq_encoded.reshape(-1, 1))
            feature_names.append(f"{col}_freq")
            print(f"  ✅ Categorical '{col}': label + frequency ({nunique} categories)")
    except Exception as e:
        print(f"  ⚠️  Categorical '{col}' error: {str(e)[:50]}")
        try:
            le = LabelEncoder()
            series = df_feat[col].fillna('_MISSING_').astype(str).str.strip()
            encoded = le.fit_transform(series)
            feature_parts.append(encoded.reshape(-1, 1).astype(float))
            feature_names.append(f"{col}_fallback")
            encoders[col] = le
        except:
            pass

# ───── TEXT FEATURES (NLP) ─────
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

for col in text_cols:
    try:
        series = df_feat[col].fillna('').astype(str)
        cleaned = series.apply(lambda t: re.sub(r'[^a-zA-Z\s]', '', str(t).lower()).strip())

        tfidf = TfidfVectorizer(max_features=300, stop_words='english', ngram_range=(1, 2),
                                min_df=2, max_df=0.9, sublinear_tf=True)
        tfidf_matrix = tfidf.fit_transform(cleaned)

        n_components = min(30, tfidf_matrix.shape[1] - 1, len(df_feat) // 10)
        n_components = max(5, n_components)
        if tfidf_matrix.shape[1] > n_components:
            svd = TruncatedSVD(n_components=n_components, random_state=42)
            text_features = svd.fit_transform(tfidf_matrix)
        else:
            text_features = tfidf_matrix.toarray()

        feature_parts.append(text_features)
        feature_names.extend([f"{col}_tfidf_{i}" for i in range(text_features.shape[1])])

        # Text statistics
        def text_stats(t):
            t = str(t)
            words = t.split()
            chars = len(t)
            n_words = len(words)
            sentences = max(1, t.count('.') + t.count('!') + t.count('?'))
            avg_word = np.mean([len(w) for w in words]) if words else 0
            avg_sent = n_words / sentences
            lex_div = len(set(words)) / max(1, n_words)
            upper = sum(1 for c in t if c.isupper()) / max(1, chars)
            digit = sum(1 for c in t if c.isdigit()) / max(1, chars)
            punct = sum(1 for c in t if c in '.,!?;:') / max(1, chars)
            readability = 206.835 - 1.015 * avg_sent - 84.6 * (sum(len(w) for w in words) / max(1, n_words) / max(1, len(t)))
            return [chars, n_words, sentences, avg_word, avg_sent, lex_div, upper, digit, punct, readability]

        text_stat_arr = np.array([text_stats(t) for t in series])
        feature_parts.append(text_stat_arr)
        stat_names = ['chars', 'words', 'sents', 'avg_word', 'avg_sent', 'lex_div', 'upper', 'digit', 'punct', 'read']
        feature_names.extend([f"{col}_{n}" for n in stat_names])

        # Simple sentiment
        positive_words = {'good', 'great', 'excellent', 'amazing', 'wonderful', 'awesome', 'nice', 'love', 'like', 'best', 'happy', 'beautiful', 'perfect'}
        negative_words = {'bad', 'terrible', 'awful', 'horrible', 'poor', 'worst', 'hate', 'disappointing', 'angry', 'sad', 'boring', 'waste', 'useless'}

        def sentiment_score(t):
            words_set = set(str(t).lower().split())
            pos = len(words_set & positive_words)
            neg = len(words_set & negative_words)
            total = max(1, pos + neg)
            sentiment = (pos - neg) / total
            intensity = (pos + neg) / max(1, len(words_set))
            return [sentiment, pos / max(1, len(words_set)), neg / max(1, len(words_set)), intensity]

        sentiment_arr = np.array([sentiment_score(t) for t in series])
        feature_parts.append(sentiment_arr)
        feature_names.extend([f"{col}_sent", f"{col}_pos", f"{col}_neg", f"{col}_int"])

        print(f"  ✅ NLP '{col}': {text_features.shape[1] + 14} features")
    except Exception as e:
        print(f"  ⚠️  NLP '{col}' error: {str(e)[:30]}")

# ───── DATETIME FEATURES ─────
for col in datetime_cols:
    try:
        dt = pd.to_datetime(df_feat[col], errors='coerce')
        dt_features = np.column_stack([
            dt.dt.year.fillna(0).values, dt.dt.month.fillna(0).values,
            dt.dt.day.fillna(0).values, dt.dt.hour.fillna(0).values,
            dt.dt.dayofweek.fillna(0).values, (dt.dt.dayofweek >= 5).astype(int).values
        ])
        feature_parts.append(dt_features.astype(float))
        feature_names.extend([f"{col}_{n}" for n in ['year', 'month', 'day', 'hour', 'dow', 'weekend']])
        print(f"  ✅ Datetime '{col}': 6 features")
    except Exception as e:
        print(f"  ⚠️  Datetime '{col}' error: {str(e)[:30]}")

# ───── CATEGORICAL INTERACTIONS ─────
if 2 <= len(categorical_cols) <= 15:
    interaction_count = 0
    cat_cardinality = sorted([(c, df_feat[c].nunique()) for c in categorical_cols], key=lambda x: x[1])
    top_cats = [c[0] for c in cat_cardinality[:6]]

    for i in range(len(top_cats)):
        for j in range(i+1, len(top_cats)):
            col1, col2 = top_cats[i], top_cats[j]
            combined = df_feat[col1].fillna('_NA_').astype(str) + "_X_" + df_feat[col2].fillna('_NA_').astype(str)
            if combined.nunique() <= 100:
                le = LabelEncoder()
                encoded = le.fit_transform(combined)
                feature_parts.append(encoded.reshape(-1, 1).astype(float))
                feature_names.append(f"{col1}_X_{col2}")
                interaction_count += 1

                freq_map = combined.value_counts(normalize=True).to_dict()
                freq_encoded = combined.map(freq_map).values.astype(float)
                feature_parts.append(freq_encoded.reshape(-1, 1))
                feature_names.append(f"{col1}_X_{col2}_freq")
                interaction_count += 1

    if interaction_count > 0:
        print(f"  ✅ Categorical interactions: {interaction_count} features")

# ───── NUMERIC-CATEGORICAL AGGREGATES ─────
if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
    agg_count = 0
    top_nums = numeric_cols[:3]
    cat_card = sorted([(c, df_feat[c].nunique()) for c in categorical_cols], key=lambda x: x[1])
    top_cats_agg = [c[0] for c in cat_card[:3] if c[1] <= 50]

    for num_col in top_nums:
        for cat_col in top_cats_agg:
            try:
                group_means = df_feat.groupby(cat_col)[num_col].mean()
                mean_map = group_means.to_dict()
                cat_series = df_feat[cat_col].fillna('_NA_').astype(str)
                agg_values = cat_series.map(mean_map).fillna(df_feat[num_col].mean()).values.astype(float)
                feature_parts.append(agg_values.reshape(-1, 1))
                feature_names.append(f"{num_col}_by_{cat_col}_mean")
                agg_count += 1

                deviation = df_feat[num_col].values - agg_values
                feature_parts.append(deviation.reshape(-1, 1))
                feature_names.append(f"{num_col}_by_{cat_col}_dev")
                agg_count += 1
            except:
                pass

    if agg_count > 0:
        print(f"  ✅ Numeric-Categorical aggregates: {agg_count} features")

# ───── COMBINE ALL FEATURES ─────
clean_parts = []
for i, part in enumerate(feature_parts):
    try:
        part_arr = np.asarray(part, dtype=float)
        part_arr = np.nan_to_num(part_arr, nan=0.0, posinf=0.0, neginf=0.0)
        clean_parts.append(part_arr)
    except (ValueError, TypeError):
        part_arr = np.asarray(part)
        clean_arr = np.zeros(part_arr.shape, dtype=float)
        if part_arr.ndim == 1:
            part_arr = part_arr.reshape(-1, 1)
            clean_arr = np.zeros(part_arr.shape, dtype=float)
        for j in range(part_arr.shape[1] if part_arr.ndim > 1 else 1):
            col_data = part_arr[:, j] if part_arr.ndim > 1 else part_arr
            try:
                clean_arr[:, j] = pd.to_numeric(col_data, errors='coerce').fillna(0)
            except:
                le_tmp = LabelEncoder()
                clean_arr[:, j] = le_tmp.fit_transform(col_data.astype(str))
        clean_parts.append(clean_arr)

X = np.hstack(clean_parts)
X = np.asarray(X, dtype=np.float64)
X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

print(f"\n  🛡️  X shape before variance filter: {X.shape}, dtype: {X.dtype}")

# Variance threshold
try:
    selector = VarianceThreshold(threshold=0.01)
    X = selector.fit_transform(X)
    mask = selector.get_support()
    feature_names = [f for f, m in zip(feature_names, mask) if m]
    print(f"  ✅ VarianceThreshold: {sum(mask)}/{len(mask)} features kept")
except Exception as e:
    print(f"  ⚠️  VarianceThreshold skipped: {e}")

print(f"  ✅ Final: {X.shape[1]} features (all numeric)")

# Ensure y is int for classification
if task_type == 'classification':
    y = y.astype(int)
else:
    y = y.astype(float)

# ──────────────────────────────────────────────────────────────
# STEP 5: TRAIN/TEST SPLIT
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  STEP 5: TRAIN/TEST SPLIT (80/20, random_state=42)")
print("=" * 60)

if task_type == 'classification':
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
    except ValueError:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
else:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

print(f"  Train: {X_train.shape[0]} samples, {X_train.shape[1]} features")
print(f"  Test:  {X_test.shape[0]} samples, {X_test.shape[1]} features")

# ──────────────────────────────────────────────────────────────
# STEP 6: TRAIN RANDOM FOREST (Same params as AutoML)
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  STEP 6: TRAINING RANDOM FOREST [Same params as AutoML]")
print("=" * 60)

# Exact same params as build_selected_models() in production_ml_core.py
rf_params = {
    'n_estimators': 150,
    'max_depth': 10,
    'random_state': 42,
    'n_jobs': -1,
    'class_weight': 'balanced'
}

print(f"  🔧 Algorithm: RandomForestClassifier")
print(f"  📋 Params: {rf_params}")

start_time = datetime.now()
model = RandomForestClassifier(**rf_params)
model.fit(X_train, y_train)
train_time = (datetime.now() - start_time).total_seconds()

print(f"  ⏱️  Training time: {train_time:.2f}s")
print(f"  ✅ Model trained successfully!")

# ──────────────────────────────────────────────────────────────
# STEP 7: EVALUATE MANUAL MODEL
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  STEP 7: MANUAL MODEL EVALUATION")
print("=" * 60)

y_pred = model.predict(X_test)

manual_accuracy = accuracy_score(y_test, y_pred)
manual_f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
manual_precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
manual_recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)

print(f"\n  ┌──────────────────────────────────────────┐")
print(f"  │  MANUAL RandomForest Results              │")
print(f"  ├──────────────────────────────────────────┤")
print(f"  │  Accuracy:    {manual_accuracy:.4f} ({manual_accuracy*100:.2f}%)       │")
print(f"  │  F1-Score:    {manual_f1:.4f}                    │")
print(f"  │  Precision:   {manual_precision:.4f}                    │")
print(f"  │  Recall:      {manual_recall:.4f}                    │")
print(f"  └──────────────────────────────────────────┘")

print(f"\n  📋 Classification Report:")
if target_encoder is not None:
    print(classification_report(y_test, y_pred, target_names=list(target_encoder.classes_), zero_division=0))
else:
    print(classification_report(y_test, y_pred, zero_division=0))

print(f"  📋 Confusion Matrix:")
cm = confusion_matrix(y_test, y_pred)
print(f"  {cm}")

# Show sample predictions
if target_encoder is not None:
    y_test_labels = target_encoder.inverse_transform(y_test)
    y_pred_labels = target_encoder.inverse_transform(y_pred)
    print(f"\n  📋 Sample Predictions (first 15):")
    print(f"  {'#':<4} {'Actual':<10} {'Predicted':<10} {'Match':<6}")
    print(f"  {'─'*35}")
    for i in range(min(15, len(y_test))):
        match = "✅" if y_test_labels[i] == y_pred_labels[i] else "❌"
        print(f"  {i+1:<4} {y_test_labels[i]:<10} {y_pred_labels[i]:<10} {match}")

# Feature importance (top 15)
importances = model.feature_importances_
indices = np.argsort(importances)[::-1]
print(f"\n  📊 Top 15 Feature Importances:")
for i in range(min(15, len(feature_names))):
    idx = indices[i]
    print(f"    {i+1:>2}. {feature_names[idx]:<35} {importances[idx]:.4f}")

# ──────────────────────────────────────────────────────────────
# STEP 8: LOAD & COMPARE AUTOML PKL
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  STEP 8: LOAD AUTOML .pkl & COMPARE")
print("=" * 60)

pkl_paths = [
    r"backend\storage\automl\d4f48123-b254-47f8-a335-6d142b3f1a72\model.pkl",
    r"model.pkl",
    r"trained_model.pkl",
]

automl_data = None
for p in pkl_paths:
    if os.path.exists(p):
        try:
            with open(p, 'rb') as f:
                automl_data = pickle.load(f)
            print(f"  📂 Loaded AutoML pkl from: {p}")
            break
        except Exception as e:
            print(f"  ⚠️  Failed to load {p}: {e}")

if automl_data is not None:
    automl_model = automl_data.get('model')
    automl_name = automl_data.get('model_name', 'Unknown')
    automl_metrics = automl_data.get('metrics', {})
    automl_task = automl_data.get('task_type', 'Unknown')
    automl_target = automl_data.get('target_column', 'Unknown')
    automl_y_test = automl_data.get('y_test')
    automl_y_pred = automl_data.get('y_pred')
    automl_target_enc = automl_data.get('target_encoder')

    print(f"\n  🤖 AutoML Model: {automl_name}")
    print(f"  🎯 AutoML Task: {automl_task}")
    print(f"  🎯 AutoML Target: {automl_target}")
    if automl_target_enc is not None:
        print(f"  🏷️  AutoML Classes: {list(automl_target_enc.classes_)}")

    # Show AutoML saved metrics
    if automl_metrics:
        print(f"\n  📊 AutoML Saved Metrics:")
        for k, v in automl_metrics.items():
            if isinstance(v, (int, float)):
                print(f"     {k}: {v:.4f}")
            else:
                print(f"     {k}: {v}")

    # Re-evaluate AutoML saved y_test/y_pred
    if automl_y_test is not None and automl_y_pred is not None:
        automl_y_test = np.array(automl_y_test)
        automl_y_pred = np.array(automl_y_pred)
        automl_acc = accuracy_score(automl_y_test, automl_y_pred)
        automl_f1 = f1_score(automl_y_test, automl_y_pred, average='weighted', zero_division=0)
        automl_prec = precision_score(automl_y_test, automl_y_pred, average='weighted', zero_division=0)
        automl_rec = recall_score(automl_y_test, automl_y_pred, average='weighted', zero_division=0)
    else:
        automl_acc = automl_metrics.get('accuracy', 0)
        automl_f1 = automl_metrics.get('f1', 0)
        automl_prec = automl_metrics.get('precision', 0)
        automl_rec = automl_metrics.get('recall', 0)

    # Try cross-prediction (AutoML model on our features)
    cross_acc = None
    if automl_model is not None:
        try:
            automl_cross_pred = automl_model.predict(X_test)
            cross_acc = accuracy_score(y_test, automl_cross_pred)
            cross_f1 = f1_score(y_test, automl_cross_pred, average='weighted', zero_division=0)
            print(f"\n  🔄 Cross-prediction (AutoML model on manual features):")
            print(f"     Accuracy: {cross_acc:.4f} ({cross_acc*100:.2f}%)")
            print(f"     F1:       {cross_f1:.4f}")
        except Exception as e:
            print(f"\n  ⚠️  Cross-prediction failed: {str(e)[:80]}")
            if hasattr(automl_model, 'n_features_in_'):
                print(f"     AutoML expects {automl_model.n_features_in_} features, we have {X_test.shape[1]}")

    # ──────────────────────────────────────────────────────────
    # FINAL COMPARISON TABLE
    # ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  🔬 FINAL COMPARISON: MANUAL vs AUTOML")
    print("=" * 60)
    print(f"\n  {'Metric':<15} {'Manual':>12} {'AutoML':>12} {'Diff':>12} {'Match?':>8}")
    print(f"  {'─'*62}")

    comparisons = [
        ('Accuracy', manual_accuracy, automl_acc),
        ('F1-Score', manual_f1, automl_f1),
        ('Precision', manual_precision, automl_prec),
        ('Recall', manual_recall, automl_rec),
    ]

    all_close = True
    for name, manual_val, automl_val in comparisons:
        diff = manual_val - automl_val
        is_close = abs(diff) < 0.05
        match_str = "✅ YES" if is_close else "❌ NO"
        if not is_close:
            all_close = False
        print(f"  {name:<15} {manual_val:>12.4f} {automl_val:>12.4f} {diff:>+12.4f} {match_str:>8}")

    print(f"\n  {'─'*62}")
    if all_close:
        print(f"  ✅ VERDICT: AutoML and Manual models are CONSISTENT!")
        print(f"              The AutoML pipeline is working CORRECTLY.")
    else:
        print(f"  ⚠️  VERDICT: Some differences detected (this is NORMAL if")
        print(f"     AutoML used a different algorithm like XGBoost/LightGBM)")
        print(f"     AutoML model: {automl_name}")
        print(f"     Manual model: RandomForest")

    if cross_acc is not None:
        print(f"\n  🔄 Cross-prediction accuracy: {cross_acc:.4f}")
        if abs(cross_acc - manual_accuracy) < 0.01:
            print(f"     ✅ Cross-prediction matches! Same pipeline confirmed.")

else:
    print(f"  ⚠️  No AutoML .pkl found. Train model first via AutoML page,")
    print(f"     then download the .pkl from ML Predictions.")
    print(f"     Or place the downloaded .pkl in this folder as 'model.pkl'")

# ──────────────────────────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  ✅ VERIFICATION COMPLETE")
print("=" * 60)
print(f"  Dataset:     adult.csv ({df.shape[0]} rows)")
print(f"  Target:      {target_col}")
print(f"  Task:        {task_type}")
print(f"  Algorithm:   RandomForest")
print(f"  Features:    {X.shape[1]}")
print(f"  Train/Test:  {len(X_train)}/{len(X_test)}")
print(f"  Accuracy:    {manual_accuracy:.4f} ({manual_accuracy*100:.2f}%)")
print(f"  F1 Score:    {manual_f1:.4f}")
if target_encoder is not None:
    print(f"  Classes:     {list(target_encoder.classes_)}")
print()
