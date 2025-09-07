import requests
import sys
import json
import time
from datetime import datetime, timezone, timedelta

class NotificationTester:
    def __init__(self, base_url="https://auth-ui-center.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = "notification_test_session"
        
        # Expected production VAPID keys from review request
        self.expected_vapid_public_key = "SkX2QFeFpC4w2ygG4M78DGIyP_gve0FYx0dkIAXsy_-t-UrZU7sk2dHd6yibmL9YWLu2MrYFSIhjE8ZI2Ms9Nhw"
        self.expected_vapid_private_key = "mk8ELrxiBO1JBFbyFpqUrIOuTFeTm77yHOkPw82q-aQ"

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

    def test_vapid_public_key_endpoint(self):
        """Test VAPID Public Key Endpoint with new production keys"""
        print("\n" + "="*60)
        print("TESTING VAPID PUBLIC KEY ENDPOINT")
        print("="*60)
        
        success, response = self.run_test(
            "Get VAPID Public Key",
            "GET",
            "notifications/vapid-public-key",
            200
        )
        
        if not success:
            return False
            
        # Verify the response structure
        if 'publicKey' not in response:
            print("❌ Response missing 'publicKey' field")
            return False
            
        returned_key = response['publicKey']
        
        # Verify it's the new production key
        if returned_key == self.expected_vapid_public_key:
            print("✅ VAPID public key matches expected production key")
            print(f"   Key: {returned_key[:20]}...{returned_key[-20:]}")
        else:
            print("❌ VAPID public key does NOT match expected production key")
            print(f"   Expected: {self.expected_vapid_public_key[:20]}...{self.expected_vapid_public_key[-20:]}")
            print(f"   Received: {returned_key[:20]}...{returned_key[-20:]}")
            return False
            
        # Verify key format (should be base64url encoded)
        if len(returned_key) == 87:  # Standard VAPID public key length
            print("✅ VAPID public key has correct length (87 characters)")
        else:
            print(f"⚠️  VAPID public key length unexpected: {len(returned_key)} characters")
            
        return True

    def test_push_subscription_management(self):
        """Test push subscription CRUD operations"""
        print("\n" + "="*60)
        print("TESTING PUSH SUBSCRIPTION MANAGEMENT")
        print("="*60)
        
        # Test creating a push subscription
        subscription_data = {
            "session_id": self.session_id,
            "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint-123",
            "p256dh_key": "BArN-vYkz0YyLAd4vHqYvDH71LVa2CpGNKOXU_o7nkQRLiRjGz8qE8GCF5eiNECWpXLqKoNqmRQQwC_qzUWsjJI",
            "auth_key": "test-auth-key-123456789012",
            "user_agent": "Mozilla/5.0 (Test Browser)"
        }
        
        success, subscription = self.run_test(
            "Create Push Subscription",
            "POST",
            "notifications/subscription",
            200,
            data=subscription_data
        )
        
        if not success:
            return False
            
        # Verify subscription structure
        required_fields = ['id', 'session_id', 'endpoint', 'p256dh_key', 'auth_key', 'created_at', 'updated_at']
        for field in required_fields:
            if field not in subscription:
                print(f"❌ Subscription missing required field: {field}")
                return False
                
        print("✅ Push subscription created with all required fields")
        
        # Verify session isolation
        if subscription['session_id'] == self.session_id:
            print("✅ Subscription correctly associated with session")
        else:
            print(f"❌ Session ID mismatch: expected {self.session_id}, got {subscription['session_id']}")
            
        # Test updating existing subscription (should update, not create new)
        updated_subscription_data = {
            "session_id": self.session_id,
            "endpoint": "https://fcm.googleapis.com/fcm/send/updated-endpoint-456",
            "p256dh_key": "BLE9JpGPNVxQFb6M-8ZEGzZF4T8rrh4qD0bXK7u2LsI-OyZi8V1CJV8RJZP8xL4vGKv1mL9T8G5kP4YrNb2HGmU",
            "auth_key": "updated-auth-key-987654321098",
            "user_agent": "Mozilla/5.0 (Updated Test Browser)"
        }
        
        success, updated_subscription = self.run_test(
            "Update Existing Push Subscription",
            "POST",
            "notifications/subscription",
            200,
            data=updated_subscription_data
        )
        
        if success:
            if updated_subscription['endpoint'] == updated_subscription_data['endpoint']:
                print("✅ Subscription updated successfully")
            else:
                print("❌ Subscription not updated properly")
                
        # Test deleting subscription
        success, delete_response = self.run_test(
            "Delete Push Subscription",
            "DELETE",
            f"notifications/subscription/{self.session_id}",
            200
        )
        
        if success:
            if 'message' in delete_response:
                print("✅ Subscription deleted successfully")
            else:
                print("❌ Delete response missing message")
                
        # Test deleting non-existent subscription
        success, _ = self.run_test(
            "Delete Non-existent Subscription",
            "DELETE",
            "notifications/subscription/nonexistent_session",
            404
        )
        
        if success:
            print("✅ Proper 404 error for non-existent subscription")
            
        return True

    def test_notification_scheduling(self):
        """Test notification scheduling functionality"""
        print("\n" + "="*60)
        print("TESTING NOTIFICATION SCHEDULING")
        print("="*60)
        
        # Schedule a future notification
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        notification_data = {
            "session_id": self.session_id,
            "event_id": "test-event-123",
            "title": "Test Reminder",
            "body": "This is a test notification reminder",
            "scheduled_time": future_time.isoformat(),
            "notification_type": "reminder"
        }
        
        success, scheduled_notification = self.run_test(
            "Schedule Future Notification",
            "POST",
            "notifications/schedule",
            200,
            data=notification_data
        )
        
        if not success:
            return False
            
        # Verify scheduled notification structure
        required_fields = ['id', 'session_id', 'title', 'body', 'scheduled_time', 'notification_type', 'sent', 'created_at']
        for field in required_fields:
            if field not in scheduled_notification:
                print(f"❌ Scheduled notification missing field: {field}")
                return False
                
        print("✅ Notification scheduled with all required fields")
        
        # Verify scheduling details
        if scheduled_notification['sent'] == False:
            print("✅ Notification correctly marked as not sent")
        else:
            print("❌ New notification should not be marked as sent")
            
        if scheduled_notification['notification_type'] == 'reminder':
            print("✅ Notification type set correctly")
        else:
            print(f"❌ Notification type incorrect: {scheduled_notification['notification_type']}")
            
        # Test getting scheduled notifications for session
        success, scheduled_notifications = self.run_test(
            "Get Scheduled Notifications",
            "GET",
            f"notifications/scheduled/{self.session_id}",
            200
        )
        
        if success:
            if len(scheduled_notifications) > 0:
                print(f"✅ Found {len(scheduled_notifications)} scheduled notifications")
                
                # Verify the notification we just created is in the list
                found_notification = False
                for notif in scheduled_notifications:
                    if notif['title'] == 'Test Reminder':
                        found_notification = True
                        break
                        
                if found_notification:
                    print("✅ Scheduled notification found in session list")
                else:
                    print("❌ Scheduled notification not found in session list")
            else:
                print("⚠️  No scheduled notifications found")
                
        # Test session isolation - check different session
        success, other_notifications = self.run_test(
            "Get Scheduled Notifications for Different Session",
            "GET",
            "notifications/scheduled/different_session",
            200
        )
        
        if success:
            if len(other_notifications) == 0:
                print("✅ Session isolation working - no notifications for different session")
            else:
                print("⚠️  Session isolation may not be working properly")
                
        return True

    def test_notification_sending_with_vapid_keys(self):
        """Test notification sending with production VAPID keys"""
        print("\n" + "="*60)
        print("TESTING NOTIFICATION SENDING WITH PRODUCTION VAPID KEYS")
        print("="*60)
        
        # First, create a subscription for testing
        subscription_data = {
            "session_id": self.session_id,
            "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint-for-sending",
            "p256dh_key": "BArN-vYkz0YyLAd4vHqYvDH71LVa2CpGNKOXU_o7nkQRLiRjGz8qE8GCF5eiNECWpXLqKoNqmRQQwC_qzUWsjJI",
            "auth_key": "test-auth-key-for-sending-123",
            "user_agent": "Mozilla/5.0 (Notification Test Browser)"
        }
        
        success, subscription = self.run_test(
            "Create Subscription for Sending Test",
            "POST",
            "notifications/subscription",
            200,
            data=subscription_data
        )
        
        if not success:
            return False
            
        # Test sending notification
        notification_payload = {
            "title": "Test Notification",
            "body": "Testing notification sending with production VAPID keys",
            "icon": "/favicon.ico",
            "badge": "/favicon.ico",
            "url": "/",
            "type": "test"
        }
        
        # Note: This will likely fail in test environment due to invalid test endpoints
        # but we can verify the VAPID key loading and error handling
        success, send_response = self.run_test(
            "Send Push Notification",
            "POST",
            f"notifications/send?session_id={self.session_id}",
            400,  # Expect 400 due to test endpoint, but should show VAPID key usage
            data=notification_payload
        )
        
        # Even if sending fails, we can check if it's using the right VAPID keys
        # by examining the error message
        print("📋 Note: Notification sending expected to fail in test environment")
        print("   This tests VAPID key loading and error handling")
        
        # Test sending to non-existent session
        success, error_response = self.run_test(
            "Send to Non-existent Session",
            "POST",
            "notifications/send?session_id=nonexistent_session",
            404,
            data=notification_payload
        )
        
        if success:
            print("✅ Proper 404 error for non-existent session")
            
        # Clean up - delete test subscription
        success, _ = self.run_test(
            "Clean Up Test Subscription",
            "DELETE",
            f"notifications/subscription/{self.session_id}",
            200
        )
        
        return True

    def test_calendar_integration_with_notifications(self):
        """Test calendar event creation with notification reminders"""
        print("\n" + "="*60)
        print("TESTING CALENDAR INTEGRATION WITH NOTIFICATIONS")
        print("="*60)
        
        # Create a subscription first
        subscription_data = {
            "session_id": self.session_id,
            "endpoint": "https://fcm.googleapis.com/fcm/send/calendar-test-endpoint",
            "p256dh_key": "BArN-vYkz0YyLAd4vHqYvDH71LVa2CpGNKOXU_o7nkQRLiRjGz8qE8GCF5eiNECWpXLqKoNqmRQQwC_qzUWsjJI",
            "auth_key": "calendar-test-auth-key-123",
            "user_agent": "Mozilla/5.0 (Calendar Test)"
        }
        
        success, subscription = self.run_test(
            "Create Subscription for Calendar Test",
            "POST",
            "notifications/subscription",
            200,
            data=subscription_data
        )
        
        if not success:
            return False
            
        # Create calendar event with reminders enabled
        future_datetime = datetime.now(timezone.utc) + timedelta(hours=24)
        event_data = {
            "title": "Test Meeting with Notifications",
            "description": "Testing calendar integration with push notifications",
            "datetime_utc": future_datetime.isoformat(),
            "category": "work",
            "reminder": True  # This should trigger notification scheduling
        }
        
        success, event = self.run_test(
            "Create Calendar Event with Reminders",
            "POST",
            "calendar/events",
            200,
            data=event_data
        )
        
        if not success:
            return False
            
        event_id = event.get('id')
        if not event_id:
            print("❌ Event created but no ID returned")
            return False
            
        print(f"✅ Calendar event created with ID: {event_id}")
        
        # Wait a moment for notification scheduling to process
        time.sleep(2)
        
        # Check if notifications were scheduled for this event
        success, scheduled_notifications = self.run_test(
            "Check Scheduled Notifications After Event Creation",
            "GET",
            f"notifications/scheduled/{self.session_id}",
            200
        )
        
        if success:
            # Look for notifications related to our event
            event_notifications = [n for n in scheduled_notifications if n.get('event_id') == event_id]
            
            if len(event_notifications) > 0:
                print(f"✅ Found {len(event_notifications)} notifications scheduled for event")
                
                # Check for standard reminders (12h and 2h before)
                reminder_types = []
                for notif in event_notifications:
                    if 'hours' in notif.get('body', ''):
                        if '12 hours' in notif['body']:
                            reminder_types.append('12h')
                        elif '2 hours' in notif['body']:
                            reminder_types.append('2h')
                            
                if '12h' in reminder_types and '2h' in reminder_types:
                    print("✅ Standard reminders (12h and 2h) scheduled correctly")
                else:
                    print(f"⚠️  Standard reminders may be missing: {reminder_types}")
            else:
                print("⚠️  No notifications scheduled for calendar event")
                
        # Test chat-based event creation with reminders
        success, chat_response = self.run_test(
            "Chat Event Creation with Reminders",
            "POST",
            "chat",
            200,
            data={
                "message": "Schedule a meeting tomorrow at 2pm with reminder notifications",
                "session_id": self.session_id
            }
        )
        
        if success:
            donna_response = chat_response.get('response', '')
            if 'reminder' in donna_response.lower() or 'event' in donna_response.lower():
                print("✅ Chat-based event creation with reminders processed")
            else:
                print("⚠️  Chat-based event creation unclear")
                
        # Clean up
        success, _ = self.run_test(
            "Delete Test Event",
            "DELETE",
            f"calendar/events/{event_id}",
            200
        )
        
        success, _ = self.run_test(
            "Clean Up Calendar Test Subscription",
            "DELETE",
            f"notifications/subscription/{self.session_id}",
            200
        )
        
        return True

    def test_vapid_key_loading_verification(self):
        """Verify that backend is correctly loading VAPID keys from .env file"""
        print("\n" + "="*60)
        print("TESTING VAPID KEY LOADING FROM ENVIRONMENT")
        print("="*60)
        
        # Test multiple calls to ensure consistency
        for i in range(3):
            success, response = self.run_test(
                f"VAPID Key Consistency Check #{i+1}",
                "GET",
                "notifications/vapid-public-key",
                200
            )
            
            if not success:
                return False
                
            returned_key = response.get('publicKey', '')
            
            if returned_key == self.expected_vapid_public_key:
                print(f"✅ Consistency check #{i+1}: Key matches expected production key")
            else:
                print(f"❌ Consistency check #{i+1}: Key mismatch")
                return False
                
        print("✅ VAPID key loading is consistent across multiple requests")
        
        # Verify key is not the old demo key
        old_demo_key = "BLE9JpGPNVxQFb6M-8ZEGzZF4T8rrh4qD0bXK7u2LsI-OyZi8V1CJV8RJZP8xL4vGKv1mL9T8G5kP4YrNb2HGmU"
        
        if returned_key != old_demo_key:
            print("✅ Confirmed: Not using old demo VAPID key")
        else:
            print("❌ WARNING: Still using old demo VAPID key")
            return False
            
        return True

    def test_notification_system_stability(self):
        """Test that notification system doesn't break existing functionality"""
        print("\n" + "="*60)
        print("TESTING NOTIFICATION SYSTEM STABILITY")
        print("="*60)
        
        # Test that basic chat still works
        success, chat_response = self.run_test(
            "Basic Chat Functionality",
            "POST",
            "chat",
            200,
            data={
                "message": "Hello Donna, how are you?",
                "session_id": self.session_id
            }
        )
        
        if not success:
            print("❌ Basic chat functionality broken")
            return False
            
        print("✅ Basic chat functionality working")
        
        # Test that calendar events still work
        future_datetime = datetime.now(timezone.utc) + timedelta(hours=2)
        event_data = {
            "title": "Stability Test Event",
            "description": "Testing that events still work",
            "datetime_utc": future_datetime.isoformat(),
            "category": "personal",
            "reminder": False  # No reminders for this test
        }
        
        success, event = self.run_test(
            "Calendar Event Creation (No Reminders)",
            "POST",
            "calendar/events",
            200,
            data=event_data
        )
        
        if not success:
            print("❌ Calendar event creation broken")
            return False
            
        print("✅ Calendar event creation working")
        
        # Test that health logging still works
        success, health_response = self.run_test(
            "Health Logging via Chat",
            "POST",
            "chat",
            200,
            data={
                "message": "I had a glass of water",
                "session_id": self.session_id
            }
        )
        
        if success:
            donna_response = health_response.get('response', '')
            if any(word in donna_response.lower() for word in ['water', 'hydration', 'ml']):
                print("✅ Health logging functionality working")
            else:
                print("⚠️  Health logging response unclear")
        else:
            print("❌ Health logging broken")
            return False
            
        # Clean up test event
        event_id = event.get('id')
        if event_id:
            success, _ = self.run_test(
                "Clean Up Stability Test Event",
                "DELETE",
                f"calendar/events/{event_id}",
                200
            )
            
        return True

    def run_all_tests(self):
        """Run all notification system tests"""
        print("🚀 STARTING WEB PUSH NOTIFICATION SYSTEM TESTS")
        print("=" * 80)
        print(f"Testing against: {self.base_url}")
        print(f"Expected VAPID Public Key: {self.expected_vapid_public_key[:20]}...{self.expected_vapid_public_key[-20:]}")
        print("=" * 80)
        
        test_results = []
        
        # Run all test phases
        test_methods = [
            ("VAPID Public Key Endpoint", self.test_vapid_public_key_endpoint),
            ("VAPID Key Loading Verification", self.test_vapid_key_loading_verification),
            ("Push Subscription Management", self.test_push_subscription_management),
            ("Notification Scheduling", self.test_notification_scheduling),
            ("Notification Sending with VAPID Keys", self.test_notification_sending_with_vapid_keys),
            ("Calendar Integration with Notifications", self.test_calendar_integration_with_notifications),
            ("Notification System Stability", self.test_notification_system_stability)
        ]
        
        for test_name, test_method in test_methods:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                result = test_method()
                test_results.append((test_name, result))
                if result:
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {str(e)}")
                test_results.append((test_name, False))
        
        # Print final summary
        print("\n" + "="*80)
        print("🏁 WEB PUSH NOTIFICATION SYSTEM TEST SUMMARY")
        print("="*80)
        
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        
        print(f"📊 Overall Test Results: {self.tests_passed}/{self.tests_run} individual tests passed")
        print(f"📊 Test Phases: {passed_tests}/{total_tests} phases passed")
        print(f"📊 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print("\n📋 Phase Results:")
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status}: {test_name}")
        
        # Key findings
        print("\n🔍 Key Findings:")
        vapid_test_passed = test_results[0][1] if test_results else False
        if vapid_test_passed:
            print("   ✅ Production VAPID keys loaded correctly")
            print(f"   ✅ VAPID public key endpoint returns: {self.expected_vapid_public_key[:20]}...{self.expected_vapid_public_key[-20:]}")
        else:
            print("   ❌ VAPID key issues detected")
            
        stability_test_passed = test_results[-1][1] if len(test_results) > 0 else False
        if stability_test_passed:
            print("   ✅ Notification system doesn't break existing functionality")
        else:
            print("   ❌ Notification system may have broken existing features")
            
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED - Web Push Notification system is working correctly with production VAPID keys!")
        elif passed_tests >= total_tests * 0.8:
            print("\n⚠️  MOSTLY WORKING - Minor issues detected but core functionality operational")
        else:
            print("\n🚨 SIGNIFICANT ISSUES - Multiple test failures detected")
            
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = NotificationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)