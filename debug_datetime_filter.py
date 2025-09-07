#!/usr/bin/env python3
"""
Debug datetime filtering in MongoDB queries
"""

import requests
import json
from datetime import datetime, timezone, timedelta

def debug_datetime_filtering():
    base_url = "https://donna-ai-assist.preview.emergentagent.com/api"
    session_id = "datetime_debug"
    
    print("🔍 Debugging datetime filtering...")
    
    # Reset and add a health entry
    reset_response = requests.post(f"{base_url}/health/stats/reset/{session_id}")
    print(f"Reset: {reset_response.status_code}")
    
    # Add health entry
    chat_response = requests.post(f"{base_url}/chat", json={
        "message": "I had a glass of water",
        "session_id": session_id
    })
    print(f"Chat: {chat_response.status_code}")
    
    # Get all entries for this session
    entries_response = requests.get(f"{base_url}/health/entries")
    if entries_response.status_code == 200:
        entries = entries_response.json()
        session_entries = [e for e in entries if e.get('session_id') == session_id]
        
        print(f"\n📊 Found {len(session_entries)} entries for session '{session_id}':")
        for entry in session_entries:
            print(f"  Entry ID: {entry.get('id')}")
            print(f"  Type: {entry.get('type')}")
            print(f"  Session: {entry.get('session_id')}")
            print(f"  DateTime: {entry.get('datetime_utc')}")
            print(f"  Description: {entry.get('description')}")
            
            # Parse the datetime to see the format
            try:
                dt_str = entry.get('datetime_utc')
                if dt_str:
                    # Try different parsing methods
                    if dt_str.endswith('Z'):
                        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                    else:
                        dt = datetime.fromisoformat(dt_str)
                    
                    print(f"  Parsed DateTime: {dt}")
                    print(f"  Date only: {dt.strftime('%Y-%m-%d')}")
                    
                    # Check if it's today
                    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
                    entry_date = dt.strftime('%Y-%m-%d')
                    print(f"  Today: {today}")
                    print(f"  Entry Date: {entry_date}")
                    print(f"  Is Today: {today == entry_date}")
                    
            except Exception as e:
                print(f"  DateTime parsing error: {e}")
            
            print()
    
    # Now test the undo API with detailed error info
    print("🔍 Testing undo API...")
    undo_response = requests.delete(f"{base_url}/health/stats/undo/{session_id}/hydration")
    print(f"Undo status: {undo_response.status_code}")
    print(f"Undo response: {undo_response.text}")

if __name__ == "__main__":
    debug_datetime_filtering()