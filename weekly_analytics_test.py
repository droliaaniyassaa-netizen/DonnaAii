import requests
import sys
import json
import time
from datetime import datetime, timezone, timedelta

class WeeklyAnalyticsAPITester:
    def __init__(self, base_url="https://donna-ai-assist.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = "weekly_analytics_test"

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

    def setup_weekly_test_data(self):
        """Setup comprehensive test data for weekly analytics"""
        print("\n" + "="*50)
        print("SETTING UP WEEKLY TEST DATA")
        print("="*50)
        
        # Reset daily stats first
        success, reset_response = self.run_test(
            "Reset Daily Health Stats",
            "POST",
            f"health/stats/reset/{self.session_id}",
            200
        )
        
        if not success:
            return False
        
        # Create realistic health data for the past week
        health_messages = [
            # Day 1 (Monday)
            "I had 2 glasses of water",
            "I ate oatmeal with berries for breakfast", 
            "I had grilled chicken salad for lunch",
            "I ate salmon with vegetables for dinner",
            "I slept 7.5 hours",
            
            # Day 2 (Tuesday) 
            "I drank a bottle of water",
            "I had scrambled eggs for breakfast",
            "I ate a turkey sandwich for lunch", 
            "I had pasta with meat sauce for dinner",
            "I slept 8 hours",
            
            # Day 3 (Wednesday)
            "I had 3 glasses of water",
            "I ate yogurt with granola",
            "I had a quinoa bowl for lunch",
            "I ate grilled fish with rice for dinner", 
            "I slept 6.5 hours",
            
            # Day 4 (Thursday)
            "I drank 4 glasses of water",
            "I had avocado toast for breakfast",
            "I ate a chicken wrap for lunch",
            "I had stir-fry with tofu for dinner",
            "I slept 8.5 hours",
            
            # Day 5 (Friday)
            "I had a bottle of water",
            "I ate cereal with milk",
            "I had a burger for lunch",
            "I ate pizza for dinner",
            "I slept 7 hours",
            
            # Day 6 (Saturday - Weekend)
            "I drank 2 glasses of water", 
            "I had pancakes for breakfast",
            "I ate a big salad for lunch",
            "I had BBQ ribs for dinner",
            "I slept 9 hours",
            
            # Day 7 (Sunday - Weekend)
            "I had 3 glasses of water",
            "I ate eggs benedict for brunch",
            "I had sushi for dinner",
            "I slept 8.5 hours"
        ]
        
        print(f"Adding {len(health_messages)} health entries via chat...")
        
        for i, message in enumerate(health_messages):
            success, response = self.run_test(
                f"Health Entry {i+1}: '{message[:30]}...'",
                "POST",
                "chat",
                200,
                data={"message": message, "session_id": self.session_id}
            )
            
            if success:
                donna_response = response.get('response', '')
                if any(word in donna_response.lower() for word in ['logged', 'noted', 'calories', 'hydration', 'sleep']):
                    print(f"✅ Health data logged successfully")
                else:
                    print(f"⚠️  Unclear response: {donna_response[:50]}...")
            
            time.sleep(0.5)  # Brief pause to avoid overwhelming the system
        
        # Verify we have daily stats
        success, daily_stats = self.run_test(
            "Verify Daily Stats Created",
            "GET",
            f"health/stats/{self.session_id}",
            200
        )
        
        if success:
            print(f"📊 Current daily stats: Calories={daily_stats.get('calories', 0)}, "
                  f"Protein={daily_stats.get('protein', 0)}, "
                  f"Hydration={daily_stats.get('hydration', 0)}, "
                  f"Sleep={daily_stats.get('sleep', 0)}")
        
        return True

    def test_weekly_analytics_endpoint(self):
        """Test GET /api/health/analytics/weekly/{session_id} endpoint"""
        print("\n" + "="*50)
        print("TESTING WEEKLY ANALYTICS ENDPOINT")
        print("="*50)
        
        # Test current week analytics (week_offset=0)
        success, analytics = self.run_test(
            "Get Current Week Analytics",
            "GET",
            f"health/analytics/weekly/{self.session_id}",
            200,
            params={"week_offset": 0}
        )
        
        if not success:
            return False
        
        # Verify WeeklyHealthAnalytics model structure
        required_fields = [
            'id', 'session_id', 'week_start', 'week_end',
            'avg_calories', 'avg_protein', 'avg_hydration', 'avg_sleep',
            'target_calories', 'target_protein', 'target_hydration', 'target_sleep',
            'calories_pattern', 'protein_pattern', 'hydration_pattern', 'sleep_pattern',
            'calories_expert', 'calories_insight', 'protein_expert', 'protein_insight',
            'hydration_expert', 'hydration_insight', 'sleep_expert', 'sleep_insight',
            'overall_expert', 'overall_insight', 'created_at'
        ]
        
        print("\n📋 Verifying WeeklyHealthAnalytics Model Structure:")
        for field in required_fields:
            if field in analytics:
                print(f"✅ {field}: {type(analytics[field]).__name__}")
            else:
                print(f"❌ Missing field: {field}")
        
        # Verify session_id matches
        if analytics.get('session_id') == self.session_id:
            print("✅ Session ID matches request")
        else:
            print(f"❌ Session ID mismatch: expected {self.session_id}, got {analytics.get('session_id')}")
        
        # Verify week dates are valid
        week_start = analytics.get('week_start')
        week_end = analytics.get('week_end')
        if week_start and week_end:
            try:
                start_date = datetime.strptime(week_start, '%Y-%m-%d')
                end_date = datetime.strptime(week_end, '%Y-%m-%d')
                if (end_date - start_date).days == 6:
                    print(f"✅ Valid week range: {week_start} to {week_end}")
                else:
                    print(f"❌ Invalid week range: {week_start} to {week_end}")
            except ValueError:
                print(f"❌ Invalid date format: {week_start}, {week_end}")
        
        # Verify aggregated data is reasonable
        avg_calories = analytics.get('avg_calories', 0)
        avg_protein = analytics.get('avg_protein', 0)
        avg_hydration = analytics.get('avg_hydration', 0)
        avg_sleep = analytics.get('avg_sleep', 0)
        
        print(f"\n📊 Aggregated Weekly Data:")
        print(f"   Average Calories: {avg_calories}")
        print(f"   Average Protein: {avg_protein}g")
        print(f"   Average Hydration: {avg_hydration}ml")
        print(f"   Average Sleep: {avg_sleep}h")
        
        if avg_calories > 0:
            print("✅ Calories data aggregated")
        else:
            print("❌ No calories data aggregated")
            
        if avg_protein > 0:
            print("✅ Protein data aggregated")
        else:
            print("❌ No protein data aggregated")
            
        if avg_hydration > 0:
            print("✅ Hydration data aggregated")
        else:
            print("❌ No hydration data aggregated")
            
        if avg_sleep > 0:
            print("✅ Sleep data aggregated")
        else:
            print("❌ No sleep data aggregated")
        
        # Test different week offsets
        success, last_week = self.run_test(
            "Get Last Week Analytics (week_offset=-1)",
            "GET",
            f"health/analytics/weekly/{self.session_id}",
            200,
            params={"week_offset": -1}
        )
        
        if success:
            last_week_start = last_week.get('week_start')
            current_week_start = analytics.get('week_start')
            if last_week_start and current_week_start:
                try:
                    last_start = datetime.strptime(last_week_start, '%Y-%m-%d')
                    current_start = datetime.strptime(current_week_start, '%Y-%m-%d')
                    if (current_start - last_start).days == 7:
                        print("✅ Week offset calculation correct")
                    else:
                        print("❌ Week offset calculation incorrect")
                except ValueError:
                    print("❌ Date parsing error for week offset")
        
        return True

    def test_llm_expert_analysis(self):
        """Test LLM-generated expert analysis quality"""
        print("\n" + "="*50)
        print("TESTING LLM EXPERT ANALYSIS")
        print("="*50)
        
        # Get analytics with expert analysis
        success, analytics = self.run_test(
            "Get Analytics for Expert Analysis Testing",
            "GET",
            f"health/analytics/weekly/{self.session_id}",
            200
        )
        
        if not success:
            return False
        
        # Test expert analysis fields
        expert_fields = [
            ('calories_expert', 'calories_insight'),
            ('protein_expert', 'protein_insight'),
            ('hydration_expert', 'hydration_insight'),
            ('sleep_expert', 'sleep_insight'),
            ('overall_expert', 'overall_insight')
        ]
        
        print("\n🧠 Testing LLM Expert Analysis Quality:")
        
        for expert_field, insight_field in expert_fields:
            expert_text = analytics.get(expert_field, '')
            insight_text = analytics.get(insight_field, '')
            
            category = expert_field.replace('_expert', '').title()
            
            print(f"\n📝 {category} Analysis:")
            
            # Check if expert analysis exists and has substance
            if expert_text and len(expert_text) > 50:
                print(f"✅ {category} expert analysis present ({len(expert_text)} chars)")
                
                # Check for Harvard-level sophistication indicators
                sophisticated_terms = [
                    'metabolic', 'physiological', 'biochemical', 'hormonal',
                    'circadian', 'synthesis', 'regulation', 'cascade',
                    'insulin', 'cortisol', 'leptin', 'ghrelin', 'vasopressin'
                ]
                
                found_terms = [term for term in sophisticated_terms if term.lower() in expert_text.lower()]
                if found_terms:
                    print(f"✅ Sophisticated terminology found: {', '.join(found_terms[:3])}")
                else:
                    print("⚠️  Limited sophisticated terminology")
                
                # Check for specific metabolic insights
                if any(word in expert_text.lower() for word in ['metabolism', 'energy', 'cellular', 'function']):
                    print("✅ Contains metabolic implications")
                else:
                    print("⚠️  Limited metabolic insights")
                    
            else:
                print(f"❌ {category} expert analysis missing or too short")
            
            # Check compact insights
            if insight_text and len(insight_text) > 20:
                print(f"✅ {category} compact insight present ({len(insight_text)} chars)")
            else:
                print(f"❌ {category} compact insight missing or too short")
            
            # Print sample of analysis (first 150 chars)
            if expert_text:
                print(f"   Sample: {expert_text[:150]}...")
        
        # Test overall analysis integration
        overall_expert = analytics.get('overall_expert', '')
        overall_insight = analytics.get('overall_insight', '')
        
        print(f"\n🔬 Overall Analysis Integration:")
        if overall_expert and len(overall_expert) > 100:
            print(f"✅ Overall expert analysis comprehensive ({len(overall_expert)} chars)")
            
            # Check for cross-system integration
            integration_terms = ['interaction', 'correlation', 'pattern', 'relationship', 'cascade', 'synergy']
            if any(term in overall_expert.lower() for term in integration_terms):
                print("✅ Shows cross-system integration")
            else:
                print("⚠️  Limited cross-system integration")
        else:
            print("❌ Overall expert analysis insufficient")
        
        if overall_insight and len(overall_insight) > 30:
            print(f"✅ Overall insight present ({len(overall_insight)} chars)")
        else:
            print("❌ Overall insight missing or too short")
        
        return True

    def test_data_aggregation_accuracy(self):
        """Test weekly data aggregation from daily health stats"""
        print("\n" + "="*50)
        print("TESTING DATA AGGREGATION ACCURACY")
        print("="*50)
        
        # Get current daily stats
        success, daily_stats = self.run_test(
            "Get Current Daily Stats",
            "GET",
            f"health/stats/{self.session_id}",
            200
        )
        
        if not success:
            return False
        
        # Get weekly analytics
        success, weekly_analytics = self.run_test(
            "Get Weekly Analytics for Aggregation Test",
            "GET",
            f"health/analytics/weekly/{self.session_id}",
            200
        )
        
        if not success:
            return False
        
        print(f"\n📊 Daily Stats: Calories={daily_stats.get('calories', 0)}, "
              f"Protein={daily_stats.get('protein', 0)}, "
              f"Hydration={daily_stats.get('hydration', 0)}, "
              f"Sleep={daily_stats.get('sleep', 0)}")
        
        print(f"📊 Weekly Averages: Calories={weekly_analytics.get('avg_calories', 0)}, "
              f"Protein={weekly_analytics.get('avg_protein', 0)}, "
              f"Hydration={weekly_analytics.get('avg_hydration', 0)}, "
              f"Sleep={weekly_analytics.get('avg_sleep', 0)}")
        
        # Verify averages are reasonable (should be > 0 if we have data)
        avg_calories = weekly_analytics.get('avg_calories', 0)
        avg_protein = weekly_analytics.get('avg_protein', 0)
        avg_hydration = weekly_analytics.get('avg_hydration', 0)
        avg_sleep = weekly_analytics.get('avg_sleep', 0)
        
        if avg_calories > 0 and avg_calories < 5000:  # Reasonable calorie range
            print("✅ Average calories calculation reasonable")
        else:
            print(f"❌ Average calories unreasonable: {avg_calories}")
        
        if avg_protein > 0 and avg_protein < 300:  # Reasonable protein range
            print("✅ Average protein calculation reasonable")
        else:
            print(f"❌ Average protein unreasonable: {avg_protein}")
        
        if avg_hydration > 0 and avg_hydration < 10000:  # Reasonable hydration range
            print("✅ Average hydration calculation reasonable")
        else:
            print(f"❌ Average hydration unreasonable: {avg_hydration}")
        
        if avg_sleep > 0 and avg_sleep < 24:  # Reasonable sleep range
            print("✅ Average sleep calculation reasonable")
        else:
            print(f"❌ Average sleep unreasonable: {avg_sleep}")
        
        return True

    def test_pattern_analysis(self):
        """Test pattern detection algorithms"""
        print("\n" + "="*50)
        print("TESTING PATTERN ANALYSIS")
        print("="*50)
        
        # Get weekly analytics with patterns
        success, analytics = self.run_test(
            "Get Analytics for Pattern Analysis",
            "GET",
            f"health/analytics/weekly/{self.session_id}",
            200
        )
        
        if not success:
            return False
        
        # Test pattern structure for each category
        pattern_categories = ['calories', 'protein', 'hydration', 'sleep']
        
        for category in pattern_categories:
            pattern_key = f"{category}_pattern"
            pattern_data = analytics.get(pattern_key, {})
            
            print(f"\n📈 {category.title()} Pattern Analysis:")
            
            # Check required pattern fields
            required_pattern_fields = ['consistency', 'trend', 'weekday_vs_weekend']
            
            for field in required_pattern_fields:
                if field in pattern_data:
                    value = pattern_data[field]
                    print(f"✅ {field}: {value}")
                    
                    # Validate field values
                    if field == 'consistency':
                        valid_consistency = ['no_data', 'very_consistent', 'consistent', 'variable', 'highly_variable']
                        if value in valid_consistency:
                            print(f"   ✅ Valid consistency value")
                        else:
                            print(f"   ❌ Invalid consistency value: {value}")
                    
                    elif field == 'trend':
                        valid_trends = ['insufficient_data', 'stable', 'increasing', 'decreasing']
                        if value in valid_trends:
                            print(f"   ✅ Valid trend value")
                        else:
                            print(f"   ❌ Invalid trend value: {value}")
                    
                    elif field == 'weekday_vs_weekend':
                        valid_patterns = ['no_pattern', 'higher_weekends', 'lower_weekends', 'similar']
                        if value in valid_patterns:
                            print(f"   ✅ Valid weekday vs weekend pattern")
                        else:
                            print(f"   ❌ Invalid weekday vs weekend pattern: {value}")
                else:
                    print(f"❌ Missing pattern field: {field}")
            
            # Check for additional pattern data
            if 'daily_values' in pattern_data:
                daily_values = pattern_data['daily_values']
                if isinstance(daily_values, list) and len(daily_values) > 0:
                    print(f"✅ Daily values present: {len(daily_values)} days")
                else:
                    print("❌ Daily values missing or empty")
            
            if 'mean' in pattern_data:
                mean_value = pattern_data['mean']
                if isinstance(mean_value, (int, float)) and mean_value >= 0:
                    print(f"✅ Mean value calculated: {mean_value}")
                else:
                    print(f"❌ Invalid mean value: {mean_value}")
        
        return True

    def test_target_integration(self):
        """Test integration with health_targets collection"""
        print("\n" + "="*50)
        print("TESTING TARGET INTEGRATION")
        print("="*50)
        
        # First, set custom health targets
        custom_targets = {
            "session_id": self.session_id,
            "calories": 2500,
            "protein": 150,
            "hydration": 3000,
            "sleep": 8.5
        }
        
        success, targets_response = self.run_test(
            "Set Custom Health Targets",
            "POST",
            "health/targets",
            200,
            data=custom_targets
        )
        
        if not success:
            return False
        
        # Regenerate analytics to pick up new targets
        success, regen_response = self.run_test(
            "Regenerate Analytics with Custom Targets",
            "POST",
            f"health/analytics/weekly/regenerate/{self.session_id}",
            200,
            params={"week_offset": 0}
        )
        
        if not success:
            return False
        
        # Get updated analytics
        success, analytics = self.run_test(
            "Get Analytics with Custom Targets",
            "GET",
            f"health/analytics/weekly/{self.session_id}",
            200
        )
        
        if not success:
            return False
        
        # Verify targets are integrated
        target_calories = analytics.get('target_calories')
        target_protein = analytics.get('target_protein')
        target_hydration = analytics.get('target_hydration')
        target_sleep = analytics.get('target_sleep')
        
        print(f"\n🎯 Target Integration Verification:")
        
        if target_calories == 2500:
            print(f"✅ Calories target integrated: {target_calories}")
        else:
            print(f"❌ Calories target not integrated: expected 2500, got {target_calories}")
        
        if target_protein == 150:
            print(f"✅ Protein target integrated: {target_protein}")
        else:
            print(f"❌ Protein target not integrated: expected 150, got {target_protein}")
        
        if target_hydration == 3000:
            print(f"✅ Hydration target integrated: {target_hydration}")
        else:
            print(f"❌ Hydration target not integrated: expected 3000, got {target_hydration}")
        
        if target_sleep == 8.5:
            print(f"✅ Sleep target integrated: {target_sleep}")
        else:
            print(f"❌ Sleep target not integrated: expected 8.5, got {target_sleep}")
        
        # Test with default targets (no custom targets set)
        # Delete custom targets first
        success, delete_response = self.run_test(
            "Delete Custom Targets",
            "DELETE",
            f"health/targets/{self.session_id}",
            200
        )
        
        # Regenerate analytics to use defaults
        success, regen_response = self.run_test(
            "Regenerate Analytics with Default Targets",
            "POST",
            f"health/analytics/weekly/regenerate/{self.session_id}",
            200
        )
        
        # Get analytics with default targets
        success, default_analytics = self.run_test(
            "Get Analytics with Default Targets",
            "GET",
            f"health/analytics/weekly/{self.session_id}",
            200
        )
        
        if success:
            default_cal_target = default_analytics.get('target_calories')
            default_protein_target = default_analytics.get('target_protein')
            
            print(f"\n🎯 Default Target Verification:")
            if default_cal_target == 2200:  # Default from model
                print(f"✅ Default calories target: {default_cal_target}")
            else:
                print(f"❌ Unexpected default calories target: {default_cal_target}")
            
            if default_protein_target == 120:  # Default from model
                print(f"✅ Default protein target: {default_protein_target}")
            else:
                print(f"❌ Unexpected default protein target: {default_protein_target}")
        
        return True

    def test_regenerate_analytics(self):
        """Test POST /api/health/analytics/weekly/regenerate/{session_id} endpoint"""
        print("\n" + "="*50)
        print("TESTING REGENERATE ANALYTICS")
        print("="*50)
        
        # Get initial analytics
        success, initial_analytics = self.run_test(
            "Get Initial Analytics",
            "GET",
            f"health/analytics/weekly/{self.session_id}",
            200
        )
        
        if not success:
            return False
        
        initial_id = initial_analytics.get('id')
        initial_created_at = initial_analytics.get('created_at')
        
        print(f"📊 Initial analytics ID: {initial_id}")
        print(f"📊 Initial created_at: {initial_created_at}")
        
        # Wait a moment to ensure timestamp difference
        time.sleep(2)
        
        # Regenerate analytics
        success, regenerated = self.run_test(
            "Regenerate Weekly Analytics",
            "POST",
            f"health/analytics/weekly/regenerate/{self.session_id}",
            200,
            params={"week_offset": 0}
        )
        
        if not success:
            return False
        
        new_id = regenerated.get('id')
        new_created_at = regenerated.get('created_at')
        
        print(f"📊 Regenerated analytics ID: {new_id}")
        print(f"📊 Regenerated created_at: {new_created_at}")
        
        # Verify new analytics were generated
        if new_id != initial_id:
            print("✅ New analytics generated (different ID)")
        else:
            print("❌ Analytics not regenerated (same ID)")
        
        if new_created_at != initial_created_at:
            print("✅ New timestamp generated")
        else:
            print("❌ Timestamp not updated")
        
        # Verify data consistency after regeneration
        initial_avg_calories = initial_analytics.get('avg_calories')
        new_avg_calories = regenerated.get('avg_calories')
        
        if initial_avg_calories == new_avg_calories:
            print("✅ Data consistency maintained after regeneration")
        else:
            print(f"⚠️  Data changed after regeneration: {initial_avg_calories} -> {new_avg_calories}")
        
        # Test caching behavior - get analytics again immediately
        success, cached_analytics = self.run_test(
            "Get Analytics After Regeneration (Cache Test)",
            "GET",
            f"health/analytics/weekly/{self.session_id}",
            200
        )
        
        if success:
            cached_id = cached_analytics.get('id')
            if cached_id == new_id:
                print("✅ Caching working correctly (same ID returned)")
            else:
                print("❌ Caching issue (different ID returned)")
        
        return True

    def test_various_data_scenarios(self):
        """Test with various data scenarios (partial weeks, missing days, zero values)"""
        print("\n" + "="*50)
        print("TESTING VARIOUS DATA SCENARIOS")
        print("="*50)
        
        # Test with no data scenario
        empty_session = "empty_test_session"
        
        success, empty_analytics = self.run_test(
            "Get Analytics for Empty Session",
            "GET",
            f"health/analytics/weekly/{empty_session}",
            200
        )
        
        if success:
            avg_calories = empty_analytics.get('avg_calories', 0)
            overall_expert = empty_analytics.get('overall_expert', '')
            overall_insight = empty_analytics.get('overall_insight', '')
            
            if avg_calories == 0:
                print("✅ Empty session returns zero averages")
            else:
                print(f"❌ Empty session has unexpected data: {avg_calories}")
            
            if 'no data' in overall_expert.lower() or 'no health data' in overall_expert.lower():
                print("✅ Appropriate message for no data")
            else:
                print(f"⚠️  Unexpected expert message for no data: {overall_expert[:50]}...")
            
            if 'start logging' in overall_insight.lower() or 'no data' in overall_insight.lower():
                print("✅ Appropriate insight for no data")
            else:
                print(f"⚠️  Unexpected insight for no data: {overall_insight[:50]}...")
        
        # Test with minimal data scenario
        minimal_session = "minimal_test_session"
        
        # Add just one entry
        success, response = self.run_test(
            "Add Minimal Data",
            "POST",
            "chat",
            200,
            data={"message": "I had a glass of water", "session_id": minimal_session}
        )
        
        if success:
            time.sleep(1)
            
            success, minimal_analytics = self.run_test(
                "Get Analytics for Minimal Data",
                "GET",
                f"health/analytics/weekly/{minimal_session}",
                200
            )
            
            if success:
                avg_hydration = minimal_analytics.get('avg_hydration', 0)
                avg_calories = minimal_analytics.get('avg_calories', 0)
                
                if avg_hydration > 0:
                    print("✅ Minimal hydration data processed")
                else:
                    print("❌ Minimal hydration data not processed")
                
                if avg_calories == 0:
                    print("✅ No calories data correctly shows zero")
                else:
                    print(f"❌ Unexpected calories data: {avg_calories}")
                
                # Check pattern analysis with minimal data
                hydration_pattern = minimal_analytics.get('hydration_pattern', {})
                consistency = hydration_pattern.get('consistency', '')
                
                if consistency in ['no_data', 'insufficient_data']:
                    print("✅ Appropriate consistency analysis for minimal data")
                else:
                    print(f"⚠️  Unexpected consistency for minimal data: {consistency}")
        
        return True

    def test_integration_with_chat_health_logging(self):
        """Test that new health entries affect weekly analytics when regenerated"""
        print("\n" + "="*50)
        print("TESTING INTEGRATION WITH CHAT HEALTH LOGGING")
        print("="*50)
        
        integration_session = "integration_test_session"
        
        # Get initial analytics (should be empty)
        success, initial_analytics = self.run_test(
            "Get Initial Analytics for Integration Test",
            "GET",
            f"health/analytics/weekly/{integration_session}",
            200
        )
        
        if not success:
            return False
        
        initial_calories = initial_analytics.get('avg_calories', 0)
        initial_hydration = initial_analytics.get('avg_hydration', 0)
        
        print(f"📊 Initial averages: Calories={initial_calories}, Hydration={initial_hydration}")
        
        # Add new health entries via chat
        new_entries = [
            "I ate a large pizza",
            "I drank 3 glasses of water",
            "I had a protein shake",
            "I slept 8 hours"
        ]
        
        print("\n🍕 Adding new health entries via chat...")
        for entry in new_entries:
            success, response = self.run_test(
                f"Add Entry: '{entry}'",
                "POST",
                "chat",
                200,
                data={"message": entry, "session_id": integration_session}
            )
            
            if success:
                donna_response = response.get('response', '')
                if any(word in donna_response.lower() for word in ['logged', 'noted', 'calories', 'hydration']):
                    print(f"✅ Entry processed: {entry}")
                else:
                    print(f"⚠️  Entry unclear: {entry}")
            
            time.sleep(0.5)
        
        # Regenerate analytics to pick up new data
        success, regenerated = self.run_test(
            "Regenerate Analytics After New Entries",
            "POST",
            f"health/analytics/weekly/regenerate/{integration_session}",
            200
        )
        
        if not success:
            return False
        
        new_calories = regenerated.get('avg_calories', 0)
        new_hydration = regenerated.get('avg_hydration', 0)
        
        print(f"📊 Updated averages: Calories={new_calories}, Hydration={new_hydration}")
        
        # Verify analytics updated
        if new_calories > initial_calories:
            print("✅ Calories analytics updated after new entries")
        else:
            print(f"❌ Calories not updated: {initial_calories} -> {new_calories}")
        
        if new_hydration > initial_hydration:
            print("✅ Hydration analytics updated after new entries")
        else:
            print(f"❌ Hydration not updated: {initial_hydration} -> {new_hydration}")
        
        # Test session-based data isolation
        # Add data to different session and verify it doesn't affect our session
        other_session = "other_test_session"
        
        success, response = self.run_test(
            "Add Data to Different Session",
            "POST",
            "chat",
            200,
            data={"message": "I ate 10 burgers and drank 5 liters of water", "session_id": other_session}
        )
        
        if success:
            time.sleep(1)
            
            # Get our session analytics again
            success, isolated_analytics = self.run_test(
                "Verify Session Isolation",
                "GET",
                f"health/analytics/weekly/{integration_session}",
                200
            )
            
            if success:
                isolated_calories = isolated_analytics.get('avg_calories', 0)
                isolated_hydration = isolated_analytics.get('avg_hydration', 0)
                
                if isolated_calories == new_calories and isolated_hydration == new_hydration:
                    print("✅ Session-based data isolation working")
                else:
                    print(f"❌ Session isolation failed: {new_calories}->{isolated_calories}, {new_hydration}->{isolated_hydration}")
        
        return True

    def test_error_handling_and_edge_cases(self):
        """Test error handling for weekly analytics"""
        print("\n" + "="*50)
        print("TESTING ERROR HANDLING AND EDGE CASES")
        print("="*50)
        
        # Test invalid session ID
        success, response = self.run_test(
            "Get Analytics for Invalid Session",
            "GET",
            "health/analytics/weekly/invalid_session_123",
            200  # Should still return 200 with empty data
        )
        
        if success:
            avg_calories = response.get('avg_calories', 0)
            if avg_calories == 0:
                print("✅ Invalid session returns empty analytics")
            else:
                print(f"❌ Invalid session has unexpected data: {avg_calories}")
        
        # Test extreme week offsets
        success, response = self.run_test(
            "Get Analytics with Large Negative Offset",
            "GET",
            f"health/analytics/weekly/{self.session_id}",
            200,
            params={"week_offset": -52}  # 1 year ago
        )
        
        if success:
            week_start = response.get('week_start')
            if week_start:
                print(f"✅ Large negative offset handled: {week_start}")
            else:
                print("❌ Large negative offset failed")
        
        success, response = self.run_test(
            "Get Analytics with Large Positive Offset",
            "GET",
            f"health/analytics/weekly/{self.session_id}",
            200,
            params={"week_offset": 10}  # 10 weeks in future
        )
        
        if success:
            week_start = response.get('week_start')
            if week_start:
                print(f"✅ Large positive offset handled: {week_start}")
            else:
                print("❌ Large positive offset failed")
        
        # Test regenerate for non-existent session
        success, response = self.run_test(
            "Regenerate Analytics for Non-existent Session",
            "POST",
            "health/analytics/weekly/regenerate/nonexistent_session",
            200  # Should still work, just return empty analytics
        )
        
        if success:
            print("✅ Regenerate handles non-existent session gracefully")
        
        return True

def main():
    print("🚀 Starting Weekly Health Analytics API Tests")
    print("=" * 60)
    
    tester = WeeklyAnalyticsAPITester()
    
    # Run comprehensive test suite
    test_suites = [
        tester.setup_weekly_test_data,
        tester.test_weekly_analytics_endpoint,
        tester.test_llm_expert_analysis,
        tester.test_data_aggregation_accuracy,
        tester.test_pattern_analysis,
        tester.test_target_integration,
        tester.test_regenerate_analytics,
        tester.test_various_data_scenarios,
        tester.test_integration_with_chat_health_logging,
        tester.test_error_handling_and_edge_cases
    ]
    
    for test_suite in test_suites:
        try:
            test_suite()
        except Exception as e:
            print(f"❌ Test suite failed with error: {str(e)}")
    
    # Print final results
    print("\n" + "="*60)
    print("📊 WEEKLY ANALYTICS TEST RESULTS")
    print("="*60)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All weekly analytics tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed - check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())