"""
Inspect Notion database structure
"""
import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

# Get environment variables
token = os.getenv("NOTION_TOKEN")
database_id = os.getenv("NOTION_DATABASE_ID")

if not token or not database_id:
    print("NOTION_TOKEN and NOTION_DATABASE_ID must be set in .env")
    exit(1)

# Create client
client = Client(auth=token)

# Get database info
print("=" * 60)
print("Notion Database Structure")
print("=" * 60)
print(f"Database ID: {database_id}")
print()

try:
    database = client.databases.retrieve(database_id)
    
    # Print database title
    title = database["title"][0]["plain_text"]
    print(f"Title: {title}")
    print()
    
    # Print properties
    print("Properties:")
    print("-" * 60)
    for prop_name, prop_data in database["properties"].items():
        prop_type = prop_data["type"]
        print(f"  {prop_name}: {prop_type}")
        
        # Print additional details based on type
        if prop_type == "select":
            options = prop_data.get("select", {}).get("options", [])
            if options:
                print(f"    Options: {[opt['name'] for opt in options]}")
        elif prop_type == "multi_select":
            options = prop_data.get("multi_select", {}).get("options", [])
            if options:
                print(f"    Options: {[opt['name'] for opt in options]}")
    
    print()
    
    # List existing items
    print("=" * 60)
    print("Existing Items")
    print("=" * 60)
    
    result = client.databases.query(database_id)
    items = result.get("results", [])
    
    if items:
        print(f"Found {len(items)} item(s)")
        print()
        for i, item in enumerate(items[:5], 1):  # Show first 5 items
            print(f"Item {i}:")
            for prop_name, prop_data in item["properties"].items():
                prop_type = prop_data["type"]
                
                # Extract value based on type
                if prop_type == "title":
                    value = prop_data.get("title", [{}])[0].get("text", {}).get("content", "")
                elif prop_type == "select":
                    value = prop_data.get("select", {}).get("name", "")
                elif prop_type == "multi_select":
                    value = ", ".join([s["name"] for s in prop_data.get("multi_select", [])])
                elif prop_type == "date":
                    value = prop_data.get("date", {}).get("start", "")
                elif prop_type == "number":
                    value = prop_data.get("number", "")
                else:
                    value = f"[{prop_type}]"
                
                if value:
                    print(f"  {prop_name}: {value}")
            print()
    else:
        print("No items found in database")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)