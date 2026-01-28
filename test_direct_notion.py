"""
Direct Notion connection test
"""
import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

# Get credentials
token = os.getenv("NOTION_TOKEN")
database_id = os.getenv("NOTION_DATABASE_ID")

print(f"Token: {token[:20]}...{token[-10:]}")
print(f"Database ID: {database_id}")

# Create client
client = Client(auth=token)

# Test 1: Try to query the database
print("\n=== Testing database query ===")
try:
    response = client.databases.query(database_id=database_id)
    print(f"Success! Found {len(response['results'])} pages")
    
    for page in response["results"]:
        props = page["properties"]
        title = props.get("Title", {}).get("title", [{}])[0].get("text", {}).get("content", "No title")
        print(f"  - {title}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Try to create a test page
print("\n=== Testing page creation ===")
try:
    page = client.pages.create(
        parent={"database_id": database_id},
        properties={
            "Title": {
                "title": [
                    {
                        "text": {
                            "content": "Direct Test Story"
                        }
                    }
                ]
            },
            "Genre": {
                "multi_select": [
                    {
                        "name": "Fantasy"
                    }
                ]
            }
        },
        children=[
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "This is a test story created directly via Notion API."
                            }
                        }
                    ]
                }
            }
        ]
    )
    print(f"Success! Created page: {page['id']}")
    print(f"URL: https://www.notion.so/{page['id'].replace('-', '')}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test complete ===")