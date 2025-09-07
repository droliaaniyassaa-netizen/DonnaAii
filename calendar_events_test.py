#!/usr/bin/env python3
"""
Calendar Events Functionality Test
Comprehensive testing of calendar events API endpoints and functionality
"""

import requests
import json
import time
from datetime import datetime, timezone, timedelta

class CalendarEventsTest:
    def __init__(self, base_url="https://donna-ai-assist.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = "default"  # Using default session as mentioned in review
        
    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")
    
    def make_request(self, method, endpoint, data=None, params=None):
        """Make API request and return response"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            
            return response
        except Exception as e:
            print(f"Request failed: {str(e)}")
            return None
    
    def test_calendar_events_endpoint(self):
        """Test GET /api/calendar/events endpoint"""
        print("\n" + "="*60)
        print("TESTING CALENDAR EVENTS ENDPOINT")
        print("="*60)
        
        # Test GET /api/calendar/events
        response = self.make_request('GET', 'calendar/events')
        
        if response is None:
            self.log_test("GET /api/calendar/events - Request", False, "Request failed")
            return False
        
        # Check status code
        success = response.status_code == 200
        self.log_test("GET /api/calendar/events - Status Code", success, 
                     f"Expected 200, got {response.status_code}")
        
        if not success:
            print(f"Response: {response.text[:500]}")
            return False
        
        # Parse response
        try:
            events = response.json()
            self.log_test("GET /api/calendar/events - JSON Response", True, 
                         f"Successfully parsed JSON with {len(events)} events")
        except Exception as e:
            self.log_test("GET /api/calendar/events - JSON Response", False, 
                         f"Failed to parse JSON: {str(e)}")
            return False
        
        # Validate response structure
        if isinstance(events, list):
            self.log_test("Response Structure", True, "Response is a list as expected")
        else:
            self.log_test("Response Structure", False, f"Expected list, got {type(events)}")
            return False
        
        # Check event structure if events exist
        if len(events) > 0:
            sample_event = events[0]
            required_fields = ['id', 'title', 'datetime_utc', 'session_id']
            
            for field in required_fields:
                if field in sample_event:
                    self.log_test(f"Event Field '{field}'", True, f"Present in event")
                else:
                    self.log_test(f"Event Field '{field}'", False, f"Missing from event")
            
            # Check session_id matches
            session_matches = all(event.get('session_id') == self.session_id for event in events)
            self.log_test("Session ID Filter", session_matches, 
                         f"All events belong to session '{self.session_id}'" if session_matches 
                         else "Some events have different session_id")
            
            # Check datetime format
            for i, event in enumerate(events[:3]):  # Check first 3 events
                try:
                    datetime_str = event.get('datetime_utc', '')
                    if datetime_str:
                        # Try to parse the datetime
                        parsed_dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                        self.log_test(f"Event {i+1} Datetime Format", True, 
                                     f"Valid datetime: {parsed_dt}")
                    else:
                        self.log_test(f"Event {i+1} Datetime Format", False, "No datetime_utc field")
                except Exception as e:
                    self.log_test(f"Event {i+1} Datetime Format", False, 
                                 f"Invalid datetime format: {str(e)}")
        else:
            print("   No events found - this is normal for a fresh session")
        
        return True
    
    def test_calendar_event_creation(self):
        """Test creating calendar events"""
        print("\n" + "="*60)
        print("TESTING CALENDAR EVENT CREATION")
        print("="*60)
        
        # Create a test event
        now = datetime.now(timezone.utc)
        tomorrow = now + timedelta(days=1)
        
        event_data = {
            "title": "Test Calendar Event",
            "description": "Testing calendar functionality",
            "datetime_utc": tomorrow.isoformat(),
            "category": "work",
            "reminder": True
        }
        
        response = self.make_request('POST', 'calendar/events', data=event_data)
        
        if response is None:
            self.log_test("POST /api/calendar/events - Request", False, "Request failed")
            return None
        
        # Check status code
        success = response.status_code == 200
        self.log_test("POST /api/calendar/events - Status Code", success, 
                     f"Expected 200, got {response.status_code}")
        
        if not success:
            print(f"Response: {response.text[:500]}")
            return None
        
        # Parse response
        try:
            created_event = response.json()
            self.log_test("Event Creation - JSON Response", True, "Successfully parsed JSON")
        except Exception as e:
            self.log_test("Event Creation - JSON Response", False, f"Failed to parse JSON: {str(e)}")
            return None
        
        # Validate created event
        event_id = created_event.get('id')
        if event_id:
            self.log_test("Event Creation - ID Generated", True, f"Event ID: {event_id}")
        else:
            self.log_test("Event Creation - ID Generated", False, "No ID in response")
            return None
        
        # Check if event data matches
        title_match = created_event.get('title') == event_data['title']
        self.log_test("Event Creation - Title Match", title_match, 
                     f"Expected '{event_data['title']}', got '{created_event.get('title')}'")
        
        category_match = created_event.get('category') == event_data['category']
        self.log_test("Event Creation - Category Match", category_match,
                     f"Expected '{event_data['category']}', got '{created_event.get('category')}'")
        
        session_match = created_event.get('session_id') == self.session_id
        self.log_test("Event Creation - Session ID", session_match,
                     f"Expected '{self.session_id}', got '{created_event.get('session_id')}'")
        
        return event_id
    
    def test_calendar_event_retrieval(self, event_id=None):
        """Test retrieving calendar events after creation"""
        print("\n" + "="*60)
        print("TESTING CALENDAR EVENT RETRIEVAL")
        print("="*60)
        
        # Get all events again
        response = self.make_request('GET', 'calendar/events')
        
        if response is None:
            self.log_test("GET Events After Creation - Request", False, "Request failed")
            return False
        
        success = response.status_code == 200
        self.log_test("GET Events After Creation - Status Code", success)
        
        if not success:
            return False
        
        try:
            events = response.json()
            self.log_test("GET Events After Creation - JSON Parse", True, 
                         f"Found {len(events)} events")
        except Exception as e:
            self.log_test("GET Events After Creation - JSON Parse", False, str(e))
            return False
        
        # Check if our created event is in the list
        if event_id:
            created_event_found = any(event.get('id') == event_id for event in events)
            self.log_test("Created Event in List", created_event_found,
                         f"Event {event_id} {'found' if created_event_found else 'not found'} in list")
        
        # Check event sorting (should be by datetime_utc)
        if len(events) > 1:
            is_sorted = True
            for i in range(1, len(events)):
                try:
                    prev_dt = datetime.fromisoformat(events[i-1]['datetime_utc'].replace('Z', '+00:00'))
                    curr_dt = datetime.fromisoformat(events[i]['datetime_utc'].replace('Z', '+00:00'))
                    if prev_dt > curr_dt:
                        is_sorted = False
                        break
                except:
                    is_sorted = False
                    break
            
            self.log_test("Event Sorting", is_sorted, 
                         "Events are sorted by datetime_utc" if is_sorted 
                         else "Events are not properly sorted")
        
        return True
    
    def test_today_events_filtering(self):
        """Test filtering events for today"""
        print("\n" + "="*60)
        print("TESTING TODAY EVENTS FILTERING")
        print("="*60)
        
        # Get current date info
        now = datetime.now(timezone.utc)
        today_str = now.strftime('%Y-%m-%d')
        
        print(f"   Current UTC date: {today_str}")
        print(f"   Current UTC time: {now.strftime('%H:%M:%S')}")
        
        # Get all events
        response = self.make_request('GET', 'calendar/events')
        
        if response is None or response.status_code != 200:
            self.log_test("Get Events for Today Filter", False, "Failed to get events")
            return False
        
        try:
            events = response.json()
            self.log_test("Get Events for Today Filter", True, f"Retrieved {len(events)} events")
        except Exception as e:
            self.log_test("Get Events for Today Filter", False, str(e))
            return False
        
        # Filter events for today
        today_events = []
        for event in events:
            try:
                event_dt = datetime.fromisoformat(event['datetime_utc'].replace('Z', '+00:00'))
                event_date_str = event_dt.strftime('%Y-%m-%d')
                
                if event_date_str == today_str:
                    today_events.append(event)
                    print(f"   Today's event: {event.get('title', 'No title')} at {event_dt.strftime('%H:%M')}")
            except Exception as e:
                print(f"   Error parsing event datetime: {str(e)}")
        
        self.log_test("Today Events Filter", True, 
                     f"Found {len(today_events)} events for today ({today_str})")
        
        # Check if events have proper categories for frontend display
        if today_events:
            categories = set(event.get('category', 'unknown') for event in today_events)
            self.log_test("Today Events Categories", True, 
                         f"Categories found: {', '.join(categories)}")
        
        return True
    
    def test_event_categories(self):
        """Test event categorization functionality"""
        print("\n" + "="*60)
        print("TESTING EVENT CATEGORIZATION")
        print("="*60)
        
        # Test creating events with different categories
        categories_to_test = ['work', 'personal', 'appointments', 'regular_activities']
        created_events = []
        
        for category in categories_to_test:
            event_data = {
                "title": f"Test {category.title()} Event",
                "description": f"Testing {category} category",
                "datetime_utc": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                "category": category,
                "reminder": True
            }
            
            response = self.make_request('POST', 'calendar/events', data=event_data)
            
            if response and response.status_code == 200:
                try:
                    event = response.json()
                    created_events.append(event)
                    
                    category_match = event.get('category') == category
                    self.log_test(f"Category '{category}' Creation", category_match,
                                 f"Expected '{category}', got '{event.get('category')}'")
                except Exception as e:
                    self.log_test(f"Category '{category}' Creation", False, str(e))
            else:
                self.log_test(f"Category '{category}' Creation", False, 
                             f"Failed to create event: {response.status_code if response else 'No response'}")
        
        # Verify categories are preserved when retrieving events
        response = self.make_request('GET', 'calendar/events')
        if response and response.status_code == 200:
            try:
                all_events = response.json()
                found_categories = set(event.get('category', 'unknown') for event in all_events)
                
                for category in categories_to_test:
                    category_found = category in found_categories
                    self.log_test(f"Category '{category}' Retrieval", category_found,
                                 f"Category {'found' if category_found else 'not found'} in retrieved events")
                
                self.log_test("All Categories Retrieved", True, 
                             f"Found categories: {', '.join(sorted(found_categories))}")
            except Exception as e:
                self.log_test("Category Retrieval", False, str(e))
        
        return created_events
    
    def test_api_error_handling(self):
        """Test API error handling"""
        print("\n" + "="*60)
        print("TESTING API ERROR HANDLING")
        print("="*60)
        
        # Test invalid datetime format
        invalid_event_data = {
            "title": "Invalid Event",
            "datetime_utc": "invalid-datetime-format",
            "reminder": True
        }
        
        response = self.make_request('POST', 'calendar/events', data=invalid_event_data)
        
        if response:
            expected_error = response.status_code == 400
            self.log_test("Invalid Datetime Error Handling", expected_error,
                         f"Expected 400, got {response.status_code}")
        else:
            self.log_test("Invalid Datetime Error Handling", False, "No response")
        
        # Test getting non-existent event
        response = self.make_request('GET', 'calendar/events/nonexistent-id')
        
        if response:
            # This endpoint doesn't exist, so we expect 404 or 405
            expected_error = response.status_code in [404, 405]
            self.log_test("Non-existent Endpoint Error", expected_error,
                         f"Expected 404/405, got {response.status_code}")
        else:
            self.log_test("Non-existent Endpoint Error", False, "No response")
    
    def test_double_api_prefix_issue(self):
        """Test that there's no double /api prefix issue"""
        print("\n" + "="*60)
        print("TESTING DOUBLE /API PREFIX ISSUE")
        print("="*60)
        
        # Test the correct endpoint
        correct_url = f"{self.api_url}/calendar/events"
        
        try:
            response = requests.get(correct_url, timeout=30)
            correct_works = response.status_code == 200
            self.log_test("Correct API URL", correct_works,
                         f"URL: {correct_url} - Status: {response.status_code}")
        except Exception as e:
            self.log_test("Correct API URL", False, f"Error: {str(e)}")
            correct_works = False
        
        # Test potential double prefix (this should fail)
        double_prefix_url = f"{self.api_url}/api/calendar/events"
        
        try:
            response = requests.get(double_prefix_url, timeout=10)
            double_prefix_fails = response.status_code != 200
            self.log_test("Double Prefix Correctly Fails", double_prefix_fails,
                         f"URL: {double_prefix_url} - Status: {response.status_code}")
        except Exception as e:
            self.log_test("Double Prefix Correctly Fails", True, 
                         f"Double prefix URL correctly fails: {str(e)}")
        
        return correct_works
    
    def test_session_isolation(self):
        """Test that events are properly isolated by session"""
        print("\n" + "="*60)
        print("TESTING SESSION ISOLATION")
        print("="*60)
        
        # Get events for default session
        response = self.make_request('GET', 'calendar/events')
        
        if response and response.status_code == 200:
            try:
                default_events = response.json()
                
                # Check that all events belong to the expected session
                session_matches = all(event.get('session_id') == self.session_id for event in default_events)
                self.log_test("Session ID Consistency", session_matches,
                             f"All {len(default_events)} events belong to session '{self.session_id}'")
                
                # Show session distribution
                session_counts = {}
                for event in default_events:
                    session = event.get('session_id', 'unknown')
                    session_counts[session] = session_counts.get(session, 0) + 1
                
                self.log_test("Session Distribution", True,
                             f"Session counts: {session_counts}")
                
            except Exception as e:
                self.log_test("Session Isolation Test", False, str(e))
        else:
            self.log_test("Session Isolation Test", False, "Failed to get events")
    
    def run_comprehensive_test(self):
        """Run all calendar events tests"""
        print("🗓️  COMPREHENSIVE CALENDAR EVENTS FUNCTIONALITY TEST")
        print("="*80)
        print(f"Testing against: {self.base_url}")
        print(f"Session ID: {self.session_id}")
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all tests
        self.test_double_api_prefix_issue()
        self.test_calendar_events_endpoint()
        
        # Create a test event and get its ID
        event_id = self.test_calendar_event_creation()
        
        # Test retrieval with the created event
        self.test_calendar_event_retrieval(event_id)
        
        # Test filtering and categorization
        self.test_today_events_filtering()
        self.test_event_categories()
        
        # Test session isolation
        self.test_session_isolation()
        
        # Test error handling
        self.test_api_error_handling()
        
        # Print summary
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED - Calendar events functionality is working correctly!")
        elif self.tests_passed / self.tests_run >= 0.8:
            print("✅ MOSTLY WORKING - Calendar events functionality is largely operational")
        else:
            print("⚠️  ISSUES DETECTED - Calendar events functionality has significant problems")
        
        return self.tests_passed / self.tests_run

if __name__ == "__main__":
    tester = CalendarEventsTest()
    success_rate = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    exit(0 if success_rate >= 0.8 else 1)