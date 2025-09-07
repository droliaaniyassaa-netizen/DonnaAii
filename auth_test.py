import requests
import sys
import json
import time
from datetime import datetime, timezone

class AuthenticationTester:
    def __init__(self, base_url="https://donna-ai-assist.emergent.host"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_token = None
        self.test_user_email = "testuser@example.com"
        self.test_user_password = "TestPass123"

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, auth_token=None):
        """Run a single API test with optional authentication"""
        url = f"{self.api_url}/{endpoint}"
        
        # Set up headers
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)
        
        # Add authentication if provided
        if auth_token:
            test_headers['Authorization'] = f'Bearer {auth_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if auth_token:
            print(f"   Auth: Bearer {auth_token[:20]}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

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

    def test_unauthenticated_access(self):
        """Test that protected endpoints return 401 without authentication"""
        print("\n" + "="*60)
        print("TESTING UNAUTHENTICATED ACCESS (SHOULD RETURN 401)")
        print("="*60)
        
        protected_endpoints = [
            ("Chat Endpoint", "POST", "chat", {"message": "Hello", "session_id": "test"}),
            ("Calendar Events", "GET", "calendar/events", None),
            ("Auth Me", "GET", "auth/me", None),
            ("Health Stats", "GET", "health/stats/test", None),
            ("User Settings", "GET", "user/settings/test", None),
            ("Career Goals", "GET", "career/goals", None),
            ("Chat History", "GET", "chat/history", None)
        ]
        
        unauthenticated_failures = 0
        
        for name, method, endpoint, data in protected_endpoints:
            success, response = self.run_test(
                f"Unauthenticated {name}",
                method,
                endpoint,
                401,  # Should return 401 Unauthorized
                data=data
            )
            
            if not success:
                unauthenticated_failures += 1
                print(f"🚨 SECURITY ISSUE: {name} allows unauthenticated access!")
        
        if unauthenticated_failures == 0:
            print(f"\n✅ ALL ENDPOINTS PROPERLY PROTECTED: {len(protected_endpoints)}/{len(protected_endpoints)} endpoints require authentication")
        else:
            print(f"\n🚨 SECURITY VULNERABILITIES FOUND: {unauthenticated_failures}/{len(protected_endpoints)} endpoints allow unauthenticated access")
        
        return unauthenticated_failures == 0

    def test_manual_registration(self):
        """Test manual user registration"""
        print("\n" + "="*60)
        print("TESTING MANUAL USER REGISTRATION")
        print("="*60)
        
        # Test registration with valid data
        registration_data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        success, response = self.run_test(
            "Manual User Registration",
            "POST",
            "auth/register",
            200,
            data=registration_data
        )
        
        if success:
            # Check response structure
            if response.get('session_token'):
                self.session_token = response['session_token']
                print(f"✅ Registration successful, session token received: {self.session_token[:20]}...")
            else:
                print("❌ Registration response missing session_token")
                return False
                
            if response.get('user'):
                user = response['user']
                if user.get('email') == self.test_user_email:
                    print("✅ User email matches registration data")
                else:
                    print(f"❌ User email mismatch: expected {self.test_user_email}, got {user.get('email')}")
            else:
                print("❌ Registration response missing user data")
                return False
        else:
            print("❌ Registration failed")
            return False
        
        # Test registration with invalid password (too short)
        invalid_data = {
            "email": "test2@example.com",
            "password": "123"  # Too short
        }
        
        success, response = self.run_test(
            "Registration with Invalid Password",
            "POST",
            "auth/register",
            422,  # Should return validation error
            data=invalid_data
        )
        
        if success:
            print("✅ Password validation working correctly")
        
        # Test registration with duplicate email
        success, response = self.run_test(
            "Registration with Duplicate Email",
            "POST",
            "auth/register",
            400,  # Should return error for duplicate
            data=registration_data
        )
        
        if success:
            print("✅ Duplicate email detection working")
        
        return True

    def test_manual_login(self):
        """Test manual user login"""
        print("\n" + "="*60)
        print("TESTING MANUAL USER LOGIN")
        print("="*60)
        
        # Test login with correct credentials
        login_data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        success, response = self.run_test(
            "Manual User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success:
            if response.get('session_token'):
                # Update session token from login
                self.session_token = response['session_token']
                print(f"✅ Login successful, session token received: {self.session_token[:20]}...")
            else:
                print("❌ Login response missing session_token")
                return False
        else:
            print("❌ Login failed")
            return False
        
        # Test login with wrong password
        wrong_password_data = {
            "email": self.test_user_email,
            "password": "WrongPassword123"
        }
        
        success, response = self.run_test(
            "Login with Wrong Password",
            "POST",
            "auth/login",
            401,  # Should return unauthorized
            data=wrong_password_data
        )
        
        if success:
            print("✅ Wrong password properly rejected")
        
        # Test login with non-existent email
        nonexistent_data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123"
        }
        
        success, response = self.run_test(
            "Login with Non-existent Email",
            "POST",
            "auth/login",
            401,  # Should return unauthorized
            data=nonexistent_data
        )
        
        if success:
            print("✅ Non-existent email properly rejected")
        
        return True

    def test_authenticated_access(self):
        """Test that authenticated requests work properly"""
        print("\n" + "="*60)
        print("TESTING AUTHENTICATED ACCESS")
        print("="*60)
        
        if not self.session_token:
            print("❌ No session token available for authenticated tests")
            return False
        
        # Test /auth/me endpoint
        success, response = self.run_test(
            "Auth Me Endpoint",
            "GET",
            "auth/me",
            200,
            auth_token=self.session_token
        )
        
        if success:
            if response.get('email') == self.test_user_email:
                print("✅ Auth me returns correct user data")
            else:
                print(f"❌ Auth me returns wrong user: expected {self.test_user_email}, got {response.get('email')}")
        
        # Test chat endpoint with authentication
        success, response = self.run_test(
            "Authenticated Chat",
            "POST",
            "chat",
            200,
            data={"message": "Hello Donna, this is an authenticated test", "session_id": "auth_test"},
            auth_token=self.session_token
        )
        
        if success:
            if response.get('response'):
                print("✅ Authenticated chat working")
            else:
                print("❌ Authenticated chat response missing")
        
        # Test calendar events with authentication
        success, response = self.run_test(
            "Authenticated Calendar Events",
            "GET",
            "calendar/events",
            200,
            auth_token=self.session_token
        )
        
        if success:
            print("✅ Authenticated calendar access working")
        
        # Test creating a calendar event
        event_data = {
            "title": "Auth Test Meeting",
            "description": "Testing authenticated event creation",
            "datetime_utc": datetime.now(timezone.utc).isoformat(),
            "category": "work",
            "reminder": True
        }
        
        success, response = self.run_test(
            "Create Calendar Event (Authenticated)",
            "POST",
            "calendar/events",
            200,
            data=event_data,
            auth_token=self.session_token
        )
        
        if success:
            if response.get('id'):
                print("✅ Authenticated event creation working")
                # Clean up - delete the test event
                event_id = response['id']
                self.run_test(
                    "Delete Test Event",
                    "DELETE",
                    f"calendar/events/{event_id}",
                    200,
                    auth_token=self.session_token
                )
            else:
                print("❌ Event creation response missing ID")
        
        return True

    def test_invalid_token_access(self):
        """Test that invalid tokens are properly rejected"""
        print("\n" + "="*60)
        print("TESTING INVALID TOKEN ACCESS")
        print("="*60)
        
        invalid_tokens = [
            "invalid_token_123",
            "Bearer invalid_token",
            "",
            "expired_token_xyz"
        ]
        
        for token in invalid_tokens:
            success, response = self.run_test(
                f"Invalid Token Test: '{token[:20]}...'",
                "GET",
                "auth/me",
                401,  # Should return unauthorized
                auth_token=token
            )
            
            if success:
                print(f"✅ Invalid token properly rejected")
            else:
                print(f"🚨 SECURITY ISSUE: Invalid token '{token[:20]}...' was accepted!")
        
        return True

    def test_session_isolation(self):
        """Test that users can only access their own data"""
        print("\n" + "="*60)
        print("TESTING SESSION ISOLATION")
        print("="*60)
        
        if not self.session_token:
            print("❌ No session token available for isolation tests")
            return False
        
        # Create a test event
        event_data = {
            "title": "Isolation Test Event",
            "description": "Testing session isolation",
            "datetime_utc": datetime.now(timezone.utc).isoformat(),
            "category": "personal",
            "reminder": False
        }
        
        success, response = self.run_test(
            "Create Event for Isolation Test",
            "POST",
            "calendar/events",
            200,
            data=event_data,
            auth_token=self.session_token
        )
        
        if success:
            # Get events with valid token
            success, user_events = self.run_test(
                "Get User's Own Events",
                "GET",
                "calendar/events",
                200,
                auth_token=self.session_token
            )
            
            if success:
                user_event_count = len(user_events)
                print(f"✅ User can access their own events: {user_event_count} events found")
                
                # Verify the test event is in the list
                test_event_found = any(event.get('title') == 'Isolation Test Event' for event in user_events)
                if test_event_found:
                    print("✅ Test event found in user's event list")
                else:
                    print("⚠️  Test event not found in user's event list")
                
                # Clean up - delete the test event
                if user_events:
                    for event in user_events:
                        if event.get('title') == 'Isolation Test Event':
                            self.run_test(
                                "Delete Isolation Test Event",
                                "DELETE",
                                f"calendar/events/{event['id']}",
                                200,
                                auth_token=self.session_token
                            )
                            break
        
        return True

    def run_all_tests(self):
        """Run all authentication tests"""
        print("🔐 DONNA AI AUTHENTICATION TESTING")
        print("="*60)
        print(f"Testing against: {self.base_url}")
        print("="*60)
        
        # Test 1: Unauthenticated access should be blocked
        unauthenticated_blocked = self.test_unauthenticated_access()
        
        # Test 2: Manual registration should work
        registration_works = self.test_manual_registration()
        
        # Test 3: Manual login should work
        login_works = self.test_manual_login()
        
        # Test 4: Authenticated access should work
        authenticated_works = self.test_authenticated_access()
        
        # Test 5: Invalid tokens should be rejected
        invalid_tokens_rejected = self.test_invalid_token_access()
        
        # Test 6: Session isolation should work
        session_isolation_works = self.test_session_isolation()
        
        # Summary
        print("\n" + "="*60)
        print("AUTHENTICATION TEST SUMMARY")
        print("="*60)
        
        total_tests = self.tests_run
        passed_tests = self.tests_passed
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n🔐 AUTHENTICATION SECURITY STATUS:")
        
        if unauthenticated_blocked:
            print("✅ PROTECTED: All endpoints require authentication")
        else:
            print("🚨 VULNERABLE: Some endpoints allow unauthenticated access")
        
        if registration_works:
            print("✅ WORKING: Manual user registration")
        else:
            print("❌ BROKEN: Manual user registration")
        
        if login_works:
            print("✅ WORKING: Manual user login")
        else:
            print("❌ BROKEN: Manual user login")
        
        if authenticated_works:
            print("✅ WORKING: Authenticated access to protected resources")
        else:
            print("❌ BROKEN: Authenticated access")
        
        if invalid_tokens_rejected:
            print("✅ SECURE: Invalid tokens properly rejected")
        else:
            print("🚨 VULNERABLE: Invalid tokens accepted")
        
        if session_isolation_works:
            print("✅ SECURE: Session isolation working")
        else:
            print("🚨 VULNERABLE: Session isolation broken")
        
        # Overall security assessment
        critical_issues = []
        if not unauthenticated_blocked:
            critical_issues.append("Unauthenticated access allowed")
        if not invalid_tokens_rejected:
            critical_issues.append("Invalid tokens accepted")
        if not session_isolation_works:
            critical_issues.append("Session isolation broken")
        
        print(f"\n🎯 OVERALL ASSESSMENT:")
        if len(critical_issues) == 0:
            print("✅ AUTHENTICATION SYSTEM IS SECURE AND WORKING PROPERLY")
        else:
            print("🚨 CRITICAL SECURITY ISSUES FOUND:")
            for issue in critical_issues:
                print(f"   - {issue}")
        
        return len(critical_issues) == 0

if __name__ == "__main__":
    tester = AuthenticationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)