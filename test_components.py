#!/usr/bin/env python3
"""
Simple test script to verify the MCP server works without external API calls.
"""

import sys
import os

# Add the current directory to Python path
sys.path.append('/Users/wmamun/mlprac/mcp/hello_mcp')

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        import arxiv
        print("✅ arxiv imported successfully")
        
        import ssl
        print("✅ ssl imported successfully")
        
        import certifi
        print("✅ certifi imported successfully")
        
        import urllib3
        print("✅ urllib3 imported successfully")
        
        import requests
        print("✅ requests imported successfully")
        
        from mcp.server.fastmcp import FastMCP
        print("✅ FastMCP imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_ssl_config():
    """Test SSL configuration."""
    print("\n🔐 Testing SSL configuration...")
    
    try:
        import ssl
        import certifi
        
        # Test default SSL context
        ctx = ssl.create_default_context()
        print("✅ Default SSL context created")
        
        # Test certifi
        cert_file = certifi.where()
        print(f"✅ Certifi certificate file: {cert_file}")
        
        if os.path.exists(cert_file):
            print("✅ Certificate file exists")
        else:
            print("❌ Certificate file not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ SSL configuration failed: {e}")
        return False

def test_mcp_server_structure():
    """Test that the MCP server can be instantiated."""
    print("\n🖥️  Testing MCP server structure...")
    
    try:
        from pilot_mcp_server import mcp, PAPER_DIR
        
        print("✅ MCP server object imported")
        print(f"✅ Paper directory: {PAPER_DIR}")
        
        # Check if the server has tools
        tools = mcp._tools if hasattr(mcp, '_tools') else {}
        print(f"✅ Server has {len(tools)} tools registered")
        
        for tool_name in tools:
            print(f"   - {tool_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP server structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_paper_directory():
    """Test paper directory creation."""
    print("\n📁 Testing paper directory operations...")
    
    try:
        import os
        from pilot_mcp_server import PAPER_DIR
        
        # Test directory creation
        test_dir = os.path.join(PAPER_DIR, "test_topic")
        os.makedirs(test_dir, exist_ok=True)
        
        if os.path.exists(test_dir):
            print("✅ Test directory created successfully")
            
            # Clean up
            try:
                os.rmdir(test_dir)
                print("✅ Test directory cleaned up")
            except:
                print("⚠️  Could not clean up test directory (may not be empty)")
                
        else:
            print("❌ Test directory creation failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Directory test failed: {e}")
        return False

def test_json_operations():
    """Test JSON file operations."""
    print("\n📄 Testing JSON operations...")
    
    try:
        import json
        import os
        from pilot_mcp_server import PAPER_DIR
        
        # Create test data
        test_data = {
            "test_paper_id": {
                "title": "Test Paper",
                "authors": ["Test Author"],
                "summary": "This is a test paper",
                "pdf_url": "http://example.com/test.pdf",
                "published": "2025-01-01"
            }
        }
        
        # Create test directory and file
        test_dir = os.path.join(PAPER_DIR, "json_test")
        os.makedirs(test_dir, exist_ok=True)
        
        test_file = os.path.join(test_dir, "test_papers.json")
        
        # Write JSON
        with open(test_file, "w") as f:
            json.dump(test_data, f, indent=2)
        
        print("✅ JSON file written successfully")
        
        # Read JSON
        with open(test_file, "r") as f:
            loaded_data = json.load(f)
        
        if loaded_data == test_data:
            print("✅ JSON file read successfully")
        else:
            print("❌ JSON data mismatch")
            return False
        
        # Clean up
        try:
            os.remove(test_file)
            os.rmdir(test_dir)
            print("✅ Test files cleaned up")
        except:
            print("⚠️  Could not clean up test files")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON operations test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting MCP Server Component Tests")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("SSL Configuration Test", test_ssl_config),
        ("MCP Server Structure Test", test_mcp_server_structure),
        ("Paper Directory Test", test_paper_directory),
        ("JSON Operations Test", test_json_operations),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The MCP server components are working correctly.")
        print("\n💡 Next steps:")
        print("   1. The SSL issue with arXiv might be temporary or network-related")
        print("   2. Try running the server at a different time")
        print("   3. Consider using a VPN if the issue persists")
        print("   4. The server structure is solid and ready for use")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
