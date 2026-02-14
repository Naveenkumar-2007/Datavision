"""
====================================================================
🔬 DATAVISION AUTOML vs MANUAL TRAINING VERIFICATION SCRIPT
====================================================================

This script replicates the EXACT AutoML pipeline manually so you can
verify that the AutoML-trained model (downloaded .pkl) produces
correct and consistent results.

WHAT THIS DOES:
1. Loads your dataset (HR Employee Attrition)
2. Replicates the EXACT same preprocessing as AutoML:
   - ProductionDataCleaner (Phase 1)
   - LabelEncoder for target (classification)
   - ProductionFeatureEngineer (Phase 2)
3. Trains a RandomForest with the SAME hyperparameters
4. Loads your downloaded AutoML .pkl file
5. Compares: Manual model vs AutoML model metrics

USAGE:
  python verify_automl_model.py --dataset "path/to/your.csv" --pkl "path/to/downloaded_model.pkl"

If no --pkl is provided, it will just train manually and show results.
====================================================================
"""

import os
import sys
import pickle
import argparse
import warnings
import numpy as np
import pandas as pd
from datetime import datetime

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION - Matches AutoML exactly
# ============================================================================

RANDOM_STATE = 42
TEST_SIZE = 0.2
RF_PARAMS = {
    'n_estimators': 150,
    'max_depth': 10,
    'random_state': 42,
    'n_jobs': -1,
    'class_weight': 'balanced'
}


def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_section(title):
    print(f"\n{'─'*50}")
    print(f"  {title}")
    print(f"{'─'*50}")


# ============================================================================
# PHASE 1: DATA CLEANING (Replicates ProductionDataCleaner)
# ============================================================================

def clean_data(df, target_col):
    """
    Replicates the ProductionDataCleaner.clean() method
    from backend/ml/production_ml_core.py
    """
    print_section("PHASE 1: DATA CLEANING (Same as AutoML)")
    original_shape = df.shape
    df = df.copy()

    # Step 0: Remove useless columns (IDs, URLs, indices)
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
        print(f"  🗑️  Removing {len(useless_cols)} useless columns: {useless_cols}")
        df = df.drop(columns=useless_cols, errors='ignore')

    # Step 1: Remove duplicates
    n_dups = df.duplicated().sum()
    if n_dups > 0:
        df = df.drop_duplicates()
        print(f"  ✅ Removed {n_dups} duplicate rows")

    # Step 2: Strip whitespace
    for col in df.columns:
        if df[col].dtype == object:
            try:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace(['nan', 'NaN', 'None', 'null', ''], np.nan)
            except:
                pass
    print(f"  ✅ Stripped whitespace and cleaned strings")

    # Step 3: Identify column types
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if target_col in numeric_cols:
        numeric_cols = [c for c in numeric_cols if c != target_col]

    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    if target_col in categorical_cols:
        categorical_cols = [c for c in categorical_cols if c != target_col]

    # Step 4: Handle missing values
    # Numeric: KNN imputer
    missing_numeric = [c for c in numeric_cols if df[c].isna().any()]
    if missing_numeric:
        try:
            from sklearn.impute import KNNImputer
            imputer = KNNImputer(n_neighbors=5, weights='distance')
            df[numeric_cols] = imputer.fit_transform(df[numeric_cols])
            print(f"  ✅ KNN imputed {len(missing_numeric)} numeric columns")
        except:
            for col in missing_numeric:
                fill_val = df[col].median()
                df[col] = df[col].fillna(fill_val if pd.notna(fill_val) else 0)
            print(f"  ✅ Median imputed {len(missing_numeric)} numeric columns")

    # Categorical: fill with mode
    for col in categorical_cols:
        if df[col].isna().sum() > 0:
            mode_vals = df[col].mode()
            fill_val = mode_vals.iloc[0] if len(mode_vals) > 0 else '_MISSING_'
            df[col] = df[col].fillna(fill_val)

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

    # Step 7: IsolationForest outlier detection (flagging only)
    numeric_cols = [c for c in numeric_cols if c in df.columns]
    if len(numeric_cols) > 0 and len(df) >= 100:
        try:
            from sklearn.ensemble import IsolationForest
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
    return df


# ============================================================================
# PHASE 2: FEATURE ENGINEERING (Replicates ProductionFeatureEngineer)
# ============================================================================

def engineer_features(df, target_col, task_type='classification'):
    """
    Replicates the ProductionFeatureEngineer.fit_transform() method
    from backend/ml/production_ml_core.py
    """
    print_section("PHASE 2: FEATURE ENGINEERING (Same as AutoML)")
    
    from sklearn.preprocessing import LabelEncoder, RobustScaler
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_selection import VarianceThreshold

    df = df.copy()
    
    # Separate target
    y = df[target_col].values
    original_columns = [c for c in df.columns if c != target_col]
    df = df.drop(columns=[target_col])

    feature_parts = []
    feature_names = []
    encoders = {}
    transformers = {}

    # Detect column types
    numeric_cols = []
    categorical_cols = []
    text_cols = []
    datetime_cols = []

    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            datetime_cols.append(col)
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            try:
                _ = df[col].astype(float).values
                numeric_cols.append(col)
            except:
                categorical_cols.append(col)
            continue

        # Object/string column
        try:
            series = df[col].astype(str)
            nunique = series.nunique()
            avg_len = series.str.len().mean()
            unique_ratio = nunique / len(df) if len(df) > 0 else 0

            # Date check
            col_lower = col.lower()
            is_date_like = any(kw in col_lower for kw in ['date', 'time', 'year', 'month', 'day', 'created', 'updated'])
            if is_date_like:
                try:
                    parsed = pd.to_datetime(df[col], errors='coerce')
                    if parsed.notna().sum() > len(df) * 0.5:
                        datetime_cols.append(col)
                        continue
                except:
                    pass

            # Text detection
            text_keywords = ['description', 'text', 'comment', 'review', 'content', 'body', 'message',
                           'title', 'summary', 'feedback', 'note', 'detail', 'caption', 'headline',
                           'tweet', 'sentence', 'post', 'question', 'answer', 'query', 'phrase']
            has_text_name = any(word in col_lower for word in text_keywords)
            sample_text = df[col].dropna().head(10).astype(str)
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

    # === NUMERIC FEATURES ===
    if numeric_cols:
        try:
            numeric_data = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

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
                print(f"  ✅ Log-transformed {len(log_transformed)} skewed features")

            numeric_values = numeric_data.values
            scaler = RobustScaler()
            numeric_scaled = scaler.fit_transform(numeric_values)
            numeric_scaled = np.nan_to_num(numeric_scaled, nan=0.0, posinf=0.0, neginf=0.0)

            transformers['numeric_scaler'] = scaler
            transformers['numeric_cols'] = numeric_cols
            transformers['log_transformed_cols'] = log_transformed
            feature_parts.append(numeric_scaled)
            feature_names.extend(numeric_cols)
            print(f"  ✅ Numeric: {len(numeric_cols)} features (scaled)")

            # Polynomial features
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
                    print(f"  ✅ Polynomial: {len(interactions)} features")
        except Exception as e:
            print(f"  ⚠️  Numeric processing error: {str(e)[:50]}")

    # === CATEGORICAL FEATURES ===
    for col in categorical_cols:
        try:
            series = df[col].fillna('_MISSING_').astype(str).str.strip()
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
                # One-hot
                dummies = pd.get_dummies(series, prefix=col, drop_first=False)
                if dummies.shape[1] > 0:
                    feature_parts.append(dummies.values.astype(float))
                    feature_names.extend(dummies.columns.tolist())
                    transformers[f'{col}_onehot'] = dummies.columns.tolist()
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
                series = df[col].fillna('_MISSING_').astype(str).str.strip()
                encoded = le.fit_transform(series)
                feature_parts.append(encoded.reshape(-1, 1).astype(float))
                feature_names.append(f"{col}_fallback")
                encoders[col] = le
            except:
                pass

    # === TEXT FEATURES ===
    for col in text_cols:
        try:
            series = df[col].fillna('').astype(str)
            import re
            cleaned = series.apply(lambda t: re.sub(r'[^a-zA-Z\s]', '', str(t).lower()).strip())

            tfidf = TfidfVectorizer(max_features=300, stop_words='english', ngram_range=(1, 2),
                                    min_df=2, max_df=0.9, sublinear_tf=True)
            tfidf_matrix = tfidf.fit_transform(cleaned)

            n_components = min(30, tfidf_matrix.shape[1] - 1, len(df) // 10)
            n_components = max(5, n_components)
            if tfidf_matrix.shape[1] > n_components:
                svd = TruncatedSVD(n_components=n_components, random_state=42)
                text_features = svd.fit_transform(tfidf_matrix)
            else:
                text_features = tfidf_matrix.toarray()

            feature_parts.append(text_features)
            feature_names.extend([f"{col}_tfidf_{i}" for i in range(text_features.shape[1])])
            print(f"  ✅ NLP '{col}': {text_features.shape[1]} features")
        except Exception as e:
            print(f"  ⚠️  NLP '{col}' error: {str(e)[:30]}")

    # === DATETIME FEATURES ===
    for col in datetime_cols:
        try:
            dt = pd.to_datetime(df[col], errors='coerce')
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

    # === CATEGORICAL INTERACTIONS ===
    if 2 <= len(categorical_cols) <= 15:
        try:
            interaction_count = 0
            cat_cardinality = sorted([(c, df[c].nunique()) for c in categorical_cols], key=lambda x: x[1])
            top_cats = [c[0] for c in cat_cardinality[:6]]

            for i in range(len(top_cats)):
                for j in range(i+1, len(top_cats)):
                    col1, col2 = top_cats[i], top_cats[j]
                    combined = df[col1].fillna('_NA_').astype(str) + "_X_" + df[col2].fillna('_NA_').astype(str)
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
        except Exception as e:
            print(f"  ⚠️  Interactions error: {str(e)[:50]}")

    # === NUMERIC-CATEGORICAL AGGREGATES ===
    if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
        try:
            agg_count = 0
            top_nums = numeric_cols[:3]
            cat_cardinality = sorted([(c, df[c].nunique()) for c in categorical_cols], key=lambda x: x[1])
            top_cats = [c[0] for c in cat_cardinality[:3] if c[1] <= 50]

            for num_col in top_nums:
                for cat_col in top_cats:
                    try:
                        group_means = df.groupby(cat_col)[num_col].mean()
                        mean_map = group_means.to_dict()
                        cat_series = df[cat_col].fillna('_NA_').astype(str)
                        agg_values = cat_series.map(mean_map).fillna(df[num_col].mean()).values.astype(float)
                        feature_parts.append(agg_values.reshape(-1, 1))
                        feature_names.append(f"{num_col}_by_{cat_col}_mean")
                        agg_count += 1

                        deviation = df[num_col].values - agg_values
                        feature_parts.append(deviation.reshape(-1, 1))
                        feature_names.append(f"{num_col}_by_{cat_col}_dev")
                        agg_count += 1
                    except:
                        pass

            if agg_count > 0:
                print(f"  ✅ Numeric-Categorical aggregates: {agg_count} features")
        except Exception as e:
            print(f"  ⚠️  Aggregates error: {str(e)[:50]}")

    # === COMBINE FEATURES ===
    if not feature_parts:
        raise ValueError("No valid features after processing!")

    # Safety: ensure numeric
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
                    le = LabelEncoder()
                    clean_arr[:, j] = le.fit_transform(col_data.astype(str))
            clean_parts.append(clean_arr)

    X = np.hstack(clean_parts)
    X = np.asarray(X, dtype=np.float64)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

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

    return X, y, feature_names, encoders, transformers


# ============================================================================
# PHASE 3: TRAIN RANDOM FOREST (Same params as AutoML)
# ============================================================================

def train_manual_model(X_train, y_train, X_test, y_test, task_type='classification'):
    """Train RandomForest with same params as AutoML's build_selected_models()"""
    print_section("PHASE 3: MANUAL RANDOM FOREST TRAINING")
    
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

    if task_type == 'classification':
        model = RandomForestClassifier(**RF_PARAMS)
    else:
        model = RandomForestRegressor(
            n_estimators=150, max_depth=10,
            random_state=42, n_jobs=-1
        )

    print(f"  🔧 Model: RandomForest")
    print(f"  📋 Params: {RF_PARAMS}")
    print(f"  📊 Training on {len(X_train)} samples, {X_train.shape[1]} features")
    
    start = datetime.now()
    model.fit(X_train, y_train)
    elapsed = (datetime.now() - start).total_seconds()
    
    print(f"  ⏱️  Training time: {elapsed:.2f}s")

    return model


# ============================================================================
# PHASE 4: EVALUATE & COMPARE
# ============================================================================

def evaluate_model(model, X_test, y_test, task_type='classification', label="Model"):
    """Evaluate model and return metrics dict"""
    from sklearn.metrics import (
        accuracy_score, f1_score, precision_score, recall_score,
        classification_report, confusion_matrix,
        r2_score, mean_squared_error, mean_absolute_error
    )

    y_pred = model.predict(X_test)
    metrics = {}

    if task_type == 'classification':
        metrics['accuracy'] = accuracy_score(y_test, y_pred)
        metrics['f1'] = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        metrics['precision'] = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        metrics['recall'] = recall_score(y_test, y_pred, average='weighted', zero_division=0)

        print(f"\n  📊 {label} Results:")
        print(f"  ┌─────────────────────────────────────┐")
        print(f"  │  Accuracy:   {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
        print(f"  │  F1-Score:   {metrics['f1']:.4f}")
        print(f"  │  Precision:  {metrics['precision']:.4f}")
        print(f"  │  Recall:     {metrics['recall']:.4f}")
        print(f"  └─────────────────────────────────────┘")

        print(f"\n  📋 Classification Report:")
        print(classification_report(y_test, y_pred, zero_division=0))

        print(f"  📋 Confusion Matrix:")
        cm = confusion_matrix(y_test, y_pred)
        print(f"  {cm}")
    else:
        metrics['r2'] = r2_score(y_test, y_pred)
        metrics['rmse'] = np.sqrt(mean_squared_error(y_test, y_pred))
        metrics['mae'] = mean_absolute_error(y_test, y_pred)

        print(f"\n  📊 {label} Results:")
        print(f"  ┌─────────────────────────────────────┐")
        print(f"  │  R² Score:   {metrics['r2']:.4f}")
        print(f"  │  RMSE:       {metrics['rmse']:.4f}")
        print(f"  │  MAE:        {metrics['mae']:.4f}")
        print(f"  └─────────────────────────────────────┘")

    return metrics, y_pred


def load_automl_pkl(pkl_path):
    """Load and inspect the AutoML .pkl file"""
    print_section("LOADING AUTOML .pkl FILE")
    
    with open(pkl_path, 'rb') as f:
        data = pickle.load(f)

    print(f"  📂 Loaded from: {pkl_path}")
    print(f"  📦 Keys in .pkl: {list(data.keys())}")

    # Extract key info
    model = data.get('model')
    model_name = data.get('model_name', 'Unknown')
    task_type = data.get('task_type', 'classification')
    task_type_simple = data.get('task_type_simple', 'classification')
    target_col = data.get('target_column', '')
    feature_cols = data.get('feature_columns', [])
    target_encoder = data.get('target_encoder')
    metrics = data.get('metrics', {})
    y_test_saved = data.get('y_test')
    y_pred_saved = data.get('y_pred')
    production_engineer = data.get('production_engineer')
    production_mode = data.get('production_mode', False)

    print(f"\n  🤖 Model Name: {model_name}")
    print(f"  🎯 Task Type: {task_type}")
    print(f"  🎯 Target Column: {target_col}")
    print(f"  📊 Feature Count: {len(feature_cols)}")
    print(f"  🏭 Production Mode: {production_mode}")
    
    if target_encoder is not None:
        print(f"  🏷️  Target Classes: {list(target_encoder.classes_)}")
    
    if metrics:
        print(f"\n  📊 Saved Metrics from AutoML:")
        for k, v in metrics.items():
            if isinstance(v, (int, float)):
                print(f"     {k}: {v:.4f}")
            else:
                print(f"     {k}: {v}")

    if y_test_saved is not None and y_pred_saved is not None:
        print(f"\n  📊 Saved Test/Pred arrays:")
        print(f"     y_test shape: {np.array(y_test_saved).shape}")
        print(f"     y_pred shape: {np.array(y_pred_saved).shape}")
        print(f"     y_test unique: {np.unique(y_test_saved)}")
        print(f"     y_pred unique: {np.unique(y_pred_saved)}")

    return data


def compare_results(manual_metrics, automl_metrics, task_type='classification'):
    """Compare manual vs AutoML metrics"""
    print_header("🔬 COMPARISON: MANUAL vs AUTOML")

    if task_type == 'classification':
        keys = ['accuracy', 'f1', 'precision', 'recall']
    else:
        keys = ['r2', 'rmse', 'mae']

    print(f"\n  {'Metric':<15} {'Manual':>12} {'AutoML':>12} {'Diff':>12} {'Match?':>8}")
    print(f"  {'─'*60}")
    
    all_close = True
    for key in keys:
        manual_val = manual_metrics.get(key, 0)
        automl_val = automl_metrics.get(key, 0)
        diff = manual_val - automl_val
        is_close = abs(diff) < 0.05  # Within 5% tolerance
        match_str = "✅ YES" if is_close else "❌ NO"
        if not is_close:
            all_close = False
        
        print(f"  {key:<15} {manual_val:>12.4f} {automl_val:>12.4f} {diff:>+12.4f} {match_str:>8}")

    print(f"\n  {'─'*60}")
    if all_close:
        print(f"  ✅ VERDICT: Models are consistent! AutoML training is CORRECT.")
    else:
        print(f"  ⚠️  VERDICT: Some differences detected.")
        print(f"     This is NORMAL if:")
        print(f"     - Different algorithm was used in AutoML (check model name)")
        print(f"     - AutoML may have used different train/test split order")
        print(f"     - Feature engineering may vary slightly due to random state")
        print(f"     - Differences < 5% are generally acceptable")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Verify AutoML model by manual training comparison")
    parser.add_argument('--dataset', '-d', type=str, required=True,
                       help='Path to your CSV dataset file')
    parser.add_argument('--target', '-t', type=str, default=None,
                       help='Target column name (auto-detected if not provided)')
    parser.add_argument('--pkl', '-p', type=str, default=None,
                       help='Path to downloaded AutoML .pkl file')
    parser.add_argument('--algorithm', '-a', type=str, default='random_forest',
                       choices=['random_forest', 'xgboost', 'lightgbm', 'decision_tree', 'gradient_boosting'],
                       help='Algorithm to use for manual training (default: random_forest)')

    args = parser.parse_args()

    print_header("🔬 DATAVISION AUTOML VERIFICATION TOOL")
    print(f"  Dataset: {args.dataset}")
    print(f"  Target:  {args.target or 'auto-detect'}")
    print(f"  PKL:     {args.pkl or 'not provided'}")
    print(f"  Algo:    {args.algorithm}")

    # ──────────────────────────────────────────────
    # 1. Load dataset
    # ──────────────────────────────────────────────
    print_section("LOADING DATASET")
    
    if args.dataset.endswith('.xlsx') or args.dataset.endswith('.xls'):
        df = pd.read_excel(args.dataset)
    else:
        df = pd.read_csv(args.dataset)
    
    print(f"  📊 Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"  📊 Columns: {list(df.columns)}")
    print(f"  📊 Dtypes:\n{df.dtypes.to_string()}")

    # ──────────────────────────────────────────────
    # 2. Detect target column
    # ──────────────────────────────────────────────
    target_col = args.target
    if not target_col:
        # Auto-detect: Look for common target column names
        target_hints = ['target', 'label', 'class', 'outcome', 'result', 'attrition',
                       'churn', 'default', 'fraud', 'survived', 'diagnosis', 'species',
                       'price', 'salary', 'revenue', 'sales']
        for col in df.columns:
            if col.lower() in target_hints:
                target_col = col
                break
        if not target_col:
            # Use last column
            target_col = df.columns[-1]
    
    print(f"  🎯 Target: {target_col}")
    print(f"  📊 Target distribution:\n{df[target_col].value_counts().to_string()}")

    # ──────────────────────────────────────────────
    # 3. Detect task type
    # ──────────────────────────────────────────────
    y_temp = df[target_col]
    if y_temp.dtype == 'object' or (y_temp.dtype in ['int64', 'float64'] and y_temp.nunique() <= 20):
        task_type = 'classification'
    else:
        task_type = 'regression'
    print(f"  🔍 Task Type: {task_type}")

    # ──────────────────────────────────────────────
    # 4. Clean data (Phase 1)
    # ──────────────────────────────────────────────
    df_clean = clean_data(df, target_col)

    # Drop NaN targets
    target_nan = df_clean[target_col].isna().sum()
    if target_nan > 0:
        df_clean = df_clean.dropna(subset=[target_col])
        print(f"  ⚠️  Dropped {target_nan} rows with missing target")

    # ──────────────────────────────────────────────
    # 5. Encode target for classification
    # ──────────────────────────────────────────────
    from sklearn.preprocessing import LabelEncoder as LE
    target_encoder = None
    if task_type == 'classification':
        target_encoder = LE()
        df_clean[target_col] = target_encoder.fit_transform(df_clean[target_col].astype(str))
        n_classes = len(target_encoder.classes_)
        print(f"\n  🏷️  Target Encoded: {list(target_encoder.classes_)} → {list(range(n_classes))}")

    # ──────────────────────────────────────────────
    # 6. Feature Engineering (Phase 2)
    # ──────────────────────────────────────────────
    X, y, feature_names, encoders, transformers = engineer_features(df_clean, target_col, task_type)

    # Ensure y is properly typed
    if task_type == 'classification':
        y = y.astype(int)
    else:
        y = y.astype(float)

    # ──────────────────────────────────────────────
    # 7. Train/Test Split
    # ──────────────────────────────────────────────
    from sklearn.model_selection import train_test_split

    print_section("TRAIN/TEST SPLIT")
    if task_type == 'classification':
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
            )
        except ValueError:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
            )
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
        )
    print(f"  Train: {len(X_train)} | Test: {len(X_test)}")

    # ──────────────────────────────────────────────
    # 8. Train Manual Model
    # ──────────────────────────────────────────────
    if args.algorithm == 'random_forest':
        manual_model = train_manual_model(X_train, y_train, X_test, y_test, task_type)
    elif args.algorithm == 'xgboost':
        import xgboost as xgb
        if task_type == 'classification':
            manual_model = xgb.XGBClassifier(
                n_estimators=150, max_depth=6, learning_rate=0.1,
                random_state=42, n_jobs=-1, verbosity=0, scale_pos_weight=10
            )
        else:
            manual_model = xgb.XGBRegressor(
                n_estimators=150, max_depth=6, learning_rate=0.1,
                random_state=42, n_jobs=-1, verbosity=0
            )
        print(f"  🔧 Training XGBoost manually...")
        manual_model.fit(X_train, y_train)
    elif args.algorithm == 'lightgbm':
        import lightgbm as lgb
        if task_type == 'classification':
            manual_model = lgb.LGBMClassifier(
                n_estimators=150, max_depth=6, learning_rate=0.1,
                random_state=42, n_jobs=-1, verbose=-1, class_weight='balanced'
            )
        else:
            manual_model = lgb.LGBMRegressor(
                n_estimators=150, max_depth=6, learning_rate=0.1,
                random_state=42, n_jobs=-1, verbose=-1
            )
        print(f"  🔧 Training LightGBM manually...")
        manual_model.fit(X_train, y_train)
    elif args.algorithm == 'decision_tree':
        from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
        if task_type == 'classification':
            manual_model = DecisionTreeClassifier(max_depth=10, random_state=42, class_weight='balanced')
        else:
            manual_model = DecisionTreeRegressor(max_depth=10, random_state=42)
        print(f"  🔧 Training DecisionTree manually...")
        manual_model.fit(X_train, y_train)
    elif args.algorithm == 'gradient_boosting':
        from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
        if task_type == 'classification':
            manual_model = GradientBoostingClassifier(
                n_estimators=120, max_depth=5, learning_rate=0.1, random_state=42
            )
        else:
            manual_model = GradientBoostingRegressor(
                n_estimators=120, max_depth=5, learning_rate=0.1, random_state=42
            )
        print(f"  🔧 Training GradientBoosting manually...")
        manual_model.fit(X_train, y_train)

    # ──────────────────────────────────────────────
    # 9. Evaluate Manual Model
    # ──────────────────────────────────────────────
    print_header("📊 MANUAL MODEL EVALUATION")
    manual_metrics, manual_pred = evaluate_model(manual_model, X_test, y_test, task_type, "Manual RandomForest")

    # Map predictions back to original labels if classification
    if task_type == 'classification' and target_encoder is not None:
        y_test_labels = target_encoder.inverse_transform(y_test)
        manual_pred_labels = target_encoder.inverse_transform(manual_pred)
        print(f"\n  Sample predictions (with original labels):")
        for i in range(min(10, len(y_test))):
            match = "✅" if y_test_labels[i] == manual_pred_labels[i] else "❌"
            print(f"    {match} Actual: {y_test_labels[i]:>6} | Predicted: {manual_pred_labels[i]:>6}")

    # ──────────────────────────────────────────────
    # 10. Load & Compare AutoML PKL (if provided)
    # ──────────────────────────────────────────────
    if args.pkl and os.path.exists(args.pkl):
        automl_data = load_automl_pkl(args.pkl)
        automl_model = automl_data.get('model')
        automl_metrics = automl_data.get('metrics', {})
        automl_y_test = automl_data.get('y_test')
        automl_y_pred = automl_data.get('y_pred')
        automl_production_engineer = automl_data.get('production_engineer')

        # Method 1: Compare saved metrics directly
        if automl_metrics:
            compare_results(manual_metrics, automl_metrics, task_type)

        # Method 2: If same data & same features, predict with AutoML model on our test set
        if automl_model is not None:
            print_section("CROSS-PREDICTION: AutoML model on Manual test data")
            try:
                automl_pred_on_our_data = automl_model.predict(X_test)
                automl_cross_metrics, _ = evaluate_model(
                    automl_model, X_test, y_test, task_type,
                    f"AutoML {automl_data.get('model_name', 'Unknown')} on Manual test split"
                )
                print(f"\n  Note: The AutoML model was re-evaluated on the same test split")
                print(f"  used by manual training. Small differences are expected if")
                print(f"  AutoML used a different train/test split.")
            except Exception as e:
                print(f"  ⚠️  Could not cross-predict: {str(e)}")
                print(f"     This may be because feature counts differ.")
                print(f"     Manual features: {X_test.shape[1]}")
                if hasattr(automl_model, 'n_features_in_'):
                    print(f"     AutoML features:  {automl_model.n_features_in_}")

        # Method 3: Compare saved y_test/y_pred directly
        if automl_y_test is not None and automl_y_pred is not None:
            print_section("AUTOML SAVED PREDICTIONS ANALYSIS")
            automl_y_test = np.array(automl_y_test)
            automl_y_pred = np.array(automl_y_pred)
            
            from sklearn.metrics import accuracy_score, f1_score
            if task_type == 'classification':
                saved_acc = accuracy_score(automl_y_test, automl_y_pred)
                saved_f1 = f1_score(automl_y_test, automl_y_pred, average='weighted', zero_division=0)
                print(f"  AutoML saved accuracy: {saved_acc:.4f} ({saved_acc*100:.2f}%)")
                print(f"  AutoML saved F1:       {saved_f1:.4f}")
                print(f"  Manual accuracy:       {manual_metrics['accuracy']:.4f} ({manual_metrics['accuracy']*100:.2f}%)")
                print(f"  Manual F1:             {manual_metrics['f1']:.4f}")
    elif args.pkl:
        print(f"\n  ⚠️  PKL file not found: {args.pkl}")
        print(f"     Download it from AutoML page → Download Model button")

    # ──────────────────────────────────────────────
    # SUMMARY
    # ──────────────────────────────────────────────
    print_header("✅ VERIFICATION COMPLETE")
    print(f"  Dataset:    {args.dataset}")
    print(f"  Target:     {target_col}")
    print(f"  Task:       {task_type}")
    print(f"  Algorithm:  {args.algorithm}")
    print(f"  Features:   {X.shape[1]}")
    print(f"  Train/Test: {len(X_train)}/{len(X_test)}")
    if task_type == 'classification':
        print(f"  Accuracy:   {manual_metrics['accuracy']:.4f} ({manual_metrics['accuracy']*100:.2f}%)")
        print(f"  F1 Score:   {manual_metrics['f1']:.4f}")
    else:
        print(f"  R² Score:   {manual_metrics['r2']:.4f}")
        print(f"  RMSE:       {manual_metrics['rmse']:.4f}")

    if target_encoder is not None:
        print(f"  Classes:    {list(target_encoder.classes_)}")

    print(f"\n  ℹ️  To compare with AutoML, download the .pkl from the ML Predictions page")
    print(f"     and run: python verify_automl_model.py --dataset your_data.csv --pkl model.pkl")
    print()


if __name__ == '__main__':
    main()
