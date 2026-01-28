#!/usr/bin/env python3
"""
Quick Notion API verification script
Uses environment variables for non-interactive testing
"""

import os
from notion_client import Client, APIResponseError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_notion_connection():
    """Verify Notion API connection"""
    
    # Get credentials from environment
    token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DATABASE_ID")
    
    print("Notion API Verification")
    print("=" * 50)
    
    # Check if credentials are provided
    if not token or not database_id:
        print("Error: NOTION_TOKEN and NOTION_DATABASE_ID must be set in .env file")
        print("\nPlease create a .env file with:")
        print("NOTION_TOKEN=your_token_here")
        print("NOTION_DATABASE_ID=your_database_id_here")
        return False
    
    # Test 1: Verify Token
    print("\n1. Testing Token...")
    try:
        client = Client(auth=token)
        user = client.users.me()
        print(f"✓ Token valid! User: {user['name']}")
    except APIResponseError as e:
        print(f"✗ Token error: {e.code} - {e.message}")
        return False
    except Exception as e:
        print(f"✗ Token error: {e}")
        return False
    
    # Test 2: Verify Database access
    print("\n2. Testing Database access...")
    try:
        database = client.databases.retrieve(database_id)
        title = database['title'][0]['plain_text']
        print(f"✓ Database accessible! Title: {title}")
    except APIResponseError as e:
        print(f"✗ Database error: {e.code} - {e.message}")
        return False
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False
    
    # Test 3: Query Database
    print("\n3. Testing Database query...")
    try:
        query_result = client.databases.query(database_id=database_id)
        count = len(query_result['results'])
        print(f"✓ Query successful! Found {count} records")
        
        # Show database structure
        print("\nDatabase properties:")
        for prop_name, prop_info in database['properties'].items():
            prop_type = prop_info['type']
            print(f"  - {prop_name}: {prop_type}")
        
    except Exception as e:
        print(f"✗ Query error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✓ All tests passed! Notion API is ready to use.")
    return True

if __name__ == "__main__":
    verify_notion_connection()