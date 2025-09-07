#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime, timezone, timedelta

class NotificationTester:
    def __init__(self, base_url="https://donna-ai-assist.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = "push_test_session"

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

    def test_web_push_notifications(self):
        """Test Web Push Notification System Implementation"""
        print("\n" + "="*50)
        print("TESTING WEB PUSH NOTIFICATION SYSTEM")
        print("="*50)
        
        session_id = "push_test_session"
        
        print("\n📡 PHASE 1: VAPID KEY ENDPOINT")
        print("="*50)
        
        # Test VAPID public key endpoint
        success, vapid_response = self.run_test(
            "Get VAPID Public Key",
            "GET",
            "notifications/vapid-public-key",
            200
        )
        
        if not success:
            return False
            
        # Verify VAPID key structure
        if vapid_response.get('publicKey'):
            vapid_key = vapid_response['publicKey']
            print(f"✅ VAPID public key retrieved: {vapid_key[:20]}...")
            
            # Basic validation - VAPID keys should be base64url encoded
            if len(vapid_key) > 50:  # VAPID keys are typically 87+ characters
                print("✅ VAPID key has expected length")
            else:
                print(f"⚠️  VAPID key seems short: {len(vapid_key)} characters")
        else:
            print("❌ VAPID response missing publicKey field")
            return False
        
        print("\n📡 PHASE 2: PUSH SUBSCRIPTION MANAGEMENT")
        print("="*50)
        
        # Test creating push subscription
        subscription_data = {
            "session_id": session_id,
            "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint-123",
            "p256dh_key": "BArN-vYkz0YyLAd4vHqYvDH71LVa2CpGNKOXU_o7nkQRLiRjGz8qE8GCF5eiNECWpXLqKoNqmRQQwC_qzUWsjJI",
            "auth_key": "BLE9JpGPNVxQFb6M-8ZEGzZF4T8rrh4qD0bXK7u2LsI",
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
        if subscription.get('session_id') == session_id:
            print("✅ Subscription created with correct session_id")
        else:
            print(f"❌ Session ID mismatch: expected {session_id}, got {subscription.get('session_id')}")
            
        if subscription.get('endpoint') == subscription_data['endpoint']:
            print("✅ Endpoint stored correctly")
        else:
            print("❌ Endpoint not stored correctly")
            
        if subscription.get('p256dh_key') and subscription.get('auth_key'):
            print("✅ Encryption keys stored")
        else:
            print("❌ Encryption keys missing")
            
        if subscription.get('id') and subscription.get('created_at'):
            print("✅ Subscription has proper metadata")
        else:
            print("❌ Missing subscription metadata")
        
        print("\n📡 PHASE 3: NOTIFICATION SENDING")
        print("="*50)
        
        # Test sending notification with valid subscription
        notification_payload = {
            "title": "Test Notification",
            "body": "This is a test push notification from Donna",
            "icon": "/favicon.ico",
            "badge": "/favicon.ico", 
            "url": "/",
            "type": "general"
        }
        
        # Note: This will likely fail in testing environment since we don't have real push service
        # But we can test the endpoint structure and error handling
        success, send_response = self.run_test(
            f"Send Push Notification to {session_id}",
            "POST",
            f"notifications/send?session_id={session_id}",
            200,  # May return 400 due to invalid push service in test
            data=notification_payload
        )
        
        # The send might fail due to test environment, but endpoint should exist
        if not success:
            # Try again expecting 400 (which is acceptable for test environment)
            success, send_response = self.run_test(
                f"Send Push Notification (Expect Error)",
                "POST", 
                f"notifications/send?session_id={session_id}",
                400,  # Expected in test environment
                data=notification_payload
            )
            
            if success:
                print("✅ Send endpoint exists and handles invalid push services properly")
            else:
                print("❌ Send endpoint not working")
        else:
            print("✅ Notification sent successfully")
        
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
        
        print("\n📡 PHASE 4: NOTIFICATION SCHEDULING")
        print("="*50)
        
        # Test scheduling future notification
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        
        scheduled_notification_data = {
            "session_id": session_id,
            "event_id": "test_event_123",
            "title": "📅 Scheduled Reminder",
            "body": "This is your scheduled reminder",
            "scheduled_time": future_time.isoformat(),
            "notification_type": "reminder"
        }
        
        success, scheduled_notification = self.run_test(
            "Schedule Future Notification",
            "POST",
            "notifications/schedule",
            200,
            data=scheduled_notification_data
        )
        
        if not success:
            return False
            
        # Verify scheduled notification structure
        if scheduled_notification.get('session_id') == session_id:
            print("✅ Scheduled notification created with correct session_id")
        else:
            print("❌ Scheduled notification session_id mismatch")
            
        if scheduled_notification.get('title') == scheduled_notification_data['title']:
            print("✅ Scheduled notification title stored correctly")
        else:
            print("❌ Scheduled notification title incorrect")
            
        if scheduled_notification.get('notification_type') == 'reminder':
            print("✅ Notification type stored correctly")
        else:
            print("❌ Notification type incorrect")
            
        if scheduled_notification.get('sent') == False:
            print("✅ Scheduled notification marked as not sent")
        else:
            print("❌ Scheduled notification sent status incorrect")
        
        # Test getting scheduled notifications for session
        success, scheduled_list = self.run_test(
            "Get Scheduled Notifications",
            "GET",
            f"notifications/scheduled/{session_id}",
            200
        )
        
        if success:
            if len(scheduled_list) > 0:
                print(f"✅ Found {len(scheduled_list)} scheduled notifications")
                
                # Verify the notification we just created is in the list
                found_notification = False
                for notif in scheduled_list:
                    if notif.get('title') == scheduled_notification_data['title']:
                        found_notification = True
                        break
                        
                if found_notification:
                    print("✅ Scheduled notification found in list")
                else:
                    print("❌ Scheduled notification not found in list")
            else:
                print("⚠️  No scheduled notifications found")
        
        print("\n📡 PHASE 5: CALENDAR INTEGRATION")
        print("="*50)
        
        # Create calendar event with reminders enabled
        future_event_time = datetime.now(timezone.utc) + timedelta(hours=24)
        calendar_event_data = {
            "title": "Test Meeting with Notifications",
            "description": "Testing notification integration",
            "datetime_utc": future_event_time.isoformat(),
            "category": "work",
            "reminder": True
        }
        
        success, calendar_event = self.run_test(
            "Create Calendar Event with Reminders",
            "POST",
            "calendar/events",
            200,
            data=calendar_event_data
        )
        
        if success:
            time.sleep(2)  # Wait for notification scheduling
            
            # Check if notifications were scheduled
            success, updated_scheduled = self.run_test(
                "Check Scheduled Notifications After Event Creation",
                "GET",
                f"notifications/scheduled/default",  # Frontend events use default session
                200
            )
            
            if success:
                new_count = len(updated_scheduled)
                if new_count > 0:
                    print(f"✅ Notifications scheduled for calendar event")
                    
                    # Look for event-related notifications
                    event_notifications = [n for n in updated_scheduled 
                                         if n.get('event_id') or 'meeting' in n.get('body', '').lower()]
                    if event_notifications:
                        print(f"✅ Found {len(event_notifications)} event-related notifications")
                    else:
                        print("⚠️  No event-related notifications found")
                else:
                    print("⚠️  No notifications scheduled for calendar event")
        
        print("\n📡 PHASE 6: SUBSCRIPTION DELETION")
        print("="*50)
        
        # Test deleting push subscription
        success, delete_response = self.run_test(
            "Delete Push Subscription",
            "DELETE",
            f"notifications/subscription/{session_id}",
            200
        )
        
        if success:
            if delete_response.get('message'):
                print("✅ Subscription deleted successfully")
            else:
                print("❌ Delete response missing message")
        
        # Verify subscription is actually deleted
        success, send_response = self.run_test(
            "Send to Deleted Subscription",
            "POST",
            f"notifications/send?session_id={session_id}",
            404,  # Should return not found
            data=notification_payload
        )
        
        if success:
            print("✅ Proper 404 error for deleted subscription")
        
        return True

def main():
    print("🚀 Testing Web Push Notification System")
    print("=" * 60)
    
    tester = NotificationTester()
    
    try:
        success = tester.test_web_push_notifications()
        
        # Print final results
        print("\n" + "="*60)
        print("📊 WEB PUSH NOTIFICATION TEST RESULTS")
        print("="*60)
        print(f"Tests Run: {tester.tests_run}")
        print(f"Tests Passed: {tester.tests_passed}")
        print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
        print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
        
        if success and tester.tests_passed == tester.tests_run:
            print("🎉 All Web Push Notification tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed - check logs above")
            return 1
            
    except Exception as e:
        print(f"❌ Test suite failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())