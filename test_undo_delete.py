#!/usr/bin/env python3
"""
Focused test for Enhanced Health Undo/Delete Functionality
Tests the new chat-based delete commands and undo API endpoints
"""

import requests
import sys
import json
import time
from datetime import datetime, timezone

class HealthUndoDeleteTester:
    def __init__(self, base_url="https://donna-companion.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = "undo_delete_test"

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

    def test_complete_health_workflow(self):
        """Test complete health logging and undo workflow"""
        print("\n" + "="*60)
        print("TESTING COMPLETE HEALTH WORKFLOW WITH UNDO/DELETE")
        print("="*60)
        
        # Reset stats for clean test
        success, reset_response = self.run_test(
            "Reset Stats for Clean Test",
            "POST",
            f"health/stats/reset/{self.session_id}",
            200
        )
        
        if not success:
            print("❌ Failed to reset stats - aborting test")
            return False
        
        print("\n🔄 STEP 1: Log hydration and verify")
        success, response = self.run_test(
            "Log Hydration via Chat",
            "POST",
            "chat",
            200,
            data={"message": "I had a glass of water", "session_id": self.session_id}
        )
        
        if success:
            donna_response = response.get('response', '')
            print(f"   Donna: {donna_response[:100]}...")
        
        time.sleep(2)  # Allow processing
        
        # Check stats after hydration
        success, stats = self.run_test(
            "Check Stats After Hydration",
            "GET",
            f"health/stats/{self.session_id}",
            200
        )
        
        hydration_before_undo = 0
        if success:
            hydration_before_undo = stats.get('hydration', 0)
            print(f"   Hydration logged: {hydration_before_undo}ml")
        
        print("\n🔄 STEP 2: Delete hydration via chat and verify")
        success, response = self.run_test(
            "Delete Hydration via Chat",
            "POST",
            "chat",
            200,
            data={"message": "undo hydration", "session_id": self.session_id}
        )
        
        if success:
            donna_response = response.get('response', '')
            print(f"   Donna undo: {donna_response[:100]}...")
        
        time.sleep(2)
        
        # Verify hydration decreased
        success, stats = self.run_test(
            "Check Stats After Hydration Undo",
            "GET",
            f"health/stats/{self.session_id}",
            200
        )
        
        if success:
            hydration_after_undo = stats.get('hydration', 0)
            if hydration_after_undo < hydration_before_undo:
                print(f"✅ Hydration decreased: {hydration_before_undo}ml → {hydration_after_undo}ml")
            else:
                print(f"❌ Hydration not decreased: {hydration_before_undo}ml → {hydration_after_undo}ml")
        
        print("\n🔄 STEP 3: Log meal and verify")
        success, response = self.run_test(
            "Log Meal via Chat",
            "POST",
            "chat",
            200,
            data={"message": "I ate pasta for lunch", "session_id": self.session_id}
        )
        
        if success:
            donna_response = response.get('response', '')
            print(f"   Donna meal: {donna_response[:100]}...")
        
        time.sleep(2)
        
        # Check meal stats
        success, stats = self.run_test(
            "Check Stats After Meal",
            "GET",
            f"health/stats/{self.session_id}",
            200
        )
        
        calories_before_undo = 0
        protein_before_undo = 0
        if success:
            calories_before_undo = stats.get('calories', 0)
            protein_before_undo = stats.get('protein', 0)
            print(f"   Meal logged: {calories_before_undo} calories, {protein_before_undo}g protein")
        
        print("\n🔄 STEP 4: Delete meal and verify recalculation")
        success, response = self.run_test(
            "Delete Meal via Chat",
            "POST",
            "chat",
            200,
            data={"message": "remove last meal", "session_id": self.session_id}
        )
        
        if success:
            donna_response = response.get('response', '')
            print(f"   Donna meal undo: {donna_response[:100]}...")
        
        time.sleep(2)
        
        # Verify meal recalculation
        success, stats = self.run_test(
            "Check Stats After Meal Undo",
            "GET",
            f"health/stats/{self.session_id}",
            200
        )
        
        if success:
            calories_after_undo = stats.get('calories', 0)
            protein_after_undo = stats.get('protein', 0)
            if calories_after_undo < calories_before_undo:
                print(f"✅ Meal recalculated: {calories_before_undo}→{calories_after_undo} cal, {protein_before_undo}→{protein_after_undo}g protein")
            else:
                print(f"❌ Meal not recalculated: {calories_before_undo}→{calories_after_undo} cal, {protein_before_undo}→{protein_after_undo}g protein")
        
        print("\n🔄 STEP 5: Log sleep and verify")
        success, response = self.run_test(
            "Log Sleep via Chat",
            "POST",
            "chat",
            200,
            data={"message": "I slept 8 hours", "session_id": self.session_id}
        )
        
        if success:
            donna_response = response.get('response', '')
            print(f"   Donna sleep: {donna_response[:100]}...")
        
        time.sleep(2)
        
        # Check sleep stats
        success, stats = self.run_test(
            "Check Stats After Sleep",
            "GET",
            f"health/stats/{self.session_id}",
            200
        )
        
        sleep_before_undo = 0
        if success:
            sleep_before_undo = stats.get('sleep', 0)
            print(f"   Sleep logged: {sleep_before_undo} hours")
        
        print("\n🔄 STEP 6: Delete sleep and verify reset")
        success, response = self.run_test(
            "Delete Sleep via Chat",
            "POST",
            "chat",
            200,
            data={"message": "undo sleep", "session_id": self.session_id}
        )
        
        if success:
            donna_response = response.get('response', '')
            print(f"   Donna sleep undo: {donna_response[:100]}...")
        
        time.sleep(2)
        
        # Verify sleep reset
        success, stats = self.run_test(
            "Check Stats After Sleep Undo",
            "GET",
            f"health/stats/{self.session_id}",
            200
        )
        
        if success:
            sleep_after_undo = stats.get('sleep', 0)
            if sleep_after_undo == 0:
                print(f"✅ Sleep reset: {sleep_before_undo} → {sleep_after_undo} hours")
            else:
                print(f"❌ Sleep not reset: {sleep_before_undo} → {sleep_after_undo} hours")
        
        return True

    def test_chat_delete_commands(self):
        """Test various chat-based delete commands"""
        print("\n" + "="*60)
        print("TESTING CHAT-BASED DELETE COMMANDS")
        print("="*60)
        
        # Reset and setup test data
        success, reset_response = self.run_test(
            "Reset for Delete Commands Test",
            "POST",
            f"health/stats/reset/{self.session_id}",
            200
        )
        
        # Add test data
        setup_messages = [
            "I had a bottle of water",  # 500ml hydration
            "I ate a sandwich",         # calories + protein
            "I slept 7 hours"          # sleep
        ]
        
        print("\nSetting up test data...")
        for message in setup_messages:
            success, response = self.run_test(
                f"Setup: '{message}'",
                "POST",
                "chat",
                200,
                data={"message": message, "session_id": self.session_id}
            )
            time.sleep(1)
        
        # Get baseline stats
        success, baseline_stats = self.run_test(
            "Get Baseline Stats",
            "GET",
            f"health/stats/{self.session_id}",
            200
        )
        
        if success:
            print(f"📊 Baseline: Calories={baseline_stats.get('calories', 0)}, "
                  f"Protein={baseline_stats.get('protein', 0)}, "
                  f"Hydration={baseline_stats.get('hydration', 0)}, "
                  f"Sleep={baseline_stats.get('sleep', 0)}")
        
        # Test delete commands
        delete_commands = [
            "delete last entry",
            "undo hydration", 
            "undo last meal",
            "remove sleep"
        ]
        
        print("\nTesting delete commands...")
        for command in delete_commands:
            success, response = self.run_test(
                f"Delete Command: '{command}'",
                "POST",
                "chat",
                200,
                data={"message": command, "session_id": self.session_id}
            )
            
            if success:
                donna_response = response.get('response', '')
                if any(word in donna_response.lower() for word in ['removed', 'deleted', 'undo', 'reset', 'entry']):
                    print(f"✅ '{command}' processed: {donna_response[:80]}...")
                else:
                    print(f"⚠️  '{command}' unclear: {donna_response[:80]}...")
            
            time.sleep(1)
        
        return True

    def test_undo_api_endpoints(self):
        """Test the undo API endpoints directly"""
        print("\n" + "="*60)
        print("TESTING UNDO API ENDPOINTS")
        print("="*60)
        
        # Reset and setup
        success, reset_response = self.run_test(
            "Reset for API Tests",
            "POST",
            f"health/stats/reset/{self.session_id}",
            200
        )
        
        # Add test data via chat
        api_setup_messages = [
            "I drank 2 glasses of water",  # ~500ml
            "I ate a burger",              # calories + protein
            "I slept 8.5 hours"           # sleep
        ]
        
        print("\nSetting up data for API tests...")
        for message in api_setup_messages:
            success, response = self.run_test(
                f"API Setup: '{message}'",
                "POST",
                "chat",
                200,
                data={"message": message, "session_id": self.session_id}
            )
            time.sleep(1)
        
        # Get baseline for API tests
        success, api_baseline = self.run_test(
            "API Baseline Stats",
            "GET",
            f"health/stats/{self.session_id}",
            200
        )
        
        if success:
            print(f"📊 API Baseline: Calories={api_baseline.get('calories', 0)}, "
                  f"Protein={api_baseline.get('protein', 0)}, "
                  f"Hydration={api_baseline.get('hydration', 0)}, "
                  f"Sleep={api_baseline.get('sleep', 0)}")
        
        # Test undo hydration API
        success, undo_response = self.run_test(
            "DELETE /api/health/stats/undo/{session}/hydration",
            "DELETE",
            f"health/stats/undo/{self.session_id}/hydration",
            200
        )
        
        if success and undo_response.get('message'):
            print(f"✅ Hydration undo API: {undo_response['message']}")
        
        # Test undo meal API
        success, undo_response = self.run_test(
            "DELETE /api/health/stats/undo/{session}/meal",
            "DELETE",
            f"health/stats/undo/{self.session_id}/meal",
            200
        )
        
        if success and undo_response.get('message'):
            print(f"✅ Meal undo API: {undo_response['message']}")
        
        # Test undo sleep API
        success, undo_response = self.run_test(
            "DELETE /api/health/stats/undo/{session}/sleep",
            "DELETE",
            f"health/stats/undo/{self.session_id}/sleep",
            200
        )
        
        if success and undo_response.get('message'):
            print(f"✅ Sleep undo API: {undo_response['message']}")
        
        # Check final stats
        success, final_stats = self.run_test(
            "Final Stats After API Undos",
            "GET",
            f"health/stats/{self.session_id}",
            200
        )
        
        if success:
            print(f"📊 Final: Calories={final_stats.get('calories', 0)}, "
                  f"Protein={final_stats.get('protein', 0)}, "
                  f"Hydration={final_stats.get('hydration', 0)}, "
                  f"Sleep={final_stats.get('sleep', 0)}")
        
        return True

    def test_error_handling(self):
        """Test error handling for undo operations"""
        print("\n" + "="*60)
        print("TESTING ERROR HANDLING")
        print("="*60)
        
        # Test undo when no entries exist
        success, error_response = self.run_test(
            "Undo Non-existent Hydration (404 Expected)",
            "DELETE",
            f"health/stats/undo/{self.session_id}/hydration",
            404
        )
        
        if success:
            print("✅ Proper 404 for non-existent hydration")
        
        # Test undo invalid type
        success, error_response = self.run_test(
            "Undo Invalid Type (404 Expected)",
            "DELETE",
            f"health/stats/undo/{self.session_id}/invalid_type",
            404
        )
        
        if success:
            print("✅ Proper error for invalid entry type")
        
        # Test chat delete when no entries
        success, response = self.run_test(
            "Chat Delete No Entries",
            "POST",
            "chat",
            200,
            data={"message": "delete last entry", "session_id": self.session_id}
        )
        
        if success:
            donna_response = response.get('response', '')
            if any(word in donna_response.lower() for word in ['no', 'found', 'recent', 'entries']):
                print(f"✅ Proper no-entries message: {donna_response[:80]}...")
            else:
                print(f"⚠️  Unclear no-entries message: {donna_response[:80]}...")
        
        return True

    def test_data_consistency(self):
        """Test data consistency after multiple operations"""
        print("\n" + "="*60)
        print("TESTING DATA CONSISTENCY")
        print("="*60)
        
        # Reset for consistency test
        success, reset_response = self.run_test(
            "Reset for Consistency Test",
            "POST",
            f"health/stats/reset/{self.session_id}",
            200
        )
        
        # Add complex data
        consistency_messages = [
            "I had 3 glasses of water",     # 750ml
            "I ate pasta with chicken",     # calories + protein
            "I had another glass of water", # +250ml = 1000ml total
            "I ate an apple",              # more calories + protein
            "I slept 7.5 hours"           # sleep
        ]
        
        print("\nAdding complex data...")
        for message in consistency_messages:
            success, response = self.run_test(
                f"Add: '{message}'",
                "POST",
                "chat",
                200,
                data={"message": message, "session_id": self.session_id}
            )
            time.sleep(1)
        
        # Get complex stats
        success, complex_stats = self.run_test(
            "Complex Stats Before Undo",
            "GET",
            f"health/stats/{self.session_id}",
            200
        )
        
        if success:
            print(f"📊 Complex: Calories={complex_stats.get('calories', 0)}, "
                  f"Protein={complex_stats.get('protein', 0)}, "
                  f"Hydration={complex_stats.get('hydration', 0)}, "
                  f"Sleep={complex_stats.get('sleep', 0)}")
        
        # Test meal recalculation
        success, response = self.run_test(
            "Remove One Meal (Test Recalculation)",
            "DELETE",
            f"health/stats/undo/{self.session_id}/meal",
            200
        )
        
        time.sleep(2)
        
        # Verify recalculation
        success, recalc_stats = self.run_test(
            "Stats After Recalculation",
            "GET",
            f"health/stats/{self.session_id}",
            200
        )
        
        if success:
            new_calories = recalc_stats.get('calories', 0)
            new_protein = recalc_stats.get('protein', 0)
            old_calories = complex_stats.get('calories', 0)
            old_protein = complex_stats.get('protein', 0)
            
            if new_calories < old_calories and new_protein < old_protein:
                print(f"✅ Recalculation working: {old_calories}→{new_calories} cal, {old_protein}→{new_protein}g protein")
            else:
                print(f"❌ Recalculation failed: {old_calories}→{new_calories} cal, {old_protein}→{new_protein}g protein")
        
        return True

def main():
    print("🚀 Enhanced Health Undo/Delete Functionality Tests")
    print("=" * 60)
    
    tester = HealthUndoDeleteTester()
    
    # Run focused test suites
    test_suites = [
        ("Complete Health Workflow", tester.test_complete_health_workflow),
        ("Chat Delete Commands", tester.test_chat_delete_commands),
        ("Undo API Endpoints", tester.test_undo_api_endpoints),
        ("Error Handling", tester.test_error_handling),
        ("Data Consistency", tester.test_data_consistency)
    ]
    
    for suite_name, test_suite in test_suites:
        print(f"\n🔄 Running {suite_name}...")
        try:
            test_suite()
        except Exception as e:
            print(f"❌ {suite_name} failed with error: {str(e)}")
    
    # Print results
    print("\n" + "="*60)
    print("📊 ENHANCED UNDO/DELETE TEST RESULTS")
    print("="*60)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    
    if tester.tests_run > 0:
        success_rate = (tester.tests_passed / tester.tests_run * 100)
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 Enhanced undo/delete functionality is working well!")
            return 0
        else:
            print("⚠️  Some issues found - check logs above")
            return 1
    else:
        print("❌ No tests were run")
        return 1

if __name__ == "__main__":
    sys.exit(main())