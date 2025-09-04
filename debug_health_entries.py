#!/usr/bin/env python3
"""
Debug script to check health entries storage
"""

import requests
import json

def check_health_entries():
    base_url = "https://quickload-5.preview.emergentagent.com/api"
    
    print("🔍 Checking health entries storage...")
    
    # Get all health entries
    response = requests.get(f"{base_url}/health/entries")
    
    if response.status_code == 200:
        entries = response.json()
        print(f"📊 Found {len(entries)} health entries:")
        
        for entry in entries[-10:]:  # Show last 10 entries
            print(f"  - {entry.get('type', 'unknown')}: {entry.get('description', 'no desc')} "
                  f"({entry.get('datetime_utc', 'no date')[:19]})")
    else:
        print(f"❌ Failed to get health entries: {response.status_code}")
        print(f"Response: {response.text}")

    # Test adding a health entry via chat
    print("\n🔍 Testing health entry creation via chat...")
    
    chat_response = requests.post(f"{base_url}/chat", json={
        "message": "I drank a glass of water for testing",
        "session_id": "debug_session"
    })
    
    if chat_response.status_code == 200:
        print("✅ Chat message sent successfully")
        print(f"Donna response: {chat_response.json().get('response', '')}")
        
        # Check entries again
        print("\n🔍 Checking entries after chat message...")
        response = requests.get(f"{base_url}/health/entries")
        
        if response.status_code == 200:
            entries = response.json()
            print(f"📊 Now found {len(entries)} health entries:")
            
            for entry in entries[-5:]:  # Show last 5 entries
                print(f"  - {entry.get('type', 'unknown')}: {entry.get('description', 'no desc')} "
                      f"({entry.get('datetime_utc', 'no date')[:19]})")
        else:
            print(f"❌ Failed to get health entries after chat: {response.status_code}")
    else:
        print(f"❌ Chat message failed: {chat_response.status_code}")

if __name__ == "__main__":
    check_health_entries()