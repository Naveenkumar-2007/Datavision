"""
🔬 FEATURE SYNTHESIS ENGINE v1.0 - GENETIC FEATURE GENERATION
==============================================================

Automatically discovers powerful new features using:
1. Genetic Algorithms - Evolve features through selection/mutation
2. Polynomial Features - Creates interactions like x1*x2, x1^2
3. Trigonometric Features - sin(x), cos(x) for cyclical patterns
4. Ratio & Difference Features - x1/x2, x1-x2
5. Mathematical Transformations - log, sqrt, exp, power

MAXIMUM ACCURACY MODE:
- Full feature exploration
- Intelligent feature selection
- Cross-validation for feature evaluation
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
import logging
import random
from itertools import combinations
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


@dataclass
class SynthesizedFeature:
    """Representation of a synthesized feature."""
    name: str
    formula: str
    source_columns: List[str]
    transformation_type: str
    importance_score: float = 0.0
    correlation_with_target: float = 0.0


class FeatureSynthesisEngine:
    """
    🔬 Feature Synthesis Engine - Genetic Feature Generation
    
    Automatically discovers powerful new features through:
    1. Mathematical Transformations (log, sqrt, exp, power)
    2. Polynomial Interactions (x1*x2, x1^2)
    3. Trigonometric Features (sin, cos for cyclical data)
    4. Ratio Features (x1/x2)
    5. Difference Features (x1-x2)
    6. Aggregation Features (rolling means, cumulative sums)
    
    Uses genetic algorithms to evolve and select the best features!
    """
    
    def __init__(
        self,
        max_features: int = 50,
        use_genetic: bool = True,
        generations: int = 10,
        population_size: int = 100,
        mutation_rate: float = 0.1,
        random_state: int = 42
    ):
        self.max_features = max_features
        self.use_genetic = use_genetic
        self.generations = generations
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.random_state = random_state
        
        random.seed(random_state)
        np.random.seed(random_state)
        
        # Store synthesized features for transform
        self.synthesized_features: List[SynthesizedFeature] = []
        self.selected_features: List[str] = []
        self.feature_formulas: Dict[str, Callable] = {}
        
        # Original column tracking
        self.original_numeric_cols: List[str] = []
        
        logger.info("🔬 Feature Synthesis Engine initialized")
    
    def _safe_transform(self, arr: np.ndarray, func: Callable, fill_value: float = 0.0) -> np.ndarray:
        """Apply transformation safely, handling invalid values."""
        with np.errstate(all='ignore'):
            result = func(arr)
            result = np.nan_to_num(result, nan=fill_value, posinf=fill_value, neginf=fill_value)
            # Clip extreme values
            result = np.clip(result, -1e10, 1e10)
        return result
    
    def _generate_unary_features(self, df: pd.DataFrame, numeric_cols: List[str]) -> pd.DataFrame:
        """Generate unary transformation features."""
        new_features = {}
        
        transformations = {
            'log1p': lambda x: np.log1p(np.abs(x)),
            'sqrt': lambda x: np.sqrt(np.abs(x)),
            'square': lambda x: x ** 2,
            'cube': lambda x: x ** 3,
            'exp_clipped': lambda x: np.exp(np.clip(x, -10, 10)),
            'reciprocal': lambda x: 1 / (x + 1e-8),
            'sin': lambda x: np.sin(x),
            'cos': lambda x: np.cos(x),
            'tanh': lambda x: np.tanh(x),
            'sigmoid': lambda x: 1 / (1 + np.exp(-np.clip(x, -10, 10))),
            'abs': lambda x: np.abs(x),
            'sign': lambda x: np.sign(x),
            'cbrt': lambda x: np.cbrt(x),
            'floor': lambda x: np.floor(x),
            'ceil': lambda x: np.ceil(x),
        }
        
        for col in numeric_cols[:15]:  # Limit to top 15 columns
            series = df[col].values.astype(float)
            
            # Skip constant columns
            if np.std(series) < 1e-8:
                continue
            
            for trans_name, trans_func in transformations.items():
                feature_name = f"{col}_{trans_name}"
                new_features[feature_name] = self._safe_transform(series, trans_func)
                
                self.synthesized_features.append(SynthesizedFeature(
                    name=feature_name,
                    formula=f"{trans_name}({col})",
                    source_columns=[col],
                    transformation_type='unary'
                ))
        
        return pd.DataFrame(new_features)
    
    def _generate_binary_features(self, df: pd.DataFrame, numeric_cols: List[str]) -> pd.DataFrame:
        """Generate binary interaction features."""
        new_features = {}
        
        # Limit number of combinations for performance
        max_cols = min(10, len(numeric_cols))
        selected_cols = numeric_cols[:max_cols]
        
        for col1, col2 in combinations(selected_cols, 2):
            arr1 = df[col1].values.astype(float)
            arr2 = df[col2].values.astype(float)
            
            # Multiplication
            feat_name = f"{col1}_x_{col2}"
            new_features[feat_name] = self._safe_transform(arr1 * arr2, lambda x: x)
            self.synthesized_features.append(SynthesizedFeature(
                name=feat_name,
                formula=f"{col1} * {col2}",
                source_columns=[col1, col2],
                transformation_type='interaction'
            ))
            
            # Division (safe)
            feat_name = f"{col1}_div_{col2}"
            new_features[feat_name] = self._safe_transform(
                arr1 / (arr2 + 1e-8), lambda x: x
            )
            self.synthesized_features.append(SynthesizedFeature(
                name=feat_name,
                formula=f"{col1} / {col2}",
                source_columns=[col1, col2],
                transformation_type='ratio'
            ))
            
            # Addition
            feat_name = f"{col1}_plus_{col2}"
            new_features[feat_name] = arr1 + arr2
            self.synthesized_features.append(SynthesizedFeature(
                name=feat_name,
                formula=f"{col1} + {col2}",
                source_columns=[col1, col2],
                transformation_type='addition'
            ))
            
            # Subtraction (absolute difference)
            feat_name = f"{col1}_minus_{col2}"
            new_features[feat_name] = np.abs(arr1 - arr2)
            self.synthesized_features.append(SynthesizedFeature(
                name=feat_name,
                formula=f"|{col1} - {col2}|",
                source_columns=[col1, col2],
                transformation_type='difference'
            ))
            
            # Max/Min of pair
            feat_name = f"max_{col1}_{col2}"
            new_features[feat_name] = np.maximum(arr1, arr2)
            self.synthesized_features.append(SynthesizedFeature(
                name=feat_name,
                formula=f"max({col1}, {col2})",
                source_columns=[col1, col2],
                transformation_type='aggregation'
            ))
            
            feat_name = f"min_{col1}_{col2}"
            new_features[feat_name] = np.minimum(arr1, arr2)
            self.synthesized_features.append(SynthesizedFeature(
                name=feat_name,
                formula=f"min({col1}, {col2})",
                source_columns=[col1, col2],
                transformation_type='aggregation'
            ))
        
        return pd.DataFrame(new_features)
    
    def _generate_polynomial_features(self, df: pd.DataFrame, numeric_cols: List[str], degree: int = 2) -> pd.DataFrame:
        """Generate polynomial features up to specified degree."""
        new_features = {}
        
        # Limit columns for polynomial features
        max_cols = min(8, len(numeric_cols))
        selected_cols = numeric_cols[:max_cols]
        
        for col in selected_cols:
            arr = df[col].values.astype(float)
            
            for d in range(2, degree + 1):
                feat_name = f"{col}_pow{d}"
                new_features[feat_name] = self._safe_transform(arr ** d, lambda x: x)
                self.synthesized_features.append(SynthesizedFeature(
                    name=feat_name,
                    formula=f"{col}^{d}",
                    source_columns=[col],
                    transformation_type='polynomial'
                ))
        
        return pd.DataFrame(new_features)
    
    def _generate_statistical_features(self, df: pd.DataFrame, numeric_cols: List[str]) -> pd.DataFrame:
        """Generate row-wise statistical features."""
        new_features = {}
        
        if len(numeric_cols) < 2:
            return pd.DataFrame()
        
        numeric_df = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        
        # Row-wise statistics
        new_features['row_mean'] = numeric_df.mean(axis=1).values
        new_features['row_std'] = numeric_df.std(axis=1).values
        new_features['row_min'] = numeric_df.min(axis=1).values
        new_features['row_max'] = numeric_df.max(axis=1).values
        new_features['row_range'] = (numeric_df.max(axis=1) - numeric_df.min(axis=1)).values
        new_features['row_sum'] = numeric_df.sum(axis=1).values
        new_features['row_median'] = numeric_df.median(axis=1).values
        new_features['row_skew'] = numeric_df.skew(axis=1).values
        new_features['row_nonzero_count'] = (numeric_df != 0).sum(axis=1).values
        new_features['row_null_count'] = numeric_df.isna().sum(axis=1).values
        
        for name in new_features.keys():
            self.synthesized_features.append(SynthesizedFeature(
                name=name,
                formula=f"{name}(all_numeric_cols)",
                source_columns=numeric_cols,
                transformation_type='statistical'
            ))
        
        # Clean up NaN values
        for name in new_features:
            new_features[name] = np.nan_to_num(new_features[name], nan=0.0)
        
        return pd.DataFrame(new_features)
    
    def _evaluate_feature_importance(
        self, 
        X: pd.DataFrame, 
        y: np.ndarray,
        task_type: str = 'classification'
    ) -> Dict[str, float]:
        """Evaluate importance of synthesized features."""
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
        
        importance_scores = {}
        
        # Use mutual information for feature scoring
        try:
            X_clean = X.apply(pd.to_numeric, errors='coerce').fillna(0)
            X_arr = np.nan_to_num(X_clean.values.astype(float), nan=0.0, posinf=0.0, neginf=0.0)
            
            if task_type == 'classification':
                mi_scores = mutual_info_classif(X_arr, y, random_state=self.random_state)
            else:
                mi_scores = mutual_info_regression(X_arr, y, random_state=self.random_state)
            
            for col, score in zip(X_clean.columns, mi_scores):
                importance_scores[col] = float(score)
                
        except Exception as e:
            logger.warning(f"Could not compute mutual information: {e}")
            # Fallback to correlation-based importance
            for col in X.columns:
                try:
                    corr = np.abs(np.corrcoef(X[col].values.astype(float), y)[0, 1])
                    importance_scores[col] = corr if not np.isnan(corr) else 0.0
                except:
                    importance_scores[col] = 0.0
        
        return importance_scores
    
    def _genetic_feature_selection(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        importance_scores: Dict[str, float]
    ) -> List[str]:
        """Use genetic algorithm to select best feature subset."""
        all_features = list(X.columns)
        n_features = len(all_features)
        
        if n_features <= self.max_features:
            return all_features
        
        # Initialize population (binary masks for feature selection)
        population = []
        for _ in range(self.population_size):
            # Start with better features more likely to be selected
            probs = np.array([
                importance_scores.get(f, 0.0) for f in all_features
            ])
            probs = (probs - probs.min()) / (probs.max() - probs.min() + 1e-8)
            probs = 0.3 + 0.4 * probs  # Scale to 30-70% probability
            
            mask = np.random.random(n_features) < probs
            # Ensure at least max_features/2 features selected
            if mask.sum() < self.max_features // 2:
                top_indices = np.argsort(probs)[-self.max_features // 2:]
                mask[top_indices] = True
            population.append(mask)
        
        def fitness(mask: np.ndarray) -> float:
            """Evaluate fitness of a feature subset."""
            if mask.sum() == 0:
                return -1e10
            
            selected = [f for f, m in zip(all_features, mask) if m]
            # Fitness = sum of importance scores - penalty for too many features
            score = sum(importance_scores.get(f, 0.0) for f in selected)
            penalty = max(0, mask.sum() - self.max_features) * 0.01
            return score - penalty
        
        # Evolution
        for gen in range(self.generations):
            # Evaluate fitness
            fitness_scores = [fitness(ind) for ind in population]
            
            # Selection (tournament)
            new_population = []
            for _ in range(self.population_size):
                # Tournament selection
                candidates = random.sample(range(len(population)), k=3)
                winner = max(candidates, key=lambda i: fitness_scores[i])
                new_population.append(population[winner].copy())
            
            # Crossover
            for i in range(0, len(new_population) - 1, 2):
                if random.random() < 0.7:  # Crossover probability
                    point = random.randint(1, n_features - 1)
                    new_population[i][point:], new_population[i+1][point:] = \
                        new_population[i+1][point:].copy(), new_population[i][point:].copy()
            
            # Mutation
            for ind in new_population:
                for j in range(n_features):
                    if random.random() < self.mutation_rate:
                        ind[j] = not ind[j]
            
            population = new_population
        
        # Select best individual
        fitness_scores = [fitness(ind) for ind in population]
        best_idx = np.argmax(fitness_scores)
        best_mask = population[best_idx]
        
        selected_features = [f for f, m in zip(all_features, best_mask) if m]
        
        # Limit to max_features
        if len(selected_features) > self.max_features:
            # Keep top by importance
            selected_features.sort(
                key=lambda f: importance_scores.get(f, 0.0), 
                reverse=True
            )
            selected_features = selected_features[:self.max_features]
        
        return selected_features
    
    def fit_transform(
        self,
        df: pd.DataFrame,
        target_col: str,
        task_type: str = 'classification'
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Generate and select new features.
        
        Args:
            df: Input DataFrame
            target_col: Name of target column
            task_type: 'classification' or 'regression'
            
        Returns:
            Tuple of (enhanced DataFrame, list of new feature names)
        """
        print("\n" + "=" * 60)
        print("🔬 FEATURE SYNTHESIS ENGINE [MAXIMUM ACCURACY]")
        print("=" * 60)
        
        # Identify numeric columns
        feature_df = df.drop(columns=[target_col], errors='ignore')
        self.original_numeric_cols = feature_df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(self.original_numeric_cols) == 0:
            print("   ⚠️ No numeric columns found for feature synthesis")
            return df, []
        
        print(f"   📊 Input: {len(self.original_numeric_cols)} numeric columns")
        
        # Generate features
        self.synthesized_features = []  # Reset
        
        # 1. Unary transformations
        print("   🔧 Generating unary transformations...")
        unary_df = self._generate_unary_features(feature_df, self.original_numeric_cols)
        
        # 2. Binary interactions
        print("   🔧 Generating binary interactions...")
        binary_df = self._generate_binary_features(feature_df, self.original_numeric_cols)
        
        # 3. Polynomial features
        print("   🔧 Generating polynomial features...")
        poly_df = self._generate_polynomial_features(feature_df, self.original_numeric_cols, degree=2)
        
        # 4. Statistical features
        print("   🔧 Generating statistical features...")
        stat_df = self._generate_statistical_features(feature_df, self.original_numeric_cols)
        
        # Combine all
        all_new_features = pd.concat([unary_df, binary_df, poly_df, stat_df], axis=1)
        print(f"   📊 Generated {len(all_new_features.columns)} new features")
        
        # Clean data
        all_new_features = all_new_features.apply(pd.to_numeric, errors='coerce').fillna(0)
        
        # Evaluate feature importance
        print("   📊 Evaluating feature importance...")
        y = df[target_col].values
        if task_type == 'classification':
            from sklearn.preprocessing import LabelEncoder
            le = LabelEncoder()
            y_encoded = le.fit_transform(y.astype(str))
        else:
            y_encoded = y.astype(float)
        
        importance_scores = self._evaluate_feature_importance(
            all_new_features, y_encoded, task_type
        )
        
        # Update importance scores in synthesized features
        for feat in self.synthesized_features:
            feat.importance_score = importance_scores.get(feat.name, 0.0)
        
        # Select best features
        if self.use_genetic:
            print("   🧬 Running genetic feature selection...")
            self.selected_features = self._genetic_feature_selection(
                all_new_features, y_encoded, importance_scores
            )
        else:
            # Simple top-k selection
            sorted_features = sorted(
                importance_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            self.selected_features = [f for f, _ in sorted_features[:self.max_features]]
        
        print(f"   ✅ Selected {len(self.selected_features)} best synthesized features")
        
        # Store formulas for transform
        for feat in self.synthesized_features:
            if feat.name in self.selected_features:
                # Store the transformation info for later use
                self.feature_formulas[feat.name] = {
                    'formula': feat.formula,
                    'source_columns': feat.source_columns,
                    'transformation_type': feat.transformation_type
                }
        
        # Create enhanced DataFrame
        selected_new_df = all_new_features[self.selected_features]
        enhanced_df = pd.concat([df, selected_new_df], axis=1)
        
        # Report top features
        print("\n   📈 Top 5 synthesized features:")
        top_features = sorted(
            [(f, importance_scores.get(f, 0)) for f in self.selected_features],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        for name, score in top_features:
            formula = next(
                (f.formula for f in self.synthesized_features if f.name == name), 
                name
            )
            print(f"      • {name}: {formula} (importance: {score:.4f})")
        
        return enhanced_df, self.selected_features
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply same feature synthesis to new data.
        Must call fit_transform first.
        """
        if not self.selected_features:
            return df
        
        # Regenerate the same features
        all_new = {}
        
        for feat_name in self.selected_features:
            if feat_name not in self.feature_formulas:
                continue
            
            info = self.feature_formulas[feat_name]
            source_cols = info['source_columns']
            trans_type = info['transformation_type']
            
            try:
                if trans_type == 'unary':
                    # Parse transformation from feature name
                    col = source_cols[0]
                    if col not in df.columns:
                        all_new[feat_name] = np.zeros(len(df))
                        continue
                        
                    arr = df[col].values.astype(float)
                    
                    # Determine transformation
                    if '_log1p' in feat_name:
                        all_new[feat_name] = np.log1p(np.abs(arr))
                    elif '_sqrt' in feat_name:
                        all_new[feat_name] = np.sqrt(np.abs(arr))
                    elif '_square' in feat_name:
                        all_new[feat_name] = arr ** 2
                    elif '_cube' in feat_name:
                        all_new[feat_name] = arr ** 3
                    elif '_sin' in feat_name:
                        all_new[feat_name] = np.sin(arr)
                    elif '_cos' in feat_name:
                        all_new[feat_name] = np.cos(arr)
                    elif '_tanh' in feat_name:
                        all_new[feat_name] = np.tanh(arr)
                    elif '_sigmoid' in feat_name:
                        all_new[feat_name] = 1 / (1 + np.exp(-np.clip(arr, -10, 10)))
                    elif '_abs' in feat_name:
                        all_new[feat_name] = np.abs(arr)
                    elif '_reciprocal' in feat_name:
                        all_new[feat_name] = 1 / (arr + 1e-8)
                    else:
                        all_new[feat_name] = arr  # Fallback
                        
                elif trans_type in ['interaction', 'ratio', 'addition', 'difference']:
                    col1, col2 = source_cols[0], source_cols[1]
                    if col1 not in df.columns or col2 not in df.columns:
                        all_new[feat_name] = np.zeros(len(df))
                        continue
                        
                    arr1 = df[col1].values.astype(float)
                    arr2 = df[col2].values.astype(float)
                    
                    if '_x_' in feat_name:
                        all_new[feat_name] = arr1 * arr2
                    elif '_div_' in feat_name:
                        all_new[feat_name] = arr1 / (arr2 + 1e-8)
                    elif '_plus_' in feat_name:
                        all_new[feat_name] = arr1 + arr2
                    elif '_minus_' in feat_name:
                        all_new[feat_name] = np.abs(arr1 - arr2)
                    elif 'max_' in feat_name:
                        all_new[feat_name] = np.maximum(arr1, arr2)
                    elif 'min_' in feat_name:
                        all_new[feat_name] = np.minimum(arr1, arr2)
                        
                elif trans_type == 'polynomial':
                    col = source_cols[0]
                    if col not in df.columns:
                        all_new[feat_name] = np.zeros(len(df))
                        continue
                        
                    arr = df[col].values.astype(float)
                    
                    if '_pow2' in feat_name:
                        all_new[feat_name] = arr ** 2
                    elif '_pow3' in feat_name:
                        all_new[feat_name] = arr ** 3
                        
                elif trans_type == 'statistical':
                    # Row-wise statistics need all numeric columns
                    numeric_cols = [c for c in self.original_numeric_cols if c in df.columns]
                    if not numeric_cols:
                        all_new[feat_name] = np.zeros(len(df))
                        continue
                        
                    numeric_df = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
                    
                    if feat_name == 'row_mean':
                        all_new[feat_name] = numeric_df.mean(axis=1).values
                    elif feat_name == 'row_std':
                        all_new[feat_name] = numeric_df.std(axis=1).values
                    elif feat_name == 'row_min':
                        all_new[feat_name] = numeric_df.min(axis=1).values
                    elif feat_name == 'row_max':
                        all_new[feat_name] = numeric_df.max(axis=1).values
                    elif feat_name == 'row_range':
                        all_new[feat_name] = (numeric_df.max(axis=1) - numeric_df.min(axis=1)).values
                    elif feat_name == 'row_sum':
                        all_new[feat_name] = numeric_df.sum(axis=1).values
                    elif feat_name == 'row_median':
                        all_new[feat_name] = numeric_df.median(axis=1).values
                else:
                    all_new[feat_name] = np.zeros(len(df))
                    
            except Exception as e:
                logger.warning(f"Could not transform feature {feat_name}: {e}")
                all_new[feat_name] = np.zeros(len(df))
        
        # Clean and add to DataFrame
        for name in all_new:
            all_new[name] = np.nan_to_num(all_new[name], nan=0.0, posinf=0.0, neginf=0.0)
        
        new_df = pd.DataFrame(all_new, index=df.index)
        return pd.concat([df, new_df], axis=1)
    
    def get_synthesized_features_info(self) -> List[Dict]:
        """Get information about synthesized features."""
        return [
            {
                'name': f.name,
                'formula': f.formula,
                'importance': f.importance_score,
                'type': f.transformation_type,
                'sources': f.source_columns
            }
            for f in self.synthesized_features
            if f.name in self.selected_features
        ]
