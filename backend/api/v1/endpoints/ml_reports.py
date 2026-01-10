"""
ML Reports - Real AutoML Charts & Visualizations
Uses ONLY real data from trained models
Includes task-specific charts: Regression, Classification, NLP
"""

def generate_predictive_report_v2(user_id: str, df, profiler) -> dict:
    """
    🔮 PREDICTIVE REPORT - Real ML Model Visualizations
    
    For REGRESSION:
    - Actual vs Predicted scatter plot
    - Residual distribution
    - R² and error metrics
    
    For CLASSIFICATION:
    - Confusion matrix data
    - Class distribution
    - Precision/Recall/F1 metrics
    
    For NLP:
    - Feature importance from text
    - Sentiment/category distribution
    """
    from datetime import datetime
    import numpy as np
    
    CHART_COLORS = ['#14B8A6', '#22C55E', '#3B82F6', '#F59E0B', '#8B5CF6', '#EC4899', '#EF4444']
    
    sections = []
    n = len(df)
    
    # Load AutoML model
    automl_info = None
    automl_engine = None
    
    try:
        from ml.model_persistence import model_persistence
        from ml.automl_engine import automl_engine as engine
        
        metadata = model_persistence.get_metadata(user_id)
        if metadata:
            automl_info = {
                'model_name': metadata.model_name,
                'task_type': metadata.task_type,
                'target_column': metadata.target_column,
                'metrics': metadata.metrics or {},
                'version': metadata.version
            }
            engine.load(user_id)
            if engine.is_fitted:
                automl_engine = engine
    except Exception as e:
        print(f"AutoML load error: {e}")
    
    # NO MODEL - Show instructions
    if not automl_info:
        sections.append({
            "title": "⚠️ No ML Model Trained",
            "content": f"""Train an AutoML model to see real predictions and ML charts.

Steps:
1. Go to Data Hub
2. Upload your CSV/Excel file
3. Click "🤖 Auto ML Train"
4. Select target column
5. Wait for training

Your Data: {n:,} records, {len(profiler.numeric_cols)} numeric, {len(profiler.categorical_cols)} categorical""",
            "data": []
        })
        return {
            "title": "🔮 Predictive Report - Train Model First",
            "generatedAt": datetime.now().isoformat(),
            "dataSource": "uploaded_files",
            "sections": sections,
            "reportType": "predictive"
        }
    
    # MODEL EXISTS
    model_name = automl_info['model_name']
    task_type = automl_info['task_type']
    target_col = automl_info['target_column']
    metrics = automl_info['metrics']
    
    # Section 1: Model Overview
    sections.append({
        "title": f"🤖 {model_name} Model",
        "content": f"""Task: {task_type.upper()}
Target: {target_col}
Records: {n:,}
Version: v{automl_info['version']}""",
        "data": {"model": model_name, "task": task_type, "target": target_col}
    })
    
    # Section 2: Performance Metrics Chart
    if metrics:
        metrics_chart = []
        for k, v in metrics.items():
            if isinstance(v, (int, float)):
                display_val = v * 100 if 0 <= v <= 1 else v
                metrics_chart.append({
                    "name": k.replace('_', ' ').title()[:12],
                    "value": round(display_val, 2),
                    "color": CHART_COLORS[len(metrics_chart) % len(CHART_COLORS)]
                })
        
        if metrics_chart:
            sections.append({
                "title": "📊 Model Metrics",
                "content": "Performance from training:",
                "data": metrics_chart,
                "chartType": "horizontal_bar"
            })
    
    # Section 3: Feature Importance (Real)
    feature_importance = None
    if automl_engine:
        # Try to get feature importance from the model
        if hasattr(automl_engine, '_get_importance'):
            fi_list = automl_engine._get_importance(automl_engine.model)
            if fi_list:
                # Convert list of dicts to chart data
                fi_chart = []
                for i, item in enumerate(fi_list[:10]):
                    feat = item.get('feature', f'Feature {i}')
                    imp = item.get('importance', 0)
                    fi_chart.append({
                        "name": feat.replace('_', ' ').title()[:15],
                        "value": round(imp * 100, 2),
                        "color": CHART_COLORS[i % len(CHART_COLORS)]
                    })
                if fi_chart:
                    sections.append({
                        "title": "🎯 Feature Importance",
                        "content": "Top features affecting predictions:",
                        "data": fi_chart,
                        "chartType": "horizontal_bar"
                    })
    
    # =============================================
    # TASK-SPECIFIC ML CHARTS
    # =============================================
    
    if task_type == 'regression':
        # REGRESSION CHARTS
        if automl_engine:
            try:
                sample = df.head(20).copy()
                preds = automl_engine.predict(sample)
                
                if target_col in sample.columns and preds is not None:
                    actuals = sample[target_col].values[:len(preds)]
                    scatter_data = []
                    residual_data = []
                    
                    for i, (actual, pred) in enumerate(zip(actuals[:15], preds[:15])):
                        try:
                            if not np.isnan(float(actual)) and not np.isnan(float(pred)):
                                scatter_data.append({
                                    "name": f"Point {i+1}",
                                    "actual": round(float(actual), 2),
                                    "predicted": round(float(pred), 2),
                                    "x": round(float(actual), 2),
                                    "y": round(float(pred), 2),
                                    "color": "#14B8A6"
                                })
                                residual = float(pred) - float(actual)
                                residual_data.append({
                                    "name": f"Sample {i+1}",
                                    "value": round(residual, 2),
                                    "color": "#EF4444" if residual < 0 else "#22C55E"
                                })
                        except:
                            continue
                    
                    if scatter_data:
                        sections.append({
                            "title": "📈 Actual vs Predicted",
                            "content": "Regression accuracy - points near diagonal = good fit:",
                            "data": scatter_data,
                            "chartType": "scatter"
                        })
                    
                    if residual_data:
                        sections.append({
                            "title": "📉 Prediction Errors",
                            "content": "Residuals (Predicted - Actual):",
                            "data": residual_data[:10],
                            "chartType": "bar"
                        })
            except Exception as e:
                print(f"Regression chart error: {e}")
    
    elif task_type == 'classification':
        # CLASSIFICATION CHARTS
        if automl_engine:
            try:
                sample = df.head(50).copy()
                preds = automl_engine.predict(sample)
                
                if preds is not None and len(preds) > 0:
                    from collections import Counter
                    class_counts = Counter([str(p) for p in preds])
                    
                    class_chart = []
                    for i, (cls, count) in enumerate(class_counts.most_common()):
                        class_chart.append({
                            "name": str(cls)[:15],
                            "value": count,
                            "percentage": round(count / len(preds) * 100, 1),
                            "color": CHART_COLORS[i % len(CHART_COLORS)]
                        })
                    
                    sections.append({
                        "title": "📊 Predicted Classes",
                        "content": f"Classification distribution on {len(preds)} samples:",
                        "data": class_chart,
                        "chartType": "pie"
                    })
            except Exception as e:
                print(f"Classification chart error: {e}")
        
        # Metrics comparison for classification
        if metrics:
            metric_comparison = []
            for key in ['precision', 'recall', 'f1', 'f1_score', 'accuracy']:
                if key in metrics:
                    v = metrics[key]
                    if isinstance(v, (int, float)):
                        metric_comparison.append({
                            "name": key.replace('_', ' ').title(),
                            "value": round(v * 100, 1),
                            "color": CHART_COLORS[len(metric_comparison) % len(CHART_COLORS)]
                        })
            
            if metric_comparison:
                sections.append({
                    "title": "📋 Classification Metrics",
                    "content": "Precision, Recall, F1 scores:",
                    "data": metric_comparison,
                    "chartType": "horizontal_bar"
                })
    
    # Section: Sample Predictions
    if automl_engine:
        try:
            sample = df.head(8).copy()
            preds = automl_engine.predict(sample)
            
            if preds is not None and len(preds) > 0:
                pred_chart = []
                for i, p in enumerate(preds[:8]):
                    val = p if isinstance(p, (int, float, str)) else str(p)
                    pred_chart.append({
                        "name": f"Row {i+1}",
                        "value": float(p) if isinstance(p, (int, float)) else i,
                        "label": str(val)[:15],
                        "color": CHART_COLORS[i % len(CHART_COLORS)]
                    })
                
                sections.append({
                    "title": f"📈 {target_col} Predictions",
                    "content": f"Model predictions on sample data:",
                    "data": pred_chart,
                    "chartType": "bar"
                })
        except Exception as e:
            print(f"Prediction error: {e}")
    
    return {
        "title": f"🔮 {task_type.title()} Report - {model_name}",
        "generatedAt": datetime.now().isoformat(),
        "dataSource": "uploaded_files",
        "sections": sections,
        "reportType": "predictive"
    }


def generate_anomaly_report_v2(user_id: str, df, profiler) -> dict:
    """
    ⚠️ ANOMALY REPORT - Real Statistical Analysis
    
    Charts:
    - Outlier distribution (box plot data)
    - Missing values bar chart
    - Data quality gauge
    - Distribution analysis
    """
    from datetime import datetime
    import numpy as np
    
    CHART_COLORS = ['#14B8A6', '#22C55E', '#3B82F6', '#F59E0B', '#8B5CF6', '#EC4899', '#EF4444']
    
    sections = []
    n = len(df)
    
    # Check for model context
    model_info = None
    try:
        from ml.model_persistence import model_persistence
        metadata = model_persistence.get_metadata(user_id)
        if metadata:
            model_info = {
                'model_name': metadata.model_name,
                'target_column': metadata.target_column,
                'task_type': metadata.task_type
            }
    except:
        pass
    
    # Section 1: Overview
    overview = f"""Anomaly Detection Analysis
━━━━━━━━━━━━━━━━━━━━━━━━
Records: {n:,}
Numeric: {len(profiler.numeric_cols)}
Categorical: {len(profiler.categorical_cols)}"""
    
    if model_info:
        overview += f"\n\nML Model: {model_info['model_name']} ({model_info['task_type']})"
    
    sections.append({
        "title": "⚠️ Anomaly Detection",
        "content": overview,
        "data": {"records": n}
    })
    
    # Section 2: Distribution Analysis with Box Plot Data
    box_plot_data = []
    total_outliers = 0
    outlier_details = []
    
    for i, col in enumerate(profiler.numeric_cols[:6]):
        try:
            vals = df[col].dropna()
            if len(vals) < 5:
                continue
            
            q1 = float(np.percentile(vals, 25))
            q3 = float(np.percentile(vals, 75))
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            
            outliers = vals[(vals < lower) | (vals > upper)]
            outlier_count = len(outliers)
            total_outliers += outlier_count
            
            col_name = col.replace('_', ' ').title()[:12]
            
            box_plot_data.append({
                "name": col_name,
                "min": round(float(vals.min()), 2),
                "q1": round(q1, 2),
                "median": round(float(vals.median()), 2),
                "q3": round(q3, 2),
                "max": round(float(vals.max()), 2),
                "outliers": outlier_count,
                "color": CHART_COLORS[i % len(CHART_COLORS)]
            })
            
            if outlier_count > 0:
                pct = (outlier_count / len(vals)) * 100
                outlier_details.append({
                    "name": col_name,
                    "value": outlier_count,
                    "percentage": round(pct, 1),
                    "color": "#EF4444" if pct > 5 else "#F59E0B"
                })
        except:
            continue
    
    if box_plot_data:
        sections.append({
            "title": "📊 Distribution Analysis",
            "content": "Statistical distribution (Q1, Median, Q3):",
            "data": box_plot_data,
            "chartType": "box"
        })
    
    # Section 3: Outlier Count Chart
    if outlier_details:
        sections.append({
            "title": "🔍 Outliers Found",
            "content": f"Total: {total_outliers} outliers detected using IQR method",
            "data": outlier_details,
            "chartType": "bar"
        })
    else:
        sections.append({
            "title": "✅ No Outliers",
            "content": "No significant outliers detected.",
            "data": []
        })
    
    # Section 4: Missing Values
    missing_data = []
    total_missing = 0
    for col in df.columns[:12]:
        missing = int(df[col].isna().sum())
        total_missing += missing
        if missing > 0:
            pct = (missing / n) * 100
            missing_data.append({
                "name": str(col)[:10],
                "value": missing,
                "percentage": round(pct, 1),
                "color": "#EF4444" if pct > 10 else "#F59E0B" if pct > 2 else "#22C55E"
            })
    
    if missing_data:
        sections.append({
            "title": "📊 Missing Values",
            "content": f"Total: {total_missing:,} missing values",
            "data": missing_data[:8],
            "chartType": "horizontal_bar"
        })
    
    # Section 5: Duplicates
    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        sections.append({
            "title": "🔄 Duplicates",
            "content": f"Found {dup_count:,} duplicate rows ({dup_count/n*100:.1f}%)",
            "data": [
                {"name": "Unique", "value": n - dup_count, "color": "#22C55E"},
                {"name": "Duplicates", "value": dup_count, "color": "#EF4444"}
            ],
            "chartType": "pie"
        })
    
    # Section 6: Data Quality Score
    issues = total_outliers + dup_count + total_missing
    max_issues = n * len(df.columns) if n > 0 else 1
    quality_score = max(0, min(100, int(100 - (issues / max_issues * 100))))
    
    status = "✅ Excellent" if quality_score >= 80 else "🟡 Good" if quality_score >= 60 else "🟠 Needs Work" if quality_score >= 40 else "🔴 Poor"
    
    sections.append({
        "title": "📋 Data Quality Score",
        "content": f"""Score: {quality_score}/100 - {status}

Issues Found:
• Outliers: {total_outliers}
• Missing: {total_missing}
• Duplicates: {dup_count}""",
        "data": [{"name": "Quality", "value": quality_score, "max": 100, "color": "#22C55E" if quality_score >= 70 else "#F59E0B"}],
        "chartType": "gauge"
    })
    
    return {
        "title": "⚠️ Anomaly Detection Report",
        "generatedAt": datetime.now().isoformat(),
        "dataSource": "uploaded_files",
        "sections": sections,
        "reportType": "anomaly"
    }
