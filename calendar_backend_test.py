import requests
import sys
import json
import time
from datetime import datetime, timezone, timedelta

class CalendarBackendTester:
    def __init__(self, base_url="https://donna-calendar-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_event_ids = []

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
                    print(f"   Response: {json.dumps(response_data, indent=2)[:300]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:300]}...")

            return success, response.json() if response.text and response.status_code < 500 else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_calendar_crud_operations(self):
        """Test comprehensive calendar CRUD operations"""
        print("\n" + "="*60)
        print("TESTING CALENDAR CRUD OPERATIONS")
        print("="*60)
        
        # Test 1: Create events in different categories
        categories = ["work", "personal", "appointments", "regular_activities"]
        created_events = []
        
        for i, category in enumerate(categories):
            # Create event for today + i days
            event_datetime = datetime.now(timezone.utc) + timedelta(days=i)
            event_data = {
                "title": f"Test {category.title()} Event",
                "description": f"Testing {category} category event for glassmorphic frontend",
                "datetime_utc": event_datetime.isoformat(),
                "category": category,
                "reminder": True
            }
            
            success, event = self.run_test(
                f"Create {category.title()} Event",
                "POST",
                "calendar/events",
                200,
                data=event_data
            )
            
            if success and event.get('id'):
                created_events.append(event)
                self.created_event_ids.append(event['id'])
                
                # Verify category is stored correctly
                if event.get('category') == category:
                    print(f"✅ {category.title()} category stored correctly")
                else:
                    print(f"❌ {category.title()} category incorrect: {event.get('category')}")
        
        # Test 2: Read all events
        success, all_events = self.run_test(
            "Get All Calendar Events",
            "GET",
            "calendar/events",
            200
        )
        
        if success:
            print(f"✅ Retrieved {len(all_events)} total events")
            
            # Verify all categories are present
            found_categories = set(event.get('category', 'unknown') for event in all_events)
            print(f"📊 Categories found: {sorted(list(found_categories))}")
            
            # Check if events are sorted by datetime
            if len(all_events) > 1:
                is_sorted = all(
                    all_events[i]['datetime_utc'] <= all_events[i+1]['datetime_utc'] 
                    for i in range(len(all_events)-1)
                )
                if is_sorted:
                    print("✅ Events are properly sorted by datetime")
                else:
                    print("⚠️  Events may not be sorted by datetime")
        
        # Test 3: Update events
        if created_events:
            first_event = created_events[0]
            event_id = first_event['id']
            
            update_data = {
                "title": "Updated Glassmorphic Event",
                "description": "Updated for new frontend design testing",
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
                if updated_event.get('title') == update_data['title']:
                    print("✅ Event title updated successfully")
                if updated_event.get('category') == update_data['category']:
                    print("✅ Event category updated successfully")
                if updated_event.get('description') == update_data['description']:
                    print("✅ Event description updated successfully")
        
        # Test 4: Delete events (clean up)
        for event_id in self.created_event_ids[-2:]:  # Delete last 2 created events
            success, _ = self.run_test(
                f"Delete Event {event_id[:8]}...",
                "DELETE",
                f"calendar/events/{event_id}",
                200
            )
            if success:
                self.created_event_ids.remove(event_id)
        
        return True

    def test_timezone_handling(self):
        """Test timezone handling for calendar events"""
        print("\n" + "="*60)
        print("TESTING TIMEZONE HANDLING")
        print("="*60)
        
        # Test different timezone formats
        timezone_tests = [
            {
                "name": "UTC with Z suffix",
                "datetime": "2025-08-27T15:30:00Z",
                "expected_valid": True
            },
            {
                "name": "UTC with +00:00 offset",
                "datetime": "2025-08-27T15:30:00+00:00",
                "expected_valid": True
            },
            {
                "name": "EST timezone",
                "datetime": "2025-08-27T10:30:00-05:00",
                "expected_valid": True
            },
            {
                "name": "PST timezone",
                "datetime": "2025-08-27T07:30:00-08:00",
                "expected_valid": True
            },
            {
                "name": "Invalid format",
                "datetime": "2025-08-27 15:30:00",
                "expected_valid": False
            }
        ]
        
        for test_case in timezone_tests:
            event_data = {
                "title": f"Timezone Test - {test_case['name']}",
                "description": "Testing timezone conversion",
                "datetime_utc": test_case['datetime'],
                "category": "work",
                "reminder": True
            }
            
            expected_status = 200 if test_case['expected_valid'] else 400
            success, event = self.run_test(
                f"Create Event - {test_case['name']}",
                "POST",
                "calendar/events",
                expected_status,
                data=event_data
            )
            
            if test_case['expected_valid'] and success:
                # Verify UTC conversion
                stored_datetime = event.get('datetime_utc')
                if stored_datetime:
                    try:
                        parsed_dt = datetime.fromisoformat(stored_datetime.replace('Z', '+00:00'))
                        if parsed_dt.tzinfo == timezone.utc:
                            print(f"✅ {test_case['name']} - Properly converted to UTC")
                        else:
                            print(f"❌ {test_case['name']} - Not in UTC timezone")
                        
                        # Store event ID for cleanup
                        if event.get('id'):
                            self.created_event_ids.append(event['id'])
                            
                    except ValueError as e:
                        print(f"❌ {test_case['name']} - Invalid datetime format: {e}")
        
        return True

    def test_today_events_filtering(self):
        """Test Today events filtering functionality"""
        print("\n" + "="*60)
        print("TESTING TODAY EVENTS FILTERING")
        print("="*60)
        
        # Create events for different days
        today = datetime.now(timezone.utc).replace(hour=14, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)
        
        test_events = [
            {
                "title": "Today's Morning Meeting",
                "datetime": today.replace(hour=9),
                "category": "work"
            },
            {
                "title": "Today's Lunch Appointment",
                "datetime": today.replace(hour=12),
                "category": "appointments"
            },
            {
                "title": "Today's Evening Workout",
                "datetime": today.replace(hour=18),
                "category": "regular_activities"
            },
            {
                "title": "Tomorrow's Planning Session",
                "datetime": tomorrow,
                "category": "work"
            },
            {
                "title": "Yesterday's Completed Task",
                "datetime": yesterday,
                "category": "personal"
            }
        ]
        
        # Create test events
        for event_info in test_events:
            event_data = {
                "title": event_info["title"],
                "description": f"Test event for {event_info['title']}",
                "datetime_utc": event_info["datetime"].isoformat(),
                "category": event_info["category"],
                "reminder": True
            }
            
            success, event = self.run_test(
                f"Create Event: {event_info['title']}",
                "POST",
                "calendar/events",
                200,
                data=event_data
            )
            
            if success and event.get('id'):
                self.created_event_ids.append(event['id'])
        
        # Get all events and filter for today
        success, all_events = self.run_test(
            "Get All Events for Today Filtering",
            "GET",
            "calendar/events",
            200
        )
        
        if success:
            # Filter events for today (frontend logic simulation)
            today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            today_events = []
            past_events = []
            future_events = []
            
            for event in all_events:
                try:
                    event_dt = datetime.fromisoformat(event['datetime_utc'].replace('Z', '+00:00'))
                    
                    if today_start <= event_dt <= today_end:
                        today_events.append(event)
                    elif event_dt < today_start:
                        past_events.append(event)
                    else:
                        future_events.append(event)
                        
                except ValueError:
                    print(f"⚠️  Invalid datetime in event: {event.get('title', 'Unknown')}")
            
            print(f"📊 Today's events: {len(today_events)}")
            print(f"📊 Past events: {len(past_events)}")
            print(f"📊 Future events: {len(future_events)}")
            
            # Verify today's events have correct categories for color coding
            if today_events:
                print("📋 Today's events by category:")
                for event in today_events:
                    category = event.get('category', 'unknown')
                    title = event.get('title', 'Unknown')
                    print(f"   - {category}: {title}")
                
                # Check if we have the expected today events
                expected_today_titles = ["Today's Morning Meeting", "Today's Lunch Appointment", "Today's Evening Workout"]
                found_titles = [event['title'] for event in today_events if event['title'] in expected_today_titles]
                
                if len(found_titles) >= 3:
                    print("✅ Today's events filtering works correctly")
                else:
                    print(f"⚠️  Expected 3+ today events, found {len(found_titles)}")
        
        return True

    def test_event_categorization(self):
        """Test event categorization for color coding"""
        print("\n" + "="*60)
        print("TESTING EVENT CATEGORIZATION FOR COLOR CODING")
        print("="*60)
        
        # Test all supported categories with realistic events
        category_tests = [
            {
                "category": "work",
                "events": [
                    "Team Standup Meeting",
                    "Client Presentation",
                    "Code Review Session"
                ]
            },
            {
                "category": "personal",
                "events": [
                    "Doctor Appointment",
                    "Family Dinner",
                    "Personal Reading Time"
                ]
            },
            {
                "category": "appointments",
                "events": [
                    "Dentist Checkup",
                    "Car Service",
                    "Hair Salon Appointment"
                ]
            },
            {
                "category": "regular_activities",
                "events": [
                    "Morning Yoga",
                    "Evening Gym Session",
                    "Weekly Grocery Shopping"
                ]
            }
        ]
        
        category_counts = {}
        
        for category_test in category_tests:
            category = category_test["category"]
            category_counts[category] = 0
            
            for i, event_title in enumerate(category_test["events"]):
                # Spread events across different times
                event_datetime = datetime.now(timezone.utc) + timedelta(hours=i*2)
                
                event_data = {
                    "title": event_title,
                    "description": f"Testing {category} category for glassmorphic color coding",
                    "datetime_utc": event_datetime.isoformat(),
                    "category": category,
                    "reminder": True
                }
                
                success, event = self.run_test(
                    f"Create {category} Event: {event_title}",
                    "POST",
                    "calendar/events",
                    200,
                    data=event_data
                )
                
                if success:
                    # Verify category is stored correctly
                    if event.get('category') == category:
                        category_counts[category] += 1
                        print(f"✅ {category} category stored correctly")
                        
                        if event.get('id'):
                            self.created_event_ids.append(event['id'])
                    else:
                        print(f"❌ Category mismatch: expected {category}, got {event.get('category')}")
        
        # Verify all categories are working
        print(f"\n📊 Category Test Results:")
        for category, count in category_counts.items():
            print(f"   - {category}: {count} events created")
        
        # Test default category behavior
        event_data = {
            "title": "Event Without Category",
            "description": "Testing default category assignment",
            "datetime_utc": datetime.now(timezone.utc).isoformat(),
            "reminder": True
            # No category specified
        }
        
        success, event = self.run_test(
            "Create Event Without Category (Default Test)",
            "POST",
            "calendar/events",
            200,
            data=event_data
        )
        
        if success:
            default_category = event.get('category')
            if default_category == 'personal':
                print("✅ Default category 'personal' assigned correctly")
            else:
                print(f"⚠️  Unexpected default category: {default_category}")
            
            if event.get('id'):
                self.created_event_ids.append(event['id'])
        
        return True

    def test_event_data_persistence(self):
        """Test event data persistence and JSON serialization"""
        print("\n" + "="*60)
        print("TESTING EVENT DATA PERSISTENCE & JSON SERIALIZATION")
        print("="*60)
        
        # Create a comprehensive event with all fields
        comprehensive_event = {
            "title": "Comprehensive Test Event",
            "description": "Testing all fields for glassmorphic frontend compatibility",
            "datetime_utc": datetime.now(timezone.utc).isoformat(),
            "category": "work",
            "reminder": True
        }
        
        success, created_event = self.run_test(
            "Create Comprehensive Event",
            "POST",
            "calendar/events",
            200,
            data=comprehensive_event
        )
        
        if success and created_event.get('id'):
            event_id = created_event['id']
            self.created_event_ids.append(event_id)
            
            # Verify all fields are present and correctly typed
            required_fields = ['id', 'title', 'description', 'datetime_utc', 'category', 'reminder', 'created_at']
            
            for field in required_fields:
                if field in created_event:
                    print(f"✅ Field '{field}' present: {type(created_event[field]).__name__}")
                else:
                    print(f"❌ Field '{field}' missing")
            
            # Test data retrieval consistency
            success, retrieved_event = self.run_test(
                "Retrieve Event by ID (via GET all)",
                "GET",
                "calendar/events",
                200
            )
            
            if success:
                # Find our event in the list
                our_event = next((e for e in retrieved_event if e.get('id') == event_id), None)
                
                if our_event:
                    print("✅ Event found in retrieval")
                    
                    # Verify data consistency
                    for field in ['title', 'description', 'category', 'reminder']:
                        if our_event.get(field) == created_event.get(field):
                            print(f"✅ Field '{field}' consistent after retrieval")
                        else:
                            print(f"❌ Field '{field}' inconsistent: {our_event.get(field)} vs {created_event.get(field)}")
                    
                    # Test datetime format consistency
                    created_dt = created_event.get('datetime_utc')
                    retrieved_dt = our_event.get('datetime_utc')
                    
                    if created_dt and retrieved_dt:
                        try:
                            created_parsed = datetime.fromisoformat(created_dt.replace('Z', '+00:00'))
                            retrieved_parsed = datetime.fromisoformat(retrieved_dt.replace('Z', '+00:00'))
                            
                            if abs((created_parsed - retrieved_parsed).total_seconds()) < 1:
                                print("✅ Datetime consistency maintained")
                            else:
                                print(f"❌ Datetime inconsistency: {created_parsed} vs {retrieved_parsed}")
                                
                        except ValueError as e:
                            print(f"❌ Datetime parsing error: {e}")
                else:
                    print("❌ Event not found in retrieval")
        
        return True

    def test_api_error_handling(self):
        """Test API error handling for calendar endpoints"""
        print("\n" + "="*60)
        print("TESTING CALENDAR API ERROR HANDLING")
        print("="*60)
        
        # Test invalid event creation
        invalid_tests = [
            {
                "name": "Missing Title",
                "data": {
                    "description": "Event without title",
                    "datetime_utc": datetime.now(timezone.utc).isoformat(),
                    "category": "work"
                },
                "expected_status": 422
            },
            {
                "name": "Invalid Datetime Format",
                "data": {
                    "title": "Invalid Datetime Event",
                    "datetime_utc": "not-a-datetime",
                    "category": "work"
                },
                "expected_status": 400
            },
            {
                "name": "Empty Title",
                "data": {
                    "title": "",
                    "datetime_utc": datetime.now(timezone.utc).isoformat(),
                    "category": "work"
                },
                "expected_status": 422
            }
        ]
        
        for test in invalid_tests:
            success, _ = self.run_test(
                f"Invalid Event Creation - {test['name']}",
                "POST",
                "calendar/events",
                test['expected_status'],
                data=test['data']
            )
        
        # Test invalid event operations
        fake_id = "non-existent-event-id"
        
        success, _ = self.run_test(
            "Update Non-existent Event",
            "PUT",
            f"calendar/events/{fake_id}",
            404,
            data={"title": "Updated Title"}
        )
        
        success, _ = self.run_test(
            "Delete Non-existent Event",
            "DELETE",
            f"calendar/events/{fake_id}",
            404
        )
        
        return True

    def cleanup_test_events(self):
        """Clean up all test events created during testing"""
        print(f"\n🧹 Cleaning up {len(self.created_event_ids)} test events...")
        
        cleaned_count = 0
        for event_id in self.created_event_ids:
            try:
                success, _ = self.run_test(
                    f"Cleanup Event {event_id[:8]}...",
                    "DELETE",
                    f"calendar/events/{event_id}",
                    200
                )
                if success:
                    cleaned_count += 1
            except:
                pass  # Ignore cleanup errors
        
        print(f"✅ Cleaned up {cleaned_count} test events")

def main():
    print("🗓️  Starting Donna AI Calendar Backend Tests")
    print("=" * 70)
    print("Testing calendar functionality for glassmorphic frontend redesign")
    print("=" * 70)
    
    tester = CalendarBackendTester()
    
    # Run all calendar test suites
    test_suites = [
        tester.test_calendar_crud_operations,
        tester.test_timezone_handling,
        tester.test_today_events_filtering,
        tester.test_event_categorization,
        tester.test_event_data_persistence,
        tester.test_api_error_handling
    ]
    
    for test_suite in test_suites:
        try:
            test_suite()
        except Exception as e:
            print(f"❌ Test suite failed with error: {str(e)}")
    
    # Clean up test events
    tester.cleanup_test_events()
    
    # Print final results
    print("\n" + "="*70)
    print("📊 CALENDAR BACKEND TEST RESULTS")
    print("="*70)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All calendar backend tests passed!")
        print("✅ Backend is ready for glassmorphic frontend redesign!")
        return 0
    else:
        print("⚠️  Some calendar tests failed - check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())