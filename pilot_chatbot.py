from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from typing import List, Dict, TypedDict
from contextlib import AsyncExitStack
import json
import asyncio
import nest_asyncio
import os
import base64
import requests
import asyncio

load_dotenv()

class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict

class MCP_ChatBot:

    def __init__(self, custom_system_prompt: str = None):
        # Initialize session and client objects
        self.sessions: List[ClientSession] = [] # new
        self.exit_stack = AsyncExitStack() # new
        self.available_tools: List[ToolDefinition] = [] # new
        self.tool_to_session: Dict[str, ClientSession] = {} # new
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.llm = self.get_llm()
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
   - Retrieving current/real-time information
   - fetch data from internet 
   - accessing internal filessytem
   - writing to files
   - searrching for latest new or any news give a specific topic
   - Search or ask about weather for a specific location
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


    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a single MCP server."""
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            ) # new
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            ) # new
            await session.initialize()
            self.sessions.append(session)
            
            # List available tools for this session
            response = await session.list_tools()
            tools = response.tools
            print(f"\nConnected to {server_name} with tools:", [t.name for t in tools])
            
            for tool in tools: # new
                self.tool_to_session[tool.name] = session
                self.available_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")

    async def connect_to_servers(self): # new
        """Connect to all configured MCP servers."""
        try:
            with open("server_config.json", "r") as file:
                data = json.load(file)
            
            servers = data.get("mcpServers", {})
            
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
        except Exception as e:
            print(f"Error loading server configuration: {e}")
            raise
    
    async def process_query(self, query):

        tools_for_openai = []
        for tool in self.available_tools:
            tools_for_openai.append({
                "type": "function",
                "function": {
                    "name": tool['name'],
                    "description": tool['description'],
                    "parameters": tool['input_schema']
                }
            })

        # Create messages for the LLM
        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=query)
        ]
        # Bind tools to the model
        if tools_for_openai:
            llm_with_tools = self.llm.bind_tools(tools_for_openai)
        else:
            llm_with_tools = self.llm
        # print(f"\nmessages: {messages}")

        # Get response from LLM
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
                        session = self.tool_to_session[tool_name]
                        result = await session.call_tool(tool_name, arguments=tool_args)
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
    
    async def cleanup(self): # new
        """Cleanly close all resources using AsyncExitStack."""
        await self.exit_stack.aclose()


async def main():
    chatbot = MCP_ChatBot()
    try:
        # the mcp clients and sessions are not initialized using "with"
        # like in the previous lesson
        # so the cleanup should be manually handled
        await chatbot.connect_to_servers() # new! 
        await chatbot.chat_loop()
    finally:
        await chatbot.cleanup() #new! 


if __name__ == "__main__":
    asyncio.run(main())