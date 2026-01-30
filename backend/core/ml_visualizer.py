"""
ML VISUALIZER - Matplotlib/Seaborn Chart Generation
====================================================

Creates machine learning visualizations as base64-encoded PNG images
that can be embedded directly in the response.

Chart Types:
1. Forecast Plot with Confidence Band
2. Feature Importance Bar Chart
3. Correlation Heatmap
4. Residual Analysis Plot
5. Distribution Plot
6. Time Series Decomposition

All charts use a premium dark theme for consistency!
"""

import numpy as np
import pandas as pd
import base64
import io
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MLVisualizer:
    """
    📊 ML VISUALIZER - Create Beautiful ML Charts
    
    Generates matplotlib/seaborn charts embedded as base64 PNG.
    All charts are dark-theme compatible and publication-ready.
    """
    
    def __init__(self):
        self._setup_style()
    
    def _setup_style(self):
        """Setup matplotlib style for premium dark theme"""
        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # Premium dark theme
            plt.style.use('dark_background')
            
            # Custom color palette
            self.colors = {
                'primary': '#6366f1',    # Indigo
                'secondary': '#22d3ee',  # Cyan
                'accent': '#f472b6',     # Pink
                'success': '#22c55e',    # Green
                'warning': '#f59e0b',    # Amber
                'error': '#ef4444',      # Red
                'text': '#f1f5f9',       # Light gray
                'bg': '#0f172a',         # Dark blue
                'grid': '#334155'        # Slate
            }
            
            # Seaborn palette
            self.palette = [
                self.colors['primary'],
                self.colors['secondary'],
                self.colors['accent'],
                self.colors['success'],
                self.colors['warning']
            ]
            
            sns.set_palette(self.palette)
            
            self.plt = plt
            self.sns = sns
            self.available = True
            
        except ImportError as e:
            logger.warning(f"Matplotlib/Seaborn not available: {e}")
            self.available = False
    
    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 PNG"""
        try:
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=120, bbox_inches='tight',
                       facecolor=self.colors['bg'], edgecolor='none')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            self.plt.close(fig)
            return f"data:image/png;base64,{img_base64}"
        except Exception as e:
            logger.error(f"Error converting figure to base64: {e}")
            return ""
    
    def create_forecast_plot(
        self,
        historical: List[float],
        predictions: List[float],
        lower_bound: List[float],
        upper_bound: List[float],
        title: str = "Forecast"
    ) -> Dict[str, Any]:
        """
        Create forecast plot with confidence band
        
        Returns:
            Dict with 'image' (base64) and 'type'
        """
        if not self.available:
            return {'type': 'ml_chart', 'image': None, 'error': 'Visualization libraries not available'}
        
        try:
            fig, ax = self.plt.subplots(figsize=(10, 6))
            
            # Historical data
            hist_x = list(range(len(historical)))
            ax.plot(hist_x, historical, 
                   color=self.colors['primary'], linewidth=2.5,
                   marker='o', markersize=6, label='Historical')
            
            # Forecast
            if predictions:
                pred_x = list(range(len(historical), len(historical) + len(predictions)))
                ax.plot(pred_x, predictions,
                       color=self.colors['accent'], linewidth=2.5,
                       marker='s', markersize=8, label='Forecast', linestyle='--')
                
                # Confidence band
                if lower_bound and upper_bound:
                    ax.fill_between(pred_x, lower_bound, upper_bound,
                                   color=self.colors['accent'], alpha=0.2,
                                   label='95% Confidence')
            
            # Styling
            ax.set_facecolor(self.colors['bg'])
            ax.set_xlabel('Period', color=self.colors['text'], fontsize=12)
            ax.set_ylabel('Value', color=self.colors['text'], fontsize=12)
            ax.set_title(title, color=self.colors['text'], fontsize=14, fontweight='bold')
            ax.legend(loc='upper left', framealpha=0.8)
            ax.grid(True, alpha=0.3, color=self.colors['grid'])
            ax.tick_params(colors=self.colors['text'])
            
            return {
                'type': 'ml_forecast',
                'image': self._fig_to_base64(fig),
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Error creating forecast plot: {e}")
            return {'type': 'ml_chart', 'image': None, 'error': str(e)}
    
    def create_feature_importance(
        self,
        importance: Dict[str, float],
        title: str = "Feature Importance"
    ) -> Dict[str, Any]:
        """Create horizontal bar chart of feature importance"""
        if not self.available or not importance:
            return {'type': 'ml_chart', 'image': None}
        
        try:
            # Sort by importance
            sorted_items = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]
            features = [item[0] for item in sorted_items]
            values = [item[1] for item in sorted_items]
            
            fig, ax = self.plt.subplots(figsize=(8, max(4, len(features) * 0.5)))
            
            # Create gradient colors based on importance
            colors = [self.colors['primary'] if v > 0.2 else self.colors['secondary'] 
                     for v in values]
            
            bars = ax.barh(features[::-1], values[::-1], color=colors[::-1])
            
            # Add value labels
            for bar, val in zip(bars, values[::-1]):
                ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                       f'{val:.1%}', va='center', color=self.colors['text'], fontsize=10)
            
            ax.set_facecolor(self.colors['bg'])
            ax.set_xlabel('Importance', color=self.colors['text'], fontsize=12)
            ax.set_title(title, color=self.colors['text'], fontsize=14, fontweight='bold')
            ax.tick_params(colors=self.colors['text'])
            ax.grid(True, axis='x', alpha=0.3, color=self.colors['grid'])
            
            return {
                'type': 'ml_importance',
                'image': self._fig_to_base64(fig),
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Error creating feature importance: {e}")
            return {'type': 'ml_chart', 'image': None, 'error': str(e)}
    
    def create_correlation_heatmap(
        self,
        df: pd.DataFrame,
        title: str = "Correlation Matrix"
    ) -> Dict[str, Any]:
        """Create correlation heatmap for numeric columns"""
        if not self.available:
            return {'type': 'ml_chart', 'image': None}
        
        try:
            # Get numeric columns only
            numeric_df = df.select_dtypes(include=[np.number])
            
            if numeric_df.shape[1] < 2:
                return {'type': 'ml_chart', 'image': None, 'error': 'Need at least 2 numeric columns'}
            
            # Limit columns for readability
            if numeric_df.shape[1] > 10:
                numeric_df = numeric_df.iloc[:, :10]
            
            corr = numeric_df.corr()
            
            fig, ax = self.plt.subplots(figsize=(10, 8))
            
            # Create heatmap
            mask = np.triu(np.ones_like(corr, dtype=bool))
            cmap = self.sns.diverging_palette(220, 20, as_cmap=True)
            
            self.sns.heatmap(corr, mask=mask, cmap=cmap, center=0,
                           square=True, linewidths=0.5,
                           annot=True, fmt='.2f', annot_kws={'size': 9},
                           cbar_kws={'shrink': 0.8})
            
            ax.set_title(title, color=self.colors['text'], fontsize=14, fontweight='bold')
            ax.tick_params(colors=self.colors['text'])
            
            return {
                'type': 'ml_correlation',
                'image': self._fig_to_base64(fig),
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Error creating correlation heatmap: {e}")
            return {'type': 'ml_chart', 'image': None, 'error': str(e)}
    
    def create_distribution_plot(
        self,
        data: List[float],
        column_name: str = "Value",
        title: str = None
    ) -> Dict[str, Any]:
        """Create distribution plot with histogram and KDE"""
        if not self.available:
            return {'type': 'ml_chart', 'image': None}
        
        try:
            fig, ax = self.plt.subplots(figsize=(10, 6))
            
            # Histogram with KDE
            self.sns.histplot(data, kde=True, ax=ax,
                            color=self.colors['primary'], 
                            edgecolor=self.colors['text'],
                            alpha=0.7, line_kws={'linewidth': 2})
            
            # Add mean and std lines
            mean_val = np.mean(data)
            std_val = np.std(data)
            
            ax.axvline(mean_val, color=self.colors['accent'], linestyle='--', 
                      linewidth=2, label=f'Mean: {mean_val:.2f}')
            ax.axvline(mean_val - std_val, color=self.colors['warning'], linestyle=':', 
                      linewidth=1.5, alpha=0.7)
            ax.axvline(mean_val + std_val, color=self.colors['warning'], linestyle=':', 
                      linewidth=1.5, alpha=0.7, label=f'±1 Std: {std_val:.2f}')
            
            ax.set_facecolor(self.colors['bg'])
            ax.set_xlabel(column_name, color=self.colors['text'], fontsize=12)
            ax.set_ylabel('Count', color=self.colors['text'], fontsize=12)
            ax.set_title(title or f'Distribution of {column_name}', 
                        color=self.colors['text'], fontsize=14, fontweight='bold')
            ax.legend(loc='upper right', framealpha=0.8)
            ax.tick_params(colors=self.colors['text'])
            ax.grid(True, alpha=0.3, color=self.colors['grid'])
            
            return {
                'type': 'ml_distribution',
                'image': self._fig_to_base64(fig),
                'title': title or f'Distribution of {column_name}'
            }
            
        except Exception as e:
            logger.error(f"Error creating distribution plot: {e}")
            return {'type': 'ml_chart', 'image': None, 'error': str(e)}
    
    def create_residual_plot(
        self,
        actual: List[float],
        predicted: List[float],
        title: str = "Residual Analysis"
    ) -> Dict[str, Any]:
        """Create residual analysis plot for model validation"""
        if not self.available:
            return {'type': 'ml_chart', 'image': None}
        
        try:
            residuals = np.array(actual) - np.array(predicted)
            
            fig, axes = self.plt.subplots(1, 2, figsize=(14, 5))
            
            # Residuals vs Predicted
            ax1 = axes[0]
            ax1.scatter(predicted, residuals, color=self.colors['primary'], 
                       alpha=0.6, s=50, edgecolors='white', linewidth=0.5)
            ax1.axhline(y=0, color=self.colors['accent'], linestyle='--', linewidth=2)
            ax1.set_xlabel('Predicted', color=self.colors['text'], fontsize=11)
            ax1.set_ylabel('Residuals', color=self.colors['text'], fontsize=11)
            ax1.set_title('Residuals vs Predicted', color=self.colors['text'], fontsize=12)
            ax1.set_facecolor(self.colors['bg'])
            ax1.tick_params(colors=self.colors['text'])
            ax1.grid(True, alpha=0.3, color=self.colors['grid'])
            
            # Residuals distribution
            ax2 = axes[1]
            self.sns.histplot(residuals, kde=True, ax=ax2,
                            color=self.colors['secondary'], alpha=0.7)
            ax2.axvline(0, color=self.colors['accent'], linestyle='--', linewidth=2)
            ax2.set_xlabel('Residual Value', color=self.colors['text'], fontsize=11)
            ax2.set_ylabel('Count', color=self.colors['text'], fontsize=11)
            ax2.set_title('Residual Distribution', color=self.colors['text'], fontsize=12)
            ax2.set_facecolor(self.colors['bg'])
            ax2.tick_params(colors=self.colors['text'])
            ax2.grid(True, alpha=0.3, color=self.colors['grid'])
            
            fig.suptitle(title, color=self.colors['text'], fontsize=14, fontweight='bold', y=1.02)
            self.plt.tight_layout()
            
            return {
                'type': 'ml_residual',
                'image': self._fig_to_base64(fig),
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Error creating residual plot: {e}")
            return {'type': 'ml_chart', 'image': None, 'error': str(e)}
    
    def create_prediction_summary(
        self,
        historical: List[float],
        predictions: List[float],
        lower_bound: List[float],
        upper_bound: List[float],
        importance: Dict[str, float] = None,
        title: str = "ML Prediction Summary"
    ) -> Dict[str, Any]:
        """Create comprehensive prediction visualization with multiple subplots"""
        if not self.available:
            return {'type': 'ml_chart', 'image': None}
        
        try:
            has_importance = importance and len(importance) > 1
            
            if has_importance:
                fig = self.plt.figure(figsize=(14, 8))
                gs = fig.add_gridspec(2, 2, height_ratios=[1.5, 1], hspace=0.3, wspace=0.3)
                ax_forecast = fig.add_subplot(gs[0, :])
                ax_importance = fig.add_subplot(gs[1, 0])
                ax_dist = fig.add_subplot(gs[1, 1])
            else:
                fig, (ax_forecast, ax_dist) = self.plt.subplots(1, 2, figsize=(14, 5))
            
            # Forecast plot
            hist_x = list(range(len(historical)))
            ax_forecast.plot(hist_x, historical, 
                           color=self.colors['primary'], linewidth=2.5,
                           marker='o', markersize=5, label='Historical')
            
            if predictions:
                pred_x = list(range(len(historical), len(historical) + len(predictions)))
                ax_forecast.plot(pred_x, predictions,
                               color=self.colors['accent'], linewidth=2.5,
                               marker='s', markersize=7, label='Forecast', linestyle='--')
                
                if lower_bound and upper_bound:
                    ax_forecast.fill_between(pred_x, lower_bound, upper_bound,
                                           color=self.colors['accent'], alpha=0.2,
                                           label='95% CI')
            
            ax_forecast.set_facecolor(self.colors['bg'])
            ax_forecast.set_xlabel('Period', color=self.colors['text'])
            ax_forecast.set_ylabel('Value', color=self.colors['text'])
            ax_forecast.set_title('Forecast with Confidence Interval', 
                                 color=self.colors['text'], fontsize=12, fontweight='bold')
            ax_forecast.legend(loc='upper left', framealpha=0.8)
            ax_forecast.grid(True, alpha=0.3, color=self.colors['grid'])
            ax_forecast.tick_params(colors=self.colors['text'])
            
            # Feature importance (if available)
            if has_importance:
                sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:6]
                features = [item[0] for item in sorted_imp]
                values = [item[1] for item in sorted_imp]
                
                ax_importance.barh(features[::-1], values[::-1], 
                                  color=self.colors['secondary'])
                ax_importance.set_facecolor(self.colors['bg'])
                ax_importance.set_xlabel('Importance', color=self.colors['text'])
                ax_importance.set_title('Key Drivers', color=self.colors['text'], 
                                       fontsize=12, fontweight='bold')
                ax_importance.tick_params(colors=self.colors['text'])
                ax_importance.grid(True, axis='x', alpha=0.3, color=self.colors['grid'])
            
            # Distribution of historical data
            self.sns.histplot(historical, kde=True, ax=ax_dist,
                            color=self.colors['primary'], alpha=0.7)
            ax_dist.axvline(np.mean(historical), color=self.colors['accent'], 
                          linestyle='--', linewidth=2, label=f'Mean: {np.mean(historical):.1f}')
            ax_dist.set_facecolor(self.colors['bg'])
            ax_dist.set_xlabel('Value', color=self.colors['text'])
            ax_dist.set_title('Value Distribution', color=self.colors['text'], 
                             fontsize=12, fontweight='bold')
            ax_dist.legend(loc='upper right', framealpha=0.8)
            ax_dist.tick_params(colors=self.colors['text'])
            ax_dist.grid(True, alpha=0.3, color=self.colors['grid'])
            
            fig.suptitle(title, color=self.colors['text'], fontsize=14, fontweight='bold', y=1.01)
            self.plt.tight_layout()
            
            return {
                'type': 'ml_summary',
                'image': self._fig_to_base64(fig),
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Error creating prediction summary: {e}")
            return {'type': 'ml_chart', 'image': None, 'error': str(e)}


# Convenience functions
def create_ml_visualization(
    viz_type: str,
    **kwargs
) -> Dict[str, Any]:
    """Create any ML visualization by type"""
    visualizer = MLVisualizer()
    
    if viz_type == 'forecast':
        return visualizer.create_forecast_plot(**kwargs)
    elif viz_type == 'importance':
        return visualizer.create_feature_importance(**kwargs)
    elif viz_type == 'correlation':
        return visualizer.create_correlation_heatmap(**kwargs)
    elif viz_type == 'distribution':
        return visualizer.create_distribution_plot(**kwargs)
    elif viz_type == 'residual':
        return visualizer.create_residual_plot(**kwargs)
    elif viz_type == 'summary':
        return visualizer.create_prediction_summary(**kwargs)
    else:
        return {'type': 'error', 'image': None, 'error': f'Unknown viz type: {viz_type}'}
