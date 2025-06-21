#!/usr/bin/env python3
"""
Simple test of the extract_info function
"""

if __name__ == "__main__":
    import sys
    import os
    
    # Add current directory to path
    sys.path.insert(0, os.getcwd())
    
    try:
        from pilot_mcp_server import extract_info
        
        print("Testing extract_info function...")
        result = extract_info('2024.01234')
        print(f"Result: {result}")
        print(f"Length: {len(result)}")
        
        # Also test with non-existent paper
        result2 = extract_info('9999.99999')
        print(f"Non-existent paper result: {result2}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
