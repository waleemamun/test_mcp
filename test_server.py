#!/usr/bin/env python3
"""
Test script for the MCP server to verify the search_papers and extract_info tools work correctly.
"""

import json
import subprocess
import sys
import time
from typing import Dict, Any

def test_mcp_server():
    """Test the MCP server by sending JSON-RPC requests."""
    
    print("🧪 Testing MCP Server...")
    print("=" * 50)
    
    # Test 1: Initialize the server
    print("\n1. Testing server initialization...")
    
    try:
        # Start the server process
        server_process = subprocess.Popen(
            [sys.executable, "pilot_mcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="/Users/wmamun/mlprac/mcp/hello_mcp"
        )
        
        # Send initialize request
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        server_process.stdin.write(json.dumps(initialize_request) + "\n")
        server_process.stdin.flush()
        
        # Read response
        response_line = server_process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            print(f"✅ Server initialized successfully")
            print(f"   Available tools: {response.get('result', {}).get('capabilities', {}).get('tools', 'Unknown')}")
        else:
            print("❌ No response from server initialization")
            return False
            
    except Exception as e:
        print(f"❌ Server initialization failed: {e}")
        return False
    
    # Test 2: List available tools
    print("\n2. Testing tools/list...")
    
    try:
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        server_process.stdin.write(json.dumps(list_tools_request) + "\n")
        server_process.stdin.flush()
        
        response_line = server_process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            tools = response.get('result', {}).get('tools', [])
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
        else:
            print("❌ No response from tools/list")
            
    except Exception as e:
        print(f"❌ Tools listing failed: {e}")
    
    # Test 3: Call search_papers tool
    print("\n3. Testing search_papers tool...")
    
    try:
        search_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_papers",
                "arguments": {
                    "topic": "mixture of experts",
                    "max_results": 3
                }
            }
        }
        
        server_process.stdin.write(json.dumps(search_request) + "\n")
        server_process.stdin.flush()
        
        # Give more time for the search to complete
        time.sleep(10)
        
        response_line = server_process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            if 'result' in response:
                content = response['result'].get('content', [])
                if content and len(content) > 0:
                    result = content[0].get('text', '')
                    print(f"✅ Search completed successfully")
                    print(f"   Result: {result}")
                else:
                    print("❌ Empty result from search")
            else:
                print(f"❌ Error in search: {response.get('error', 'Unknown error')}")
        else:
            print("❌ No response from search_papers")
            
    except Exception as e:
        print(f"❌ Search papers failed: {e}")
    
    # Terminate the server process
    try:
        server_process.terminate()
        server_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server_process.kill()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")
    return True

def test_direct_function_call():
    """Test the search function directly without MCP protocol."""
    
    print("\n🔧 Testing direct function calls...")
    print("=" * 50)
    
    try:
        # Import the server module
        sys.path.append('/Users/wmamun/mlprac/mcp/hello_mcp')
        from pilot_mcp_server import search_papers, extract_info
        
        print("\n1. Testing search_papers function directly...")
        
        # Test search_papers
        result = search_papers("mixture of experts", 2)
        print(f"✅ Direct search completed")
        print(f"   Paper IDs found: {result}")
        
        # Test extract_info if we have paper IDs
        if result and len(result) > 0 and not result[0].startswith("Error"):
            print(f"\n2. Testing extract_info with paper ID: {result[0]}")
            info = extract_info(result[0])
            print(f"✅ Paper info extracted")
            print(f"   Info length: {len(info)} characters")
            if len(info) < 500:  # Show short results
                print(f"   Info: {info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting MCP Server Tests")
    
    # First test direct function calls (easier to debug)
    success1 = test_direct_function_call()
    
    # Then test MCP protocol (more complex)
    if success1:
        print("\n" + "🔄" * 20)
        success2 = test_mcp_server()
    else:
        print("\n⚠️  Skipping MCP protocol test due to direct function test failure")
    
    print("\n🎯 Test Summary:")
    print(f"   Direct function test: {'✅ PASSED' if success1 else '❌ FAILED'}")
    if success1:
        print(f"   MCP protocol test: {'✅ PASSED' if 'success2' in locals() and success2 else '❌ FAILED'}")
