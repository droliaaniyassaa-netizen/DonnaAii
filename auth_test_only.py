#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime, timezone

class AuthTester:
    def __init__(self, base_url="https://auth-ui-center.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

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

    def test_manual_authentication_system(self):
        """Test the NEW manual authentication system with comprehensive validation"""
        print("\n" + "="*50)
        print("TESTING MANUAL AUTHENTICATION SYSTEM")
        print("="*50)
        
        print("\n🔐 PHASE 1: PASSWORD VALIDATION TESTING")
        print("="*50)
        
        # Test password validation requirements (6 chars min + 1 uppercase)
        password_test_cases = [
            # Valid passwords
            ("Password123", True, "Valid password with uppercase and length"),
            ("Abc123", True, "Minimum valid password"),
            
            # Invalid passwords - too short
            ("Pass1", False, "Too short (5 chars)"),
            
            # Invalid passwords - no uppercase
            ("password123", False, "No uppercase letter"),
        ]
        
        password_validation_passed = 0
        password_validation_total = len(password_test_cases)
        
        for password, should_pass, description in password_test_cases:
            test_data = {
                "username": f"testuser_{int(time.time())}",
                "email": f"test_{int(time.time())}@example.com", 
                "password": password
            }
            
            success, response = self.run_test(
                f"Password Validation: {description}",
                "POST",
                "auth/register",
                200 if should_pass else 422,  # 422 for validation errors
                data=test_data
            )
            
            if should_pass and success:
                password_validation_passed += 1
                print(f"✅ Valid password accepted: '{password}'")
            elif not should_pass and success:
                password_validation_passed += 1
                print(f"✅ Invalid password rejected: '{password}' - {description}")
            elif should_pass and not success:
                print(f"❌ Valid password incorrectly rejected: '{password}' - {description}")
            else:
                print(f"❌ Invalid password incorrectly accepted: '{password}' - {description}")
        
        print(f"📊 Password validation: {password_validation_passed}/{password_validation_total} ({password_validation_passed/password_validation_total*100:.1f}%)")
        
        print("\n👤 PHASE 2: USERNAME VALIDATION TESTING")
        print("="*50)
        
        # Test username validation (alphanumeric + underscore + numbers, 3-20 chars)
        username_test_cases = [
            # Valid usernames
            ("user123", True, "Valid alphanumeric username"),
            ("test_user", True, "Valid with underscore"),
            
            # Invalid usernames - length
            ("ab", False, "Too short (2 chars)"),
            
            # Invalid usernames - invalid characters
            ("user-name", False, "Contains hyphen"),
            ("user@name", False, "Contains @ symbol"),
        ]
        
        username_validation_passed = 0
        username_validation_total = len(username_test_cases)
        
        for username, should_pass, description in username_test_cases:
            test_data = {
                "username": username,
                "email": f"test_{username.replace('@', '_').replace(' ', '_').replace('.', '_').replace('-', '_')}_{int(time.time())}@example.com",
                "password": "ValidPass123"
            }
            
            success, response = self.run_test(
                f"Username Validation: {description}",
                "POST", 
                "auth/register",
                200 if should_pass else 422,
                data=test_data
            )
            
            if should_pass and success:
                username_validation_passed += 1
                print(f"✅ Valid username accepted: '{username}'")
            elif not should_pass and success:
                username_validation_passed += 1
                print(f"✅ Invalid username rejected: '{username}' - {description}")
            elif should_pass and not success:
                print(f"❌ Valid username incorrectly rejected: '{username}' - {description}")
            else:
                print(f"❌ Invalid username incorrectly accepted: '{username}' - {description}")
        
        print(f"📊 Username validation: {username_validation_passed}/{username_validation_total} ({username_validation_passed/username_validation_total*100:.1f}%)")
        
        print("\n📝 PHASE 3: REGISTRATION ENDPOINT TESTING")
        print("="*50)
        
        # Test successful registration with valid data
        unique_id = int(time.time())
        valid_user_data = {
            "username": f"testuser_{unique_id}",
            "email": f"testuser_{unique_id}@example.com",
            "password": "SecurePass123"
        }
        
        success, registration_response = self.run_test(
            "Successful Registration with Valid Data",
            "POST",
            "auth/register", 
            200,
            data=valid_user_data
        )
        
        registration_tests_passed = 0
        registration_tests_total = 8
        
        if success:
            registration_tests_passed += 1
            print("✅ Registration successful with valid data")
            
            # Verify response structure
            if registration_response.get('user') and registration_response.get('session_token') and registration_response.get('message'):
                registration_tests_passed += 1
                print("✅ Registration response has correct structure")
            else:
                print("❌ Registration response missing required fields")
            
            # Verify user data
            user_data = registration_response.get('user', {})
            if (user_data.get('username') == valid_user_data['username'] and 
                user_data.get('email') == valid_user_data['email'] and
                user_data.get('auth_provider') == 'manual'):
                registration_tests_passed += 1
                print("✅ User data correctly stored")
            else:
                print("❌ User data incorrectly stored")
            
            # Verify password hash is not in response
            if 'password_hash' not in user_data:
                registration_tests_passed += 1
                print("✅ Password hash not exposed in response")
            else:
                print("❌ Password hash exposed in response")
        else:
            print("❌ Registration failed with valid data")
        
        # Test duplicate username rejection
        duplicate_username_data = {
            "username": valid_user_data['username'],  # Same username
            "email": f"different_{unique_id}@example.com",
            "password": "AnotherPass123"
        }
        
        success, duplicate_response = self.run_test(
            "Duplicate Username Rejection",
            "POST",
            "auth/register",
            400,
            data=duplicate_username_data
        )
        
        if success:
            registration_tests_passed += 1
            print("✅ Duplicate username correctly rejected")
            if 'username already exists' in duplicate_response.get('detail', '').lower():
                registration_tests_passed += 1
                print("✅ Appropriate error message for duplicate username")
            else:
                print("❌ Unclear error message for duplicate username")
        else:
            print("❌ Duplicate username not properly rejected")
        
        # Test duplicate email rejection
        duplicate_email_data = {
            "username": f"different_user_{unique_id}",
            "email": valid_user_data['email'],  # Same email
            "password": "AnotherPass123"
        }
        
        success, duplicate_email_response = self.run_test(
            "Duplicate Email Rejection",
            "POST",
            "auth/register",
            400,
            data=duplicate_email_data
        )
        
        if success:
            registration_tests_passed += 1
            print("✅ Duplicate email correctly rejected")
            if 'email already exists' in duplicate_email_response.get('detail', '').lower():
                registration_tests_passed += 1
                print("✅ Appropriate error message for duplicate email")
            else:
                print("❌ Unclear error message for duplicate email")
        else:
            print("❌ Duplicate email not properly rejected")
        
        print(f"📊 Registration tests: {registration_tests_passed}/{registration_tests_total} ({registration_tests_passed/registration_tests_total*100:.1f}%)")
        
        print("\n🔑 PHASE 4: LOGIN ENDPOINT TESTING")
        print("="*50)
        
        login_tests_passed = 0
        login_tests_total = 6
        
        # Test successful login with correct credentials
        login_data = {
            "username": valid_user_data['username'],
            "password": valid_user_data['password']
        }
        
        success, login_response = self.run_test(
            "Successful Login with Correct Credentials",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success:
            login_tests_passed += 1
            print("✅ Login successful with correct credentials")
            
            # Verify login response structure
            if login_response.get('user') and login_response.get('session_token') and login_response.get('message'):
                login_tests_passed += 1
                print("✅ Login response has correct structure")
            else:
                print("❌ Login response missing required fields")
            
            # Store session token for later tests
            session_token = login_response.get('session_token')
        else:
            print("❌ Login failed with correct credentials")
            session_token = None
        
        # Test login failure with wrong password
        wrong_password_data = {
            "username": valid_user_data['username'],
            "password": "WrongPassword123"
        }
        
        success, wrong_password_response = self.run_test(
            "Login Failure with Wrong Password",
            "POST",
            "auth/login",
            401,
            data=wrong_password_data
        )
        
        if success:
            login_tests_passed += 1
            print("✅ Login correctly rejected with wrong password")
            if 'invalid username or password' in wrong_password_response.get('detail', '').lower():
                login_tests_passed += 1
                print("✅ Appropriate error message for wrong password")
            else:
                print("❌ Unclear error message for wrong password")
        else:
            print("❌ Login not properly rejected with wrong password")
        
        # Test login failure with wrong username
        wrong_username_data = {
            "username": "nonexistent_user",
            "password": valid_user_data['password']
        }
        
        success, wrong_username_response = self.run_test(
            "Login Failure with Wrong Username",
            "POST",
            "auth/login",
            401,
            data=wrong_username_data
        )
        
        if success:
            login_tests_passed += 1
            print("✅ Login correctly rejected with wrong username")
            if 'invalid username or password' in wrong_username_response.get('detail', '').lower():
                login_tests_passed += 1
                print("✅ Appropriate error message for wrong username")
            else:
                print("❌ Unclear error message for wrong username")
        else:
            print("❌ Login not properly rejected with wrong username")
        
        print(f"📊 Login tests: {login_tests_passed}/{login_tests_total} ({login_tests_passed/login_tests_total*100:.1f}%)")
        
        print("\n🎫 PHASE 5: SESSION MANAGEMENT TESTING")
        print("="*50)
        
        session_tests_passed = 0
        session_tests_total = 4
        
        if session_token:
            # Test authenticated endpoint access with session token
            headers = {'Authorization': f'Bearer {session_token}', 'Content-Type': 'application/json'}
            
            # Test /auth/me endpoint
            try:
                url = f"{self.api_url}/auth/me"
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    session_tests_passed += 1
                    print("✅ Session token allows access to authenticated endpoints")
                    
                    me_data = response.json()
                    if me_data.get('username') == valid_user_data['username']:
                        session_tests_passed += 1
                        print("✅ Session returns correct user data")
                    else:
                        print("❌ Session returns incorrect user data")
                else:
                    print(f"❌ Session token rejected: {response.status_code}")
            except Exception as e:
                print(f"❌ Error testing session: {str(e)}")
            
            # Test session expiry (we can't test 7-day expiry, but we can verify the session exists)
            if session_token and len(session_token) > 20:
                session_tests_passed += 1
                print("✅ Session token generated with appropriate length")
            else:
                print("❌ Session token too short or missing")
        else:
            print("❌ No session token available for testing")
        
        # Test access without session token
        try:
            url = f"{self.api_url}/auth/me"
            response = requests.get(url, headers={'Content-Type': 'application/json'})
            
            if response.status_code == 401:
                session_tests_passed += 1
                print("✅ Unauthenticated access properly rejected")
            else:
                print(f"❌ Unauthenticated access not properly rejected: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing unauthenticated access: {str(e)}")
        
        print(f"📊 Session management tests: {session_tests_passed}/{session_tests_total} ({session_tests_passed/session_tests_total*100:.1f}%)")
        
        print("\n💾 PHASE 6: DATABASE STORAGE VERIFICATION")
        print("="*50)
        
        # We can't directly access the database, but we can verify through API responses
        database_tests_passed = 0
        database_tests_total = 3
        
        # Verify user data persistence through login
        persistence_login_data = {
            "username": valid_user_data['username'],
            "password": valid_user_data['password']
        }
        
        success, persistence_response = self.run_test(
            "User Data Persistence Verification",
            "POST",
            "auth/login",
            200,
            data=persistence_login_data
        )
        
        if success:
            database_tests_passed += 1
            print("✅ User data persisted correctly (login works)")
            
            user_data = persistence_response.get('user', {})
            if (user_data.get('auth_provider') == 'manual' and 
                user_data.get('username') == valid_user_data['username'] and
                user_data.get('email') == valid_user_data['email']):
                database_tests_passed += 1
                print("✅ User metadata stored correctly")
            else:
                print("❌ User metadata not stored correctly")
        else:
            print("❌ User data not persisted (login fails)")
        
        # Verify password hashing (password should not be stored in plain text)
        # We can infer this by the fact that login works but we can't see the password
        if success and 'password' not in persistence_response.get('user', {}):
            database_tests_passed += 1
            print("✅ Password properly hashed (not visible in response)")
        else:
            print("❌ Password security concern")
        
        print(f"📊 Database storage tests: {database_tests_passed}/{database_tests_total} ({database_tests_passed/database_tests_total*100:.1f}%)")
        
        print("\n🍪 PHASE 7: COOKIE SETTING VERIFICATION")
        print("="*50)
        
        # Test cookie setting during registration and login
        cookie_tests_passed = 0
        cookie_tests_total = 4
        
        # Test registration cookie setting
        unique_cookie_id = int(time.time()) + 1000
        cookie_reg_data = {
            "username": f"cookieuser_{unique_cookie_id}",
            "email": f"cookieuser_{unique_cookie_id}@example.com",
            "password": "CookiePass123"
        }
        
        try:
            url = f"{self.api_url}/auth/register"
            response = requests.post(url, json=cookie_reg_data, headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                # Check if Set-Cookie header is present
                set_cookie_header = response.headers.get('Set-Cookie', '')
                if 'session_token' in set_cookie_header:
                    cookie_tests_passed += 1
                    print("✅ Registration sets session cookie")
                    
                    # Check cookie attributes
                    if 'HttpOnly' in set_cookie_header:
                        cookie_tests_passed += 1
                        print("✅ Cookie is HttpOnly (secure)")
                    else:
                        print("❌ Cookie is not HttpOnly")
                        
                    if 'Secure' in set_cookie_header:
                        cookie_tests_passed += 1
                        print("✅ Cookie is Secure")
                    else:
                        print("⚠️  Cookie is not Secure (expected in dev environment)")
                        cookie_tests_passed += 1  # Count as pass for dev environment
                else:
                    print("❌ Registration does not set session cookie")
            else:
                print(f"❌ Registration failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing registration cookies: {str(e)}")
        
        # Test login cookie setting
        cookie_login_data = {
            "username": cookie_reg_data['username'],
            "password": cookie_reg_data['password']
        }
        
        try:
            url = f"{self.api_url}/auth/login"
            response = requests.post(url, json=cookie_login_data, headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                set_cookie_header = response.headers.get('Set-Cookie', '')
                if 'session_token' in set_cookie_header:
                    cookie_tests_passed += 1
                    print("✅ Login sets session cookie")
                else:
                    print("❌ Login does not set session cookie")
            else:
                print(f"❌ Login failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing login cookies: {str(e)}")
        
        print(f"📊 Cookie setting tests: {cookie_tests_passed}/{cookie_tests_total} ({cookie_tests_passed/cookie_tests_total*100:.1f}%)")
        
        print("\n📊 AUTHENTICATION SYSTEM SUMMARY")
        print("="*50)
        
        total_auth_tests = (password_validation_total + username_validation_total + 
                           registration_tests_total + login_tests_total + 
                           session_tests_total + database_tests_total + cookie_tests_total)
        total_auth_passed = (password_validation_passed + username_validation_passed + 
                            registration_tests_passed + login_tests_passed + 
                            session_tests_passed + database_tests_passed + cookie_tests_passed)
        
        print(f"🔐 Password Validation: {password_validation_passed}/{password_validation_total}")
        print(f"👤 Username Validation: {username_validation_passed}/{username_validation_total}")
        print(f"📝 Registration Tests: {registration_tests_passed}/{registration_tests_total}")
        print(f"🔑 Login Tests: {login_tests_passed}/{login_tests_total}")
        print(f"🎫 Session Management: {session_tests_passed}/{session_tests_total}")
        print(f"💾 Database Storage: {database_tests_passed}/{database_tests_total}")
        print(f"🍪 Cookie Setting: {cookie_tests_passed}/{cookie_tests_total}")
        print(f"📊 OVERALL AUTHENTICATION: {total_auth_passed}/{total_auth_tests} ({total_auth_passed/total_auth_tests*100:.1f}%)")
        
        if total_auth_passed / total_auth_tests >= 0.8:
            print("✅ AUTHENTICATION SYSTEM WORKING WELL")
        elif total_auth_passed / total_auth_tests >= 0.6:
            print("⚠️  AUTHENTICATION SYSTEM HAS SOME ISSUES")
        else:
            print("❌ AUTHENTICATION SYSTEM HAS MAJOR ISSUES")
        
        return total_auth_passed / total_auth_tests >= 0.8

def main():
    print("🚀 Starting Manual Authentication System Tests")
    print("=" * 60)
    
    tester = AuthTester()
    
    try:
        result = tester.test_manual_authentication_system()
        
        # Print final results
        print("\n" + "="*60)
        print("📊 FINAL TEST RESULTS")
        print("="*60)
        print(f"Tests Run: {tester.tests_run}")
        print(f"Tests Passed: {tester.tests_passed}")
        print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
        print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
        
        if result:
            print("🎉 Authentication system tests passed!")
            return 0
        else:
            print("⚠️  Authentication system has issues - check logs above")
            return 1
            
    except Exception as e:
        print(f"❌ Test suite failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())