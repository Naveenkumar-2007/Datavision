"""
Dynamic Visual Count Calculator
=================================
Calculates optimal number of visuals based on data complexity.

NO hardcoded limits - purely calculated from:
- Data dimensionality
- Insight density
- Relationship complexity
- Mode (overview vs dashboard)
"""

from typing import Dict, Any, List
from typing import Dict, Any


class VisualCountCalculator:
    """
    Dynamically calculates how many visuals to show.
    Range: 5-30 visuals (auto-scaled based on data).
    """
    
    def calculate(self, data_profile: Dict, insights: List[Dict], mode: str) -> int:
        """
        Calculate optimal visual count.
        
        Args:
            data_profile: Column information and statistics
            insights: Discovered patterns
            mode: 'overview' or 'dashboard'
        
        Returns:
            Visual count (5-30)
        """
        # Factor 1: Data Complexity (0.0-1.0)
        complexity = self._calculate_complexity(data_profile)
        
        # Factor 2: Insight Density (0.0-2.0+)
        insight_density = len(insights) / 10.0
        
        # Factor 3: Relationship Richness (0.0-1.0)
        relationship_richness = self._calculate_relationship_richness(insights)
        
        # Combined richness score
        richness = (complexity + insight_density + relationship_richness) / 3
        
        # Mode-based scaling
        if mode == 'overview':
            base_count = 5
            multiplier = 1.5
            max_count = 12
        else:  # dashboard
            base_count = 10
            multiplier = 2.5
            max_count = 30
        
        # Calculate
        visual_count = int(base_count + richness * multiplier)
        
        # Apply bounds
        visual_count = max(5, min(visual_count, max_count))
        
        print(f"\n🎯 Visual Count Calculation:")
        print(f"   Complexity: {complexity:.2f}")
        print(f"   Insight Density: {insight_density:.2f}")
        print(f"   Richness: {richness:.2f}")
        print(f"   → {visual_count} visuals for {mode}\n")
        
        return visual_count
    
    def _calculate_complexity(self, data_profile: Dict) -> float:
        """Calculate data complexity score."""
        numeric_count = len(data_profile.get('numeric', []))
        categorical_count = len(data_profile.get('categorical', []))
        datetime_count = len(data_profile.get('datetime', []))
        
        # Weighted sum (temporal columns are most valuable)
        complexity = (
            numeric_count * 0.3 +
            categorical_count * 0.2 +
            datetime_count * 0.5
        ) / 10.0  # Normalize to ~0-1
        
        return min(complexity, 1.0)
    
    def _calculate_relationship_richness(self, insights: List[Dict]) -> float:
        """Calculate relationship complexity from insights."""
        correlation_count = sum(1 for i in insights if i.get('type') == 'correlation')
        cluster_count = sum(1 for i in insights if i.get('type') == 'clustering')
        
        richness = (correlation_count + cluster_count * 2) / 10.0
        
        return min(richness, 1.0)
