#!/usr/bin/env python3
"""
Detailed debug script to check health entries storage with session_id
"""

import requests
import json
from datetime import datetime, timezone

def debug_health_entries():
    base_url = "https://fitness-donna.preview.emergentagent.com/api"
    session_id = "debug_session_detailed"
    
    print("🔍 Debugging health entries with session_id...")
    
    # Reset stats first
    reset_response = requests.post(f"{base_url}/health/stats/reset/{session_id}")
    print(f"Reset response: {reset_response.status_code}")
    
    # Send a health message
    print("\n🔍 Sending health message...")
    chat_response = requests.post(f"{base_url}/chat", json={
        "message": "I drank a glass of water for debugging",
        "session_id": session_id
    })
    
    if chat_response.status_code == 200:
        print("✅ Chat message sent successfully")
        print(f"Donna response: {chat_response.json().get('response', '')}")
        
        # Check all health entries
        print("\n🔍 Checking all health entries...")
        entries_response = requests.get(f"{base_url}/health/entries")
        
        if entries_response.status_code == 200:
            entries = entries_response.json()
            print(f"📊 Total entries: {len(entries)}")
            
            # Look for our session entries
            session_entries = [e for e in entries if e.get('session_id') == session_id]
            print(f"📊 Entries for session '{session_id}': {len(session_entries)}")
            
            for entry in session_entries:
                print(f"  - Type: {entry.get('type')}")
                print(f"    Description: {entry.get('description')}")
                print(f"    Session ID: {entry.get('session_id')}")
                print(f"    DateTime: {entry.get('datetime_utc')}")
                print(f"    Value: {entry.get('value')}")
                print()
            
            # Check recent entries (last 5)
            print("📊 Recent entries (all sessions):")
            for entry in entries[-5:]:
                print(f"  - {entry.get('type', 'unknown')} ({entry.get('session_id', 'no_session')}): "
                      f"{entry.get('description', 'no desc')} - {entry.get('datetime_utc', 'no date')[:19]}")
        
        # Try the undo API
        print(f"\n🔍 Testing undo API for session '{session_id}'...")
        undo_response = requests.delete(f"{base_url}/health/stats/undo/{session_id}/hydration")
        print(f"Undo response: {undo_response.status_code}")
        print(f"Undo message: {undo_response.text}")
        
        # Check stats
        print(f"\n🔍 Checking stats for session '{session_id}'...")
        stats_response = requests.get(f"{base_url}/health/stats/{session_id}")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"Stats: Hydration={stats.get('hydration', 0)}ml")
        
    else:
        print(f"❌ Chat message failed: {chat_response.status_code}")
        print(f"Response: {chat_response.text}")

if __name__ == "__main__":
    debug_health_entries()