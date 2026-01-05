
import sys
import os
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core import llm
from config.settings import Settings

def test_fallback():
    print("🧪 Testing Multi-Key Fallback...")
    
    # 1. Setup Mock Keys
    Settings.GROQ_API_KEYS = ["INVALID_KEY", "VALID_KEY"]
    
    # 2. Mock litellm.completion
    with patch('core.llm.litellm.completion') as mock_completion:
        # Define side effects:
        # Call 1: Error (Rate Limit)
        # Call 2: Success
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Fallback Success!"))]
        
        def side_effect(*args, **kwargs):
            api_key = kwargs.get('api_key')
            if api_key == "INVALID_KEY":
                print("   ➡️ Mocking failure for INVALID_KEY")
                raise Exception("Rate limit reached (429)")
            elif api_key == "VALID_KEY":
                print("   ➡️ Mocking success for VALID_KEY")
                return mock_response
            else:
                return mock_response

        mock_completion.side_effect = side_effect
        
        # 3. Run Chat
        response = llm.chat("Test Query")
        
        # 4. Verify
        print(f"   📝 Response: {response}")
        
        if response == "Fallback Success!":
            print("✅ TEST PASSED: Fallback worked correctly.")
            return True
        else:
            print("❌ TEST FAILED: Unexpected response.")
            return False

if __name__ == "__main__":
    test_fallback()
