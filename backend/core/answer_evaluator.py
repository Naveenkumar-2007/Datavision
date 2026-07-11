"""
Answer Evaluator - Check if AI response is grounded in data
============================================================

Simple evaluation to ensure answers are based on provided context.
Returns confidence score and flags unverified claims.
"""

import re
from typing import Dict, List, Tuple


def extract_numbers(text: str) -> List[str]:
    """Extract all numbers (including currency) from text"""
    # Match numbers with optional currency symbols and commas
    patterns = [
        r'[\$€£₹]?\s*[\d,]+\.?\d*\s*(?:million|billion|M|B|K)?',
        r'\d+\.?\d*\s*%',  # Percentages
        r'\d+',  # Plain numbers
    ]
    
    numbers = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        numbers.extend([m.strip() for m in matches if m.strip()])
    
    return list(set(numbers))


def extract_entities(text: str) -> List[str]:
    """Extract key entities (names, terms) from text"""
    # Remove common stop words and extract significant terms
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                  'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                  'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                  'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
                  'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
                  'through', 'during', 'before', 'after', 'above', 'below',
                  'between', 'under', 'again', 'further', 'then', 'once',
                  'here', 'there', 'when', 'where', 'why', 'how', 'all',
                  'each', 'few', 'more', 'most', 'other', 'some', 'such',
                  'no', 'nor', 'not', 'only', 'own', 'same', 'than', 'too',
                  'very', 'just', 'and', 'but', 'or', 'if', 'because',
                  'this', 'that', 'these', 'those', 'it', 'its'}
    
    # Extract words that look like entities (capitalized or specific patterns)
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
    
    # Also get quoted terms
    quoted = re.findall(r'"([^"]+)"', text)
    
    # Filter and combine
    entities = []
    for word in words + quoted:
        if word.lower() not in stop_words and len(word) > 2:
            entities.append(word)
    
    return list(set(entities))


def normalize_number(num_str: str) -> float:
    """Convert number string to float for comparison"""
    try:
        # Remove currency symbols and commas
        cleaned = re.sub(r'[\$€£₹,\s]', '', num_str)
        
        # Handle M/K/B suffixes
        multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000,
                       'million': 1000000, 'billion': 1000000000}
        
        for suffix, mult in multipliers.items():
            if cleaned.lower().endswith(suffix):
                cleaned = cleaned[:-len(suffix)]
                return float(cleaned) * mult
        
        return float(cleaned)
    except:
        return None


def evaluate_answer(answer: str, context: str, query: str = "") -> Dict:
    """
    Evaluate if answer is grounded in the provided context.
    
    Args:
        answer: The AI-generated response
        context: The retrieved context/data
        query: Original user query (optional)
        
    Returns:
        {
            "grounded": bool,
            "confidence": int (0-100),
            "verified_claims": [...],
            "unverified_claims": [...],
            "warning": str or None
        }
    """
    if not answer or not context:
        return {
            "grounded": False,
            "confidence": 0,
            "verified_claims": [],
            "unverified_claims": [],
            "warning": "Missing answer or context"
        }
    
    context_lower = context.lower()
    answer_lower = answer.lower()
    
    # ⚡ FIX: Truncate context to prevent catastrophic regex CPU hanging on massive datasets
    max_context_len = 5000
    safe_context = context if len(context) < max_context_len else context[:max_context_len]
    
    # Extract numbers from answer
    answer_numbers = extract_numbers(answer)
    context_numbers = extract_numbers(safe_context)
    
    # Extract entities from answer
    answer_entities = extract_entities(answer)
    
    verified_claims = []
    unverified_claims = []
    
    # Check numbers
    for num in answer_numbers:
        num_normalized = normalize_number(num)
        found = False
        
        # Direct string match
        if num.lower() in context_lower:
            found = True
        
        # Normalized value match
        if not found and num_normalized:
            for ctx_num in context_numbers:
                ctx_normalized = normalize_number(ctx_num)
                if ctx_normalized and abs(num_normalized - ctx_normalized) < 0.01:
                    found = True
                    break
        
        if found:
            verified_claims.append(f"Number: {num}")
        else:
            unverified_claims.append(f"Number: {num}")
    
    # Check entities
    for entity in answer_entities:
        if entity.lower() in context_lower:
            verified_claims.append(f"Entity: {entity}")
        else:
            # Partial match
            entity_words = entity.lower().split()
            if any(word in context_lower for word in entity_words if len(word) > 3):
                verified_claims.append(f"Entity (partial): {entity}")
            else:
                unverified_claims.append(f"Entity: {entity}")
    
    # Calculate confidence
    total_claims = len(verified_claims) + len(unverified_claims)
    if total_claims == 0:
        confidence = 70  # Neutral if no claims to verify
    else:
        confidence = int((len(verified_claims) / total_claims) * 100)
    
    # Determine grounding
    grounded = confidence >= 50
    
    # Generate warning if needed
    warning = None
    if len(unverified_claims) > 0:
        if confidence < 30:
            warning = "⚠️ Low confidence: Many claims could not be verified in the data."
        elif confidence < 60:
            warning = "⚠️ Some claims may not be directly supported by the data."
    
    return {
        "grounded": grounded,
        "confidence": confidence,
        "verified_claims": verified_claims[:5],  # Limit for display
        "unverified_claims": unverified_claims[:5],
        "warning": warning
    }


def get_confidence_badge(confidence: int) -> str:
    """Return emoji badge based on confidence level"""
    if confidence >= 90:
        return "🟢 High Confidence"
    elif confidence >= 70:
        return "🟡 Medium Confidence"
    elif confidence >= 50:
        return "🟠 Low Confidence"
    else:
        return "🔴 Very Low Confidence"


# Test
if __name__ == "__main__":
    context = """
    Revenue data from hr_dataset_500_rows.csv:
    - Total employees: 500
    - Average salary: $75,000
    - Department: Engineering, Sales, Marketing, HR
    - Performance ratings: 1-5 scale
    """
    
    # Good answer (grounded)
    good_answer = "There are 500 employees with an average salary of $75,000 across Engineering, Sales, and Marketing departments."
    
    # Bad answer (hallucinated)
    bad_answer = "The company has $50 million in revenue and 10,000 customers across 50 countries."
    
    print("=== Good Answer ===")
    result = evaluate_answer(good_answer, context)
    print(f"Confidence: {result['confidence']}%")
    print(f"Grounded: {result['grounded']}")
    print(f"Verified: {result['verified_claims']}")
    print(f"Unverified: {result['unverified_claims']}")
    
    print("\n=== Bad Answer ===")
    result = evaluate_answer(bad_answer, context)
    print(f"Confidence: {result['confidence']}%")
    print(f"Grounded: {result['grounded']}")
    print(f"Warning: {result['warning']}")
