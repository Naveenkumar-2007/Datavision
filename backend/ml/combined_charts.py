"""
🎨 COMBINED CHARTS - Multi-Mode ML Comparison Visualizations
============================================================

Production-level charts for comparing ML, NLP, and Deep Learning models
when multiple modes are trained together.

Charts Generated:
- Mode Performance Comparison (Bar chart)
- Metrics Radar Chart (Multi-mode)
- Leaderboard Heatmap
- Training Time Comparison
- Accuracy Distribution
"""

import io
import base64
import logging
from typing import Dict, List, Optional, Any
import numpy as np

logger = logging.getLogger(__name__)

# Professional Light Theme Color Palette (Matches chart_generator.py)
COLORS = [
    '#2563eb',  # Primary Blue
    '#16a34a',  # Success Green
    '#dc2626',  # Alert Red
    '#f59e0b',  # Warning Amber
    '#8b5cf6',  # Purple
    '#ec4899',  # Pink
    '#06b6d4',  # Cyan
    '#84cc16',  # Lime
    '#f97316',  # Orange
    '#6366f1',  # Indigo
]

# Mode-specific colors
MODE_COLORS = {
    'traditional': '#2563eb',  # Blue for Traditional ML
    'Traditional ML': '#2563eb',
    'nlp': '#16a34a',  # Green for NLP
    'NLP': '#16a34a',
    'deep_learning': '#8b5cf6',  # Purple for Deep Learning
    'Deep Learning': '#8b5cf6',
}


def _fig_to_base64(fig) -> str:
    """Convert matplotlib figure to base64 string"""
    try:
        import matplotlib.pyplot as plt
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=150, 
                   facecolor='white', edgecolor='none')
        buf.seek(0)
        data = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return data
    except Exception as e:
        logger.error(f"Figure to base64 error: {e}")
        return ""


def generate_combined_charts(
    all_results: Dict[str, Any],
    leaderboard: List[Dict],
    best_overall_model: Optional[Dict] = None
) -> Dict[str, str]:
    """
    🎨 Generate combined comparison charts for multi-mode training
    
    Args:
        all_results: Results dictionary with keys like 'traditional', 'nlp', 'deep_learning'
        leaderboard: Combined leaderboard with all models
        best_overall_model: The best model across all modes
        
    Returns:
        Dictionary of chart name -> base64 encoded PNG
    """
    charts = {}
    
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
        plt.style.use('seaborn-v0_8-whitegrid')
    except:
        try:
            plt.style.use('seaborn-whitegrid')
        except:
            pass
    
    # Get successful modes
    successful_modes = []
    mode_metrics = {}
    
    for mode in ['traditional', 'nlp', 'deep_learning']:
        result = all_results.get(mode, {})
        if result.get('success'):
            metrics = result.get('metrics', {})
            # Only add if we have actual metrics
            if metrics and isinstance(metrics, dict) and len(metrics) > 0:
                successful_modes.append(mode)
                mode_metrics[mode] = metrics
    
    if len(successful_modes) < 1:
        logger.info("No successful modes with metrics for combined charts")
        return charts
    
    # 1. MODE PERFORMANCE COMPARISON BAR CHART
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        mode_names = []
        mode_scores = []
        bar_colors = []
        
        for mode in successful_modes:
            metrics = mode_metrics.get(mode, {})
            if not metrics:
                continue
            # Get primary score (accuracy for classification, r2 for regression)
            score = metrics.get('accuracy', metrics.get('r2', metrics.get('f1', 0)))
            if score is None:
                score = 0
            try:
                score = float(score)
                if score <= 1:
                    score = score * 100  # Convert to percentage
            except (TypeError, ValueError):
                score = 0
            
            display_name = {
                'traditional': 'Traditional ML',
                'nlp': 'NLP',
                'deep_learning': 'Deep Learning'
            }.get(mode, mode)
            
            mode_names.append(display_name)
            mode_scores.append(score)
            bar_colors.append(MODE_COLORS.get(mode, COLORS[0]))
        
        bars = ax.bar(range(len(mode_names)), mode_scores, color=bar_colors, 
                     edgecolor='#333333', linewidth=0.5)
        
        # Mark the best model
        if best_overall_model:
            best_mode = best_overall_model.get('mode', '')
            for i, mode in enumerate(successful_modes):
                if mode == best_mode:
                    ax.annotate('🏆 BEST', xy=(i, mode_scores[i]), 
                               xytext=(i, mode_scores[i] + 3),
                               ha='center', fontsize=12, fontweight='bold', 
                               color=bar_colors[i])
                    bars[i].set_edgecolor('gold')
                    bars[i].set_linewidth(3)
        
        # Add value labels
        for bar, score in zip(bars, mode_scores):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                   f'{score:.1f}%', ha='center', fontsize=11, fontweight='bold',
                   color='#333333')
        
        ax.set_xticks(range(len(mode_names)))
        ax.set_xticklabels(mode_names, fontsize=12)
        ax.set_ylabel('Score (%)', fontsize=12, color='#333333')
        ax.set_title('🎯 Multi-Mode Performance Comparison', fontsize=14, 
                    fontweight='bold', color='#333333', pad=20)
        max_score = max(mode_scores) if mode_scores and max(mode_scores) > 0 else 100
        ax.set_ylim(0, max_score * 1.15)
        
        plt.tight_layout()
        charts['combined_mode_comparison'] = _fig_to_base64(fig)
        
    except Exception as e:
        logger.warning(f"Mode comparison chart error: {e}")
    
    # 2. MULTI-MODE METRICS RADAR CHART (if multiple modes)
    if len(successful_modes) >= 2:
        try:
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
            
            # Get common metrics
            metric_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
            metric_keys = ['accuracy', 'precision', 'recall', 'f1']
            
            angles = np.linspace(0, 2 * np.pi, len(metric_names), endpoint=False).tolist()
            angles += angles[:1]  # Close the polygon
            
            for mode in successful_modes:
                metrics = mode_metrics.get(mode, {})
                if not metrics:
                    continue
                values = []
                for key in metric_keys:
                    val = metrics.get(key, 0)
                    if val is None:
                        val = 0
                    try:
                        val = float(val)
                        values.append(val if val <= 1 else val / 100)  # Normalize to 0-1
                    except (TypeError, ValueError):
                        values.append(0)
                values += values[:1]  # Close the polygon
                
                display_name = {
                    'traditional': 'Traditional ML',
                    'nlp': 'NLP', 
                    'deep_learning': 'Deep Learning'
                }.get(mode, mode)
                
                color = MODE_COLORS.get(mode, COLORS[0])
                ax.plot(angles, values, 'o-', linewidth=2, label=display_name, 
                       color=color, markersize=6)
                ax.fill(angles, values, alpha=0.15, color=color)
            
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(metric_names, size=11, color='#333333')
            ax.set_ylim(0, 1)
            ax.set_title('📊 Multi-Mode Metrics Comparison', size=14, 
                        fontweight='bold', color='#333333', y=1.1)
            ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
            
            plt.tight_layout()
            charts['combined_metrics_radar'] = _fig_to_base64(fig)
            
        except Exception as e:
            logger.warning(f"Metrics radar chart error: {e}")
    
    # 3. LEADERBOARD HORIZONTAL BAR CHART
    if leaderboard and len(leaderboard) >= 2:
        try:
            fig, ax = plt.subplots(figsize=(12, max(6, len(leaderboard[:10]) * 0.6)))
            
            top_models = leaderboard[:10]
            model_names = []
            scores = []
            bar_colors = []
            
            for item in top_models:
                name = str(item.get('model', 'Unknown'))[:25]
                mode = str(item.get('mode', 'Unknown'))
                score = item.get('score', 0)
                
                # Safe score conversion
                if score is None:
                    score = 0
                try:
                    score = float(score)
                    if score <= 1:
                        score = score * 100
                except (TypeError, ValueError):
                    score = 0
                
                model_names.append(f"{name} ({mode})")
                scores.append(score)
                
                # Get mode-specific color
                mode_key = mode.lower().replace(' ', '_')
                bar_colors.append(MODE_COLORS.get(mode, MODE_COLORS.get(mode_key, COLORS[0])))
            
            # Only proceed if we have valid scores
            if not scores or all(s == 0 for s in scores):
                plt.close(fig)
            else:
                # Reverse for horizontal bar (best at top)
                model_names = model_names[::-1]
                scores = scores[::-1]
                bar_colors = bar_colors[::-1]
                
                bars = ax.barh(range(len(model_names)), scores, color=bar_colors,
                              edgecolor='#333333', linewidth=0.5, height=0.7)
                
                # Highlight the best model
                if len(bars) > 0:
                    bars[-1].set_edgecolor('gold')
                    bars[-1].set_linewidth(3)
                
                # Add value labels
                for bar, score in zip(bars, scores):
                    ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                           f'{score:.1f}%', va='center', fontsize=10, color='#333333')
                
                ax.set_yticks(range(len(model_names)))
                ax.set_yticklabels(model_names, fontsize=10)
                ax.set_xlabel('Score (%)', fontsize=12, color='#333333')
                ax.set_title('🏆 Combined Model Leaderboard', fontsize=14,
                            fontweight='bold', color='#333333', pad=20)
                max_score = max(scores) if scores and max(scores) > 0 else 100
                ax.set_xlim(0, max_score * 1.15)
                
                plt.tight_layout()
            charts['combined_leaderboard'] = _fig_to_base64(fig)
            
        except Exception as e:
            logger.warning(f"Leaderboard chart error: {e}")
    
    # 4. MODE METRICS HEATMAP
    if len(successful_modes) >= 2:
        try:
            import seaborn as sns
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Build metrics matrix
            metric_keys = ['accuracy', 'precision', 'recall', 'f1', 'r2', 'mae', 'rmse']
            metric_labels = ['Accuracy', 'Precision', 'Recall', 'F1-Score', 'R²', 'MAE', 'RMSE']
            
            # Find which metrics are available
            available_metrics = []
            for key in metric_keys:
                for mode in successful_modes:
                    if key in mode_metrics[mode]:
                        if key not in [m[0] for m in available_metrics]:
                            available_metrics.append((key, metric_labels[metric_keys.index(key)]))
                        break
            
            if available_metrics:
                matrix = []
                mode_labels = []
                
                for mode in successful_modes:
                    row = []
                    for key, _ in available_metrics:
                        val = mode_metrics[mode].get(key, np.nan)
                        if isinstance(val, (int, float)):
                            row.append(val)
                        else:
                            row.append(np.nan)
                    matrix.append(row)
                    
                    display_name = {
                        'traditional': 'Traditional ML',
                        'nlp': 'NLP',
                        'deep_learning': 'Deep Learning'
                    }.get(mode, mode)
                    mode_labels.append(display_name)
                
                matrix = np.array(matrix)
                metric_display = [m[1] for m in available_metrics]
                
                sns.heatmap(matrix, annot=True, fmt='.3f', cmap='RdYlGn',
                           xticklabels=metric_display, yticklabels=mode_labels,
                           ax=ax, linewidths=0.5, cbar_kws={'shrink': 0.8})
                
                ax.set_title('📊 Metrics Comparison Heatmap', fontsize=14,
                            fontweight='bold', color='#333333', pad=20)
                
                plt.tight_layout()
                charts['combined_metrics_heatmap'] = _fig_to_base64(fig)
                
        except Exception as e:
            logger.warning(f"Metrics heatmap error: {e}")
    
    # 5. MODE DISTRIBUTION PIE CHART (Model Count per Mode)
    try:
        fig, ax = plt.subplots(figsize=(8, 8))
        
        mode_counts = {}
        for item in leaderboard:
            mode = item.get('mode', 'Unknown')
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        if mode_counts:
            labels = list(mode_counts.keys())
            sizes = list(mode_counts.values())
            colors_pie = [MODE_COLORS.get(l, MODE_COLORS.get(l.lower().replace(' ', '_'), COLORS[0])) 
                         for l in labels]
            
            explode = [0.05] * len(labels)
            
            wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels,
                                              colors=colors_pie, autopct='%1.1f%%',
                                              startangle=90, pctdistance=0.75,
                                              wedgeprops=dict(edgecolor='white', linewidth=2))
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(11)
            
            ax.set_title('🎯 Model Distribution by Mode', fontsize=14,
                        fontweight='bold', color='#333333', pad=20)
            
            plt.tight_layout()
            charts['combined_mode_distribution'] = _fig_to_base64(fig)
            
    except Exception as e:
        logger.warning(f"Mode distribution chart error: {e}")
    
    # 6. BEST MODEL METRICS CARD (Visual Summary)
    if best_overall_model:
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.axis('off')
            
            metrics = best_overall_model.get('metrics', {})
            mode = best_overall_model.get('mode', 'Unknown')
            name = best_overall_model.get('name', 'Unknown')
            
            display_mode = {
                'traditional': 'Traditional ML',
                'nlp': 'NLP',
                'deep_learning': 'Deep Learning'
            }.get(mode, mode)
            
            # Create a visual card
            card_text = f"""
🏆 BEST MODEL

Mode: {display_mode}
Model: {name}

"""
            # Add metrics
            for key, val in metrics.items():
                if isinstance(val, float):
                    card_text += f"{key.capitalize()}: {val:.4f}\n"
                else:
                    card_text += f"{key.capitalize()}: {val}\n"
            
            color = MODE_COLORS.get(mode, COLORS[0])
            ax.text(0.5, 0.5, card_text, transform=ax.transAxes, fontsize=14,
                   verticalalignment='center', horizontalalignment='center',
                   fontfamily='monospace',
                   bbox=dict(boxstyle='round,pad=1', facecolor=color, alpha=0.1,
                            edgecolor=color, linewidth=3))
            
            plt.tight_layout()
            charts['combined_best_model_card'] = _fig_to_base64(fig)
            
        except Exception as e:
            logger.warning(f"Best model card error: {e}")
    
    logger.info(f"✨ Generated {len(charts)} combined charts: {list(charts.keys())}")
    return charts


def generate_mode_summary_chart(
    mode: str,
    metrics: Dict[str, float],
    model_name: str
) -> Optional[str]:
    """
    Generate a single mode summary chart with key metrics
    
    Args:
        mode: 'traditional', 'nlp', or 'deep_learning'
        metrics: Dictionary of metric values
        model_name: Name of the model
        
    Returns:
        Base64 encoded PNG or None
    """
    try:
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Extract key metrics
        metric_names = []
        values = []
        
        key_metrics = ['accuracy', 'precision', 'recall', 'f1', 'r2', 'mae']
        display_names = ['Accuracy', 'Precision', 'Recall', 'F1', 'R²', 'MAE']
        
        for key, display in zip(key_metrics, display_names):
            if key in metrics:
                metric_names.append(display)
                val = metrics[key]
                if isinstance(val, (int, float)):
                    # Convert to percentage for scores 0-1
                    values.append(val * 100 if val <= 1 else val)
                else:
                    values.append(0)
        
        if not values:
            return None
        
        color = MODE_COLORS.get(mode, COLORS[0])
        bars = ax.bar(range(len(metric_names)), values, color=color,
                     edgecolor='#333333', linewidth=0.5)
        
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                   f'{val:.1f}%', ha='center', fontsize=10, fontweight='bold')
        
        ax.set_xticks(range(len(metric_names)))
        ax.set_xticklabels(metric_names, fontsize=11)
        ax.set_ylabel('Score (%)', fontsize=12)
        
        display_mode = {
            'traditional': 'Traditional ML',
            'nlp': 'NLP',
            'deep_learning': 'Deep Learning'
        }.get(mode, mode)
        
        ax.set_title(f'{display_mode}: {model_name}', fontsize=14, 
                    fontweight='bold', color='#333333')
        ax.set_ylim(0, max(values) * 1.15 if values else 100)
        
        plt.tight_layout()
        return _fig_to_base64(fig)
        
    except Exception as e:
        logger.warning(f"Mode summary chart error: {e}")
        return None
