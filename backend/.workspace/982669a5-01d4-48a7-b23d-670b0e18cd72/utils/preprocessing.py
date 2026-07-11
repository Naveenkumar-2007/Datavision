"""
🔧 Preprocessing Utilities — Mirrors DataVision AutoML Pipeline
===================================================================
These utilities replicate the EXACT preprocessing pipeline used by
DataVision's ProductionDataCleaner + ProductionFeatureEngineer.

Pipeline steps:
1. Remove useless columns (IDs, URLs, high-cardinality strings)
2. Remove duplicates
3. Smart type conversion (parse $, M/K units, commas)
4. KNN imputation for numerics (median fallback)
5. Mode fill for categoricals
6. Replace inf/-inf with median
7. Remove constant columns
8. IQR-based outlier capping
9. Log-transform skewed features
10. RobustScaler for numeric features
11. Categorical encoding (binary→label, low-card→one-hot, high-card→label+freq)
12. VarianceThreshold to remove near-constant features
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, RobustScaler
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import KNNImputer

TARGET_COLUMN = 'price_range'
TASK_TYPE = 'classification'
FEATURE_COLUMNS = ['battery_power', 'blue', 'clock_speed', 'dual_sim', 'fc', 'four_g', 'int_memory', 'm_dep', 'mobile_wt', 'n_cores', 'pc', 'px_height', 'px_width', 'ram', 'sc_h', 'sc_w', 'talk_time', 'three_g', 'touch_screen', 'wifi']


def detect_task_type(y):
    """Auto-detect classification vs regression."""
    if y.dtype == 'object' or y.nunique() < 20:
        return 'classification'
    return 'regression'


def remove_useless_columns(df, target_col=TARGET_COLUMN):
    """Remove ID-like, URL, and high-cardinality columns (same as DataVision)."""
    id_patterns = ['unnamed', 'index', '_id', 'guid', 'uuid', 'url', 'link', 'href', 'path']
    cols_to_drop = []
    for col in df.columns:
        if col == target_col:
            continue
        col_lower = col.lower().strip()
        if any(pat in col_lower for pat in id_patterns):
            cols_to_drop.append(col)
        elif df[col].dtype == 'object' and df[col].nunique() / max(len(df), 1) > 0.9:
            cols_to_drop.append(col)
    return df.drop(columns=cols_to_drop, errors='ignore') if cols_to_drop else df


def smart_type_conversion(df, target_col=TARGET_COLUMN):
    """Parse hidden numerics: $, M/K units, commas (same as DataVision)."""
    for col in df.select_dtypes(include=['object']).columns:
        if col == target_col:
            continue
        sample = df[col].dropna().head(20)
        if len(sample) == 0:
            continue
        converted = 0
        for val in sample:
            try:
                v = str(val).replace('$', '').replace(',', '').strip()
                if v.upper().endswith(('M', 'K', '+')):
                    float(v[:-1])
                else:
                    float(v)
                converted += 1
            except:
                pass
        if converted / max(len(sample), 1) > 0.6:
            def parse_val(val):
                if pd.isna(val):
                    return np.nan
                v = str(val).replace('$', '').replace(',', '').strip()
                try:
                    if v.upper().endswith('M'): return float(v[:-1]) * 1e6
                    if v.upper().endswith('K'): return float(v[:-1]) * 1e3
                    if v.endswith('+'): return float(v[:-1])
                    return float(v)
                except:
                    return np.nan
            df[col] = df[col].apply(parse_val)
    return df


def impute_missing(df, target_col=TARGET_COLUMN):
    """KNN imputation for numerics, mode fill for categoricals (same as DataVision)."""
    numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != target_col]
    if numeric_cols and df[numeric_cols].isna().any().any():
        try:
            imputer = KNNImputer(n_neighbors=5, weights='distance')
            df[numeric_cols] = imputer.fit_transform(df[numeric_cols])
        except:
            for col in numeric_cols:
                df[col] = df[col].fillna(df[col].median())
    
    for col in df.select_dtypes(include=['object', 'category']).columns:
        if col == target_col:
            continue
        mode = df[col].mode()
        df[col] = df[col].fillna(mode.iloc[0] if len(mode) > 0 else '_MISSING_')
    return df


def cap_outliers_iqr(df, target_col=TARGET_COLUMN):
    """IQR-based outlier capping with [1st, 99th] percentile bounds (same as DataVision)."""
    for col in df.select_dtypes(include=[np.number]).columns:
        if col == target_col:
            continue
        Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        IQR = Q3 - Q1
        p1, p99 = df[col].quantile(0.01), df[col].quantile(0.99)
        lower = max(p1, Q1 - 3 * IQR)
        upper = min(p99, Q3 + 3 * IQR)
        df[col] = df[col].clip(lower=lower, upper=upper)
    return df


def engineer_features(X):
    """Feature engineering matching DataVision's ProductionFeatureEngineer."""
    label_encoders = {}
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Log-transform skewed numerics (skewness > 2, non-negative)
    for col in numeric_cols:
        if (X[col] >= 0).all() and abs(X[col].skew()) > 2:
            X[f'{col}_log'] = np.log1p(X[col])
    
    # RobustScaler (same as DataVision, not StandardScaler)
    numeric_cols_all = X.select_dtypes(include=[np.number]).columns.tolist()
    scaler = RobustScaler()
    if numeric_cols_all:
        X[numeric_cols_all] = scaler.fit_transform(X[numeric_cols_all])
    
    # Polynomial features (top 4 numeric, squared + interactions)
    if 2 <= len(numeric_cols) <= 10:
        top_n = min(4, len(numeric_cols))
        top_cols = numeric_cols[:top_n]
        for col in top_cols:
            X[f'{col}_sq'] = X[col] ** 2
        for i in range(len(top_cols)):
            for j in range(i + 1, len(top_cols)):
                X[f'{top_cols[i]}_x_{top_cols[j]}'] = X[top_cols[i]] * X[top_cols[j]]
    
    # Categorical encoding
    for col in categorical_cols:
        nuniq = X[col].nunique()
        if nuniq <= 2:  # Binary → LabelEncoder
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            label_encoders[col] = le
        elif nuniq <= 10:  # Low cardinality → one-hot
            dummies = pd.get_dummies(X[col], prefix=col, drop_first=False)
            X = pd.concat([X.drop(columns=[col]), dummies], axis=1)
        else:  # High cardinality → label + frequency encoding
            le = LabelEncoder()
            X[f'{col}_label'] = le.fit_transform(X[col].astype(str))
            freq = X[col].value_counts(normalize=True)
            X[f'{col}_freq'] = X[col].map(freq)
            label_encoders[col] = le
            X = X.drop(columns=[col])
    
    # Force float + clean
    for col in X.columns:
        try:
            X[col] = X[col].astype(float)
        except:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str)).astype(float)
    X = X.replace([np.inf, -np.inf], 0).fillna(0)
    
    # VarianceThreshold (remove near-constant, threshold=0.01)
    try:
        vt = VarianceThreshold(threshold=0.01)
        X = pd.DataFrame(vt.fit_transform(X), columns=X.columns[vt.get_support()], index=X.index)
    except:
        pass
    
    return X, label_encoders, scaler


def full_preprocess(df, target_column=TARGET_COLUMN):
    """Complete DataVision preprocessing pipeline.
    
    Combines ProductionDataCleaner.clean() + ProductionFeatureEngineer.fit_transform().
    """
    # Step 1: Clean
    df = df.dropna(subset=[target_column])
    df = df.drop_duplicates()
    
    # Strip whitespace and replace string NaN variants
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip()
        df[col] = df[col].replace(['nan', 'NaN', 'None', 'null', 'NULL', ''], np.nan)
    
    df = remove_useless_columns(df, target_column)
    df = smart_type_conversion(df, target_column)
    df = impute_missing(df, target_column)
    
    # Replace inf, remove constant columns
    for col in df.select_dtypes(include=[np.number]).columns:
        if col != target_column:
            df[col] = df[col].replace([np.inf, -np.inf], df[col].replace([np.inf, -np.inf], np.nan).median())
    const_cols = [c for c in df.columns if c != target_column and df[c].nunique() <= 1]
    df = df.drop(columns=const_cols, errors='ignore')
    
    df = cap_outliers_iqr(df, target_column)
    df[df.select_dtypes(include=[np.number]).columns] = df.select_dtypes(include=[np.number]).fillna(0)
    
    # Step 2: Split target
    X = df.drop(columns=[target_column])
    y = df[target_column]
    
    task_type = detect_task_type(y)
    target_encoder = None
    if task_type == 'classification':
        target_encoder = LabelEncoder()
        y = pd.Series(target_encoder.fit_transform(y))
    
    # Step 3: Engineer features
    X, label_encoders, scaler = engineer_features(X)
    feature_cols = X.columns.tolist()
    
    return X, y, task_type, target_encoder, label_encoders, scaler, feature_cols
