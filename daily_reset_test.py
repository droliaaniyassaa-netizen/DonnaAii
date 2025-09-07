import requests
import sys
import json
import time
from datetime import datetime, timezone, timedelta

class DailyResetTester:
    def __init__(self, base_url="https://auth-ui-center.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = "daily_reset_test_session"

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

    def test_reset_endpoint_basic(self):
        """Test the basic reset endpoint functionality"""
        print("\n" + "="*60)
        print("TESTING RESET ENDPOINT - BASIC FUNCTIONALITY")
        print("="*60)
        
        # First, create some health data for today
        print("\n📊 Setting up health data for reset test...")
        
        # Add hydration via chat
        success, response = self.run_test(
            "Add Hydration Before Reset",
            "POST",
            "chat",
            200,
            data={"message": "I had 3 glasses of water", "session_id": self.session_id}
        )
        
        time.sleep(1)
        
        # Add meal via chat
        success, response = self.run_test(
            "Add Meal Before Reset",
            "POST",
            "chat",
            200,
            data={"message": "I ate a burger for lunch", "session_id": self.session_id}
        )
        
        time.sleep(1)
        
        # Add sleep via chat
        success, response = self.run_test(
            "Add Sleep Before Reset",
            "POST",
            "chat",
            200,
            data={"message": "I slept 8 hours", "session_id": self.session_id}
        )
        
        time.sleep(1)
        
        # Get current stats before reset
        success, stats_before_reset = self.run_test(
            "Get Stats Before Reset",
            "GET",
            f"health/stats/{self.session_id}",
            200
        )
        
        if success:
            print(f"📊 Stats before reset: Calories={stats_before_reset.get('calories', 0)}, "
                  f"Protein={stats_before_reset.get('protein', 0)}, "
                  f"Hydration={stats_before_reset.get('hydration', 0)}, "
                  f"Sleep={stats_before_reset.get('sleep', 0)}")
            
            # Verify we have data to reset
            if (stats_before_reset.get('calories', 0) > 0 or 
                stats_before_reset.get('hydration', 0) > 0 or 
                stats_before_reset.get('sleep', 0) > 0):
                print("✅ Health data successfully created for reset test")
            else:
                print("❌ No health data created - reset test may not be meaningful")
        
        # Test the reset endpoint
        success, reset_response = self.run_test(
            "Reset Daily Health Stats",
            "POST",
            f"health/stats/reset/{self.session_id}",
            200
        )
        
        if not success:
            return False
            
        # Verify reset response
        if reset_response.get('message') and reset_response.get('date'):
            print(f"✅ Reset response contains message and date: {reset_response['message']}")
            print(f"   Reset date: {reset_response['date']}")
        else:
            print("❌ Reset response missing required fields")
        
        # Get stats after reset
        success, stats_after_reset = self.run_test(
            "Get Stats After Reset",
            "GET",
            f"health/stats/{self.session_id}",
            200
        )
        
        if success:
            print(f"📊 Stats after reset: Calories={stats_after_reset.get('calories', 0)}, "
                  f"Protein={stats_after_reset.get('protein', 0)}, "
                  f"Hydration={stats_after_reset.get('hydration', 0)}, "
                  f"Sleep={stats_after_reset.get('sleep', 0)}")
            
            # Verify all stats are reset to 0
            if (stats_after_reset.get('calories', 0) == 0 and
                stats_after_reset.get('protein', 0) == 0 and
                stats_after_reset.get('hydration', 0) == 0 and
                stats_after_reset.get('sleep', 0) == 0):
                print("✅ All health stats successfully reset to 0")
            else:
                print("❌ Health stats not properly reset to 0")
        
        return True

    def test_reset_with_different_sessions(self):
        """Test reset endpoint with different session IDs to ensure isolation"""
        print("\n" + "="*60)
        print("TESTING RESET ENDPOINT - SESSION ISOLATION")
        print("="*60)
        
        session_a = "reset_test_session_a"
        session_b = "reset_test_session_b"
        
        # Add data to session A
        print(f"\n📊 Adding data to session A ({session_a})...")
        success, response = self.run_test(
            "Add Data to Session A",
            "POST",
            "chat",
            200,
            data={"message": "I had 2 glasses of water and ate pasta", "session_id": session_a}
        )
        
        time.sleep(1)
        
        # Add different data to session B
        print(f"\n📊 Adding data to session B ({session_b})...")
        success, response = self.run_test(
            "Add Data to Session B",
            "POST",
            "chat",
            200,
            data={"message": "I had a bottle of water and ate a sandwich", "session_id": session_b}
        )
        
        time.sleep(1)
        
        # Get stats for both sessions before reset
        success, stats_a_before = self.run_test(
            "Get Session A Stats Before Reset",
            "GET",
            f"health/stats/{session_a}",
            200
        )
        
        success, stats_b_before = self.run_test(
            "Get Session B Stats Before Reset",
            "GET",
            f"health/stats/{session_b}",
            200
        )
        
        if success:
            print(f"📊 Session A before: Hydration={stats_a_before.get('hydration', 0)}, Calories={stats_a_before.get('calories', 0)}")
            print(f"📊 Session B before: Hydration={stats_b_before.get('hydration', 0)}, Calories={stats_b_before.get('calories', 0)}")
        
        # Reset only session A
        success, reset_response = self.run_test(
            "Reset Session A Only",
            "POST",
            f"health/stats/reset/{session_a}",
            200
        )
        
        if not success:
            return False
        
        # Get stats for both sessions after reset
        success, stats_a_after = self.run_test(
            "Get Session A Stats After Reset",
            "GET",
            f"health/stats/{session_a}",
            200
        )
        
        success, stats_b_after = self.run_test(
            "Get Session B Stats After Reset",
            "GET",
            f"health/stats/{session_b}",
            200
        )
        
        if success:
            print(f"📊 Session A after: Hydration={stats_a_after.get('hydration', 0)}, Calories={stats_a_after.get('calories', 0)}")
            print(f"📊 Session B after: Hydration={stats_b_after.get('hydration', 0)}, Calories={stats_b_after.get('calories', 0)}")
            
            # Verify session A is reset
            if (stats_a_after.get('hydration', 0) == 0 and stats_a_after.get('calories', 0) == 0):
                print("✅ Session A successfully reset to 0")
            else:
                print("❌ Session A not properly reset")
            
            # Verify session B is unchanged
            if (stats_b_after.get('hydration', 0) == stats_b_before.get('hydration', 0) and
                stats_b_after.get('calories', 0) == stats_b_before.get('calories', 0)):
                print("✅ Session B data preserved (session isolation working)")
            else:
                print("❌ Session B data changed unexpectedly")
        
        return True

    def test_data_preservation_historical(self):
        """Test that reset preserves historical data in daily_health_stats"""
        print("\n" + "="*60)
        print("TESTING DATA PRESERVATION - HISTORICAL DATA")
        print("="*60)
        
        # This test simulates having data from previous days
        # Since we can't easily create historical data with different dates,
        # we'll test the reset behavior and verify it only affects today's data
        
        session_id = "historical_test_session"
        
        # Create some health data for today
        print("\n📊 Creating health data for today...")
        
        health_messages = [
            "I had 4 glasses of water",
            "I ate chicken and rice for dinner", 
            "I slept 7.5 hours last night"
        ]
        
        for message in health_messages:
            success, response = self.run_test(
                f"Add Health Data: '{message}'",
                "POST",
                "chat",
                200,
                data={"message": message, "session_id": session_id}
            )
            time.sleep(1)
        
        # Get today's stats before reset
        success, today_stats_before = self.run_test(
            "Get Today's Stats Before Reset",
            "GET",
            f"health/stats/{session_id}",
            200
        )
        
        if success:
            today_date = today_stats_before.get('date')
            print(f"📅 Today's date: {today_date}")
            print(f"📊 Today's stats before reset: Calories={today_stats_before.get('calories', 0)}, "
                  f"Protein={today_stats_before.get('protein', 0)}, "
                  f"Hydration={today_stats_before.get('hydration', 0)}, "
                  f"Sleep={today_stats_before.get('sleep', 0)}")
        
        # Perform reset
        success, reset_response = self.run_test(
            "Reset Today's Health Stats",
            "POST",
            f"health/stats/reset/{session_id}",
            200
        )
        
        if not success:
            return False
        
        # Verify reset worked for today
        success, today_stats_after = self.run_test(
            "Get Today's Stats After Reset",
            "GET",
            f"health/stats/{session_id}",
            200
        )
        
        if success:
            print(f"📊 Today's stats after reset: Calories={today_stats_after.get('calories', 0)}, "
                  f"Protein={today_stats_after.get('protein', 0)}, "
                  f"Hydration={today_stats_after.get('hydration', 0)}, "
                  f"Sleep={today_stats_after.get('sleep', 0)}")
            
            # Verify today's data is reset
            if (today_stats_after.get('calories', 0) == 0 and
                today_stats_after.get('protein', 0) == 0 and
                today_stats_after.get('hydration', 0) == 0 and
                today_stats_after.get('sleep', 0) == 0):
                print("✅ Today's stats successfully reset to 0")
            else:
                print("❌ Today's stats not properly reset")
            
            # Verify date remains the same (today)
            if today_stats_after.get('date') == today_date:
                print("✅ Date consistency maintained after reset")
            else:
                print(f"❌ Date changed unexpectedly: {today_date} -> {today_stats_after.get('date')}")
        
        # Test that we can add new data after reset
        print("\n📊 Testing new data addition after reset...")
        success, response = self.run_test(
            "Add New Data After Reset",
            "POST",
            "chat",
            200,
            data={"message": "I had a glass of water after the reset", "session_id": session_id}
        )
        
        time.sleep(1)
        
        # Verify new data is tracked
        success, stats_after_new_data = self.run_test(
            "Get Stats After Adding New Data",
            "GET",
            f"health/stats/{session_id}",
            200
        )
        
        if success:
            new_hydration = stats_after_new_data.get('hydration', 0)
            if new_hydration > 0:
                print(f"✅ New data tracked after reset: {new_hydration}ml hydration")
            else:
                print("❌ New data not tracked after reset")
        
        return True

    def test_date_handling_consistency(self):
        """Test date handling and formatting consistency"""
        print("\n" + "="*60)
        print("TESTING DATE HANDLING - CONSISTENCY")
        print("="*60)
        
        session_id = "date_test_session"
        
        # Get current stats to check date format
        success, current_stats = self.run_test(
            "Get Current Stats for Date Check",
            "GET",
            f"health/stats/{session_id}",
            200
        )
        
        if success:
            current_date = current_stats.get('date')
            print(f"📅 Current date format: {current_date}")
            
            # Verify date format is YYYY-MM-DD
            try:
                parsed_date = datetime.strptime(current_date, '%Y-%m-%d')
                print("✅ Date format is correct YYYY-MM-DD")
                
                # Verify it's today's date (UTC)
                today_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d')
                if current_date == today_utc:
                    print(f"✅ Date matches today's UTC date: {today_utc}")
                else:
                    print(f"⚠️  Date mismatch - Current: {current_date}, Expected: {today_utc}")
                    
            except ValueError:
                print(f"❌ Invalid date format: {current_date}")
        
        # Perform reset and check date consistency
        success, reset_response = self.run_test(
            "Reset for Date Consistency Check",
            "POST",
            f"health/stats/reset/{session_id}",
            200
        )
        
        if success:
            reset_date = reset_response.get('date')
            print(f"📅 Reset response date: {reset_date}")
            
            # Verify reset date format
            try:
                parsed_reset_date = datetime.strptime(reset_date, '%Y-%m-%d')
                print("✅ Reset date format is correct YYYY-MM-DD")
                
                # Verify reset date matches current date
                if reset_date == current_date:
                    print("✅ Reset date matches current date")
                else:
                    print(f"❌ Reset date mismatch: {reset_date} vs {current_date}")
                    
            except ValueError:
                print(f"❌ Invalid reset date format: {reset_date}")
        
        # Get stats after reset and verify date consistency
        success, stats_after_reset = self.run_test(
            "Get Stats After Reset for Date Check",
            "GET",
            f"health/stats/{session_id}",
            200
        )
        
        if success:
            final_date = stats_after_reset.get('date')
            print(f"📅 Final stats date: {final_date}")
            
            if final_date == reset_date:
                print("✅ Date consistency maintained throughout reset process")
            else:
                print(f"❌ Date inconsistency: {reset_date} -> {final_date}")
        
        return True

    def test_integration_with_health_logging(self):
        """Test that reset works properly with existing health logging system"""
        print("\n" + "="*60)
        print("TESTING INTEGRATION - HEALTH LOGGING SYSTEM")
        print("="*60)
        
        session_id = "integration_test_session"
        
        # Test complete workflow: Add data -> Reset -> Add more data -> Verify
        print("\n📊 Phase 1: Adding initial health data...")
        
        initial_messages = [
            "I had 2 glasses of water",
            "I ate a salad for lunch",
            "I slept 8 hours"
        ]
        
        for message in initial_messages:
            success, response = self.run_test(
                f"Initial Data: '{message}'",
                "POST",
                "chat",
                200,
                data={"message": message, "session_id": session_id}
            )
            time.sleep(1)
        
        # Get initial stats
        success, initial_stats = self.run_test(
            "Get Initial Stats",
            "GET",
            f"health/stats/{session_id}",
            200
        )
        
        if success:
            print(f"📊 Initial stats: Calories={initial_stats.get('calories', 0)}, "
                  f"Protein={initial_stats.get('protein', 0)}, "
                  f"Hydration={initial_stats.get('hydration', 0)}, "
                  f"Sleep={initial_stats.get('sleep', 0)}")
        
        print("\n🔄 Phase 2: Performing reset...")
        
        # Reset the stats
        success, reset_response = self.run_test(
            "Reset Stats",
            "POST",
            f"health/stats/reset/{session_id}",
            200
        )
        
        if not success:
            return False
        
        print("\n📊 Phase 3: Adding new health data after reset...")
        
        post_reset_messages = [
            "I had a bottle of water",
            "I ate pasta for dinner", 
            "I'm planning to sleep 7 hours tonight"
        ]
        
        for message in post_reset_messages:
            success, response = self.run_test(
                f"Post-Reset Data: '{message}'",
                "POST",
                "chat",
                200,
                data={"message": message, "session_id": session_id}
            )
            time.sleep(1)
        
        # Get final stats
        success, final_stats = self.run_test(
            "Get Final Stats After Reset and New Data",
            "GET",
            f"health/stats/{session_id}",
            200
        )
        
        if success:
            print(f"📊 Final stats: Calories={final_stats.get('calories', 0)}, "
                  f"Protein={final_stats.get('protein', 0)}, "
                  f"Hydration={final_stats.get('hydration', 0)}, "
                  f"Sleep={final_stats.get('sleep', 0)}")
            
            # Verify new data is properly tracked
            if (final_stats.get('hydration', 0) > 0 and 
                final_stats.get('calories', 0) > 0):
                print("✅ Health logging system working properly after reset")
            else:
                print("❌ Health logging system not working after reset")
            
            # Verify stats are different from initial (should be new data, not accumulated)
            if (final_stats.get('hydration', 0) != initial_stats.get('hydration', 0) or
                final_stats.get('calories', 0) != initial_stats.get('calories', 0)):
                print("✅ Reset successfully created fresh start (data not accumulated)")
            else:
                print("⚠️  Final stats match initial stats - may indicate reset didn't work")
        
        print("\n🔄 Phase 4: Testing undo functionality after reset...")
        
        # Test that undo works after reset
        success, response = self.run_test(
            "Test Undo After Reset",
            "POST",
            "chat",
            200,
            data={"message": "undo hydration", "session_id": session_id}
        )
        
        if success:
            donna_response = response.get('response', '')
            if any(word in donna_response.lower() for word in ['removed', 'undo', 'hydration']):
                print("✅ Undo functionality working after reset")
            else:
                print("⚠️  Undo functionality unclear after reset")
        
        return True

    def test_weekly_analytics_after_reset(self):
        """Test that weekly analytics can still access data after reset"""
        print("\n" + "="*60)
        print("TESTING INTEGRATION - WEEKLY ANALYTICS AFTER RESET")
        print("="*60)
        
        session_id = "analytics_test_session"
        
        # Add some health data
        print("\n📊 Adding health data for analytics test...")
        
        success, response = self.run_test(
            "Add Data for Analytics",
            "POST",
            "chat",
            200,
            data={"message": "I had 3 glasses of water and ate a burger", "session_id": session_id}
        )
        
        time.sleep(2)
        
        # Get weekly analytics before reset
        success, analytics_before = self.run_test(
            "Get Weekly Analytics Before Reset",
            "GET",
            f"health/analytics/weekly/{session_id}",
            200
        )
        
        if success:
            print(f"📊 Analytics before reset available: {bool(analytics_before.get('avg_calories', 0) > 0)}")
        
        # Perform reset
        success, reset_response = self.run_test(
            "Reset for Analytics Test",
            "POST",
            f"health/stats/reset/{session_id}",
            200
        )
        
        if not success:
            return False
        
        # Get weekly analytics after reset
        success, analytics_after = self.run_test(
            "Get Weekly Analytics After Reset",
            "GET",
            f"health/analytics/weekly/{session_id}",
            200
        )
        
        if success:
            print(f"📊 Analytics after reset available: {bool(analytics_after.get('avg_calories', 0) > 0)}")
            
            # Weekly analytics should still be accessible (they aggregate historical data)
            if analytics_after.get('session_id') == session_id:
                print("✅ Weekly analytics accessible after reset")
            else:
                print("❌ Weekly analytics not accessible after reset")
            
            # Check if analytics contain meaningful data structure
            if (analytics_after.get('week_start') and 
                analytics_after.get('week_end') and
                'avg_calories' in analytics_after):
                print("✅ Weekly analytics structure intact after reset")
            else:
                print("❌ Weekly analytics structure damaged after reset")
        
        # Test regenerating analytics after reset
        success, regenerated_analytics = self.run_test(
            "Regenerate Weekly Analytics After Reset",
            "POST",
            f"health/analytics/weekly/regenerate/{session_id}",
            200
        )
        
        if success:
            print("✅ Weekly analytics regeneration working after reset")
        else:
            print("❌ Weekly analytics regeneration failed after reset")
        
        return True

    def test_error_handling_reset(self):
        """Test error handling for reset endpoint"""
        print("\n" + "="*60)
        print("TESTING ERROR HANDLING - RESET ENDPOINT")
        print("="*60)
        
        # Test reset with non-existent session_id (should still work - creates new stats)
        success, response = self.run_test(
            "Reset Non-existent Session",
            "POST",
            "health/stats/reset/nonexistent_session_12345",
            200  # Should succeed and create new stats
        )
        
        if success:
            if response.get('message') and response.get('date'):
                print("✅ Reset works with non-existent session (creates new stats)")
            else:
                print("❌ Reset response incomplete for non-existent session")
        
        # Test multiple resets in same day (should be safe)
        session_id = "multiple_reset_test"
        
        # First reset
        success, first_reset = self.run_test(
            "First Reset of Day",
            "POST",
            f"health/stats/reset/{session_id}",
            200
        )
        
        if success:
            first_date = first_reset.get('date')
            print(f"📅 First reset date: {first_date}")
        
        # Add some data
        success, response = self.run_test(
            "Add Data Between Resets",
            "POST",
            "chat",
            200,
            data={"message": "I had a glass of water", "session_id": session_id}
        )
        
        time.sleep(1)
        
        # Second reset (same day)
        success, second_reset = self.run_test(
            "Second Reset Same Day",
            "POST",
            f"health/stats/reset/{session_id}",
            200
        )
        
        if success:
            second_date = second_reset.get('date')
            print(f"📅 Second reset date: {second_date}")
            
            if first_date == second_date:
                print("✅ Multiple resets in same day work safely")
            else:
                print("❌ Date inconsistency in multiple resets")
        
        # Verify stats are still reset after multiple resets
        success, final_stats = self.run_test(
            "Check Stats After Multiple Resets",
            "GET",
            f"health/stats/{session_id}",
            200
        )
        
        if success:
            if (final_stats.get('calories', 0) == 0 and
                final_stats.get('hydration', 0) == 0):
                print("✅ Stats properly reset after multiple resets")
            else:
                print("❌ Stats not properly reset after multiple resets")
        
        return True

    def test_timezone_handling_reset(self):
        """Test timezone handling in reset functionality"""
        print("\n" + "="*60)
        print("TESTING TIMEZONE HANDLING - RESET FUNCTIONALITY")
        print("="*60)
        
        session_id = "timezone_test_session"
        
        # The backend should work with UTC dates consistently
        # Test that reset uses proper UTC date handling
        
        # Get current UTC date
        utc_now = datetime.now(timezone.utc)
        utc_date_str = utc_now.strftime('%Y-%m-%d')
        
        print(f"🌍 Current UTC date: {utc_date_str}")
        print(f"🌍 Current UTC time: {utc_now.strftime('%H:%M:%S')}")
        
        # Perform reset
        success, reset_response = self.run_test(
            "Reset with UTC Timezone Check",
            "POST",
            f"health/stats/reset/{session_id}",
            200
        )
        
        if success:
            reset_date = reset_response.get('date')
            print(f"📅 Reset returned date: {reset_date}")
            
            # Verify reset date matches UTC date
            if reset_date == utc_date_str:
                print("✅ Reset uses correct UTC date")
            else:
                print(f"⚠️  Reset date mismatch - Expected: {utc_date_str}, Got: {reset_date}")
        
        # Get stats and verify date consistency
        success, stats = self.run_test(
            "Get Stats for Timezone Check",
            "GET",
            f"health/stats/{session_id}",
            200
        )
        
        if success:
            stats_date = stats.get('date')
            if stats_date == utc_date_str:
                print("✅ Stats date matches UTC date")
            else:
                print(f"❌ Stats date mismatch - Expected: {utc_date_str}, Got: {stats_date}")
        
        return True

def main():
    print("🌅 Starting Daily 6 AM Reset Functionality Tests")
    print("=" * 70)
    
    tester = DailyResetTester()
    
    # Run comprehensive reset tests
    test_suites = [
        tester.test_reset_endpoint_basic,
        tester.test_reset_with_different_sessions,
        tester.test_data_preservation_historical,
        tester.test_date_handling_consistency,
        tester.test_integration_with_health_logging,
        tester.test_weekly_analytics_after_reset,
        tester.test_error_handling_reset,
        tester.test_timezone_handling_reset
    ]
    
    for test_suite in test_suites:
        try:
            test_suite()
        except Exception as e:
            print(f"❌ Test suite failed with error: {str(e)}")
    
    # Print final results
    print("\n" + "="*70)
    print("📊 DAILY RESET TEST RESULTS")
    print("="*70)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All daily reset tests passed!")
        return 0
    else:
        print("⚠️  Some daily reset tests failed - check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())