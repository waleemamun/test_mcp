#!/usr/bin/env python3
"""
Test script to verify AzureChatOpenAI integration works.
"""

import asyncio
from dotenv import load_dotenv

async def test_azure_llm():
    """Test that AzureChatOpenAI initialization works."""
    print("🔧 Testing AzureChatOpenAI integration...")
    
    try:
        from pilot_mcp_client import MCP_ChatBot
        
        # Initialize the chatbot (this will test the LLM setup)
        print("📋 Creating MCP_ChatBot instance...")
        chatbot = MCP_ChatBot()
        print(f"✅ MCP_ChatBot initialized with LLM type: {type(chatbot.llm)}")
        
        # Check if the LLM has expected attributes
        if hasattr(chatbot.llm, 'deployment_name'):
            print(f"✅ LLM deployment: {chatbot.llm.deployment_name}")
        
        if hasattr(chatbot.llm, 'azure_endpoint'):
            print(f"✅ LLM endpoint: {chatbot.llm.azure_endpoint}")
        
        print("✅ Basic initialization test passed")
        return True
        
    except Exception as e:
        print(f"❌ Azure LLM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    load_dotenv()
    success = asyncio.run(test_azure_llm())
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
