#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime, timezone

class GiftFlowTester:
    def __init__(self, base_url="https://donna-companion.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = "gift_test_session"

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    return success, response_data
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:300]}...")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_birthday_anniversary_gift_flow(self):
        """Test the Birthday & Anniversary Gift Flow comprehensively"""
        print("\n" + "="*60)
        print("🎁 TESTING BIRTHDAY & ANNIVERSARY GIFT FLOW")
        print("="*60)
        
        session_id = self.session_id
        
        print("\n🎂 PHASE 1: BIRTHDAY DETECTION")
        print("="*50)
        
        # Test realistic birthday messages
        birthday_tests = [
            "It's my mom's birthday today",
            "My dad's birthday is tomorrow", 
            "Kyle's birthday next Friday",
            "My wife's birthday is coming up next week",
            "My boss has a birthday on Monday"
        ]
        
        birthday_success = 0
        
        for message in birthday_tests:
            success, response = self.run_test(
                f"Birthday: '{message}'",
                "POST",
                "chat",
                200,
                data={"message": message, "session_id": session_id}
            )
            
            if success:
                donna_response = response.get('response', '')
                # Check for gift flow indicators
                if any(indicator in donna_response.lower() for indicator in ['gift', 'amazon', 'saved:', 'birthday']):
                    birthday_success += 1
                    print(f"✅ Gift flow triggered: {donna_response[:120]}...")
                    
                    # Check for Amazon links
                    if 'amazon.com' in donna_response:
                        print(f"✅ Amazon suggestions provided")
                    else:
                        print(f"⚠️  No Amazon links found")
                else:
                    print(f"❌ Gift flow not triggered: {donna_response[:120]}...")
            
            time.sleep(2)  # Pause between requests
        
        print(f"\n📊 Birthday Detection: {birthday_success}/{len(birthday_tests)} successful")
        
        print("\n💍 PHASE 2: ANNIVERSARY DETECTION")
        print("="*50)
        
        anniversary_tests = [
            "Our anniversary is next Friday",
            "It's our wedding anniversary today",
            "My anniversary with Sarah is tomorrow"
        ]
        
        anniversary_success = 0
        
        for message in anniversary_tests:
            success, response = self.run_test(
                f"Anniversary: '{message}'",
                "POST",
                "chat",
                200,
                data={"message": message, "session_id": session_id}
            )
            
            if success:
                donna_response = response.get('response', '')
                if any(indicator in donna_response.lower() for indicator in ['gift', 'amazon', 'saved:', 'anniversary']):
                    anniversary_success += 1
                    print(f"✅ Anniversary gift flow triggered: {donna_response[:120]}...")
                    
                    if 'amazon.com' in donna_response:
                        print(f"✅ Amazon suggestions provided")
                else:
                    print(f"❌ Anniversary gift flow not triggered: {donna_response[:120]}...")
            
            time.sleep(2)
        
        print(f"\n📊 Anniversary Detection: {anniversary_success}/{len(anniversary_tests)} successful")
        
        print("\n📅 PHASE 3: CALENDAR INTEGRATION")
        print("="*50)
        
        # Get initial calendar events
        success, initial_events = self.run_test(
            "Get Initial Calendar Events",
            "GET",
            "calendar/events",
            200
        )
        
        initial_count = len(initial_events) if success else 0
        
        # Test calendar event creation
        success, response = self.run_test(
            "Calendar Creation Test: 'My mom's birthday is tomorrow'",
            "POST",
            "chat",
            200,
            data={"message": "My mom's birthday is tomorrow", "session_id": session_id}
        )
        
        if success:
            time.sleep(3)  # Wait for processing
            
            success, updated_events = self.run_test(
                "Check Updated Calendar Events",
                "GET",
                "calendar/events",
                200
            )
            
            if success:
                new_count = len(updated_events)
                if new_count > initial_count:
                    print(f"✅ Calendar event created: {initial_count} → {new_count} events")
                    
                    # Look for birthday events
                    gift_events = [e for e in updated_events if any(word in e.get('title', '').lower() 
                                  for word in ['birthday', 'anniversary'])]
                    print(f"✅ Found {len(gift_events)} gift-related events")
                else:
                    print(f"❌ No new events created: {initial_count} → {new_count}")
        
        print("\n🛒 PHASE 4: AMAZON LINK GENERATION")
        print("="*50)
        
        relationship_tests = [
            ("My mom's birthday next week", "mom"),
            ("My dad's birthday tomorrow", "dad"),
            ("My wife's birthday is coming", "wife"),
            ("My friend Jake's birthday next week", "friend")
        ]
        
        amazon_success = 0
        
        for message, relationship in relationship_tests:
            success, response = self.run_test(
                f"Amazon Links for {relationship}",
                "POST",
                "chat",
                200,
                data={"message": message, "session_id": session_id}
            )
            
            if success:
                donna_response = response.get('response', '')
                
                if 'amazon.com' in donna_response:
                    amazon_success += 1
                    link_count = donna_response.count('amazon.com')
                    print(f"✅ {link_count} Amazon links generated for {relationship}")
                else:
                    print(f"❌ No Amazon links for {relationship}")
            
            time.sleep(2)
        
        print(f"\n📊 Amazon Link Generation: {amazon_success}/{len(relationship_tests)} successful")
        
        print("\n🔄 PHASE 5: INTEGRATION WITH EXISTING FEATURES")
        print("="*50)
        
        # Test health logging still works
        success, response = self.run_test(
            "Health Integration: 'I had a glass of water'",
            "POST",
            "chat",
            200,
            data={"message": "I had a glass of water", "session_id": session_id}
        )
        
        health_works = False
        if success:
            donna_response = response.get('response', '')
            if any(word in donna_response.lower() for word in ['hydration', 'water', 'ml']):
                health_works = True
                print("✅ Health logging still functional")
            else:
                print("❌ Health logging may be broken")
        
        # Test regular event creation still works
        success, response = self.run_test(
            "Regular Event: 'I have a meeting tomorrow at 2 PM'",
            "POST",
            "chat",
            200,
            data={"message": "I have a meeting tomorrow at 2 PM", "session_id": session_id}
        )
        
        event_works = False
        if success:
            donna_response = response.get('response', '')
            if any(word in donna_response.lower() for word in ['meeting', 'event', 'reminder']):
                event_works = True
                print("✅ Regular event creation still functional")
            else:
                print("❌ Regular event creation may be broken")
        
        print("\n🧪 PHASE 6: EDGE CASES")
        print("="*50)
        
        # Test messages that should NOT trigger gift flow
        edge_cases = [
            "I need to buy something",
            "Birthday party planning in general",
            "What should I get for a birthday?",
            "Anniversary sale at the store"
        ]
        
        false_positives = 0
        
        for message in edge_cases:
            success, response = self.run_test(
                f"Edge Case: '{message}'",
                "POST",
                "chat",
                200,
                data={"message": message, "session_id": session_id}
            )
            
            if success:
                donna_response = response.get('response', '')
                if 'amazon.com' in donna_response or 'saved:' in donna_response.lower():
                    false_positives += 1
                    print(f"⚠️  False positive: {donna_response[:80]}...")
                else:
                    print(f"✅ Correctly handled as regular chat")
            
            time.sleep(1)
        
        edge_case_success = len(edge_cases) - false_positives
        print(f"\n📊 Edge Case Handling: {edge_case_success}/{len(edge_cases)} correct")
        
        print("\n📊 FINAL GIFT FLOW RESULTS")
        print("="*50)
        
        total_gift_tests = len(birthday_tests) + len(anniversary_tests) + len(relationship_tests)
        successful_gift_tests = birthday_success + anniversary_success + amazon_success
        
        print(f"Gift Detection & Processing: {successful_gift_tests}/{total_gift_tests} ({successful_gift_tests/total_gift_tests*100:.1f}%)")
        print(f"Calendar Integration: {'✅ Working' if new_count > initial_count else '❌ Not Working'}")
        print(f"Health Integration: {'✅ Working' if health_works else '❌ Not Working'}")
        print(f"Event Integration: {'✅ Working' if event_works else '❌ Not Working'}")
        print(f"Edge Case Handling: {edge_case_success}/{len(edge_cases)} ({edge_case_success/len(edge_cases)*100:.1f}%)")
        
        # Overall assessment
        overall_score = (
            (successful_gift_tests / total_gift_tests) * 0.4 +  # 40% weight
            (1 if new_count > initial_count else 0) * 0.2 +     # 20% weight
            (1 if health_works else 0) * 0.2 +                  # 20% weight
            (edge_case_success / len(edge_cases)) * 0.2          # 20% weight
        ) * 100
        
        print(f"\n🎯 OVERALL GIFT FLOW SCORE: {overall_score:.1f}%")
        
        if overall_score >= 80:
            print("🎉 Gift Flow feature is working excellently!")
            return True
        elif overall_score >= 60:
            print("⚠️  Gift Flow feature is working but has some issues")
            return True
        else:
            print("❌ Gift Flow feature needs significant fixes")
            return False

def main():
    print("🎁 Starting Birthday & Anniversary Gift Flow Tests")
    print("=" * 60)
    
    tester = GiftFlowTester()
    
    try:
        success = tester.test_birthday_anniversary_gift_flow()
        
        print(f"\n📊 TEST SUMMARY")
        print(f"Tests Run: {tester.tests_run}")
        print(f"Tests Passed: {tester.tests_passed}")
        print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())