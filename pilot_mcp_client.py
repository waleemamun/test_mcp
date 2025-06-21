from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from typing import List
import asyncio
import nest_asyncio
import os
import base64
import requests
import json

nest_asyncio.apply()

load_dotenv()

class MCP_ChatBot:

    def get_llm(self):
        self.client_id = os.getenv('CLIENT_ID')
        self.client_secret = os.getenv('CLIENT_SECRET')
        self.cisco_openai_app_key = os.getenv('CISCO_OPENAI_APP_KEY')
        self.cisco_brain_user_id = os.getenv('CISCO_BRAIN_USER_ID')
        auth_value = base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode('utf-8')).decode('utf-8')

        # Request OAuth2 token
        url = "https://id.cisco.com/oauth2/default/v1/token"
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_value}"
        }
        payload = "grant_type=client_credentials"
        token_response = requests.post(url, headers=headers, data=payload)

        # Extract and return access token
        self.access_token = token_response.json().get("access_token")
        llm = AzureChatOpenAI(
                deployment_name="gpt-4o-mini",
                azure_endpoint='https://chat-ai.cisco.com',
                api_key=self.access_token,
                api_version="2023-08-01-preview",
                model_kwargs=dict(
                    user=f'{{"appkey": "{self.cisco_openai_app_key}", "user": "{self.cisco_brain_user_id}"}}'
                )
        )
        return llm

    def __init__(self, custom_system_prompt: str = None):
        # Initialize session and client objects
        self.session: ClientSession = None
        self.llm = self.get_llm()
        self.available_tools: List[dict] = []
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.custom_system_prompt = custom_system_prompt

    def get_system_prompt(self) -> str:
        """Generate system prompt instructing the LLM to use tools appropriately."""
        tool_descriptions = []
        for tool in self.available_tools:
            tool_descriptions.append(f"- {tool['name']}: {tool['description']}")
        
        tools_list = "\n".join(tool_descriptions) if tool_descriptions else "No tools available."
        
        system_prompt = f"""You are a helpful AI assistant with access to specialized tools for research and information retrieval.

AVAILABLE TOOLS:
{tools_list}

TOOL USAGE GUIDELINES:
1. **ONLY use tools when absolutely necessary** - if you can answer from your knowledge, do so directly
2. **Think before using tools**: Ask yourself "Do I need external data to answer this question?"
3. **Use tools for**:
   - Searching research papers or academic publications
   - Finding specific data or information not in your knowledge base
   - Performing calculations or data analysis
   - Retrieving current/real-time information
4. **DON'T use tools for**:
   - General knowledge questions you can answer directly
   - Explanations of well-known concepts
   - Conversational responses or greetings
   - Questions about your own capabilities

RESPONSE STRATEGY:
- First, determine if you can answer the question directly
- If tools are needed, explain what you're doing and why
- Use the minimum number of tools necessary
- Provide clear, comprehensive answers based on tool results

Be efficient, helpful, and only use tools when they add real value to your response."""

        # If a custom system prompt is provided, use it
        if self.custom_system_prompt:
            system_prompt = self.custom_system_prompt

        return system_prompt

    async def process_query(self, query):
        # Convert tools to OpenAI function format
        tools_for_openai = []
        for tool in self.available_tools:
            tools_for_openai.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            })
        
        # Create messages with system prompt and user query
        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=query)
        ]
        
        # Bind tools to the model
        if tools_for_openai:
            llm_with_tools = self.llm.bind_tools(tools_for_openai)
        else:
            llm_with_tools = self.llm
        
        max_iterations = 3
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Get response from LLM
            response = llm_with_tools.invoke(messages)
            
            # Check if the response has tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # Add the assistant's response to messages
                messages.append(response)
                
                # Process each tool call
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_call_id = tool_call["id"]
                    
                    print(f"Calling tool {tool_name} with args {tool_args}")
                    
                    try:
                        # Call the MCP tool
                        result = await self.session.call_tool(tool_name, arguments=tool_args)
                        tool_result = str(result.content) if result.content else "Tool executed successfully"
                        
                        # Add tool result to messages
                        messages.append(ToolMessage(
                            content=tool_result,
                            tool_call_id=tool_call_id
                        ))
                        
                    except Exception as e:
                        print(f"Error calling tool {tool_name}: {str(e)}")
                        messages.append(ToolMessage(
                            content=f"Error: {str(e)}",
                            tool_call_id=tool_call_id
                        ))
                
                # Continue the loop to get the final response after tool usage
                continue
            else:
                # No tool calls, this is the final response
                print(response.content)
                break

    
    
    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
        
                if query.lower() == 'quit':
                    break
                    
                await self.process_query(query)
                print("\n")
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def connect_to_server_and_run(self):
        # Create server parameters for stdio connection
        server_params = StdioServerParameters(
            command="uv",  # Executable
            args=["run", "pilot_mcp_server.py"],  # Optional command line arguments
            env=None,  # Optional environment variables
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                # Initialize the connection
                await session.initialize()
    
                # List available tools
                response = await session.list_tools()
                
                tools = response.tools
                print("\nConnected to server with tools:", [tool.name for tool in tools])
                
                self.available_tools = [{
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                } for tool in response.tools]
    
                await self.chat_loop()


async def main():
    chatbot = MCP_ChatBot()
    await chatbot.connect_to_server_and_run()
  

if __name__ == "__main__":
    asyncio.run(main())