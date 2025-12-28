"""
Color Derivation Engine - Mathematical Palette Generation
==========================================================
Derives color palettes mathematically from data behavior and fingerprints.

NO COLOR PRESETS. All colors computed from:
- Data fingerprint (structure hash)
- Variance scores
- Complexity metrics
- Signal confidence

Formulas:
- hue = (fingerprint_hash + variance) % 360
- saturation = complexity * 100
- contrast = noise / polarity
- lightness = signal_confidence * 100
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
import hashlib
import colorsys


@dataclass
class ColorPalette:
    """Mathematically derived color palette"""
    primary: List[str]           # Main data colors (5-7 colors)
    secondary: List[str]          # Supporting colors (3-5 colors)
    accents: List[str]            # Highlight colors (2-3 colors)
    background_gradient: List[str]  # Background colors (2 colors)
    text_colors: Dict[str, str]   # Light/dark text colors
    
    # Metadata
    base_hue: float
    saturation_range: Tuple[float, float]
    lightness_range: Tuple[float, float]
    palette_fingerprint: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "accents": self.accents,
            "background_gradient": self.background_gradient,
            "text_colors": self.text_colors,
            "metadata": {
                "base_hue": round(self.base_hue, 2),
                "saturation_range": [round(s, 2) for s in self.saturation_range],
                "lightness_range": [round(l, 2) for l in self.lightness_range],
                "palette_fingerprint": self.palette_fingerprint
            }
        }


class ColorDerivationEngine:
    """
    Mathematical color generator - NO hardcoded palettes.
    
    Example:
        engine = ColorDerivationEngine()
        palette = engine.derive_palette(df, behavior_scores)
        # Returns: ColorPalette with mathematically generated colors
    """
    
    def derive_palette(self, df: pd.DataFrame, behavior_scores: Any) -> ColorPalette:
        """
        Derive complete color palette from data behavior.
        
        Args:
            df: The dataset
            behavior_scores: BehaviorScores object from data_behavior_scorer
            
        Returns:
            ColorPalette with all derived colors
        """
        # Extract behavior metrics
        density = behavior_scores.density
        complexity = behavior_scores.complexity
        volatility = behavior_scores.volatility
        sparsity = behavior_scores.sparsity
        fingerprint = behavior_scores.data_fingerprint
        
        # 1. Calculate base hue from data fingerprint
        base_hue = self._calculate_base_hue(fingerprint, df)
        
        # 2. Calculate saturation from complexity
        base_saturation = self._calculate_saturation(complexity, density)
        
        # 3. Calculate lightness from signal confidence
        base_lightness = self._calculate_lightness(sparsity, density)
        
        # 4. Calculate variance offset
        hue_variance = self._calculate_hue_variance(volatility)
        
        # 5. Generate color groups
        primary_colors = self._generate_primary_palette(
            base_hue, base_saturation, base_lightness, hue_variance, 6
        )
        
        secondary_colors = self._generate_secondary_palette(
            base_hue, base_saturation, base_lightness, 4
        )
        
        accent_colors = self._generate_accent_palette(
            base_hue, complexity, volatility, 3
        )
        
        background_gradient = self._generate_background_gradient(
            base_hue, base_saturation, sparsity
        )
        
        text_colors = self._generate_text_colors(base_lightness)
        
        # Generate palette fingerprint for uniqueness validation
        palette_fingerprint = self._generate_palette_fingerprint(
            primary_colors, secondary_colors, accent_colors
        )
        
        return ColorPalette(
            primary=primary_colors,
            secondary=secondary_colors,
            accents=accent_colors,
            background_gradient=background_gradient,
            text_colors=text_colors,
            base_hue=base_hue,
            saturation_range=(base_saturation - 20, base_saturation + 20),
            lightness_range=(base_lightness - 20, base_lightness + 20),
            palette_fingerprint=palette_fingerprint
        )
    
    def _calculate_base_hue(self, fingerprint: str, df: pd.DataFrame) -> float:
        """
        Calculate base hue from data structure fingerprint + variance.
        
        Formula: (hash(fingerprint) + variance_score) % 360
        """
        # Hash fingerprint to number
        hash_value = int(hashlib.md5(fingerprint.encode()).hexdigest(), 16)
        base_from_hash = hash_value % 360
        
        # Add variance from numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            variances = [df[col].var() for col in numeric_cols]
            mean_var = np.mean([v for v in variances if not np.isnan(v)])
            # Normalize variance to 0-60 range
            var_offset = min(abs(mean_var) % 60, 60)
        else:
            var_offset = 0
        
        final_hue = (base_from_hash + var_offset) % 360
        
        return float(final_hue)
    
    def _calculate_saturation(self, complexity: float, density: float) -> float:
        """
        Calculate saturation from complexity and density.
        
        Formula: (complexity * 60) + (density * 20) + 20
        Range: 20-100%
        
        More complex/dense data = more saturated colors
        """
        saturation = (complexity * 60) + (density * 20) + 20
        return float(np.clip(saturation, 20, 100))
    
    def _calculate_lightness(self, sparsity: float, density: float) -> float:
        """
        Calculate lightness from sparsity and density.
        
        Formula: (1 - sparsity) * 40 + 30
        Range: 30-70%
        
        Less sparse, more dense = darker colors
        """
        signal_confidence = 1 - sparsity
        lightness = (signal_confidence * 40) + 30
        
        # Adjust based on density
        if density > 0.7:
            lightness -= 10  # Denser data = darker
        
        return float(np.clip(lightness, 30, 70))
    
    def _calculate_hue_variance(self, volatility: float) -> float:
        """
        Calculate hue variance from volatility.
        
        Higher volatility = wider color spread
        Range: 15-60 degrees
        """
        variance = 15 + (volatility * 45)
        return float(variance)
    
    def _generate_primary_palette(self, base_hue: float, saturation: float, 
                                   lightness: float, hue_variance: float, 
                                   count: int) -> List[str]:
        """
        Generate primary color palette using analogous color scheme.
        
        Spreads colors around base hue using variance.
        """
        colors = []
        step = hue_variance / (count - 1) if count > 1 else 0
        
        for i in range(count):
            hue = (base_hue + (i - count//2) * step) % 360
            sat = saturation + np.random.uniform(-5, 5)  # Small random variation
            light = lightness + np.random.uniform(-5, 5)
            
            colors.append(self._hsl_to_css(hue, sat, light))
        
        return colors
    
    def _generate_secondary_palette(self, base_hue: float, saturation: float, 
                                     lightness: float, count: int) -> List[str]:
        """
        Generate secondary colors using complementary hues.
        
        Uses complementary (180°) and split-complementary colors.
        """
        colors = []
        
        # Complementary hue
        comp_hue = (base_hue + 180) % 360
        
        for i in range(count):
            # Vary around complementary
            hue = (comp_hue + np.random.uniform(-30, 30)) % 360
            sat = saturation * 0.8  # Slightly desaturated
            light = lightness + 10  # Slightly lighter
            
            colors.append(self._hsl_to_css(hue, sat, light))
        
        return colors
    
    def _generate_accent_palette(self, base_hue: float, complexity: float, 
                                  volatility: float, count: int) -> List[str]:
        """
        Generate accent colors for highlights and anomalies.
        
        Uses triadic color scheme (120° apart).
        High saturation, dynamic lightness.
        """
        colors = []
        
        # Triadic hues
        triadic_offsets = [120, 240]
        
        for i in range(count):
            offset = triadic_offsets[i % len(triadic_offsets)]
            hue = (base_hue + offset) % 360
            sat = 90 + (complexity * 10)  # High saturation
            light = 50 + (volatility * 20)  # Dynamic lightness
            
            colors.append(self._hsl_to_css(hue, sat, light))
        
        return colors
    
    def _generate_background_gradient(self, base_hue: float, saturation: float, 
                                       sparsity: float) -> List[str]:
        """
        Generate background gradient (2 colors).
        
        Low saturation, dark tones.
        """
        # Top color
        top_sat = min(saturation * 0.3, 20)  # Very desaturated
        top_light = 15 + (sparsity * 10)  # Darker for dense data
        
        # Bottom color (slightly darker)
        bottom_sat = min(saturation * 0.2, 15)
        bottom_light = 8 + (sparsity * 8)
        
        return [
            self._hsl_to_css(base_hue, top_sat, top_light),
            self._hsl_to_css(base_hue, bottom_sat, bottom_light)
        ]
    
    def _generate_text_colors(self, base_lightness: float) -> Dict[str, str]:
        """
        Generate text colors based on background lightness.
        """
        if base_lightness > 50:
            # Light background → dark text
            return {
                "primary": "hsl(0, 0%, 10%)",
                "secondary": "hsl(0, 0%, 30%)",
                "muted": "hsl(0, 0%, 50%)"
            }
        else:
            # Dark background → light text
            return {
                "primary": "hsl(0, 0%, 95%)",
                "secondary": "hsl(0, 0%, 80%)",
                "muted": "hsl(0, 0%, 60%)"
            }
    
    def _hsl_to_css(self, h: float, s: float, l: float) -> str:
        """Convert HSL to CSS hsl() string"""
        return f"hsl({h:.0f}, {s:.0f}%, {l:.0f}%)"
    
    def _generate_palette_fingerprint(self, primary: List[str], 
                                      secondary: List[str], 
                                      accents: List[str]) -> str:
        """Generate unique fingerprint for palette"""
        all_colors = "_".join(primary + secondary + accents)
        hash_obj = hashlib.md5(all_colors.encode())
        return hash_obj.hexdigest()[:16]
    
    def calculate_palette_distance(self, palette1: ColorPalette, 
                                   palette2: ColorPalette) -> float:
        """
        Calculate color distance between two palettes.
        
        Uses Delta-E approximation for perceptual color difference.
        Returns: 0-1 (0 = identical, 1 = maximally different)
        
        If distance < 0.3, palettes are too similar.
        """
        def parse_hsl(hsl_str: str) -> Tuple[float, float, float]:
            """Parse 'hsl(h, s%, l%)' string"""
            parts = hsl_str.replace('hsl(', '').replace(')', '').split(',')
            h = float(parts[0].strip())
            s = float(parts[1].strip().replace('%', ''))
            l = float(parts[2].strip().replace('%', ''))
            return h, s, l
        
        # Compare primary colors
        distances = []
        
        for c1, c2 in zip(palette1.primary[:3], palette2.primary[:3]):
            h1, s1, l1 = parse_hsl(c1)
            h2, s2, l2 = parse_hsl(c2)
            
            # Hue distance (circular)
            hue_dist = min(abs(h1 - h2), 360 - abs(h1 - h2)) / 180
            
            # Saturation and lightness distance
            sat_dist = abs(s1 - s2) / 100
            light_dist = abs(l1 - l2) / 100
            
            # Combined perceptual distance
            color_dist = np.sqrt(hue_dist**2 + sat_dist**2 + light_dist**2) / np.sqrt(3)
            distances.append(color_dist)
        
        mean_distance = np.mean(distances)
        
        return float(np.clip(mean_distance, 0.0, 1.0))


# Example usage
if __name__ == "__main__":
    from data_behavior_scorer import DataBehaviorScorer, BehaviorScores
    
    # Test with sample data
    test_data = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=100),
        'revenue': np.random.normal(10000, 2000, 100),
        'customers': np.random.poisson(50, 100),
    })
    
    # Score behavior
    scorer = DataBehaviorScorer()
    behavior = scorer.score(test_data)
    
    # Derive palette
    engine = ColorDerivationEngine()
    palette = engine.derive_palette(test_data, behavior)
    
    print("Derived Color Palette:")
    print(f"  Base Hue: {palette.base_hue:.0f}°")
    print(f"  Primary Colors: {palette.primary[:3]}")
    print(f"  Secondary Colors: {palette.secondary[:2]}")
    print(f"  Accent Colors: {palette.accents}")
    print(f"  Palette Fingerprint: {palette.palette_fingerprint}")
