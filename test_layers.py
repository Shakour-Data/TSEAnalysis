import sys
import os

# Add current directory to path to import app
sys.path.append(os.getcwd())

import json
from app import TSETMCClient, API_KEY

def check_connection():
    print("--- Diagnostic Connection Check ---")
    client = TSETMCClient(api_key=API_KEY)
    
    print(f"Using API Key: {API_KEY[:5]}...")
    print(f"Active Primary Client: {client.client_name}")
    
    # Test a simple endpoint
    print("\nTesting 'AllSymbols.php' (type 1)...")
    result = client.get_all_symbols("1")
    
    if isinstance(result, list):
        print(f"SUCCESS! Received {len(result)} symbols.")
        print(f"First symbol sample: {result[0].get('l18', 'N/A')} - {result[0].get('l30', 'N/A')}")
    elif isinstance(result, dict) and "error" in result:
        print(f"FAILED: {result['error']}")
    else:
        print(f"FAILED: Unknown response format: {type(result)}")
        print(result)

if __name__ == "__main__":
    check_connection()
