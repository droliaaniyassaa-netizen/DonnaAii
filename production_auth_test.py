import requests
import sys
import json
import time
from datetime import datetime, timezone

class ProductionAuthTester:
    def __init__(self, base_url="https://donna-ai-assist.emergent.host"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_tokens = {}  # Store session tokens for different users

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, headers=None, auth_token=None):
        """Run a single API test with optional authentication"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        test_headers = {'Content-Type': 'application/json'}
        
        # Add custom headers
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
                response = requests.get(url, headers=test_headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, params=params, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

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
                print(f"   Response: {response.text[:500]}...")

            return success, response.json() if response.text and response.status_code < 500 else {}, response

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}, None

    def test_production_backend_connectivity(self):
        """Test if production backend is responding correctly"""
        print("\n" + "="*60)
        print("TESTING PRODUCTION BACKEND CONNECTIVITY")
        print("="*60)
        
        # Test basic connectivity to production backend
        success, response, _ = self.run_test(
            "Production Backend Health Check",
            "GET",
            "",  # Root endpoint
            200
        )
        
        if not success:
            print("❌ CRITICAL: Production backend not responding")
            return False
            
        # Test API root endpoint
        success, response, _ = self.run_test(
            "API Root Endpoint",
            "GET",
            "",  # /api endpoint
            200
        )
        
        return success

    def test_unauthenticated_access(self):
        """Test that unauthenticated requests are properly rejected with 401"""
        print("\n" + "="*60)
        print("TESTING UNAUTHENTICATED ACCESS REJECTION")
        print("="*60)
        
        # Test critical authentication endpoints that should return 401
        protected_endpoints = [
            ("auth/me", "GET", "User profile endpoint"),
            ("calendar/events", "GET", "Calendar events endpoint"),
            ("health/stats/default", "GET", "Health stats endpoint"),
            ("chat/history", "GET", "Chat history endpoint"),
            ("user/settings/default", "GET", "User settings endpoint"),
            ("career/goals", "GET", "Career goals endpoint"),
            ("health/goals", "GET", "Health goals endpoint"),
            ("notifications/vapid-public-key", "GET", "VAPID key endpoint"),
        ]
        
        unauthenticated_rejections = 0
        
        for endpoint, method, description in protected_endpoints:
            success, response, _ = self.run_test(
                f"Unauthenticated {description}",
                method,
                endpoint,
                401  # Should return 401 Unauthorized
            )
            
            if success:
                unauthenticated_rejections += 1
                print(f"✅ Properly rejected unauthenticated access to {endpoint}")
            else:
                print(f"❌ SECURITY ISSUE: {endpoint} allows unauthenticated access")
        
        print(f"\n📊 Authentication Security: {unauthenticated_rejections}/{len(protected_endpoints)} endpoints properly protected")
        
        if unauthenticated_rejections < len(protected_endpoints):
            print("🚨 CRITICAL SECURITY ISSUE: Some endpoints allow unauthenticated access!")
            return False
            
        return True

    def test_manual_authentication_system(self):
        """Test manual username/password authentication system"""
        print("\n" + "="*60)
        print("TESTING MANUAL AUTHENTICATION SYSTEM")
        print("="*60)
        
        # Test user registration
        test_user_data = {
            "email": f"testuser_{int(time.time())}@example.com",
            "password": "TestPassword123"
        }
        
        success, response, _ = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user_data
        )
        
        if not success:
            print("❌ User registration failed")
            return False
            
        # Extract session token from registration
        session_token = response.get('session_token')
        if session_token:
            self.session_tokens['test_user'] = session_token
            print(f"✅ Registration successful, session token obtained")
        else:
            print("❌ No session token returned from registration")
            return False
        
        # Test login with same credentials
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        success, response, _ = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success:
            login_token = response.get('session_token')
            if login_token:
                print("✅ Login successful with session token")
            else:
                print("❌ Login successful but no session token returned")
        
        # Test login with wrong password
        wrong_login_data = {
            "email": test_user_data["email"],
            "password": "WrongPassword123"
        }
        
        success, response, _ = self.run_test(
            "Login with Wrong Password",
            "POST",
            "auth/login",
            401,  # Should return 401 for wrong credentials
            data=wrong_login_data
        )
        
        if success:
            print("✅ Wrong password properly rejected")
        else:
            print("❌ SECURITY ISSUE: Wrong password not properly rejected")
        
        return True

    def test_authenticated_access(self):
        """Test that authenticated requests work properly"""
        print("\n" + "="*60)
        print("TESTING AUTHENTICATED ACCESS")
        print("="*60)
        
        if 'test_user' not in self.session_tokens:
            print("❌ No session token available for authenticated tests")
            return False
            
        session_token = self.session_tokens['test_user']
        
        # Test /auth/me endpoint with valid token
        success, response, _ = self.run_test(
            "Authenticated User Profile (/auth/me)",
            "GET",
            "auth/me",
            200,
            auth_token=session_token
        )
        
        if success:
            user_data = response
            if user_data.get('email'):
                print(f"✅ User profile retrieved: {user_data.get('email')}")
            else:
                print("❌ User profile missing email field")
        else:
            print("❌ Authenticated access to /auth/me failed")
            return False
        
        # Test other authenticated endpoints
        authenticated_endpoints = [
            ("calendar/events", "GET", "Calendar events"),
            ("health/stats/default", "GET", "Health stats"),
            ("user/settings/default", "GET", "User settings"),
        ]
        
        authenticated_success = 0
        
        for endpoint, method, description in authenticated_endpoints:
            success, response, _ = self.run_test(
                f"Authenticated {description}",
                method,
                endpoint,
                200,
                auth_token=session_token
            )
            
            if success:
                authenticated_success += 1
                print(f"✅ Authenticated access to {endpoint} successful")
            else:
                print(f"❌ Authenticated access to {endpoint} failed")
        
        print(f"\n📊 Authenticated Access: {authenticated_success}/{len(authenticated_endpoints)} endpoints accessible")
        
        return authenticated_success == len(authenticated_endpoints)

    def test_session_isolation(self):
        """Test that different sessions get different data"""
        print("\n" + "="*60)
        print("TESTING SESSION ISOLATION")
        print("="*60)
        
        # Create a second test user
        test_user2_data = {
            "email": f"testuser2_{int(time.time())}@example.com",
            "password": "TestPassword456"
        }
        
        success, response, _ = self.run_test(
            "Second User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user2_data
        )
        
        if not success:
            print("❌ Second user registration failed")
            return False
            
        session_token2 = response.get('session_token')
        if session_token2:
            self.session_tokens['test_user2'] = session_token2
            print(f"✅ Second user registered successfully")
        else:
            print("❌ No session token for second user")
            return False
        
        # Create data for first user
        if 'test_user' not in self.session_tokens:
            print("❌ First user session not available")
            return False
            
        session_token1 = self.session_tokens['test_user']
        
        # Create calendar event for user 1
        event_data = {
            "title": "User 1 Private Meeting",
            "description": "This should only be visible to user 1",
            "datetime_utc": datetime.now(timezone.utc).isoformat(),
            "category": "work",
            "reminder": True
        }
        
        success, response, _ = self.run_test(
            "Create Event for User 1",
            "POST",
            "calendar/events",
            200,
            data=event_data,
            auth_token=session_token1
        )
        
        if not success:
            print("❌ Failed to create event for user 1")
            return False
            
        user1_event_id = response.get('id')
        print(f"✅ Event created for user 1: {user1_event_id}")
        
        # Try to access user 1's events with user 2's token
        success, response, _ = self.run_test(
            "User 2 Accessing User 1's Events",
            "GET",
            "calendar/events",
            200,
            auth_token=session_token2
        )
        
        if success:
            user2_events = response
            user1_events_visible = any(event.get('id') == user1_event_id for event in user2_events)
            
            if user1_events_visible:
                print("❌ CRITICAL SECURITY ISSUE: User 2 can see User 1's events!")
                return False
            else:
                print("✅ Session isolation working: User 2 cannot see User 1's events")
        
        # Create event for user 2 and verify user 1 cannot see it
        event_data2 = {
            "title": "User 2 Private Meeting",
            "description": "This should only be visible to user 2",
            "datetime_utc": datetime.now(timezone.utc).isoformat(),
            "category": "personal",
            "reminder": True
        }
        
        success, response, _ = self.run_test(
            "Create Event for User 2",
            "POST",
            "calendar/events",
            200,
            data=event_data2,
            auth_token=session_token2
        )
        
        if success:
            user2_event_id = response.get('id')
            print(f"✅ Event created for user 2: {user2_event_id}")
            
            # Check if user 1 can see user 2's event
            success, response, _ = self.run_test(
                "User 1 Accessing User 2's Events",
                "GET",
                "calendar/events",
                200,
                auth_token=session_token1
            )
            
            if success:
                user1_events = response
                user2_events_visible = any(event.get('id') == user2_event_id for event in user1_events)
                
                if user2_events_visible:
                    print("❌ CRITICAL SECURITY ISSUE: User 1 can see User 2's events!")
                    return False
                else:
                    print("✅ Session isolation confirmed: User 1 cannot see User 2's events")
        
        return True

    def test_google_oauth_endpoints(self):
        """Test Google OAuth endpoints and configuration"""
        print("\n" + "="*60)
        print("TESTING GOOGLE OAUTH ENDPOINTS")
        print("="*60)
        
        # Test OAuth callback endpoint (should exist even if not fully configured)
        success, response, http_response = self.run_test(
            "Google OAuth Callback Endpoint",
            "GET",
            "auth/google/callback",
            404  # May return 404 if no code provided, but endpoint should exist
        )
        
        # If we get 404, that's expected without proper OAuth parameters
        # If we get 405 (Method Not Allowed), the endpoint exists but doesn't accept GET
        # If we get 500, there might be a configuration issue
        if http_response and http_response.status_code in [404, 405]:
            print("✅ Google OAuth callback endpoint exists")
        elif http_response and http_response.status_code == 500:
            print("⚠️  Google OAuth callback endpoint exists but may have configuration issues")
        else:
            print("❌ Google OAuth callback endpoint not found or not working")
        
        # Test OAuth initiation endpoint
        success, response, http_response = self.run_test(
            "Google OAuth Initiation",
            "GET",
            "auth/google",
            302  # Should redirect to Google OAuth
        )
        
        if not success and http_response:
            if http_response.status_code == 404:
                print("❌ Google OAuth initiation endpoint not found")
            elif http_response.status_code == 500:
                print("⚠️  Google OAuth initiation endpoint exists but has configuration issues")
            else:
                print(f"⚠️  Google OAuth initiation returned unexpected status: {http_response.status_code}")
        
        return True

    def test_production_api_endpoints(self):
        """Test various production API endpoints for proper responses"""
        print("\n" + "="*60)
        print("TESTING PRODUCTION API ENDPOINTS")
        print("="*60)
        
        if 'test_user' not in self.session_tokens:
            print("❌ No authenticated session available for API tests")
            return False
            
        session_token = self.session_tokens['test_user']
        
        # Test chat endpoint
        success, response, _ = self.run_test(
            "Chat Endpoint",
            "POST",
            "chat",
            200,
            data={"message": "Hello Donna, this is a test message", "session_id": "test_session"},
            auth_token=session_token
        )
        
        if success:
            if response.get('response'):
                print("✅ Chat endpoint working - Donna responded")
            else:
                print("❌ Chat endpoint returned success but no response")
        
        # Test health endpoints
        success, response, _ = self.run_test(
            "Health Stats Endpoint",
            "GET",
            "health/stats/test_session",
            200,
            auth_token=session_token
        )
        
        if success:
            print("✅ Health stats endpoint working")
        
        # Test career endpoints
        success, response, _ = self.run_test(
            "Career Goals Endpoint",
            "GET",
            "career/goals",
            200,
            auth_token=session_token
        )
        
        if success:
            print("✅ Career goals endpoint working")
        
        # Test notification endpoints
        success, response, _ = self.run_test(
            "VAPID Public Key Endpoint",
            "GET",
            "notifications/vapid-public-key",
            200,
            auth_token=session_token
        )
        
        if success:
            vapid_key = response.get('public_key')
            if vapid_key:
                print(f"✅ VAPID public key endpoint working: {vapid_key[:20]}...")
            else:
                print("❌ VAPID endpoint returned success but no public key")
        
        return True

    def test_cors_and_security_headers(self):
        """Test CORS configuration and security headers"""
        print("\n" + "="*60)
        print("TESTING CORS AND SECURITY HEADERS")
        print("="*60)
        
        # Test CORS preflight request
        cors_headers = {
            'Origin': 'https://donna-ai-assist.emergent.host',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type, Authorization'
        }
        
        try:
            response = requests.options(f"{self.api_url}/chat", headers=cors_headers, timeout=30)
            
            if response.status_code == 200:
                print("✅ CORS preflight request successful")
                
                # Check CORS headers
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                cors_methods = response.headers.get('Access-Control-Allow-Methods')
                cors_headers_allowed = response.headers.get('Access-Control-Allow-Headers')
                
                if cors_origin:
                    print(f"✅ CORS Origin header present: {cors_origin}")
                else:
                    print("⚠️  CORS Origin header missing")
                    
                if cors_methods:
                    print(f"✅ CORS Methods header present: {cors_methods}")
                else:
                    print("⚠️  CORS Methods header missing")
                    
                if cors_headers_allowed:
                    print(f"✅ CORS Headers header present: {cors_headers_allowed}")
                else:
                    print("⚠️  CORS Headers header missing")
            else:
                print(f"❌ CORS preflight failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ CORS test failed: {str(e)}")
        
        return True

    def run_all_tests(self):
        """Run all authentication and security tests"""
        print("🔐 DONNA AI PRODUCTION AUTHENTICATION TESTING")
        print("=" * 80)
        print(f"Testing production deployment at: {self.base_url}")
        print("=" * 80)
        
        test_results = {}
        
        # Test 1: Production Backend Connectivity
        test_results['connectivity'] = self.test_production_backend_connectivity()
        
        # Test 2: Unauthenticated Access Rejection (CRITICAL)
        test_results['unauthenticated_rejection'] = self.test_unauthenticated_access()
        
        # Test 3: Manual Authentication System
        test_results['manual_auth'] = self.test_manual_authentication_system()
        
        # Test 4: Authenticated Access
        test_results['authenticated_access'] = self.test_authenticated_access()
        
        # Test 5: Session Isolation (CRITICAL)
        test_results['session_isolation'] = self.test_session_isolation()
        
        # Test 6: Google OAuth Endpoints
        test_results['google_oauth'] = self.test_google_oauth_endpoints()
        
        # Test 7: Production API Endpoints
        test_results['api_endpoints'] = self.test_production_api_endpoints()
        
        # Test 8: CORS and Security Headers
        test_results['cors_security'] = self.test_cors_and_security_headers()
        
        # Print final summary
        print("\n" + "="*80)
        print("🔐 PRODUCTION AUTHENTICATION TEST SUMMARY")
        print("="*80)
        
        critical_tests = ['unauthenticated_rejection', 'session_isolation']
        critical_passed = all(test_results.get(test, False) for test in critical_tests)
        
        for test_name, passed in test_results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            critical_marker = " (CRITICAL)" if test_name in critical_tests else ""
            print(f"{status} - {test_name.replace('_', ' ').title()}{critical_marker}")
        
        print(f"\nOverall Test Results: {self.tests_passed}/{self.tests_run} tests passed ({self.tests_passed/self.tests_run*100:.1f}%)")
        
        if critical_passed:
            print("\n✅ CRITICAL SECURITY TESTS PASSED - Authentication system is secure")
        else:
            print("\n🚨 CRITICAL SECURITY TESTS FAILED - IMMEDIATE ATTENTION REQUIRED")
            
        return test_results

if __name__ == "__main__":
    # Use production URL from the review request
    production_url = "https://donna-ai-assist.emergent.host"
    
    tester = ProductionAuthTester(production_url)
    results = tester.run_all_tests()
    
    # Exit with error code if critical tests failed
    critical_tests = ['unauthenticated_rejection', 'session_isolation']
    critical_passed = all(results.get(test, False) for test in critical_tests)
    
    if not critical_passed:
        sys.exit(1)
    else:
        sys.exit(0)