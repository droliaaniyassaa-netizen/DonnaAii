#!/usr/bin/env python3

import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

async def test_gift_detection_llm():
    """Test the LLM gift detection directly"""
    
    # Load environment variables
    ROOT_DIR = Path(__file__).parent / 'backend'
    load_dotenv(ROOT_DIR / '.env')
    
    # Get API key from environment
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    if not openai_api_key:
        print("❌ No OpenAI API key found")
        return
    
    system_message = """You are a gift occasion detector. Analyze messages for birthday or anniversary mentions.

Extract these details:
- occasion: "birthday" or "anniversary" 
- relationship: mom/mother/momma, dad/father/daddy/papa, wife, girlfriend, boss, colleague, friend, child/kid, uncle, aunt, or any proper name
- date: parse relative dates like "next Friday", "tomorrow", "12 Oct" to YYYY-MM-DD format

Return JSON only:
{
  "detected": true/false,
  "occasion": "birthday|anniversary|null", 
  "relationship": "relationship_or_name",
  "date": "YYYY-MM-DD",
  "confidence": 0.0-1.0,
  "event_title": "Mom's Birthday" 
}

Examples:
"It's my mom's birthday" → {"detected": true, "occasion": "birthday", "relationship": "mom", "date": "2025-09-06", "confidence": 0.9, "event_title": "Mom's Birthday"}
"Our anniversary next Friday" → {"detected": true, "occasion": "anniversary", "relationship": "partner", "date": "2025-09-13", "confidence": 0.8, "event_title": "Anniversary"}
"Kyle's birthday tomorrow" → {"detected": true, "occasion": "birthday", "relationship": "Kyle", "date": "2025-09-07", "confidence": 0.9, "event_title": "Kyle's Birthday"}"""
    
    chat = LlmChat(
        api_key=openai_api_key,
        session_id="gift_detection_test",
        system_message=system_message
    ).with_model("openai", "gpt-4o-mini")
    
    test_messages = [
        "It's my mom's birthday today and I need gift ideas",
        "My dad's birthday is tomorrow",
        "Our anniversary is next Friday",
        "Kyle's birthday next week"
    ]
    
    for message in test_messages:
        print(f"\n🔍 Testing: '{message}'")
        
        try:
            user_msg = UserMessage(text=f"Analyze this message: {message}")
            response = await chat.send_message(user_msg)
            
            print(f"Raw LLM response: {response}")
            
            # Try to parse JSON
            try:
                result_dict = json.loads(response.strip())
                print(f"Parsed JSON: {json.dumps(result_dict, indent=2)}")
                
                # Check confidence
                confidence = result_dict.get('confidence', 0.0)
                detected = result_dict.get('detected', False)
                
                print(f"Detected: {detected}, Confidence: {confidence}")
                
                if detected and confidence > 0.7:
                    print("✅ Would trigger gift flow (confidence > 0.7)")
                else:
                    print("❌ Would NOT trigger gift flow")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error: {e}")
                
        except Exception as e:
            print(f"❌ LLM error: {e}")

if __name__ == "__main__":
    asyncio.run(test_gift_detection_llm())