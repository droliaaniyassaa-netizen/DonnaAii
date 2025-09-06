#!/usr/bin/env python3
"""
Detailed Career Goal Creation Test
Focus: Testing the "Generate plan" button functionality for career goals
"""

import requests
import json
import time
from datetime import datetime

class CareerGoalDetailedTester:
    def __init__(self, base_url="https://donna-companion.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = "career_test_session"

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

    def test_career_goal_creation_detailed(self):
        """Test career goal creation with realistic data as requested"""
        print("\n" + "="*70)
        print("DETAILED CAREER GOAL CREATION TEST")
        print("Testing: 'Generate plan' button functionality")
        print("="*70)
        
        # Test 1: Create career goal with realistic data
        realistic_goal = {
            "goal": "Become a Senior Software Engineer at Google",
            "timeframe": "18 months"
        }
        
        print(f"\n🎯 Testing with realistic goal: '{realistic_goal['goal']}'")
        print(f"   Timeframe: {realistic_goal['timeframe']}")
        
        try:
            response = requests.post(
                f"{self.api_url}/career/goals",
                json=realistic_goal,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                goal_data = response.json()
                self.log_test("Career Goal Creation", True, f"Goal ID: {goal_data.get('id')}")
                
                # Test 2: Verify LLM-powered action plan generation
                action_plan = goal_data.get('action_plan', [])
                if action_plan and len(action_plan) > 0:
                    self.log_test("LLM Action Plan Generation", True, f"Generated {len(action_plan)} steps")
                    
                    # Test 3: Verify response includes personalized action_plan array
                    if isinstance(action_plan, list):
                        self.log_test("Action Plan Array Format", True, "Response contains array of action steps")
                        
                        # Test 4: Verify action plan has expected number of steps (5)
                        if len(action_plan) == 5:
                            self.log_test("Action Plan Step Count", True, "Contains exactly 5 strategic steps")
                        else:
                            self.log_test("Action Plan Step Count", False, f"Expected 5 steps, got {len(action_plan)}")
                        
                        # Test 5: Verify action plan steps are specific and actionable
                        print(f"\n📋 ANALYZING ACTION PLAN QUALITY:")
                        print(f"   Goal: {realistic_goal['goal']}")
                        print(f"   Generated Action Plan:")
                        
                        specific_indicators = [
                            'google', 'senior', 'engineer', 'technical', 'system design',
                            'leetcode', 'interview', 'portfolio', 'project', 'skill',
                            'network', 'mentor', 'experience', 'leadership', 'architecture'
                        ]
                        
                        actionable_indicators = [
                            'build', 'create', 'develop', 'practice', 'study', 'learn',
                            'apply', 'join', 'attend', 'complete', 'implement', 'prepare',
                            'schedule', 'reach out', 'connect', 'update', 'improve'
                        ]
                        
                        specific_count = 0
                        actionable_count = 0
                        
                        for i, step in enumerate(action_plan, 1):
                            print(f"   {i}. {step}")
                            
                            step_lower = step.lower()
                            
                            # Check for specific content
                            if any(indicator in step_lower for indicator in specific_indicators):
                                specific_count += 1
                            
                            # Check for actionable language
                            if any(indicator in step_lower for indicator in actionable_indicators):
                                actionable_count += 1
                        
                        # Test 6: Verify steps are specific (not generic)
                        specificity_threshold = 3  # At least 3 steps should be specific
                        if specific_count >= specificity_threshold:
                            self.log_test("Action Plan Specificity", True, 
                                        f"{specific_count}/5 steps contain specific, relevant content")
                        else:
                            self.log_test("Action Plan Specificity", False, 
                                        f"Only {specific_count}/5 steps are specific (need ≥{specificity_threshold})")
                        
                        # Test 7: Verify steps are actionable
                        actionable_threshold = 4  # At least 4 steps should be actionable
                        if actionable_count >= actionable_threshold:
                            self.log_test("Action Plan Actionability", True, 
                                        f"{actionable_count}/5 steps contain actionable language")
                        else:
                            self.log_test("Action Plan Actionability", False, 
                                        f"Only {actionable_count}/5 steps are actionable (need ≥{actionable_threshold})")
                        
                        # Test 8: Verify resources are provided
                        resources = goal_data.get('resources', [])
                        if resources and len(resources) > 0:
                            self.log_test("Resource Generation", True, f"Generated {len(resources)} resources")
                            print(f"   📚 Resources: {', '.join(resources)}")
                        else:
                            self.log_test("Resource Generation", False, "No resources generated")
                        
                        # Store goal ID for persistence test
                        self.created_goal_id = goal_data.get('id')
                        
                    else:
                        self.log_test("Action Plan Array Format", False, "Action plan is not an array")
                else:
                    self.log_test("LLM Action Plan Generation", False, "No action plan generated")
            else:
                self.log_test("Career Goal Creation", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Career Goal Creation", False, f"Exception: {str(e)}")

    def test_data_persistence(self):
        """Test GET /api/career/goals to ensure data persistence"""
        print(f"\n🔍 TESTING DATA PERSISTENCE")
        
        try:
            response = requests.get(
                f"{self.api_url}/career/goals",
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                goals = response.json()
                self.log_test("Career Goals Retrieval", True, f"Retrieved {len(goals)} goals")
                
                # Verify our created goal exists
                if hasattr(self, 'created_goal_id') and self.created_goal_id:
                    found_goal = None
                    for goal in goals:
                        if goal.get('id') == self.created_goal_id:
                            found_goal = goal
                            break
                    
                    if found_goal:
                        self.log_test("Data Persistence", True, "Created goal found in database")
                        
                        # Verify all fields are persisted
                        required_fields = ['id', 'goal', 'timeframe', 'action_plan', 'resources', 'created_at']
                        missing_fields = [field for field in required_fields if field not in found_goal]
                        
                        if not missing_fields:
                            self.log_test("Field Persistence", True, "All required fields persisted")
                        else:
                            self.log_test("Field Persistence", False, f"Missing fields: {missing_fields}")
                        
                        # Verify action plan persisted correctly
                        persisted_plan = found_goal.get('action_plan', [])
                        if persisted_plan and len(persisted_plan) == 5:
                            self.log_test("Action Plan Persistence", True, "5-step action plan persisted correctly")
                        else:
                            self.log_test("Action Plan Persistence", False, 
                                        f"Action plan not persisted correctly (got {len(persisted_plan)} steps)")
                    else:
                        self.log_test("Data Persistence", False, "Created goal not found in database")
                else:
                    self.log_test("Data Persistence", False, "No goal ID to verify (creation may have failed)")
            else:
                self.log_test("Career Goals Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Career Goals Retrieval", False, f"Exception: {str(e)}")

    def test_additional_realistic_goals(self):
        """Test with additional realistic career goals to verify consistency"""
        print(f"\n🎯 TESTING ADDITIONAL REALISTIC GOALS")
        
        additional_goals = [
            {
                "goal": "Transition to Product Management at a tech startup",
                "timeframe": "12 months"
            },
            {
                "goal": "Become a Machine Learning Engineer at Netflix",
                "timeframe": "24 months"
            }
        ]
        
        for i, goal_data in enumerate(additional_goals, 1):
            print(f"\n   Testing Goal {i}: {goal_data['goal']}")
            
            try:
                response = requests.post(
                    f"{self.api_url}/career/goals",
                    json=goal_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    action_plan = result.get('action_plan', [])
                    
                    # Quick quality check
                    if len(action_plan) == 5:
                        self.log_test(f"Additional Goal {i} - Plan Generation", True, 
                                    f"Generated 5-step plan for {goal_data['goal'][:30]}...")
                    else:
                        self.log_test(f"Additional Goal {i} - Plan Generation", False, 
                                    f"Generated {len(action_plan)} steps instead of 5")
                else:
                    self.log_test(f"Additional Goal {i} - Creation", False, 
                                f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Additional Goal {i} - Creation", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all career goal tests"""
        print("🚀 Starting Detailed Career Goal Tests")
        print("Focus: 'Generate plan' button functionality")
        print("="*70)
        
        # Run test suites
        self.test_career_goal_creation_detailed()
        self.test_data_persistence()
        self.test_additional_realistic_goals()
        
        # Print results
        print("\n" + "="*70)
        print("📊 DETAILED TEST RESULTS")
        print("="*70)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        
        if self.tests_run > 0:
            success_rate = (self.tests_passed / self.tests_run) * 100
            print(f"Success Rate: {success_rate:.1f}%")
            
            if success_rate >= 90:
                print("🎉 Career goal functionality is working excellently!")
                return True
            elif success_rate >= 75:
                print("✅ Career goal functionality is working well with minor issues")
                return True
            else:
                print("⚠️  Career goal functionality has significant issues")
                return False
        else:
            print("❌ No tests were run")
            return False

def main():
    tester = CareerGoalDetailedTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())