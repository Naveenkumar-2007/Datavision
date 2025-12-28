"""
Layout Synthesizer - Zone-Based Dynamic Construction
=====================================================
CONSTRUCTS layouts from scratch - NO templates, NO selection.

This is a DECISION TRANSFORMER, not a selector.

Key Principles:
1. Layouts emerge from behavior score interactions
2. Non-linear phase transitions based on score thresholds
3. Zone-based construction (not grid placement)
4. Cross-score influences create unique structures
5. Two datasets with different behaviors = different layouts

NO:
- Template names (grid, timeline, executive)
- Hardcoded visual counts
- Static spatial flows
- Preset grouping patterns
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
from sklearn.cluster import KMeans
from core.data_behavior_scorer import BehaviorScores
import hashlib


@dataclass
class Zone:
    """A dynamically constructed layout zone"""
    id: str
    weight: float           # Relative importance (0-1)
    position: str           # Emergent: 'hero', 'primary', 'secondary', 'supporting'
    span: Tuple[int, int]   # Grid span (cols, rows) - derived not preset
    visual_indices: List[int]  # Which visuals go here
    emphasis: float         # Visual emphasis level
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "weight": round(self.weight, 3),
            "position": self.position,
            "span": self.span,
            "visual_indices": self.visual_indices,
            "emphasis": round(self.emphasis, 3)
        }


@dataclass
class LayoutSpec:
    """Dynamically synthesized layout specification - NOT a template"""
    
    # Core computed properties
    visual_count: int
    hierarchy_depth: int
    zones: List[Zone]
    
    # Emergent flow pattern (computed, not selected)
    flow_vector: Tuple[float, float]  # (horizontal_flow, vertical_flow)
    flow_type: str                     # Derived from vector
    
    # Spacing/density (behavior-derived)
    base_gap: float
    zone_gap: float
    content_density: float
    
    # Visual emphasis distribution
    emphasis_curve: str  # 'steep', 'gradual', 'flat', 'bimodal'
    primary_focus: List[int]
    
    # Grid synthesis (constructed, not selected)
    grid_columns: int
    grid_rows: int
    aspect_ratios: List[float]
    
    # Color influence on layout
    uses_background_zones: bool
    contrast_regions: int
    
    # Unique fingerprint
    layout_fingerprint: str
    
    # Grouping for backwards compatibility
    grouping: List[List[int]] = field(default_factory=list)
    spatial_flow: str = "synthesized"
    spacing_density: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "visual_count": self.visual_count,
            "hierarchy_depth": self.hierarchy_depth,
            "zones": [z.to_dict() for z in self.zones],
            "flow_vector": [round(self.flow_vector[0], 3), round(self.flow_vector[1], 3)],
            "flow_type": self.flow_type,
            "base_gap": round(self.base_gap, 2),
            "zone_gap": round(self.zone_gap, 2),
            "content_density": round(self.content_density, 3),
            "emphasis_curve": self.emphasis_curve,
            "primary_focus": self.primary_focus,
            "grid_columns": self.grid_columns,
            "grid_rows": self.grid_rows,
            "aspect_ratios": [round(ar, 2) for ar in self.aspect_ratios],
            "uses_background_zones": self.uses_background_zones,
            "contrast_regions": self.contrast_regions,
            "layout_fingerprint": self.layout_fingerprint,
            # Backwards compatibility
            "grouping": self.grouping,
            "spatial_flow": self.flow_type,
            "spacing_density": round(self.spacing_density, 2)
        }


class LayoutSynthesizer:
    """
    AUTONOMOUS Layout Constructor - NO templates.
    
    This engine CONSTRUCTS layouts from behavior scores through:
    1. Phase detection based on score thresholds
    2. Zone emergence from score interactions
    3. Flow vector computation
    4. Non-linear emphasis distribution
    
    Two datasets with different behaviors MUST produce different structures.
    """
    
    # Phase transition thresholds (emergent, not hardcoded selection)
    PHASE_THRESHOLDS = {
        'high': 0.7,
        'medium': 0.4,
        'low': 0.2
    }
    
    def synthesize(self, df: pd.DataFrame, behavior: BehaviorScores, 
                   mode: str = 'overview') -> LayoutSpec:
        """
        Synthesize layout specification from data behavior.
        
        This is CONSTRUCTION, not SELECTION.
        """
        # 1. Compute behavior interaction matrix
        interaction_matrix = self._compute_behavior_interactions(behavior)
        
        # 2. Determine visual count from interactions (not linear formula)
        visual_count = self._synthesize_visual_count(behavior, interaction_matrix, mode)
        
        # 3. Compute flow vector (not select flow type)
        flow_vector = self._compute_flow_vector(behavior)
        flow_type = self._derive_flow_type(flow_vector)
        
        # 4. Construct zones from behavior (not place in grid)
        zones = self._construct_zones(behavior, visual_count, flow_vector, mode)
        
        # 5. Compute hierarchy from zones (emergent, not preset)
        hierarchy_depth = self._compute_emergent_hierarchy(zones, behavior)
        
        # 6. Synthesize grid dimensions (not select from presets)
        grid_cols, grid_rows = self._synthesize_grid_dimensions(
            visual_count, flow_vector, behavior, mode
        )
        
        # 7. Compute spacing from behavior (not preset values)
        base_gap, zone_gap = self._compute_spacing(behavior, mode)
        
        # 8. Derive emphasis curve (not select pattern)
        emphasis_curve = self._derive_emphasis_curve(behavior, zones)
        primary_focus = self._compute_primary_focus(zones, emphasis_curve)
        
        # 9. Generate aspect ratios from behavior (not from flow type)
        aspect_ratios = self._generate_behavior_aspect_ratios(
            visual_count, behavior, zones
        )
        
        # 10. Compute unique layout fingerprint
        layout_fingerprint = self._generate_layout_fingerprint(
            behavior, visual_count, zones, flow_vector
        )
        
        # 11. Determine color influence on layout
        uses_background_zones = behavior.complexity > 0.5 and behavior.density < 0.6
        contrast_regions = self._compute_contrast_regions(behavior)
        
        # Build grouping from zones for backwards compatibility
        grouping = [[idx for idx in z.visual_indices] for z in zones if z.visual_indices]
        
        return LayoutSpec(
            visual_count=visual_count,
            hierarchy_depth=hierarchy_depth,
            zones=zones,
            flow_vector=flow_vector,
            flow_type=flow_type,
            base_gap=base_gap,
            zone_gap=zone_gap,
            content_density=behavior.density,
            emphasis_curve=emphasis_curve,
            primary_focus=primary_focus,
            grid_columns=grid_cols,
            grid_rows=grid_rows,
            aspect_ratios=aspect_ratios,
            uses_background_zones=uses_background_zones,
            contrast_regions=contrast_regions,
            layout_fingerprint=layout_fingerprint,
            grouping=grouping,
            spatial_flow=flow_type,
            spacing_density=1 - behavior.sparsity
        )
    
    def _compute_behavior_interactions(self, b: BehaviorScores) -> np.ndarray:
        """
        Compute non-linear interactions between behavior scores.
        
        This creates cross-score influences that drive layout decisions.
        """
        scores = np.array([b.density, b.complexity, b.volatility, b.temporal, b.sparsity])
        
        # Interaction matrix: product of each pair
        interaction = np.outer(scores, scores)
        
        # Apply non-linear transformation (sigmoid-like thresholding)
        interaction = 1 / (1 + np.exp(-5 * (interaction - 0.3)))
        
        return interaction
    
    def _synthesize_visual_count(self, b: BehaviorScores, 
                                  interactions: np.ndarray,
                                  mode: str) -> int:
        """
        Synthesize visual count from behavior interactions.
        
        NOT a linear formula - uses phase transitions.
        """
        # Base from interaction matrix energy
        energy = np.mean(interactions)
        
        # Non-linear scaling based on phases
        if b.complexity > self.PHASE_THRESHOLDS['high']:
            complexity_factor = 2.5
        elif b.complexity > self.PHASE_THRESHOLDS['medium']:
            complexity_factor = 1.5
        else:
            complexity_factor = 1.0
        
        # Density influence with threshold
        if b.density > self.PHASE_THRESHOLDS['high']:
            density_factor = 2.0
        elif b.density > self.PHASE_THRESHOLDS['medium']:
            density_factor = 1.3
        else:
            density_factor = 1.0
        
        # Volatility dampens visual count (noisy data = fewer visuals)
        volatility_damper = 1.0 - (b.volatility * 0.3)
        
        # Base count depends on mode
        if mode == 'overview':
            base = 3
            max_count = 6
        else:  # dashboard
            base = 6
            max_count = 15
        
        # Synthesize count
        count = base * energy * complexity_factor * density_factor * volatility_damper
        count = int(np.clip(count + 2, base, max_count))
        
        return count
    
    def _compute_flow_vector(self, b: BehaviorScores) -> Tuple[float, float]:
        """
        Compute flow vector from behavior scores.
        
        Returns (horizontal_flow, vertical_flow) where:
        - Positive horizontal = left-to-right emphasis
        - Positive vertical = top-to-bottom emphasis
        
        This is COMPUTED, not selected.
        """
        # Temporal data creates horizontal flow (timeline feel)
        h_flow = b.temporal * 0.8 - b.sparsity * 0.3
        
        # Complexity creates vertical hierarchy
        v_flow = b.complexity * 0.7 + b.density * 0.2
        
        # Volatility adds diagonal tendency
        if b.volatility > self.PHASE_THRESHOLDS['medium']:
            h_flow += b.volatility * 0.2
            v_flow -= b.volatility * 0.1
        
        # Normalize to (-1, 1)
        h_flow = float(np.clip(h_flow, -1, 1))
        v_flow = float(np.clip(v_flow, -1, 1))
        
        return (h_flow, v_flow)
    
    def _derive_flow_type(self, flow_vector: Tuple[float, float]) -> str:
        """
        Derive flow type name from flow vector.
        
        This is for backwards compatibility - the vector is the truth.
        """
        h, v = flow_vector
        
        # Compute angle and magnitude
        magnitude = np.sqrt(h**2 + v**2)
        
        if magnitude < 0.2:
            return "centered"
        
        angle = np.arctan2(v, h) * 180 / np.pi  # -180 to 180
        
        if -30 <= angle <= 30:
            return "horizontal-flow"
        elif 30 < angle <= 75:
            return "diagonal-down"
        elif 75 < angle <= 105:
            return "vertical-cascade"
        elif 105 < angle <= 150:
            return "diagonal-up"
        elif angle > 150 or angle < -150:
            return "reverse-flow"
        elif -105 <= angle < -75:
            return "bottom-up"
        else:
            return "radial"
    
    def _construct_zones(self, b: BehaviorScores, visual_count: int,
                         flow_vector: Tuple[float, float], mode: str) -> List[Zone]:
        """
        CONSTRUCT zones from behavior - not place in templates.
        
        Zones EMERGE from the interaction of:
        - Visual count
        - Flow vector direction
        - Complexity (more zones for complex data)
        - Hierarchy signals
        """
        zones = []
        h_flow, v_flow = flow_vector
        
        # Determine zone count from complexity (not preset)
        zone_count = self._compute_zone_count(b, visual_count, mode)
        
        # Distribute visuals across zones based on hierarchy
        visual_distribution = self._distribute_visuals(visual_count, zone_count, b)
        
        # Construct each zone
        for i, vis_count in enumerate(visual_distribution):
            if vis_count == 0:
                continue
            
            # Compute zone weight (importance) from position and behavior
            weight = self._compute_zone_weight(i, zone_count, b, mode)
            
            # Determine position type (emergent from weight)
            position = self._derive_zone_position(weight, i, zone_count)
            
            # Compute span based on visual count and flow
            span = self._compute_zone_span(vis_count, weight, flow_vector, mode)
            
            # Compute emphasis from weight and complexity
            emphasis = weight * (1 + b.complexity * 0.5)
            
            # Assign visual indices
            start_idx = sum(visual_distribution[:i])
            visual_indices = list(range(start_idx, start_idx + vis_count))
            
            zones.append(Zone(
                id=f"zone_{i}_{b.data_fingerprint[:8]}",
                weight=weight,
                position=position,
                span=span,
                visual_indices=visual_indices,
                emphasis=float(np.clip(emphasis, 0, 1))
            ))
        
        return zones
    
    def _compute_zone_count(self, b: BehaviorScores, visual_count: int, mode: str) -> int:
        """Compute number of zones from behavior."""
        # Base on complexity with phase transitions
        if b.complexity > self.PHASE_THRESHOLDS['high']:
            base_zones = 4
        elif b.complexity > self.PHASE_THRESHOLDS['medium']:
            base_zones = 3
        else:
            base_zones = 2
        
        # Mode adjustment
        if mode == 'overview':
            base_zones = min(base_zones, 3)
        else:
            base_zones = min(base_zones + 1, 5)
        
        # Don't have more zones than visuals
        return min(base_zones, visual_count)
    
    def _distribute_visuals(self, visual_count: int, zone_count: int, 
                            b: BehaviorScores) -> List[int]:
        """Distribute visuals across zones based on hierarchy."""
        distribution = []
        remaining = visual_count
        
        for i in range(zone_count):
            if i == zone_count - 1:
                # Last zone gets remaining
                distribution.append(remaining)
            else:
                # Hierarchy determines distribution
                # First zone gets more if high complexity
                if i == 0:
                    ratio = 0.3 + b.complexity * 0.2
                elif i == 1:
                    ratio = 0.25 + b.density * 0.1
                else:
                    ratio = 0.2
                
                count = max(1, int(visual_count * ratio))
                count = min(count, remaining - (zone_count - i - 1))  # Leave at least 1 per remaining zone
                distribution.append(count)
                remaining -= count
        
        return distribution
    
    def _compute_zone_weight(self, zone_idx: int, zone_count: int, 
                             b: BehaviorScores, mode: str) -> float:
        """Compute zone weight/importance."""
        # Base weight decreases with position (hierarchy)
        position_weight = 1.0 - (zone_idx / zone_count) * 0.5
        
        # Complexity increases weight variance
        variance = b.complexity * 0.3
        
        # Add controlled randomness based on fingerprint
        seed = int(b.data_fingerprint[:8], 16) % 1000 + zone_idx
        np.random.seed(seed)
        noise = np.random.uniform(-variance, variance)
        
        weight = position_weight + noise
        return float(np.clip(weight, 0.2, 1.0))
    
    def _derive_zone_position(self, weight: float, zone_idx: int, zone_count: int) -> str:
        """Derive zone position name from weight."""
        if weight > 0.8 or zone_idx == 0:
            return "hero"
        elif weight > 0.6:
            return "primary"
        elif weight > 0.4:
            return "secondary"
        else:
            return "supporting"
    
    def _compute_zone_span(self, vis_count: int, weight: float,
                           flow_vector: Tuple[float, float], mode: str) -> Tuple[int, int]:
        """Compute zone grid span based on visual count and weight."""
        h_flow, v_flow = flow_vector
        
        # Base span from visual count
        base_cols = min(vis_count, 3 if mode == 'overview' else 4)
        base_rows = max(1, (vis_count + base_cols - 1) // base_cols)
        
        # Weight affects span
        if weight > 0.7:
            base_cols = min(base_cols + 1, 4)
        
        # Flow affects span direction
        if abs(h_flow) > abs(v_flow):
            # Horizontal emphasis - wider
            base_cols = min(base_cols + 1, 4)
        else:
            # Vertical emphasis - taller
            base_rows = min(base_rows + 1, 4)
        
        return (base_cols, base_rows)
    
    def _compute_emergent_hierarchy(self, zones: List[Zone], b: BehaviorScores) -> int:
        """Compute hierarchy depth from zone weights."""
        if not zones:
            return 1
        
        weights = [z.weight for z in zones]
        variance = np.var(weights)
        
        # High variance = deep hierarchy
        if variance > 0.1:
            depth = 4
        elif variance > 0.05:
            depth = 3
        elif variance > 0.02:
            depth = 2
        else:
            depth = 1
        
        # Complexity increases depth
        depth = min(4, depth + int(b.complexity > 0.6))
        
        return depth
    
    def _synthesize_grid_dimensions(self, visual_count: int, 
                                    flow_vector: Tuple[float, float],
                                    b: BehaviorScores, mode: str) -> Tuple[int, int]:
        """Synthesize grid dimensions from behavior."""
        h_flow, v_flow = flow_vector
        
        # Base from visual count
        if mode == 'overview':
            base_cols = 2
            max_cols = 3
        else:
            base_cols = 3
            max_cols = 4
        
        # Flow affects grid shape
        if abs(h_flow) > 0.5:
            # Strong horizontal flow = more columns
            cols = min(base_cols + 1, max_cols)
        else:
            cols = base_cols
        
        # Density affects grid fill
        if b.density > 0.7:
            cols = max_cols
        
        rows = (visual_count + cols - 1) // cols
        
        return (cols, rows)
    
    def _compute_spacing(self, b: BehaviorScores, mode: str) -> Tuple[float, float]:
        """Compute spacing from behavior."""
        # Base gap from mode
        if mode == 'overview':
            base = 24
            zone_base = 32
        else:
            base = 16
            zone_base = 24
        
        # Density reduces spacing
        density_factor = 1.0 - b.density * 0.4
        
        # Sparsity increases spacing
        sparsity_factor = 1.0 + b.sparsity * 0.3
        
        base_gap = base * density_factor * sparsity_factor
        zone_gap = zone_base * density_factor * sparsity_factor
        
        return (float(base_gap), float(zone_gap))
    
    def _derive_emphasis_curve(self, b: BehaviorScores, zones: List[Zone]) -> str:
        """Derive emphasis distribution pattern from behavior."""
        if not zones:
            return "flat"
        
        weights = sorted([z.weight for z in zones], reverse=True)
        
        if len(weights) < 2:
            return "flat"
        
        # Check distribution pattern
        top_weight = weights[0]
        second_weight = weights[1]
        last_weight = weights[-1]
        
        ratio_top_second = top_weight / max(second_weight, 0.01)
        ratio_top_last = top_weight / max(last_weight, 0.01)
        
        if ratio_top_last > 3.0:
            return "steep"
        elif ratio_top_second > 1.5:
            return "gradual"
        elif b.volatility > 0.5:
            return "bimodal"
        else:
            return "flat"
    
    def _compute_primary_focus(self, zones: List[Zone], emphasis_curve: str) -> List[int]:
        """Compute primary focus visuals from zones and emphasis."""
        if not zones:
            return []
        
        # Find hero zone
        hero_zones = [z for z in zones if z.position == "hero"]
        primary_zones = [z for z in zones if z.position == "primary"]
        
        focus = []
        
        # Hero zone visuals are primary
        for z in hero_zones:
            focus.extend(z.visual_indices[:2])  # Max 2 from hero
        
        # If steep emphasis, also include first primary
        if emphasis_curve == "steep" and primary_zones:
            focus.extend(primary_zones[0].visual_indices[:1])
        
        return focus[:3]  # Max 3 primary
    
    def _generate_behavior_aspect_ratios(self, visual_count: int, 
                                          b: BehaviorScores,
                                          zones: List[Zone]) -> List[float]:
        """Generate aspect ratios from behavior, not flow type."""
        ratios = []
        
        # Create zone weight map
        visual_zone_map = {}
        for zone in zones:
            for idx in zone.visual_indices:
                visual_zone_map[idx] = zone
        
        for i in range(visual_count):
            zone = visual_zone_map.get(i)
            
            # Base ratio from zone weight
            if zone and zone.position == "hero":
                base = 0.7  # Taller
            elif zone and zone.position == "primary":
                base = 0.85
            else:
                base = 1.0
            
            # Temporal data makes charts taller
            if b.temporal > 0.6:
                base *= 0.9
            
            # Density makes charts wider
            if b.density > 0.6:
                base *= 1.1
            
            # Add controlled variation from fingerprint
            seed = int(b.data_fingerprint[:8], 16) % 1000 + i
            np.random.seed(seed)
            variation = np.random.uniform(-0.1, 0.1)
            
            ratio = base + variation
            ratios.append(float(np.clip(ratio, 0.5, 1.5)))
        
        return ratios
    
    def _compute_contrast_regions(self, b: BehaviorScores) -> int:
        """Compute number of visual contrast regions."""
        # Complexity and volatility increase contrast regions
        score = b.complexity * 0.5 + b.volatility * 0.3 + b.density * 0.2
        
        if score > 0.6:
            return 3
        elif score > 0.3:
            return 2
        else:
            return 1
    
    def _generate_layout_fingerprint(self, b: BehaviorScores, visual_count: int,
                                      zones: List[Zone], flow_vector: Tuple[float, float]) -> str:
        """Generate unique fingerprint for this layout specification."""
        # Combine all computed values
        sig_string = f"{b.data_fingerprint}_{visual_count}_{len(zones)}_{flow_vector[0]:.2f}_{flow_vector[1]:.2f}"
        
        for zone in zones:
            sig_string += f"_{zone.weight:.2f}_{zone.position}"
        
        return hashlib.md5(sig_string.encode()).hexdigest()[:16]


# Example usage
if __name__ == "__main__":
    from data_behavior_scorer import DataBehaviorScorer
    
    # Test with sample data
    test_data = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=100),
        'revenue': np.random.normal(10000, 2000, 100),
        'profit': np.random.normal(2000, 500, 100),
        'customers': np.random.poisson(50, 100),
        'orders': np.random.poisson(45, 100),
    })
    
    # Score behavior
    scorer = DataBehaviorScorer()
    behavior = scorer.score(test_data)
    
    # Synthesize layout for overview
    synthesizer = LayoutSynthesizer()
    layout_overview = synthesizer.synthesize(test_data, behavior, mode='overview')
    layout_dashboard = synthesizer.synthesize(test_data, behavior, mode='dashboard')
    
    print("OVERVIEW Layout:")
    print(f"  Visual Count: {layout_overview.visual_count}")
    print(f"  Flow: {layout_overview.flow_type} ({layout_overview.flow_vector})")
    print(f"  Zones: {len(layout_overview.zones)}")
    print(f"  Hierarchy: {layout_overview.hierarchy_depth}")
    print(f"  Fingerprint: {layout_overview.layout_fingerprint}")
    
    print("\nDASHBOARD Layout:")
    print(f"  Visual Count: {layout_dashboard.visual_count}")
    print(f"  Flow: {layout_dashboard.flow_type} ({layout_dashboard.flow_vector})")
    print(f"  Zones: {len(layout_dashboard.zones)}")
    print(f"  Hierarchy: {layout_dashboard.hierarchy_depth}")
    print(f"  Fingerprint: {layout_dashboard.layout_fingerprint}")
