"""
Visual Force Engine
===================
Translates mathematical data signals into abstract visual forces.
The 'Physics' of the visualization system.

Mapping Logic:
- Temporal Strength -> Flow (Directionality)
- Entropy -> Fragmentation (Particle count/Dispersion)
- Variance Pressure -> Contrast (Scale differentials/Color spread)
- Relationship Density -> Cohesion (Gravity/Clustering)
- Compactness -> Dominance (Weight/Fill/Whitespace)

Output: VisualForces object
"""

from dataclasses import dataclass, asdict
from typing import Dict

@dataclass
class VisualForces:
    flow: float          # 0.0 (Static) -> 1.0 (River-like)
    fragmentation: float # 0.0 (Monolithic) -> 1.0 (Particulate)
    contrast: float      # 0.0 (Uniform) -> 1.0 (Extreme)
    cohesion: float      # 0.0 (Dispersed) -> 1.0 (Tightly Bound)
    dominance: float     # 0.0 (Light/Airy) -> 1.0 (Heavy/Solid)
    
    def to_dict(self):
        return asdict(self)

class VisualForceEngine:
    def compute_forces(self, signals: Dict[str, float]) -> VisualForces:
        """
        Map Data Signals -> Visual Forces
        """
        return VisualForces(
            flow = self._compute_flow(signals),
            fragmentation = self._compute_fragmentation(signals),
            contrast = self._compute_contrast(signals),
            cohesion = self._compute_cohesion(signals),
            dominance = self._compute_dominance(signals)
        )

    def _compute_flow(self, s):
        # Temporal strength directly drives flow.
        # But high entropy can disrupt it.
        base = s.get('temporal_strength', 0.0)
        chaos = s.get('entropy', 0.0)
        # Flow reduced by chaos
        return max(0.0, min(1.0, base - (chaos * 0.2)))

    def _compute_fragmentation(self, s):
        # Entropy is primary driver.
        # Inverse of relationship density (high relations -> low fragmentation)
        ent = s.get('entropy', 0.0)
        rel = s.get('relationship_density', 0.0)
        return max(0.0, min(1.0, ent + (1.0 - rel) * 0.3))

    def _compute_contrast(self, s):
        # Variance pressure is primary.
        # Compactness amplifies contrast (dense data makes contrast pop)
        var = s.get('variance_pressure', 0.0)
        comp = s.get('compactness', 0.0)
        return max(0.0, min(1.0, var * 0.8 + comp * 0.2))

    def _compute_cohesion(self, s):
        # Relationship density is primary.
        return s.get('relationship_density', 0.0)

    def _compute_dominance(self, s):
        # Compactness is primary.
        # Variance reduces dominance (makes things skinny/spiky)
        comp = s.get('compactness', 0.0)
        var = s.get('variance_pressure', 0.0)
        return max(0.0, min(1.0, comp - (var * 0.1)))
