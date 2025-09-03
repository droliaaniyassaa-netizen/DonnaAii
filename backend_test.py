import requests
import sys
import json
import time
from datetime import datetime, timezone

class DonnaAPITester:
    def __init__(self, base_url="https://loadnow-1.preview.emergentagent.com"):
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
        
        # Test timezone-aware event creation with category
        utc_datetime = datetime.now(timezone.utc).isoformat()
        event_data = {
            "title": "Test Meeting",
            "description": "API test meeting with timezone",
            "datetime_utc": utc_datetime,
            "category": "work",
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
        
        # Verify UTC datetime storage and category
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
        
        # Verify category
        if event.get('category') == 'work':
            print("✅ Event category stored correctly")
        else:
            print(f"❌ Event category incorrect: {event.get('category')}")
        
        # Test event update functionality
        if event_id:
            update_data = {
                "title": "Updated Test Meeting",
                "description": "Updated description",
                "category": "personal"
            }
            
            success, updated_event = self.run_test(
                "Update Calendar Event",
                "PUT",
                f"calendar/events/{event_id}",
                200,
                data=update_data
            )
            
            if success:
                if updated_event.get('title') == 'Updated Test Meeting':
                    print("✅ Event title updated successfully")
                else:
                    print("❌ Event title not updated")
                
                if updated_event.get('category') == 'personal':
                    print("✅ Event category updated successfully")
                else:
                    print("❌ Event category not updated")
        
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
            
            # Check if events have proper categories
            categories = [event.get('category', 'unknown') for event in events]
            unique_categories = set(categories)
            print(f"📊 Event categories found: {list(unique_categories)}")
        
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
        """Test health tracking functionality with timezone awareness"""
        print("\n" + "="*50)
        print("TESTING HEALTH FUNCTIONALITY WITH TIMEZONE")
        print("="*50)
        
        # Create health entry with UTC datetime
        utc_datetime = datetime.now(timezone.utc).isoformat()
        entry_data = {
            "type": "meal",
            "description": "Grilled chicken with vegetables",
            "datetime_utc": utc_datetime,
            "value": "500 calories"
        }
        
        success, entry = self.run_test(
            "Create Health Entry (UTC)",
            "POST",
            "health/entries",
            200,
            data=entry_data
        )
        
        if not success:
            return False
        
        # Verify UTC datetime storage
        if entry.get('datetime_utc'):
            print("✅ Health entry stored with UTC datetime")
            try:
                stored_dt = datetime.fromisoformat(entry['datetime_utc'].replace('Z', '+00:00'))
                print(f"   Stored datetime: {stored_dt}")
            except ValueError:
                print("❌ Invalid datetime format in health entry response")
        else:
            print("❌ No datetime_utc field in health entry response")
        
        # Test invalid datetime format for health entry
        invalid_entry_data = {
            "type": "exercise",
            "description": "Morning run",
            "datetime_utc": "not-a-datetime"
        }
        
        success, _ = self.run_test(
            "Create Health Entry with Invalid Datetime",
            "POST",
            "health/entries",
            400,  # Should return bad request
            data=invalid_entry_data
        )
        
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

    def test_health_targets_crud(self):
        """Test Health Targets CRUD operations for stat card personalization"""
        print("\n" + "="*50)
        print("TESTING HEALTH TARGETS CRUD OPERATIONS")
        print("="*50)
        
        session_id = "test_session"
        
        # Test creating health targets
        targets_data = {
            "session_id": session_id,
            "calories": 1800,
            "protein": 120,
            "hydration": 2800,
            "sleep": 8.0
        }
        
        success, targets = self.run_test(
            "Create Health Targets",
            "POST",
            "health/targets",
            200,
            data=targets_data
        )
        
        if not success:
            return False
            
        # Verify created targets structure
        if targets.get('session_id') == session_id:
            print("✅ Health targets created with correct session_id")
        else:
            print(f"❌ Session ID mismatch: expected {session_id}, got {targets.get('session_id')}")
            
        if targets.get('calories') == 1800:
            print("✅ Calories target set correctly")
        else:
            print(f"❌ Calories target incorrect: {targets.get('calories')}")
            
        if targets.get('protein') == 120:
            print("✅ Protein target set correctly")
        else:
            print(f"❌ Protein target incorrect: {targets.get('protein')}")
            
        if targets.get('hydration') == 2800:
            print("✅ Hydration target set correctly")
        else:
            print(f"❌ Hydration target incorrect: {targets.get('hydration')}")
            
        if targets.get('sleep') == 8.0:
            print("✅ Sleep target set correctly")
        else:
            print(f"❌ Sleep target incorrect: {targets.get('sleep')}")
            
        if targets.get('id') and targets.get('created_at') and targets.get('updated_at'):
            print("✅ Health targets have proper metadata (id, timestamps)")
        else:
            print("❌ Missing metadata fields")
        
        # Test retrieving health targets
        success, retrieved_targets = self.run_test(
            "Get Health Targets",
            "GET",
            f"health/targets/{session_id}",
            200
        )
        
        if success:
            if retrieved_targets.get('calories') == 1800:
                print("✅ Retrieved targets match created targets")
            else:
                print("❌ Retrieved targets don't match created targets")
        
        # Test updating health targets (partial update)
        update_data = {
            "calories": 2000,
            "protein": 150
        }
        
        success, updated_targets = self.run_test(
            "Update Health Targets (Partial)",
            "PUT",
            f"health/targets/{session_id}",
            200,
            data=update_data
        )
        
        if success:
            if updated_targets.get('calories') == 2000:
                print("✅ Calories updated successfully")
            else:
                print(f"❌ Calories not updated: {updated_targets.get('calories')}")
                
            if updated_targets.get('protein') == 150:
                print("✅ Protein updated successfully")
            else:
                print(f"❌ Protein not updated: {updated_targets.get('protein')}")
                
            # Verify unchanged fields remain the same
            if updated_targets.get('hydration') == 2800:
                print("✅ Hydration preserved during partial update")
            else:
                print(f"❌ Hydration changed unexpectedly: {updated_targets.get('hydration')}")
                
            if updated_targets.get('sleep') == 8.0:
                print("✅ Sleep preserved during partial update")
            else:
                print(f"❌ Sleep changed unexpectedly: {updated_targets.get('sleep')}")
                
            # Check updated_at timestamp changed
            if updated_targets.get('updated_at') != targets.get('updated_at'):
                print("✅ Updated timestamp changed correctly")
            else:
                print("❌ Updated timestamp not changed")
        
        # Test retrieving updated targets to verify persistence
        success, final_targets = self.run_test(
            "Verify Updated Health Targets",
            "GET",
            f"health/targets/{session_id}",
            200
        )
        
        if success:
            if final_targets.get('calories') == 2000 and final_targets.get('protein') == 150:
                print("✅ Updates persisted correctly")
            else:
                print("❌ Updates not persisted")
        
        # Test creating/updating targets for same session (should update, not create new)
        duplicate_data = {
            "session_id": session_id,
            "calories": 2200,
            "protein": 160,
            "hydration": 3000,
            "sleep": 7.5
        }
        
        success, duplicate_targets = self.run_test(
            "Create Targets for Existing Session (Should Update)",
            "POST",
            "health/targets",
            200,
            data=duplicate_data
        )
        
        if success:
            if duplicate_targets.get('calories') == 2200:
                print("✅ Existing session targets updated via POST")
            else:
                print("❌ POST to existing session didn't update properly")
        
        # Test error cases
        # Test getting targets for non-existent session
        success, _ = self.run_test(
            "Get Non-existent Health Targets",
            "GET",
            "health/targets/nonexistent_session",
            404
        )
        
        # Test updating targets for non-existent session
        success, _ = self.run_test(
            "Update Non-existent Health Targets",
            "PUT",
            "health/targets/nonexistent_session",
            404,
            data={"calories": 1500}
        )
        
        # Test deleting health targets
        success, delete_response = self.run_test(
            "Delete Health Targets",
            "DELETE",
            f"health/targets/{session_id}",
            200
        )
        
        if success:
            if delete_response.get('message'):
                print("✅ Health targets deleted successfully")
            else:
                print("❌ Delete response missing message")
        
        # Verify targets are actually deleted
        success, _ = self.run_test(
            "Verify Health Targets Deleted",
            "GET",
            f"health/targets/{session_id}",
            404
        )
        
        # Test deleting non-existent targets
        success, _ = self.run_test(
            "Delete Non-existent Health Targets",
            "DELETE",
            "health/targets/nonexistent_session",
            404
        )
        
        return True

    def test_smart_suggestions_telemetry(self):
        """Test Smart Suggestions telemetry logging endpoints"""
        print("\n" + "="*50)
        print("TESTING SMART SUGGESTIONS TELEMETRY")
        print("="*50)
        
        # Test telemetry logging with sample data
        telemetry_data = {
            "session_id": "test_session_123",
            "event_type": "impression",
            "suggestion_type": "dense_block",
            "suggestion_id": "dense_suggestion_test",
            "action": None,
            "metadata": {"test": "data"},
            "latency_ms": None
        }
        
        success, response = self.run_test(
            "Log Telemetry Data (Impression)",
            "POST",
            "telemetry/log",
            200,
            data=telemetry_data
        )
        
        if not success:
            return False
            
        # Verify response contains success and id
        if response.get('success') and response.get('id'):
            print("✅ Telemetry logged successfully with ID")
        else:
            print("❌ Telemetry response missing success or id field")
        
        # Test telemetry logging with dismiss action
        dismiss_data = {
            "session_id": "test_session_123",
            "event_type": "dismiss",
            "suggestion_type": "dense_block",
            "suggestion_id": "dense_suggestion_test",
            "action": "dismiss",
            "metadata": {"reason": "not_relevant"},
            "latency_ms": 150
        }
        
        success, response = self.run_test(
            "Log Telemetry Data (Dismiss)",
            "POST",
            "telemetry/log",
            200,
            data=dismiss_data
        )
        
        # Test telemetry analytics
        success, analytics = self.run_test(
            "Get Telemetry Analytics",
            "GET",
            "telemetry/analytics",
            200
        )
        
        if success and analytics.get('analytics'):
            print("✅ Telemetry analytics retrieved successfully")
            analytics_data = analytics['analytics']
            if len(analytics_data) > 0:
                print(f"   Found {len(analytics_data)} analytics entries")
                for entry in analytics_data[:3]:  # Show first 3 entries
                    print(f"   - {entry['event_type']}/{entry['suggestion_type']}: {entry['count']} events")
            else:
                print("   No analytics data found (expected if no telemetry logged yet)")
        else:
            print("❌ Failed to retrieve telemetry analytics")
        
        return True

    def test_user_settings(self):
        """Test User Settings endpoints for weekend mode and timezone"""
        print("\n" + "="*50)
        print("TESTING USER SETTINGS")
        print("="*50)
        
        session_id = "test_session_123"
        
        # Test getting default settings for new session
        success, settings = self.run_test(
            "Get Default User Settings",
            "GET",
            f"user/settings/{session_id}",
            200
        )
        
        if not success:
            return False
            
        # Verify default settings
        if settings.get('session_id') == session_id:
            print("✅ Settings returned with correct session_id")
        else:
            print("❌ Settings session_id mismatch")
            
        if settings.get('weekend_mode') == 'relaxed':
            print("✅ Default weekend_mode is 'relaxed'")
        else:
            print(f"❌ Default weekend_mode incorrect: {settings.get('weekend_mode')}")
        
        # Test updating user settings
        update_data = {
            "weekend_mode": "active",
            "timezone": "America/New_York"
        }
        
        success, updated_settings = self.run_test(
            "Update User Settings",
            "PUT",
            f"user/settings/{session_id}",
            200,
            data=update_data
        )
        
        if success:
            # Verify updated settings
            if updated_settings.get('weekend_mode') == 'active':
                print("✅ Weekend mode updated to 'active'")
            else:
                print(f"❌ Weekend mode not updated: {updated_settings.get('weekend_mode')}")
                
            if updated_settings.get('timezone') == 'America/New_York':
                print("✅ Timezone updated to 'America/New_York'")
            else:
                print(f"❌ Timezone not updated: {updated_settings.get('timezone')}")
                
            if updated_settings.get('updated_at'):
                print("✅ Updated timestamp present")
            else:
                print("❌ Updated timestamp missing")
        
        # Test partial update (only weekend_mode)
        partial_update = {
            "weekend_mode": "relaxed"
        }
        
        success, partial_settings = self.run_test(
            "Partial Update User Settings",
            "PUT",
            f"user/settings/{session_id}",
            200,
            data=partial_update
        )
        
        if success:
            if partial_settings.get('weekend_mode') == 'relaxed':
                print("✅ Partial update successful - weekend_mode changed")
            else:
                print("❌ Partial update failed")
                
            # Timezone should remain unchanged
            if partial_settings.get('timezone') == 'America/New_York':
                print("✅ Timezone preserved during partial update")
            else:
                print("❌ Timezone lost during partial update")
        
        # Test getting settings again to verify persistence
        success, final_settings = self.run_test(
            "Get Updated User Settings",
            "GET",
            f"user/settings/{session_id}",
            200
        )
        
        if success:
            if final_settings.get('weekend_mode') == 'relaxed':
                print("✅ Settings persisted correctly")
            else:
                print("❌ Settings not persisted")
        
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
        
        # Test invalid telemetry data
        success, _ = self.run_test(
            "Invalid Telemetry Data",
            "POST",
            "telemetry/log",
            422,  # Validation error
            data={"invalid": "telemetry"}
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
        tester.test_health_targets_crud,
        tester.test_smart_suggestions_telemetry,
        tester.test_user_settings,
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