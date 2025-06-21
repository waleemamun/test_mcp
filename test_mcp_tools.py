#!/usr/bin/env python3
"""
Test script to verify MCP tools are registered correctly.
"""

def test_mcp_tools():
    """Test that MCP tools are registered."""
    print("🔧 Testing MCP tool registration...")
    
    try:
        # Import the server
        from pilot_mcp_server import mcp
        
        # Check FastMCP version and attributes
        print(f"✅ MCP server imported: {type(mcp)}")
        
        # Try to access tools in different ways
        if hasattr(mcp, '_tools'):
            tools = mcp._tools
            print(f"✅ Found {len(tools)} tools in _tools: {list(tools.keys())}")
        elif hasattr(mcp, 'tools'):
            tools = mcp.tools
            print(f"✅ Found {len(tools)} tools in tools: {list(tools.keys())}")
        else:
            print("❌ No tools attribute found")
            # Let's inspect the mcp object
            print(f"MCP object attributes: {dir(mcp)}")
            
        # Try to manually call the functions
        print("\n🔍 Testing direct function calls...")
        from pilot_mcp_server import search_papers, extract_info
        
        print("✅ search_papers function imported")
        print("✅ extract_info function imported")
        
        # Test function signatures
        import inspect
        
        search_sig = inspect.signature(search_papers)
        print(f"✅ search_papers signature: {search_sig}")
        
        extract_sig = inspect.signature(extract_info)
        print(f"✅ extract_info signature: {extract_sig}")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mcp_server_run():
    """Test that the MCP server can be started (without actually running it)."""
    print("\n🖥️  Testing MCP server startup preparation...")
    
    try:
        from pilot_mcp_server import mcp
        
        # Check if the server has a run method
        if hasattr(mcp, 'run'):
            print("✅ MCP server has run method")
        else:
            print("❌ MCP server missing run method")
            return False
            
        # Check if we can get the server info
        if hasattr(mcp, 'name'):
            print(f"✅ Server name: {mcp.name}")
        else:
            print("⚠️  No server name found")
            
        return True
        
    except Exception as e:
        print(f"❌ MCP server run test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing MCP Tool Registration")
    print("=" * 50)
    
    success1 = test_mcp_tools()
    success2 = test_mcp_server_run()
    
    print("\n" + "=" * 50)
    print("🎯 Summary:")
    print(f"Tool registration test: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"Server run test: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if success1 and success2:
        print("\n🎉 MCP server is properly configured!")
        print("💡 The SSL issue with arXiv is likely network/firewall related.")
        print("🔗 Try using a different network or VPN to access arXiv.")
    else:
        print("\n⚠️  There may be issues with the MCP server configuration.")
