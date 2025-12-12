"""
Groq Multi-API-Key Load Balancer with Auto-Fallback
Production-grade load balancer for Groq API with:
- 3-key rotation (round-robin)
- Automatic fallback on errors
- Retry logic with exponential backoff
- Temporary blacklisting for failed keys
- Usage statistics tracking
"""

import os
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from groq import Groq, AsyncGroq
from groq.types.chat import ChatCompletion

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

API_KEYS = [
    os.getenv("GROQ_KEY_1"),
    os.getenv("GROQ_KEY_2"),
    os.getenv("GROQ_KEY_3"),
]

# Filter out None values if environment variables are not set
API_KEYS = [key for key in API_KEYS if key]

if not API_KEYS:
    logger.warning("No Groq API keys configured. Load balancer will not work.")

# Default model
DEFAULT_MODEL = "openai/gpt-oss-20b"

# Configuration
MAX_RETRIES_PER_KEY = 3
RETRY_DELAY_MS = 200  # Base delay between retries
BLACKLIST_DURATION_SECONDS = 60
RECOVERABLE_ERRORS = {
    "ECONNRESET",
    "ETIMEDOUT",
    "429",  # Rate limit
    "500", "502", "503", "504",  # Server errors
}


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

class KeyState:
    """Track state for each API key"""
    def __init__(self, key: str):
        self.key = key
        self.usage_count = 0
        self.fail_count = 0
        self.consecutive_fails = 0
        self.last_success: Optional[datetime] = None
        self.last_failure: Optional[datetime] = None
        self.blacklisted_until: Optional[datetime] = None
    
    def is_blacklisted(self) -> bool:
        """Check if key is currently blacklisted"""
        if self.blacklisted_until is None:
            return False
        if datetime.now() > self.blacklisted_until:
            self.blacklisted_until = None
            self.consecutive_fails = 0
            return False
        return True
    
    def blacklist(self):
        """Blacklist this key temporarily"""
        self.blacklisted_until = datetime.now() + timedelta(seconds=BLACKLIST_DURATION_SECONDS)
        logger.warning(f"Key {self.key[:8]}... blacklisted until {self.blacklisted_until}")
    
    def record_success(self):
        """Record successful request"""
        self.usage_count += 1
        self.consecutive_fails = 0
        self.last_success = datetime.now()
    
    def record_failure(self):
        """Record failed request"""
        self.fail_count += 1
        self.consecutive_fails += 1
        self.last_failure = datetime.now()
        
        # Blacklist after 3 consecutive failures
        if self.consecutive_fails >= MAX_RETRIES_PER_KEY:
            self.blacklist()


# Initialize key states
key_states: Dict[str, KeyState] = {
    key: KeyState(key) for key in API_KEYS
}

# Current key index for round-robin
current_key_index = 0


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_current_key() -> Optional[str]:
    """Get current API key, skipping blacklisted ones"""
    global current_key_index
    
    if not API_KEYS:
        return None
    
    attempts = 0
    max_attempts = len(API_KEYS)
    
    while attempts < max_attempts:
        key = API_KEYS[current_key_index]
        state = key_states[key]
        
        if not state.is_blacklisted():
            return key
        
        # Try next key
        rotate_key()
        attempts += 1
    
    # All keys blacklisted
    logger.error("All Groq API keys are blacklisted!")
    return None


def rotate_key():
    """Rotate to next key in round-robin fashion"""
    global current_key_index
    current_key_index = (current_key_index + 1) % len(API_KEYS)


async def sleep_with_backoff(attempt: int):
    """Sleep with exponential backoff"""
    delay_ms = RETRY_DELAY_MS * (2 ** attempt)
    await asyncio.sleep(delay_ms / 1000)


def is_recoverable_error(error: Exception) -> bool:
    """Check if error is recoverable (should retry)"""
    error_str = str(error).upper()
    
    for recoverable in RECOVERABLE_ERRORS:
        if recoverable in error_str:
            return True
    
    return False


# ============================================================================
# MAIN LOAD BALANCER FUNCTION
# ============================================================================

async def groq_request(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    **kwargs
) -> ChatCompletion:
    """
    Make a Groq API request with automatic load balancing and fallback.
    
    Args:
        messages: List of chat messages
        model: Model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        **kwargs: Additional arguments to pass to Groq API
    
    Returns:
        ChatCompletion response
    
    Raises:
        Exception: If all keys fail
    """
    if not API_KEYS:
        raise Exception("No Groq API keys configured")
    
    max_attempts = len(API_KEYS) * MAX_RETRIES_PER_KEY
    attempt = 0
    last_error = None
    
    while attempt < max_attempts:
        # Get current key
        current_key = get_current_key()
        if current_key is None:
            # All keys blacklisted, wait and retry
            logger.warning("All keys blacklisted, waiting before retry...")
            await asyncio.sleep(5)
            continue
        
        state = key_states[current_key]
        
        try:
            # Create client with current key
            client = AsyncGroq(api_key=current_key)
            
            # Make request
            logger.info(f"Groq request using key {current_key[:8]}... (attempt {attempt + 1}/{max_attempts})")
            
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Success!
            state.record_success()
            logger.info(f"✓ Groq request succeeded with key {current_key[:8]}...")
            
            return response
        
        except Exception as e:
            last_error = e
            state.record_failure()
            
            logger.error(f"✗ Groq request failed with key {current_key[:8]}...: {str(e)}")
            
            # Check if error is recoverable
            if is_recoverable_error(e):
                # Rotate to next key
                rotate_key()
                
                # Sleep with backoff
                await sleep_with_backoff(attempt)
                
                attempt += 1
            else:
                # Non-recoverable error, raise immediately
                raise e
    
    # All attempts failed
    raise Exception(f"All Groq API keys failed after {max_attempts} attempts. Last error: {str(last_error)}")


# ============================================================================
# STATISTICS AND DEBUGGING
# ============================================================================

def get_key_stats() -> Dict[str, Any]:
    """Get usage statistics for all keys"""
    stats = {}
    
    for key, state in key_states.items():
        key_preview = f"{key[:8]}..." if key else "None"
        stats[key_preview] = {
            "usage_count": state.usage_count,
            "fail_count": state.fail_count,
            "consecutive_fails": state.consecutive_fails,
            "last_success": state.last_success.isoformat() if state.last_success else None,
            "last_failure": state.last_failure.isoformat() if state.last_failure else None,
            "is_blacklisted": state.is_blacklisted(),
            "blacklisted_until": state.blacklisted_until.isoformat() if state.blacklisted_until else None,
        }
    
    stats["current_key_index"] = current_key_index
    stats["total_keys"] = len(API_KEYS)
    
    return stats


def reset_stats():
    """Reset all statistics (useful for testing)"""
    global key_states, current_key_index
    
    key_states = {
        key: KeyState(key) for key in API_KEYS
    }
    current_key_index = 0
    
    logger.info("Groq load balancer stats reset")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def groq_chat(
    prompt: str,
    system_message: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    **kwargs
) -> str:
    """
    Simplified chat function for single-turn conversations.
    
    Args:
        prompt: User prompt
        system_message: Optional system message
        model: Model to use
        **kwargs: Additional arguments
    
    Returns:
        Generated text response
    """
    messages = []
    
    if system_message:
        messages.append({"role": "system", "content": system_message})
    
    messages.append({"role": "user", "content": prompt})
    
    response = await groq_request(messages=messages, model=model, **kwargs)
    
    return response.choices[0].message.content


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    async def test():
        """Test the load balancer"""
        
        # Example 1: Simple chat
        response = await groq_chat(
            prompt="What is the capital of France?",
            system_message="You are a helpful assistant."
        )
        print("Response:", response)
        
        # Example 2: Multi-turn conversation
        messages = [
            {"role": "system", "content": "You are a business analyst."},
            {"role": "user", "content": "Analyze this revenue data: Q1: $100k, Q2: $150k, Q3: $180k"},
        ]
        
        response = await groq_request(messages=messages)
        print("Analysis:", response.choices[0].message.content)
        
        # Example 3: Check statistics
        stats = get_key_stats()
        print("\nKey Statistics:")
        import json
        print(json.dumps(stats, indent=2))
    
    # Run test
    asyncio.run(test())
