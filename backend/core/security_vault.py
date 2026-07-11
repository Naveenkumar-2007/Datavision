import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SecurityVault:
    """
    Enterprise-grade Data Privacy and Security Guardrails for DataVision V4.
    Scrubs PII (Personally Identifiable Information) before it reaches the LLM.
    """
    
    @staticmethod
    def mask_pii(text: str) -> str:
        """
        Detects and masks sensitive PII in raw text data.
        """
        if not isinstance(text, str):
            return text
            
        # Mask Emails
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        text = re.sub(email_pattern, '[REDACTED_EMAIL]', text)
        
        # Mask Social Security Numbers (SSN)
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        text = re.sub(ssn_pattern, '[REDACTED_SSN]', text)
        
        # Mask Credit Cards (simplified pattern)
        cc_pattern = r'\b(?:\d[ -]*?){13,16}\b'
        text = re.sub(cc_pattern, '[REDACTED_CREDIT_CARD]', text)
        
        # Mask Phone Numbers (US standard)
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        text = re.sub(phone_pattern, '[REDACTED_PHONE]', text)
        
        return text

    @staticmethod
    def apply_nemo_guardrails(llm_response: str) -> str:
        """
        Simulates output guardrails to prevent harmful, hallucinatory, or unsafe code execution.
        """
        dangerous_patterns = [
            "os.system", "subprocess", "rm -rf", "drop table",
            "I can guarantee these financial returns", "invest all your money"
        ]
        
        for pattern in dangerous_patterns:
            if pattern.lower() in llm_response.lower():
                logger.warning(f"Guardrail triggered! Blocked pattern: {pattern}")
                return "⚠️ [Security Guardrail Triggered]: The AI's response was blocked because it contained potentially unsafe code or hallucinatory financial advice."
                
        return llm_response
