
import sys
import os
import asyncio
from datetime import datetime

# Add backend to path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

# Mock objects
class MockRequest:
    def __init__(self):
        self.message = "List all Enterprise segment orders"
        self.mode = "analyst"
        self.conversationId = "debug_conv"
        self.userId = "user_123"
        self.user_id = "user_123"
        self.attachedFiles = []
        self.compareFiles = False

async def debug():
    print("🚀 Starting debug test...")
    
    try:
        # Import chat endpoint
        print("📥 Importing chat module...")
        from api.v1.endpoints import chat
        
        # Manually set overrides if needed
        chat.MODE_ENGINES_AVAILABLE = True
        
        # Initialize router/engines if needed
        # We need to simulate the request handling logic
        
        user_id = "user_123"
        query = "List all Enterprise segment orders"
        mode = "analyst"
        
        print(f"🔄 Testing mode: {mode}")
        
        # 1. Test RAG Search
        print("🔍 Testing rag_search...")
        from core.rag import rag_search
        context, sources = rag_search(user_id, query, k=10)
        print(f"✅ RAG Search result: {len(context)} chars context, {len(sources)} sources")
        
        # 2. Test Analyst Response
        print("🧠 Testing analyst_response_sync...")
        from core.mode_engines.analyst_engine import analyst_response_sync
        response = analyst_response_sync(user_id, query, context)
        print(f"✅ Analyst Response: {len(response)} chars")
        print(f"Response preview: {response[:100]}...")
        
        # 3. Test Chart Generation
        print("📊 Testing append_chart_if_needed...")
        from api.v1.endpoints.chat import append_chart_if_needed
        final_response = append_chart_if_needed(response, query, user_id)
        print(f"✅ Final Response: {len(final_response)} chars")
        
        print("🎉 TEST PASSED SUCCESSFULLY!")
        
    except Exception as e:
        print("\n❌ ERROR CAUGHT:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug())
