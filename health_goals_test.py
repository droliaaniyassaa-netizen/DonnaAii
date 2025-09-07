#!/usr/bin/env python3
"""
Health Goals Backend API Testing
Focus: Testing Health Goal functionality to understand stat card update issues
"""

import requests
import json
import sys
from datetime import datetime, timezone, timedelta

class HealthGoalsAPITester:
    def __init__(self, base_url="https://auth-ui-center.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = "health_test_session"
        self.created_goal_ids = []
        self.created_entry_ids = []

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
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            return response
        except Exception as e:
            print(f"Request failed: {str(e)}")
            return None

    def test_health_goal_creation(self):
        """Test creating health goals with different goal types"""
        print("\n🎯 TESTING HEALTH GOAL CREATION")
        print("=" * 50)
        
        # Test different goal types
        test_goals = [
            {
                "goal_type": "weight_loss",
                "target": "Lose 15 pounds in 3 months",
                "current_progress": "Starting weight: 180 lbs"
            },
            {
                "goal_type": "muscle_gain", 
                "target": "Gain 10 pounds of muscle in 6 months",
                "current_progress": "Current muscle mass: 140 lbs"
            },
            {
                "goal_type": "maintain",
                "target": "Maintain current weight and fitness level",
                "current_progress": "Current weight: 165 lbs, exercising 3x/week"
            },
            {
                "goal_type": "fitness",
                "target": "Run a 5K in under 25 minutes",
                "current_progress": "Current 5K time: 32 minutes"
            }
        ]
        
        for i, goal_data in enumerate(test_goals):
            response = self.make_request('POST', 'health/goals', data=goal_data)
            
            if response and response.status_code == 200:
                goal = response.json()
                self.created_goal_ids.append(goal.get('id'))
                
                # Verify goal structure
                required_fields = ['id', 'goal_type', 'target', 'current_progress', 'created_at']
                missing_fields = [field for field in required_fields if field not in goal]
                
                if not missing_fields:
                    self.log_test(f"Create {goal_data['goal_type']} goal", True, 
                                f"Goal ID: {goal.get('id')[:8]}...")
                else:
                    self.log_test(f"Create {goal_data['goal_type']} goal", False,
                                f"Missing fields: {missing_fields}")
            else:
                status = response.status_code if response else "No response"
                self.log_test(f"Create {goal_data['goal_type']} goal", False,
                            f"Status: {status}")

    def test_health_goal_retrieval(self):
        """Test retrieving health goals"""
        print("\n📋 TESTING HEALTH GOAL RETRIEVAL")
        print("=" * 50)
        
        response = self.make_request('GET', 'health/goals')
        
        if response and response.status_code == 200:
            goals = response.json()
            
            if isinstance(goals, list):
                self.log_test("Retrieve health goals", True, 
                            f"Found {len(goals)} goals")
                
                # Verify goal structure and data
                for goal in goals:
                    if goal.get('id') in self.created_goal_ids:
                        # Check if goal has all required fields
                        required_fields = ['id', 'goal_type', 'target', 'current_progress']
                        has_all_fields = all(field in goal for field in required_fields)
                        
                        if has_all_fields:
                            self.log_test(f"Goal structure validation", True,
                                        f"Goal type: {goal['goal_type']}")
                        else:
                            missing = [f for f in required_fields if f not in goal]
                            self.log_test(f"Goal structure validation", False,
                                        f"Missing: {missing}")
            else:
                self.log_test("Retrieve health goals", False, 
                            "Response is not a list")
        else:
            status = response.status_code if response else "No response"
            self.log_test("Retrieve health goals", False, f"Status: {status}")

    def test_health_entries_creation(self):
        """Test creating health entries for tracking progress"""
        print("\n📝 TESTING HEALTH ENTRIES CREATION")
        print("=" * 50)
        
        # Create various health entries
        current_time = datetime.now(timezone.utc)
        
        test_entries = [
            {
                "type": "meal",
                "description": "Grilled chicken breast with quinoa and vegetables",
                "value": "450 calories",
                "datetime_utc": current_time.isoformat()
            },
            {
                "type": "exercise", 
                "description": "30-minute cardio workout",
                "value": "300 calories burned",
                "datetime_utc": (current_time - timedelta(hours=2)).isoformat()
            },
            {
                "type": "hydration",
                "description": "Water intake",
                "value": "8 glasses",
                "datetime_utc": current_time.isoformat()
            },
            {
                "type": "sleep",
                "description": "Night sleep",
                "value": "7.5 hours",
                "datetime_utc": (current_time - timedelta(hours=8)).isoformat()
            }
        ]
        
        for entry_data in test_entries:
            response = self.make_request('POST', 'health/entries', data=entry_data)
            
            if response and response.status_code == 200:
                entry = response.json()
                self.created_entry_ids.append(entry.get('id'))
                
                # Verify entry structure
                required_fields = ['id', 'type', 'description', 'datetime_utc', 'created_at']
                missing_fields = [field for field in required_fields if field not in entry]
                
                if not missing_fields:
                    self.log_test(f"Create {entry_data['type']} entry", True,
                                f"Entry ID: {entry.get('id')[:8]}...")
                else:
                    self.log_test(f"Create {entry_data['type']} entry", False,
                                f"Missing fields: {missing_fields}")
            else:
                status = response.status_code if response else "No response"
                self.log_test(f"Create {entry_data['type']} entry", False,
                            f"Status: {status}")

    def test_health_analytics(self):
        """Test health analytics endpoint that powers stat cards"""
        print("\n📊 TESTING HEALTH ANALYTICS (STAT CARDS)")
        print("=" * 50)
        
        response = self.make_request('GET', 'health/analytics')
        
        if response and response.status_code == 200:
            analytics = response.json()
            
            if isinstance(analytics, dict):
                self.log_test("Get health analytics", True,
                            f"Analytics keys: {list(analytics.keys())}")
                
                # Check expected analytics fields
                expected_fields = ['meals_this_week', 'water_glasses_today', 
                                 'workouts_this_week', 'average_sleep']
                
                for field in expected_fields:
                    if field in analytics:
                        value = analytics[field]
                        self.log_test(f"Analytics field: {field}", True,
                                    f"Value: {value}")
                    else:
                        self.log_test(f"Analytics field: {field}", False,
                                    "Field missing from analytics")
                
                # Test if analytics reflect our created entries
                if analytics.get('meals_this_week', 0) > 0:
                    self.log_test("Meal tracking in analytics", True,
                                f"Meals counted: {analytics['meals_this_week']}")
                else:
                    self.log_test("Meal tracking in analytics", False,
                                "No meals found in analytics")
                    
                if analytics.get('workouts_this_week', 0) > 0:
                    self.log_test("Exercise tracking in analytics", True,
                                f"Workouts counted: {analytics['workouts_this_week']}")
                else:
                    self.log_test("Exercise tracking in analytics", False,
                                "No workouts found in analytics")
                    
            else:
                self.log_test("Get health analytics", False,
                            "Response is not a dictionary")
        else:
            status = response.status_code if response else "No response"
            self.log_test("Get health analytics", False, f"Status: {status}")

    def test_goal_progress_calculation(self):
        """Test if goals and entries work together for progress tracking"""
        print("\n🎯 TESTING GOAL PROGRESS CALCULATION")
        print("=" * 50)
        
        # Get current goals
        goals_response = self.make_request('GET', 'health/goals')
        entries_response = self.make_request('GET', 'health/entries')
        
        if (goals_response and goals_response.status_code == 200 and 
            entries_response and entries_response.status_code == 200):
            
            goals = goals_response.json()
            entries = entries_response.json()
            
            self.log_test("Retrieve goals and entries for progress", True,
                        f"Goals: {len(goals)}, Entries: {len(entries)}")
            
            # Check if we can correlate goals with entries
            goal_types = [goal.get('goal_type') for goal in goals]
            entry_types = [entry.get('type') for entry in entries]
            
            # Look for logical connections
            if 'weight_loss' in goal_types and 'exercise' in entry_types:
                self.log_test("Weight loss goal + exercise entries", True,
                            "Found correlation for progress tracking")
            
            if 'muscle_gain' in goal_types and 'meal' in entry_types:
                self.log_test("Muscle gain goal + meal entries", True,
                            "Found correlation for nutrition tracking")
            
            if 'fitness' in goal_types and 'exercise' in entry_types:
                self.log_test("Fitness goal + exercise entries", True,
                            "Found correlation for fitness tracking")
                            
            # Check if there's any automatic progress calculation
            for goal in goals:
                if 'progress' in goal and goal['progress'] != 0:
                    self.log_test("Automatic progress calculation", True,
                                f"Goal {goal['goal_type']} has progress: {goal['progress']}")
                    break
            else:
                self.log_test("Automatic progress calculation", False,
                            "No automatic progress found in goals")
                            
        else:
            self.log_test("Retrieve goals and entries for progress", False,
                        "Failed to get goals or entries")

    def test_stat_card_data_flow(self):
        """Test the complete data flow from goals to stat cards"""
        print("\n🔄 TESTING STAT CARD DATA FLOW")
        print("=" * 50)
        
        # This tests the complete flow that should update stat cards
        
        # 1. Create a specific goal
        weight_goal = {
            "goal_type": "weight_loss",
            "target": "Lose 5 pounds this month",
            "current_progress": "Starting: 170 lbs"
        }
        
        goal_response = self.make_request('POST', 'health/goals', data=weight_goal)
        
        if goal_response and goal_response.status_code == 200:
            goal = goal_response.json()
            goal_id = goal.get('id')
            
            self.log_test("Create test weight loss goal", True,
                        f"Goal ID: {goal_id[:8]}...")
            
            # 2. Add related health entries
            related_entries = [
                {
                    "type": "exercise",
                    "description": "45-minute gym session - weight training",
                    "value": "400 calories burned",
                    "datetime_utc": datetime.now(timezone.utc).isoformat()
                },
                {
                    "type": "meal",
                    "description": "Healthy lunch - salad with protein",
                    "value": "350 calories",
                    "datetime_utc": datetime.now(timezone.utc).isoformat()
                }
            ]
            
            entries_created = 0
            for entry_data in related_entries:
                entry_response = self.make_request('POST', 'health/entries', data=entry_data)
                if entry_response and entry_response.status_code == 200:
                    entries_created += 1
            
            self.log_test("Create related health entries", entries_created == 2,
                        f"Created {entries_created}/2 entries")
            
            # 3. Check if analytics reflect the new data
            analytics_response = self.make_request('GET', 'health/analytics')
            
            if analytics_response and analytics_response.status_code == 200:
                analytics = analytics_response.json()
                
                # Check if our new entries are reflected
                meals_count = analytics.get('meals_this_week', 0)
                workouts_count = analytics.get('workouts_this_week', 0)
                
                self.log_test("Analytics reflect new entries", 
                            meals_count > 0 and workouts_count > 0,
                            f"Meals: {meals_count}, Workouts: {workouts_count}")
                
                # 4. Check if there's any goal-specific analytics
                # (This would be where stat cards get their goal progress data)
                
                # Get updated goals to see if progress changed
                updated_goals_response = self.make_request('GET', 'health/goals')
                if updated_goals_response and updated_goals_response.status_code == 200:
                    updated_goals = updated_goals_response.json()
                    
                    # Find our goal
                    our_goal = next((g for g in updated_goals if g.get('id') == goal_id), None)
                    
                    if our_goal:
                        self.log_test("Goal persists after entries", True,
                                    f"Goal type: {our_goal['goal_type']}")
                        
                        # Check if there's any progress tracking mechanism
                        if 'progress' in our_goal:
                            self.log_test("Goal has progress field", True,
                                        f"Progress: {our_goal['progress']}")
                        else:
                            self.log_test("Goal has progress field", False,
                                        "No progress field found")
                    else:
                        self.log_test("Goal persists after entries", False,
                                    "Goal not found after creating entries")
            else:
                self.log_test("Analytics after goal+entries", False,
                            "Failed to get analytics")
        else:
            self.log_test("Create test weight loss goal", False,
                        "Failed to create goal")

    def test_potential_issues(self):
        """Test for potential issues that could cause stat card problems"""
        print("\n🔍 TESTING POTENTIAL ISSUES")
        print("=" * 50)
        
        # Test 1: Check if there are any goal-specific analytics endpoints
        potential_endpoints = [
            'health/goals/analytics',
            'health/goals/progress', 
            'health/stats',
            'health/dashboard'
        ]
        
        for endpoint in potential_endpoints:
            response = self.make_request('GET', endpoint)
            if response and response.status_code == 200:
                self.log_test(f"Found endpoint: {endpoint}", True,
                            "This endpoint exists and might be used by stat cards")
            elif response and response.status_code == 404:
                self.log_test(f"Endpoint {endpoint} not found", True,
                            "Expected - this endpoint doesn't exist")
            else:
                status = response.status_code if response else "No response"
                self.log_test(f"Test endpoint: {endpoint}", False,
                            f"Unexpected status: {status}")
        
        # Test 2: Check if analytics endpoint has any goal-related data
        analytics_response = self.make_request('GET', 'health/analytics')
        if analytics_response and analytics_response.status_code == 200:
            analytics = analytics_response.json()
            
            # Look for goal-related fields
            goal_related_fields = [key for key in analytics.keys() 
                                 if 'goal' in key.lower() or 'target' in key.lower() 
                                 or 'progress' in key.lower()]
            
            if goal_related_fields:
                self.log_test("Analytics contains goal-related data", True,
                            f"Fields: {goal_related_fields}")
            else:
                self.log_test("Analytics contains goal-related data", False,
                            "No goal-related fields in analytics - this might be the issue!")
        
        # Test 3: Check if there's a way to get goal progress
        goals_response = self.make_request('GET', 'health/goals')
        if goals_response and goals_response.status_code == 200:
            goals = goals_response.json()
            
            goals_with_progress = [g for g in goals if 'progress' in g and g['progress'] != 0]
            
            if goals_with_progress:
                self.log_test("Goals have progress tracking", True,
                            f"Found {len(goals_with_progress)} goals with progress")
            else:
                self.log_test("Goals have progress tracking", False,
                            "No goals have progress values - stat cards can't show progress!")

    def cleanup(self):
        """Clean up created test data"""
        print("\n🧹 CLEANING UP TEST DATA")
        print("=" * 30)
        
        # Note: The API doesn't seem to have delete endpoints for goals/entries
        # This is just for completeness
        print(f"Created {len(self.created_goal_ids)} goals and {len(self.created_entry_ids)} entries")
        print("Note: No cleanup endpoints available - test data will remain")

    def run_all_tests(self):
        """Run all health goal tests"""
        print("🏥 HEALTH GOALS BACKEND API TESTING")
        print("=" * 60)
        print("Focus: Testing Health Goal functionality for stat card updates")
        print("=" * 60)
        
        # Run test suites
        self.test_health_goal_creation()
        self.test_health_goal_retrieval()
        self.test_health_entries_creation()
        self.test_health_analytics()
        self.test_goal_progress_calculation()
        self.test_stat_card_data_flow()
        self.test_potential_issues()
        
        # Cleanup
        self.cleanup()
        
        # Final results
        print("\n" + "=" * 60)
        print("📊 HEALTH GOALS TEST RESULTS")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        # Analysis
        print("\n🔍 ANALYSIS FOR STAT CARD ISSUES:")
        print("-" * 40)
        
        if self.tests_passed < self.tests_run:
            print("❌ Issues found that could affect stat card updates:")
            print("   - Check failed tests above for specific problems")
        else:
            print("✅ All health goal endpoints working correctly")
            print("   - If stat cards aren't updating, the issue is likely in frontend integration")
        
        return self.tests_passed == self.tests_run

def main():
    tester = HealthGoalsAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())