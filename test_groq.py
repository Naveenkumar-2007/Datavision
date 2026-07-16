import sys
sys.path.append('backend')
from config.settings import Settings
import os
import litellm

try:
    os.environ['GROQ_API_KEY'] = Settings.GROQ_API_KEYS[0]
    print("Testing groq/llama-3.1-70b-versatile")
    response = litellm.completion(model='groq/llama-3.1-70b-versatile', messages=[{'role': 'user', 'content': 'hi'}])
    print("SUCCESS:", response)
except Exception as e:
    print("ERROR:", str(e))
    print(repr(e))
