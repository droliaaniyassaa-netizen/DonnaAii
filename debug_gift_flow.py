#!/usr/bin/env python3

import requests
import json
import time

def test_gift_detection():
    """Debug the gift detection specifically"""
    
    base_url = "https://auth-ui-center.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Test a very clear birthday message
    test_message = "It's my mom's birthday today and I need gift ideas"
    
    print(f"🔍 Testing gift detection with: '{test_message}'")
    
    response = requests.post(
        f"{api_url}/chat",
        json={"message": test_message, "session_id": "debug_session"},
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        donna_response = data.get('response', '')
        
        print(f"Response length: {len(donna_response)}")
        print(f"Full response: {donna_response}")
        
        # Check for gift indicators
        indicators = {
            'amazon.com': 'amazon.com' in donna_response,
            'gift': 'gift' in donna_response.lower(),
            'suggestion': 'suggestion' in donna_response.lower(),
            'saved:': 'saved:' in donna_response.lower(),
            'birthday': 'birthday' in donna_response.lower(),
            'reminder': 'reminder' in donna_response.lower()
        }
        
        print("\nIndicators found:")
        for indicator, found in indicators.items():
            status = "✅" if found else "❌"
            print(f"  {status} {indicator}")
        
        # Count Amazon links
        amazon_count = donna_response.count('amazon.com')
        print(f"\nAmazon links found: {amazon_count}")
        
        if amazon_count > 0:
            print("✅ Gift flow with Amazon links is working!")
        else:
            print("❌ Gift flow detected but no Amazon links generated")
            
    else:
        print(f"❌ Request failed: {response.text}")

def test_multiple_messages():
    """Test multiple gift messages to see patterns"""
    
    base_url = "https://auth-ui-center.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    messages = [
        "My mom's birthday is tomorrow and I need gift suggestions",
        "It's my dad's birthday next week, what should I get him?",
        "My wife's birthday is coming up, I need Amazon gift ideas",
        "Kyle's birthday is Friday, need gift recommendations"
    ]
    
    for i, message in enumerate(messages):
        print(f"\n🔍 Test {i+1}: '{message}'")
        
        response = requests.post(
            f"{api_url}/chat",
            json={"message": message, "session_id": f"debug_session_{i}"},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            donna_response = data.get('response', '')
            
            amazon_count = donna_response.count('amazon.com')
            has_gift_indicators = any(word in donna_response.lower() 
                                    for word in ['gift', 'suggestion', 'amazon'])
            
            print(f"  Amazon links: {amazon_count}")
            print(f"  Gift indicators: {'✅' if has_gift_indicators else '❌'}")
            print(f"  Response preview: {donna_response[:150]}...")
        else:
            print(f"  ❌ Failed: {response.status_code}")
        
        time.sleep(2)

if __name__ == "__main__":
    print("🎁 Debugging Gift Flow Detection")
    print("=" * 50)
    
    test_gift_detection()
    
    print("\n" + "=" * 50)
    print("🔍 Testing Multiple Messages")
    print("=" * 50)
    
    test_multiple_messages()