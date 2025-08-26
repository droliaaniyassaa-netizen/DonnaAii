import requests
import sys
import json
import time
from datetime import datetime, timezone

class DonnaAPITester:
    def __init__(self, base_url="https://daily-donna.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = "test_session"

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
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
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:300]}...")

            return success, response.json() if response.text and response.status_code < 500 else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_chat_functionality(self):
        """Test chat endpoints and LLM integration"""
        print("\n" + "="*50)
        print("TESTING CHAT FUNCTIONALITY")
        print("="*50)
        
        # Test basic chat
        success, response = self.run_test(
            "Basic Chat with Donna",
            "POST",
            "chat",
            200,
            data={"message": "Hello Donna, how are you today?", "session_id": self.session_id}
        )
        
        if not success:
            return False
            
        # Wait a moment for processing
        time.sleep(2)
        
        # Test chat history
        success, history = self.run_test(
            "Get Chat History",
            "GET",
            f"chat/history/{self.session_id}",
            200
        )
        
        if success and len(history) >= 2:
            print("✅ Chat history contains user and Donna messages")
        else:
            print("❌ Chat history incomplete or missing")
            
        return success

    def test_context_processing(self):
        """Test automatic context processing for calendar and health"""
        print("\n" + "="*50)
        print("TESTING CONTEXT PROCESSING")
        print("="*50)
        
        # Test calendar context - send message about meeting
        success, response = self.run_test(
            "Chat Message with Meeting Context",
            "POST",
            "chat",
            200,
            data={"message": "I have a meeting with the team tomorrow at 2 PM", "session_id": self.session_id}
        )
        
        if success:
            time.sleep(3)  # Wait for context processing
            
            # Check if calendar event was created
            success, events = self.run_test(
                "Check Auto-Created Calendar Events",
                "GET",
                "calendar/events",
                200
            )
            
            if success and len(events) > 0:
                print("✅ Calendar event auto-created from chat context")
            else:
                print("⚠️  No calendar events found - context processing may not be working")
        
        # Test health context - send message about meal
        success, response = self.run_test(
            "Chat Message with Health Context",
            "POST",
            "chat",
            200,
            data={"message": "I ate a healthy salad for lunch today", "session_id": self.session_id}
        )
        
        if success:
            time.sleep(3)  # Wait for context processing
            
            # Check if health entry was created
            success, entries = self.run_test(
                "Check Auto-Created Health Entries",
                "GET",
                "health/entries",
                200
            )
            
            if success and len(entries) > 0:
                print("✅ Health entry auto-created from chat context")
            else:
                print("⚠️  No health entries found - context processing may not be working")
        
        return True

    def test_calendar_crud(self):
        """Test calendar CRUD operations with timezone awareness"""
        print("\n" + "="*50)
        print("TESTING CALENDAR CRUD WITH TIMEZONE")
        print("="*50)
        
        # Test timezone-aware event creation
        utc_datetime = datetime.now(timezone.utc).isoformat()
        event_data = {
            "title": "Test Meeting",
            "description": "API test meeting with timezone",
            "datetime_utc": utc_datetime,
            "reminder": True
        }
        
        success, event = self.run_test(
            "Create Calendar Event (UTC)",
            "POST",
            "calendar/events",
            200,
            data=event_data
        )
        
        if not success:
            return False
            
        event_id = event.get('id')
        
        # Verify UTC datetime storage
        if event.get('datetime_utc'):
            print("✅ Event stored with UTC datetime")
            # Verify it's a valid ISO datetime
            try:
                stored_dt = datetime.fromisoformat(event['datetime_utc'].replace('Z', '+00:00'))
                print(f"   Stored datetime: {stored_dt}")
            except ValueError:
                print("❌ Invalid datetime format in response")
        else:
            print("❌ No datetime_utc field in response")
        
        # Test invalid datetime format
        invalid_event_data = {
            "title": "Invalid Event",
            "datetime_utc": "invalid-datetime",
            "reminder": True
        }
        
        success, _ = self.run_test(
            "Create Event with Invalid Datetime",
            "POST",
            "calendar/events",
            400,  # Should return bad request
            data=invalid_event_data
        )
        
        # Get all events
        success, events = self.run_test(
            "Get All Calendar Events",
            "GET",
            "calendar/events",
            200
        )
        
        if success and len(events) > 0:
            print(f"✅ Found {len(events)} calendar events")
        
        # Delete event
        if event_id:
            success, _ = self.run_test(
                "Delete Calendar Event",
                "DELETE",
                f"calendar/events/{event_id}",
                200
            )
        
        return True

    def test_career_functionality(self):
        """Test career goal creation and management"""
        print("\n" + "="*50)
        print("TESTING CAREER FUNCTIONALITY")
        print("="*50)
        
        # Create career goal
        goal_data = {
            "goal": "Become a senior software engineer",
            "timeframe": "12 months"
        }
        
        success, goal = self.run_test(
            "Create Career Goal",
            "POST",
            "career/goals",
            200,
            data=goal_data
        )
        
        if not success:
            return False
            
        goal_id = goal.get('id')
        
        # Check if action plan was generated
        if goal.get('action_plan') and len(goal['action_plan']) > 0:
            print("✅ AI-generated action plan created")
        else:
            print("⚠️  No action plan generated")
        
        # Get all goals
        success, goals = self.run_test(
            "Get All Career Goals",
            "GET",
            "career/goals",
            200
        )
        
        # Update progress
        if goal_id:
            success, _ = self.run_test(
                "Update Goal Progress",
                "PUT",
                f"career/goals/{goal_id}/progress",
                200,
                params={"progress": 25}
            )
        
        return True

    def test_health_functionality(self):
        """Test health tracking functionality"""
        print("\n" + "="*50)
        print("TESTING HEALTH FUNCTIONALITY")
        print("="*50)
        
        # Create health entry
        entry_data = {
            "type": "meal",
            "description": "Grilled chicken with vegetables",
            "date": "2024-12-19"
        }
        
        success, entry = self.run_test(
            "Create Health Entry",
            "POST",
            "health/entries",
            200,
            data=entry_data
        )
        
        if not success:
            return False
        
        # Create health goal
        goal_data = {
            "goal_type": "weight_loss",
            "target": "Lose 10 pounds",
            "current_progress": "Lost 2 pounds"
        }
        
        success, goal = self.run_test(
            "Create Health Goal",
            "POST",
            "health/goals",
            200,
            data=goal_data
        )
        
        # Get health entries
        success, entries = self.run_test(
            "Get Health Entries",
            "GET",
            "health/entries",
            200
        )
        
        # Get health goals
        success, goals = self.run_test(
            "Get Health Goals",
            "GET",
            "health/goals",
            200
        )
        
        # Get health analytics
        success, analytics = self.run_test(
            "Get Health Analytics",
            "GET",
            "health/analytics",
            200
        )
        
        if success and analytics:
            print("✅ Health analytics generated successfully")
        
        return True

    def test_error_handling(self):
        """Test API error handling"""
        print("\n" + "="*50)
        print("TESTING ERROR HANDLING")
        print("="*50)
        
        # Test invalid endpoints
        success, _ = self.run_test(
            "Invalid Endpoint",
            "GET",
            "invalid/endpoint",
            404
        )
        
        # Test invalid data
        success, _ = self.run_test(
            "Invalid Chat Data",
            "POST",
            "chat",
            422,  # Validation error
            data={"invalid": "data"}
        )
        
        return True

def main():
    print("🚀 Starting Donna AI Assistant API Tests")
    print("=" * 60)
    
    tester = DonnaAPITester()
    
    # Run all test suites
    test_suites = [
        tester.test_chat_functionality,
        tester.test_context_processing,
        tester.test_calendar_crud,
        tester.test_career_functionality,
        tester.test_health_functionality,
        tester.test_error_handling
    ]
    
    for test_suite in test_suites:
        try:
            test_suite()
        except Exception as e:
            print(f"❌ Test suite failed with error: {str(e)}")
    
    # Print final results
    print("\n" + "="*60)
    print("📊 FINAL TEST RESULTS")
    print("="*60)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed - check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())