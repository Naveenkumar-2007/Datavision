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
            # Load the model and check if it has a trained model
            if engine.load(user_id) and engine.model is not None:
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
    
    # MODEL EXISTS - Robust Data Extraction
    model_name = automl_info.get('model_name', 'Unknown Model')
    task_type = automl_info.get('task_type', 'unknown')
    
    # Robust target column extraction
    target_col = automl_info.get('target_column')
    if not target_col and automl_engine:
        target_col = getattr(automl_engine, 'target_column', 'Unknown Target')
    if not target_col:
        target_col = "Unknown Target"
        
    metrics = automl_info.get('metrics') or {}
    # Fallback to engine metrics if metadata empty
    if not metrics and automl_engine:
        metrics = getattr(automl_engine, 'metrics', {})
    
    # ---------------------------------------------
    # PRE-LOAD REAL CHARTS (To decide on legacy sections)
    # ---------------------------------------------
    real_charts = {}
    if automl_engine:
        try:
            from ml.model_persistence import model_persistence
            # 1. Try to load saved charts
            saved_charts = model_persistence.get_charts(user_id)
            if saved_charts:
                real_charts = saved_charts
        except:
            pass
            
    # ---------------------------------------------
    # GENERATE DYNAMIC INSIGHTS (Natural Language)
    # ---------------------------------------------
    primary_metric = "Accuracy" if task_type == "classification" else "R² Score"
    primary_score = metrics.get('accuracy', metrics.get('r2_score', 0))
    
    # Format score for display
    if primary_metric == "R² Score" and primary_score < -1:
        score_display = "(Negative R²)"
    else:
        score_display = f"{primary_score:.1%}"
    
    performance_text = "moderate"
    if primary_score > 0.85: performance_text = "excellent"
    elif primary_score > 0.7: performance_text = "good" 
    elif primary_score < 0.5: performance_text = "poor"
    
    # Get top features for narrative
    top_features_text = ""
    if automl_engine and hasattr(automl_engine, '_get_importance'):
        fi_list = automl_engine._get_importance(automl_engine.model)
        if fi_list:
            top_3 = [f.get('feature', '').replace('_', ' ').title() for f in fi_list[:3]]
            if top_3:
                top_features_text = f"The most influential factors driving these predictions are {', '.join(top_3)}."

    # Section 0: Executive Summary
    sections.append({
        "title": "📝 Executive Summary",
        "content": f"""The {model_name} model has been trained for {task_type.upper()} tasks on the target '{target_col}'.

Performance Assessment:
The model demonstrates {performance_text} performance with a {primary_metric} of {score_display}. {top_features_text}

Recommendation:
{("Reliable for automated decision making." if primary_score > 0.8 else "Use for guidance, but verify critical cases manually.")}""",
        "data": {"model": model_name, "score": primary_score, "quality": performance_text}
    })
    
    # Section 1: Model Overview
    sections.append({
        "title": f"🤖 Model Configuration",
        "content": f"""• Algorithm: {model_name}
• Task Type: {task_type.title()}
• Target Variable: {target_col}
• Training Records: {n:,}
• Model Version: v{automl_info.get('version', '1')}""",
        "data": {"model": model_name, "task": task_type, "target": target_col}
    })
    
    # Section 2: Performance Metrics Chart (Legacy - ONLY if no real charts, or if explicit metric charts missing)
    # We hide this if we have the new visual charts to avoid duplication
    if metrics and not real_charts:
        metrics_chart = []
        metric_names = {
            'accuracy': 'Accuracy', 'precision': 'Precision', 'recall': 'Recall', 'f1': 'F1 Score', 'f1_score': 'F1 Score',
            'r2_score': 'R² Score', 'mae': 'MAE (Error)', 'rmse': 'RMSE (Error)'
        }
        
        for k, v in metrics.items():
            if isinstance(v, (int, float)) and k in metric_names:
                display_val = v
                # Normalize 0-1 metrics to percentages for display, keep errors as is
                if k not in ['mae', 'rmse'] and 0 <= v <= 1:
                     display_val = v * 100
                
                metrics_chart.append({
                    "name": metric_names.get(k, k),
                    "value": round(display_val, 2),
                    "color": CHART_COLORS[len(metrics_chart) % len(CHART_COLORS)]
                })
        
        if metrics_chart:
            sections.append({
                "title": "📊 Performance Metrics",
                "content": f"Key performance indicators for {model_name}. Higher is better (except error metrics).",
                "data": metrics_chart,
                "chartType": "horizontal_bar"
            })
    
    # Section 3: Feature Importance (Legacy - ONLY if no real charts)
    feature_importance = None
    if automl_engine and not real_charts:
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
                        "title": "🎯 Key Drivers (Feature Importance)",
                        "content": "These features have the strongest impact on the target variable. Focus on optimizing these factors to influence outcomes.",
                        "data": fi_chart,
                        "chartType": "horizontal_bar"
                    })
    
    # =============================================
    # TASK-SPECIFIC REAL ML CHARTS (Images)
    # =============================================
    
    if automl_engine:
        try:
            # 2. Fallback: Regenerate if missing (Logic for legacy or prediction-only)
            if not real_charts and target_col in df.columns:
                # Use a larger sample for chart generation to ensure representative visuals
                chart_sample_size = min(500, len(df))
                sample = df.head(chart_sample_size).copy()
                preds = automl_engine.predict(sample)
                
                # Get probabilities if available (for ROC/PR curves)
                probs = None
                if task_type == 'classification' and hasattr(automl_engine.model, 'predict_proba'):
                    try:
                        probs = automl_engine.model.predict_proba(sample)
                    except:
                        pass
                
                y_true = sample[target_col].values
                from ml.chart_generator import generate_ml_charts
                
                # Generate comprehensive chart suite on the fly
                real_charts = generate_ml_charts(
                    task_type=task_type,
                    y_test=y_true,
                    y_pred=preds,
                    y_proba=probs,
                    model_name=model_name,
                    class_names=automl_engine.classes_ if hasattr(automl_engine, 'classes_') else None
                )
            
            # 3. Add charts to sections
            # Map charts to friendly titles and descriptions
            chart_descriptions = {
                'confusion_matrix': ('Confusion Matrix', 'Visualizes how often the model confuses different classes. Diagonal values represent correct predictions.'),
                'roc_curve': ('ROC Curve', 'Shows the trade-off between True Positive Rate and False Positive Rate. AUC score closer to 1.0 is better.'),
                'feature_importance': ('Feature Importance', 'Ranks features by their influence on the model\'s decisions.'),
                'actual_vs_predicted': ('Actual vs Predicted', 'Comparison of model predictions against real values. Points along the diagonal line indicate perfect accuracy.'),
                'residuals_analysis': ('Residuals Analysis', 'Analyzes prediction errors to check for bias or patterns.'),
                'class_distribution': ('Class Distribution', 'Compare predicted class frequencies against actual frequencies.'),
                'precision_recall': ('Precision-Recall Curve', 'Trade-off between Precision and Recall, crucial for imbalanced datasets.'),
                'prediction_overview': ('Prediction Overview', 'Visualizes predictions against actual values across the dataset.'),
                'error_distribution': ('Error Distribution', 'Histogram of prediction errors. Narrower distribution centered at 0 means better accuracy.'),
                'distribution_grid': ('Feature Distributions', 'Histograms showing the spread of data for top numeric features.'),
                'boxplot_grid': ('Feature Box Plots', 'Box plots showing outliers and quartiles for numeric features.'),
                'correlation_heatmap': ('Correlation Heatmap', 'Heatmap showing how features correlate with each other.'),
                'model_comparison': ('Model Comparison', 'Performance comparison of all trained models.')
            }
            
            for chart_key, base64_img in real_charts.items():
                if chart_key in chart_descriptions:
                    title, desc = chart_descriptions[chart_key]
                    sections.append({
                        "title": f"📊 {title}",
                        "content": desc,
                        "data": {"image": base64_img},
                        "chartType": "image"
                    })
            
            # 4. Handle Prediction-Only Mode (No Target Column AND No Saved Charts)
            if not real_charts and target_col not in df.columns:
                # No ground truth - Prediction Only Mode
                if preds is not None:
                    # Add Prediction Distribution (Pie Chart)
                    if task_type == 'classification':
                        from collections import Counter
                        class_counts = Counter([str(p) for p in preds])
                        class_chart = [{"name": str(k)[:15], "value": v, "color": CHART_COLORS[i % len(CHART_COLORS)]} 
                                      for i, (k, v) in enumerate(class_counts.most_common(10))]
                        sections.append({
                            "title": "📊 Predicted Class Distribution",
                            "content": f"Distribution of predicted classes for the {len(preds)} analyzed records.",
                            "data": class_chart,
                            "chartType": "pie"
                        })
                    
                    # Add Sample Predictions
                    pred_chart = []
                    for i, p in enumerate(preds[:10]):
                        val = p if isinstance(p, (int, float, str)) else str(p)
                        pred_chart.append({
                            "name": f"Rec {i+1}",
                            "value": float(p) if isinstance(p, (int, float)) else i,
                            "label": str(val)[:15],
                            "color": CHART_COLORS[i % len(CHART_COLORS)]
                        })
                    sections.append({
                        "title": "🔎 Prediction Samples",
                        "content": "A glimpse of the model's output on your data.",
                        "data": pred_chart,
                        "chartType": "bar"
                    })

        except Exception as e:
            print(f"Real ML Chart Generation Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Section: Strategic Recommendations (Action Item for Frontend)
    sections.append({
        "title": "⚡ Strategic Recommendations",
        "content": f"""1. Verify the model's predictions on new data using the 'Predict' tab.
2. Focus on the key drivers ({top_3[0] if 'top_3' in locals() and top_3 else 'identified features'}) to influence outcomes.
3. {("Since the model is highly accurate, consider automating workflows." if primary_score > 0.8 else "Use these predictions as a support tool for human subject matter experts.")}""",
        "data": []
    })

    return {
        "title": f"🔮 AI Predictive Report - {model_name}",
        "generatedAt": datetime.now().isoformat(),
        "dataSource": "AutoML Engine",
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
    
    # Section 7: Recommended Actions
    actions = []
    
    # ===========================================
    # SECTION 8: ML Anomaly Visualization (Isolation Forest)
    # ===========================================
    if len(profiler.numeric_cols) >= 2 and n >= 10:
        try:
            from sklearn.ensemble import IsolationForest
            from ml.chart_generator import generate_ml_charts
            
            # Prepare data
            X = df[profiler.numeric_cols].dropna().values
            # Run Isolation Forest
            iso = IsolationForest(contamination=0.05, random_state=42)
            y_pred = iso.fit_predict(X) # 1 for normal, -1 for anomaly
            
            # Convert to cluster labels (0=Anomaly, 1=Normal)
            # IsolationForest returns -1 for anomaly, 1 for normal
            # Let's map -1 -> 0 (Anomaly), 1 -> 1 (Normal) for better visualization colors
            cluster_labels = np.where(y_pred == -1, 0, 1)
            
            charts = generate_ml_charts(
                task_type='clustering',
                y_test=cluster_labels, # Dummy ground truth (same as pred) to satisfy signature
                y_pred=cluster_labels,
                X_test=X,
                feature_names=profiler.numeric_cols,
                class_names=['Anomaly', 'Normal']
            )
            
            if 'cluster_scatter' in charts:
                sections.append({
                    "title": "📊 Anomaly Visualization (PCA)",
                    "content": "2D projection of data using Principal Component Analysis (PCA). Points in Cluster 0 (Anomaly) are statistically distinct from normal patterns.",
                    "data": {"image": charts['cluster_scatter']},
                    "chartType": "image"
                })
                
                # Check for other useful charts like 'cluster_box_plots'
                if 'cluster_box_plots' in charts:
                    sections.append({
                        "title": "📦 Feature Distribution by Anomaly Status",
                        "content": "Comparison of feature distributions between Normal (1) and Anomalous (0) records.",
                        "data": {"image": charts['cluster_box_plots']},
                        "chartType": "image"
                    })
                    
        except Exception as e:
            print(f"Anomaly ML visual error: {e}")

    if total_outliers > 0:
        actions.append(f"1. Investigate the {total_outliers} detected outliers in the 'Outliers Found' section.")
    if total_missing > 0:
        actions.append(f"2. Consider imputing or removing the {total_missing} missing values.")
    if dup_count > 0:
        actions.append(f"3. Remove {dup_count} duplicate records to prevent data leakage.")
    
    if not actions:
        actions.append("1. Data quality is excellent. Proceed with analysis or modeling.")
        
    sections.append({
        "title": "⚡ Recommended Actions",
        "content": "\n".join(actions),
        "data": []
    })
    
    return {
        "title": "⚠️ Anomaly Detection Report",
        "generatedAt": datetime.now().isoformat(),
        "dataSource": "uploaded_files",
        "sections": sections,
        "reportType": "anomaly"
    }
