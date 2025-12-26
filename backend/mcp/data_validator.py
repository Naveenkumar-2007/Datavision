# MCP Data Validator Module
"""
Data Validation and Quality Assessment Tools for MCP Integration.

Features:
- Schema validation
- Business rule checks
- Data quality scoring
- Cross-reference validation
- Constraint checking
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union, Callable
from enum import Enum
import re


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """A single validation issue"""
    rule: str
    message: str
    severity: ValidationSeverity
    column: Optional[str] = None
    row_indices: Optional[List[int]] = None
    sample_values: Optional[List[Any]] = None


@dataclass
class ValidationResult:
    """Result from validation"""
    is_valid: bool
    issues: List[ValidationIssue]
    quality_score: float  # 0-100
    total_checks: int
    passed_checks: int
    summary: str


class DataValidator:
    """
    Enterprise Data Validator MCP.
    
    Provides comprehensive data validation:
    - Schema validation
    - Value constraints
    - Business rules
    - Referential integrity
    - Data quality scoring
    """
    
    def __init__(self):
        self.issues: List[ValidationIssue] = []
        self.checks_run = 0
        self.checks_passed = 0
    
    def validate(
        self,
        data: Any,
        schema: Optional[Dict] = None,
        rules: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive validation on data.
        
        Args:
            data: DataFrame or dict data
            schema: Expected schema definition
            rules: Custom validation rules
            
        Returns:
            Validation results
        """
        try:
            import pandas as pd
            
            self.issues = []
            self.checks_run = 0
            self.checks_passed = 0
            
            if isinstance(data, pd.DataFrame):
                df = data.copy()
            else:
                df = pd.DataFrame(data)
            
            # Run validations
            self._validate_schema(df, schema)
            self._validate_completeness(df)
            self._validate_uniqueness(df)
            self._validate_data_types(df)
            self._validate_custom_rules(df, rules)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(df)
            
            is_valid = not any(
                issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
                for issue in self.issues
            )
            
            return {
                "success": True,
                "is_valid": is_valid,
                "quality_score": quality_score,
                "total_checks": self.checks_run,
                "passed_checks": self.checks_passed,
                "issues": [
                    {
                        "rule": i.rule,
                        "message": i.message,
                        "severity": i.severity.value,
                        "column": i.column,
                        "affected_rows": len(i.row_indices) if i.row_indices else 0
                    }
                    for i in self.issues
                ],
                "summary": self._generate_summary()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _validate_schema(self, df, schema: Optional[Dict]) -> None:
        """Validate data against expected schema"""
        self.checks_run += 1
        
        if not schema:
            self.checks_passed += 1
            return
        
        # Check required columns
        required_cols = schema.get('required_columns', [])
        missing = [col for col in required_cols if col not in df.columns]
        
        if missing:
            self.issues.append(ValidationIssue(
                rule="required_columns",
                message=f"Missing required columns: {', '.join(missing)}",
                severity=ValidationSeverity.ERROR
            ))
        else:
            self.checks_passed += 1
        
        # Check column types
        expected_types = schema.get('column_types', {})
        for col, expected_type in expected_types.items():
            self.checks_run += 1
            if col not in df.columns:
                continue
            
            actual_type = str(df[col].dtype)
            if not self._types_compatible(actual_type, expected_type):
                self.issues.append(ValidationIssue(
                    rule="column_type",
                    message=f"Column '{col}' expected type '{expected_type}', got '{actual_type}'",
                    severity=ValidationSeverity.WARNING,
                    column=col
                ))
            else:
                self.checks_passed += 1
    
    def _types_compatible(self, actual: str, expected: str) -> bool:
        """Check if types are compatible"""
        type_groups = {
            'numeric': ['int64', 'float64', 'int32', 'float32', 'int', 'float'],
            'string': ['object', 'str', 'string'],
            'datetime': ['datetime64', 'datetime'],
            'bool': ['bool', 'boolean']
        }
        
        for group, types in type_groups.items():
            if expected.lower() in types and actual.lower() in types:
                return True
        
        return expected.lower() in actual.lower()
    
    def _validate_completeness(self, df) -> None:
        """Check for completeness (null values)"""
        for col in df.columns:
            self.checks_run += 1
            null_count = df[col].isna().sum()
            null_pct = (null_count / len(df)) * 100
            
            if null_pct > 50:
                self.issues.append(ValidationIssue(
                    rule="completeness",
                    message=f"Column '{col}' has {null_pct:.1f}% null values ({null_count} rows)",
                    severity=ValidationSeverity.ERROR,
                    column=col,
                    row_indices=list(df[df[col].isna()].index[:10])
                ))
            elif null_pct > 20:
                self.issues.append(ValidationIssue(
                    rule="completeness",
                    message=f"Column '{col}' has {null_pct:.1f}% null values",
                    severity=ValidationSeverity.WARNING,
                    column=col
                ))
                self.checks_passed += 1
            else:
                self.checks_passed += 1
    
    def _validate_uniqueness(self, df) -> None:
        """Check for potential unique key violations"""
        # Auto-detect potential ID columns
        id_patterns = ['id', 'key', 'code', 'number', 'no']
        
        for col in df.columns:
            col_lower = col.lower()
            is_id_col = any(p in col_lower for p in id_patterns)
            
            if is_id_col:
                self.checks_run += 1
                duplicates = df[col].duplicated().sum()
                
                if duplicates > 0:
                    self.issues.append(ValidationIssue(
                        rule="uniqueness",
                        message=f"Potential ID column '{col}' has {duplicates} duplicate values",
                        severity=ValidationSeverity.WARNING,
                        column=col,
                        sample_values=df[df[col].duplicated()][col].head(5).tolist()
                    ))
                else:
                    self.checks_passed += 1
    
    def _validate_data_types(self, df) -> None:
        """Validate data type consistency within columns"""
        for col in df.columns:
            if df[col].dtype == 'object':
                self.checks_run += 1
                
                # Check for mixed types
                types_found = df[col].dropna().apply(type).unique()
                
                if len(types_found) > 1:
                    self.issues.append(ValidationIssue(
                        rule="type_consistency",
                        message=f"Column '{col}' contains mixed types: {[t.__name__ for t in types_found]}",
                        severity=ValidationSeverity.INFO,
                        column=col
                    ))
                else:
                    self.checks_passed += 1
    
    def _validate_custom_rules(self, df, rules: Optional[List[Dict]]) -> None:
        """Apply custom validation rules"""
        if not rules:
            return
        
        for rule in rules:
            self.checks_run += 1
            rule_type = rule.get('type')
            column = rule.get('column')
            
            if column and column not in df.columns:
                continue
            
            if rule_type == 'range':
                self._check_range(df, column, rule.get('min'), rule.get('max'))
            elif rule_type == 'regex':
                self._check_regex(df, column, rule.get('pattern'))
            elif rule_type == 'allowed_values':
                self._check_allowed_values(df, column, rule.get('values', []))
            elif rule_type == 'not_null':
                self._check_not_null(df, column)
            else:
                self.checks_passed += 1
    
    def _check_range(self, df, column: str, min_val: Any, max_val: Any) -> None:
        """Check if values are within range"""
        import pandas as pd
        
        violations = df[
            (df[column] < min_val) | (df[column] > max_val)
        ] if min_val is not None and max_val is not None else pd.DataFrame()
        
        if len(violations) > 0:
            self.issues.append(ValidationIssue(
                rule="range",
                message=f"Column '{column}' has {len(violations)} values outside range [{min_val}, {max_val}]",
                severity=ValidationSeverity.ERROR,
                column=column,
                row_indices=list(violations.index[:10]),
                sample_values=violations[column].head(5).tolist()
            ))
        else:
            self.checks_passed += 1
    
    def _check_regex(self, df, column: str, pattern: str) -> None:
        """Check if values match regex pattern"""
        if not pattern:
            self.checks_passed += 1
            return
        
        regex = re.compile(pattern)
        violations = df[~df[column].astype(str).str.match(pattern, na=False)]
        
        if len(violations) > 0:
            self.issues.append(ValidationIssue(
                rule="regex",
                message=f"Column '{column}' has {len(violations)} values not matching pattern '{pattern}'",
                severity=ValidationSeverity.WARNING,
                column=column,
                row_indices=list(violations.index[:10])
            ))
        else:
            self.checks_passed += 1
    
    def _check_allowed_values(self, df, column: str, allowed: List[Any]) -> None:
        """Check if all values are in allowed list"""
        violations = df[~df[column].isin(allowed)]
        
        if len(violations) > 0:
            invalid_values = violations[column].unique()[:5].tolist()
            self.issues.append(ValidationIssue(
                rule="allowed_values",
                message=f"Column '{column}' has invalid values: {invalid_values}",
                severity=ValidationSeverity.ERROR,
                column=column,
                row_indices=list(violations.index[:10]),
                sample_values=invalid_values
            ))
        else:
            self.checks_passed += 1
    
    def _check_not_null(self, df, column: str) -> None:
        """Check that column has no null values"""
        null_count = df[column].isna().sum()
        
        if null_count > 0:
            self.issues.append(ValidationIssue(
                rule="not_null",
                message=f"Column '{column}' has {null_count} null values but is marked as required",
                severity=ValidationSeverity.ERROR,
                column=column,
                row_indices=list(df[df[column].isna()].index[:10])
            ))
        else:
            self.checks_passed += 1
    
    def _calculate_quality_score(self, df) -> float:
        """Calculate overall data quality score (0-100)"""
        import pandas as pd
        
        scores = []
        
        # Completeness score (0-30 points)
        null_ratio = df.isna().sum().sum() / df.size
        completeness_score = (1 - null_ratio) * 30
        scores.append(completeness_score)
        
        # Uniqueness score for ID columns (0-20 points)
        id_cols = [c for c in df.columns if any(p in c.lower() for p in ['id', 'key'])]
        if id_cols:
            dup_ratio = sum(df[c].duplicated().sum() for c in id_cols) / (len(df) * len(id_cols))
            uniqueness_score = (1 - dup_ratio) * 20
        else:
            uniqueness_score = 20
        scores.append(uniqueness_score)
        
        # Consistency score based on issues (0-30 points)
        error_count = sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)
        consistency_score = max(0, 30 - (error_count * 5) - (warning_count * 2))
        scores.append(consistency_score)
        
        # Validity score based on checks passed (0-20 points)
        if self.checks_run > 0:
            validity_score = (self.checks_passed / self.checks_run) * 20
        else:
            validity_score = 20
        scores.append(validity_score)
        
        return round(sum(scores), 1)
    
    def _generate_summary(self) -> str:
        """Generate human-readable validation summary"""
        error_count = sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)
        
        if error_count == 0 and warning_count == 0:
            return "✅ Data validation passed with no issues"
        elif error_count == 0:
            return f"⚠️ Data validation passed with {warning_count} warning(s)"
        else:
            return f"❌ Data validation failed: {error_count} error(s), {warning_count} warning(s)"


# Convenience functions for direct MCP calls
def validate_data(data, schema=None, rules=None):
    """Run comprehensive data validation"""
    validator = DataValidator()
    return validator.validate(data, schema, rules)


def check_data_quality(data):
    """Quick data quality check"""
    validator = DataValidator()
    result = validator.validate(data)
    return {
        "quality_score": result.get("quality_score", 0),
        "is_valid": result.get("is_valid", False),
        "summary": result.get("summary", "")
    }


def validate_schema_compliance(data, schema):
    """Validate data against a specific schema"""
    validator = DataValidator()
    result = validator.validate(data, schema=schema)
    schema_issues = [i for i in result.get("issues", []) if i.get("rule") in ["required_columns", "column_type"]]
    return {
        "compliant": len(schema_issues) == 0,
        "issues": schema_issues
    }


# Quick test
if __name__ == "__main__":
    test_data = [
        {"id": 1, "name": "Alice", "age": 25, "email": "alice@test.com"},
        {"id": 2, "name": "Bob", "age": None, "email": "bob@test.com"},
        {"id": 2, "name": "Charlie", "age": 35, "email": "invalid"},
        {"id": 4, "name": None, "age": 45, "email": "dave@test.com"},
    ]
    
    # Define schema
    schema = {
        "required_columns": ["id", "name", "age"],
        "column_types": {"id": "int", "age": "int"}
    }
    
    # Define custom rules
    rules = [
        {"type": "range", "column": "age", "min": 0, "max": 120},
        {"type": "regex", "column": "email", "pattern": r".*@.*\..*"},
    ]
    
    result = validate_data(test_data, schema, rules)
    
    print("Validation Result:")
    print(f"  Valid: {result['is_valid']}")
    print(f"  Quality Score: {result['quality_score']}")
    print(f"  Summary: {result['summary']}")
    print(f"\nIssues ({len(result['issues'])}):")
    for issue in result['issues']:
        print(f"  [{issue['severity']}] {issue['rule']}: {issue['message']}")
