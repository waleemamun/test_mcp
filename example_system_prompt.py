#!/usr/bin/env python3
"""
Example usage of the enhanced MCP ChatBot with system prompt for tool usage control.
"""

import asyncio
from pilot_mcp_client import MCP_ChatBot

async def example_usage():
    """Demonstrate the enhanced chatbot with system prompt."""
    
    print("🤖 MCP ChatBot with System Prompt Example")
    print("=" * 50)
    
    # Example 1: Default system prompt
    print("\n📋 Using Default System Prompt:")
    chatbot = MCP_ChatBot()
    system_prompt = chatbot.get_system_prompt()
    print("System prompt configured ✅")
    print(f"Prompt length: {len(system_prompt)} characters")
    
    # Example 2: Custom system prompt
    print("\n📋 Using Custom System Prompt:")
    custom_prompt = """You are a research-focused AI assistant.
    
RULES:
- Only use tools when searching for academic papers or research data
- Always explain your reasoning before using any tool
- Provide direct answers for general questions
- Be concise and academic in your responses"""
    
    custom_chatbot = MCP_ChatBot(custom_system_prompt=custom_prompt)
    print("Custom system prompt configured ✅")
    print(f"Custom prompt: {custom_chatbot.get_system_prompt()}")
    
    print("\n🎯 The system prompt will now:")
    print("  • Guide the LLM to use tools only when necessary")
    print("  • Encourage direct answers for general questions")
    print("  • Ensure efficient tool usage")
    print("  • Provide clear explanations when tools are used")
    
    print("\n✅ Ready to run with: python pilot_mcp_client.py")

if __name__ == "__main__":
    asyncio.run(example_usage())
