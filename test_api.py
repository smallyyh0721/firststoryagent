"""
Test the Story Agent API
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    """Test health check endpoint"""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_generate_story():
    """Test story generation endpoint"""
    print("Testing story generation...")
    
    payload = {
        "prompt": "一只勇敢的小猫在森林里寻找回家的路",
        "genre": "Fantasy",
        "length": "short"
    }
    
    print(f"Request: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/stories/generate",
            json=payload,
            timeout=120  # 2 minutes timeout for LLM generation
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Story generated successfully!")
            print(f"Title: {result['story']['title']}")
            print(f"Genre: {result['story']['genre']}")
            print(f"Word count: {result['story']['word_count']}")
            print(f"Content preview: {result['story']['content'][:200]}...")
            print(f"Notion URL: {result['story']['url']}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")
    
    print()

def test_list_stories():
    """Test list stories endpoint"""
    print("Testing list stories...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/stories")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Total stories: {result['total']}")
            for story in result['stories']:
                print(f"  - {story['title']} ({story['genre']}) - {story['status']}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")
    
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("Story Agent API Test")
    print("=" * 60)
    print()
    
    test_health()
    test_generate_story()
    test_list_stories()
    
    print("=" * 60)
    print("Test complete!")
    print("=" * 60)