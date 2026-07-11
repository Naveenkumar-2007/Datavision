import pandas as pd
from typing import List, Dict, Any, Tuple
import logging
from utils.paths import get_user_paths

logger = logging.getLogger(__name__)

class MultiDatasetEngine:
    """Intelligent engine for analyzing and joining multiple datasets"""
    
    @staticmethod
    def infer_joins(df1: pd.DataFrame, df2: pd.DataFrame, df1_name: str, df2_name: str) -> List[Dict[str, Any]]:
        """
        Intelligently infer possible join keys between two dataframes based on column names and content.
        Returns a list of suggested joins ranked by confidence.
        """
        suggestions = []
        
        cols1 = set(df1.columns)
        cols2 = set(df2.columns)
        
        # 1. Exact match on ID-like columns
        id_keywords = ['id', 'uuid', 'key']
        exact_matches = cols1.intersection(cols2)
        for col in exact_matches:
            if any(kw in col.lower() for kw in id_keywords):
                # Verify type compatibility
                if df1[col].dtype == df2[col].dtype:
                    # Calculate overlap
                    overlap = len(set(df1[col]).intersection(set(df2[col])))
                    if overlap > 0:
                        confidence = 0.95 if overlap > len(df1) * 0.1 or overlap > len(df2) * 0.1 else 0.7
                        suggestions.append({
                            "left_key": col,
                            "right_key": col,
                            "confidence": confidence,
                            "reason": f"Exact match on ID column '{col}' with data overlap."
                        })
        
        # 2. Heuristic match (e.g. 'customer_id' in df1, 'id' in df2 where df2 is 'customers')
        for col1 in cols1:
            for col2 in cols2:
                # If col1 is like 'table2_id' and col2 is 'id'
                if col1.lower() == f"{df2_name.lower().replace('.csv', '')}_id" and col2.lower() == 'id':
                    overlap = len(set(df1[col1]).intersection(set(df2[col2])))
                    if overlap > 0:
                        suggestions.append({
                            "left_key": col1,
                            "right_key": col2,
                            "confidence": 0.85,
                            "reason": f"Inferred foreign key relationship '{col1}' -> '{col2}'."
                        })
                # If col2 is like 'table1_id' and col1 is 'id'
                elif col2.lower() == f"{df1_name.lower().replace('.csv', '')}_id" and col1.lower() == 'id':
                    overlap = len(set(df1[col1]).intersection(set(df2[col2])))
                    if overlap > 0:
                        suggestions.append({
                            "left_key": col1,
                            "right_key": col2,
                            "confidence": 0.85,
                            "reason": f"Inferred foreign key relationship '{col1}' <- '{col2}'."
                        })
        
        # Sort by confidence descending
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        return suggestions

    @staticmethod
    def join_datasets(
        df1: pd.DataFrame, 
        df2: pd.DataFrame, 
        left_on: str, 
        right_on: str, 
        how: str = 'left'
    ) -> pd.DataFrame:
        """
        Execute the join between two datasets.
        Handles duplicates and renaming intelligently.
        """
        # Ensure compatible types for joining
        if df1[left_on].dtype != df2[right_on].dtype:
            try:
                # Attempt to coerce to string for joining if types mismatch
                df1[left_on] = df1[left_on].astype(str)
                df2[right_on] = df2[right_on].astype(str)
            except Exception as e:
                logger.warning(f"Could not coerce types for join: {e}")
                
        # Perform merge
        merged = pd.merge(df1, df2, left_on=left_on, right_on=right_on, how=how, suffixes=('_left', '_right'))
        
        # If right_on is different from left_on, we might have redundant columns, but pandas merge handles it.
        # If they are different names, both are kept. We can drop the right_on if it's redundant.
        if left_on != right_on and right_on in merged.columns:
            # Only drop if the values are identical (as in inner/left join)
            if how in ['left', 'inner']:
                merged = merged.drop(columns=[right_on])
                
        return merged
