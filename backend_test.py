#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for SkillSwap Marketplace
Tests all implemented backend features including authentication, user management,
skill management, and AI matching system.
"""

import requests
import json
import time
import random
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configuration
BASE_URL = "https://18295a7a-1618-48b1-b41c-520e04b88368.preview.emergentagent.com/api"
TIMEOUT = 30

class SkillSwapTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.test_user_id = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {details}")
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None, params: Dict = None) -> requests.Response:
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        
        # Add auth header if token exists
        if self.auth_token and headers is None:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
        elif self.auth_token and headers:
            headers["Authorization"] = f"Bearer {self.auth_token}"
            
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=headers, params=params)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=headers, params=params)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise
    
    def test_health_check(self):
        """Test basic API health"""
        try:
            response = self.make_request("GET", "/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("API Health Check", True, f"API is running: {data.get('message', '')}", data)
            else:
                self.log_test("API Health Check", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("API Health Check", False, f"Error: {str(e)}")
    
    def test_user_registration(self):
        """Test user registration"""
        try:
            # Generate unique test data
            timestamp = int(time.time())
            test_data = {
                "email": f"testuser{timestamp}@skillswap.com",
                "username": f"testuser{timestamp}",
                "password": "SecurePassword123!",
                "first_name": "Sarah",
                "last_name": "Johnson",
                "bio": "Passionate software developer and language enthusiast",
                "location": "San Francisco, CA",
                "timezone": "America/Los_Angeles",
                "role": "both"
            }
            
            response = self.make_request("POST", "/auth/register", test_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.test_user_id = data.get("user", {}).get("id")
                self.log_test("User Registration", True, f"User registered successfully: {data.get('user', {}).get('username')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("User Registration", False, f"Registration failed: {error_detail}")
                
        except Exception as e:
            self.log_test("User Registration", False, f"Error: {str(e)}")
    
    def test_user_login(self):
        """Test user login with existing credentials"""
        try:
            # Use the registered user's credentials
            if not hasattr(self, 'registered_email'):
                # Create a test user first
                timestamp = int(time.time())
                register_data = {
                    "email": f"logintest{timestamp}@skillswap.com",
                    "username": f"logintest{timestamp}",
                    "password": "LoginTest123!",
                    "first_name": "Alex",
                    "last_name": "Smith",
                    "role": "both"
                }
                
                reg_response = self.make_request("POST", "/auth/register", register_data)
                if reg_response.status_code != 200:
                    self.log_test("User Login", False, "Could not create test user for login test")
                    return
                
                self.registered_email = register_data["email"]
                self.registered_password = register_data["password"]
            
            login_data = {
                "email": self.registered_email,
                "password": self.registered_password
            }
            
            response = self.make_request("POST", "/auth/login", login_data)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                user_info = data.get("user", {})
                self.log_test("User Login", True, f"Login successful for user: {user_info.get('username')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("User Login", False, f"Login failed: {error_detail}")
                
        except Exception as e:
            self.log_test("User Login", False, f"Error: {str(e)}")
    
    def test_get_current_user(self):
        """Test getting current user profile"""
        if not self.auth_token:
            self.log_test("Get Current User", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/auth/me")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Current User", True, f"Retrieved profile for: {data.get('username')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Current User", False, f"Failed to get current user: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Current User", False, f"Error: {str(e)}")
    
    def test_get_user_profile(self):
        """Test getting user profile (GET /api/users/profile)"""
        if not self.auth_token:
            self.log_test("Get User Profile", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/users/profile")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get User Profile", True, f"Retrieved profile for: {data.get('username')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get User Profile", False, f"Failed to get profile: {error_detail}")
                
        except Exception as e:
            self.log_test("Get User Profile", False, f"Error: {str(e)}")

    def test_update_user_profile(self):
        """Test updating user profile with new fields (PUT /api/users/profile)"""
        if not self.auth_token:
            self.log_test("Update User Profile", False, "No auth token available")
            return
            
        try:
            update_data = {
                "bio": "Updated bio: Full-stack developer with expertise in Python, React, and AI",
                "location": "Seattle, WA",
                "timezone": "America/Los_Angeles",
                "teaching_style": "Interactive and hands-on approach",
                "learning_style": "Visual learner who prefers practical examples",
                "languages": ["English", "Spanish", "French"],
                "availability": {
                    "monday": ["09:00", "17:00"],
                    "tuesday": ["09:00", "17:00"],
                    "wednesday": ["09:00", "17:00"]
                },
                "profile_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
            }
            
            response = self.make_request("PUT", "/users/profile", update_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Update User Profile", True, f"Profile updated successfully with new fields", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Update User Profile", False, f"Profile update failed: {error_detail}")
                
        except Exception as e:
            self.log_test("Update User Profile", False, f"Error: {str(e)}")
    
    def test_get_all_skills(self):
        """Test getting all available skills"""
        try:
            response = self.make_request("GET", "/skills/")
            
            if response.status_code == 200:
                data = response.json()
                skill_count = len(data)
                self.log_test("Get All Skills", True, f"Retrieved {skill_count} skills", {"skill_count": skill_count, "sample_skills": data[:3] if data else []})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get All Skills", False, f"Failed to get skills: {error_detail}")
                
        except Exception as e:
            self.log_test("Get All Skills", False, f"Error: {str(e)}")
    
    def test_search_skills(self):
        """Test skill search functionality"""
        try:
            # Test searching for programming skills
            response = self.make_request("GET", "/skills/search/query", params={"query": "Python"})
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Search Skills", True, f"Found {len(data)} skills matching 'Python'", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Search Skills", False, f"Skill search failed: {error_detail}")
                
        except Exception as e:
            self.log_test("Search Skills", False, f"Error: {str(e)}")
    
    def test_get_popular_skills(self):
        """Test getting popular skills"""
        try:
            response = self.make_request("GET", "/skills/popular/list")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Popular Skills", True, f"Retrieved {len(data)} popular skills", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Popular Skills", False, f"Failed to get popular skills: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Popular Skills", False, f"Error: {str(e)}")
    
    def test_get_skill_categories(self):
        """Test getting skill categories"""
        try:
            response = self.make_request("GET", "/skills/categories/list")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Skill Categories", True, f"Retrieved {len(data)} skill categories", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Skill Categories", False, f"Failed to get skill categories: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Skill Categories", False, f"Error: {str(e)}")
    
    def test_add_user_skill(self):
        """Test adding skills to user profile"""
        if not self.auth_token:
            self.log_test("Add User Skill", False, "No auth token available")
            return
            
        try:
            # First get available skills to add
            skills_response = self.make_request("GET", "/skills/")
            if skills_response.status_code != 200:
                self.log_test("Add User Skill", False, "Could not retrieve skills list")
                return
                
            skills = skills_response.json()
            if not skills:
                self.log_test("Add User Skill", False, "No skills available to add")
                return
            
            # Add a Python skill
            python_skill = next((skill for skill in skills if "Python" in skill.get("name", "")), skills[0])
            
            skill_data = {
                "skill_id": python_skill["id"],
                "skill_name": python_skill["name"],
                "level": "intermediate",
                "years_experience": 3,
                "certifications": ["Python Institute PCAP"],
                "self_assessment": "Comfortable with web development, data analysis, and automation"
            }
            
            response = self.make_request("POST", "/users/skills", skill_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Add User Skill", True, f"Added skill: {data.get('skill_name')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Add User Skill", False, f"Failed to add skill: {error_detail}")
                
        except Exception as e:
            self.log_test("Add User Skill", False, f"Error: {str(e)}")
    
    def test_get_user_skills(self):
        """Test getting user's skills"""
        if not self.auth_token:
            self.log_test("Get User Skills", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/users/skills")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get User Skills", True, f"Retrieved {len(data)} user skills", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get User Skills", False, f"Failed to get user skills: {error_detail}")
                
        except Exception as e:
            self.log_test("Get User Skills", False, f"Error: {str(e)}")
    
    def test_update_skill_preferences(self):
        """Test updating user skill preferences"""
        if not self.auth_token:
            self.log_test("Update Skill Preferences", False, "No auth token available")
            return
            
        try:
            preferences_data = {
                "skills_offered": ["Python", "JavaScript", "React"],
                "skills_wanted": ["Machine Learning", "DevOps", "UI/UX Design"]
            }
            
            response = self.make_request("PUT", "/users/preferences", params=preferences_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Update Skill Preferences", True, "Skill preferences updated successfully", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Update Skill Preferences", False, f"Failed to update preferences: {error_detail}")
                
        except Exception as e:
            self.log_test("Update Skill Preferences", False, f"Error: {str(e)}")
    
    def test_search_users(self):
        """Test user search functionality"""
        try:
            # Search for users with Python skills
            response = self.make_request("GET", "/users/search", params={"query": "Python"})
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Search Users", True, f"Found {len(data)} users matching 'Python'", {"user_count": len(data)})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Search Users", False, f"User search failed: {error_detail}")
                
        except Exception as e:
            self.log_test("Search Users", False, f"Error: {str(e)}")
    
    def test_get_user_statistics(self):
        """Test getting user statistics"""
        if not self.auth_token:
            self.log_test("Get User Statistics", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/users/statistics")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get User Statistics", True, "Retrieved user statistics", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get User Statistics", False, f"Failed to get statistics: {error_detail}")
                
        except Exception as e:
            self.log_test("Get User Statistics", False, f"Error: {str(e)}")
    
    def test_get_leaderboard(self):
        """Test getting leaderboard"""
        try:
            response = self.make_request("GET", "/users/leaderboard", params={"category": "experience"})
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Leaderboard", True, f"Retrieved leaderboard with {len(data)} users", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Leaderboard", False, f"Failed to get leaderboard: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Leaderboard", False, f"Error: {str(e)}")
    
    def test_find_matches(self):
        """Test AI-powered matching system"""
        if not self.auth_token:
            self.log_test("Find Matches", False, "No auth token available")
            return
            
        try:
            # First ensure user has some skills to match against
            self.test_update_skill_preferences()
            
            response = self.make_request("POST", "/matching/find")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Find Matches", True, f"Found {len(data)} potential matches", {"match_count": len(data)})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Find Matches", False, f"Failed to find matches: {error_detail}")
                
        except Exception as e:
            self.log_test("Find Matches", False, f"Error: {str(e)}")
    
    def test_get_my_matches(self):
        """Test getting user's matches"""
        if not self.auth_token:
            self.log_test("Get My Matches", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/matching/my-matches")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get My Matches", True, f"Retrieved {len(data)} matches", {"match_count": len(data)})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get My Matches", False, f"Failed to get matches: {error_detail}")
                
        except Exception as e:
            self.log_test("Get My Matches", False, f"Error: {str(e)}")
    
    def test_get_match_suggestions(self):
        """Test getting AI match suggestions"""
        if not self.auth_token:
            self.log_test("Get Match Suggestions", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/matching/suggestions")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Match Suggestions", True, f"Retrieved {len(data)} match suggestions", {"suggestion_count": len(data)})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Match Suggestions", False, f"Failed to get suggestions: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Match Suggestions", False, f"Error: {str(e)}")
    
    def test_get_matching_analytics(self):
        """Test getting matching analytics"""
        if not self.auth_token:
            self.log_test("Get Matching Analytics", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/matching/analytics")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Matching Analytics", True, "Retrieved matching analytics", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Matching Analytics", False, f"Failed to get analytics: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Matching Analytics", False, f"Error: {str(e)}")
    
    def test_token_refresh(self):
        """Test JWT token refresh"""
        if not self.auth_token:
            self.log_test("Token Refresh", False, "No auth token available")
            return
            
        try:
            response = self.make_request("POST", "/auth/refresh")
            
            if response.status_code == 200:
                data = response.json()
                new_token = data.get("access_token")
                self.log_test("Token Refresh", True, "Token refreshed successfully", {"token_type": data.get("token_type")})
                # Update token for future tests
                self.auth_token = new_token
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Token Refresh", False, f"Token refresh failed: {error_detail}")
                
        except Exception as e:
            self.log_test("Token Refresh", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting SkillSwap Marketplace Backend API Tests")
        print("=" * 60)
        
        # Basic API tests
        self.test_health_check()
        
        # Authentication tests
        self.test_user_registration()
        self.test_user_login()
        self.test_get_current_user()
        self.test_token_refresh()
        
        # User management tests
        self.test_update_user_profile()
        self.test_get_user_statistics()
        self.test_search_users()
        self.test_get_leaderboard()
        
        # Skill management tests
        self.test_get_all_skills()
        self.test_search_skills()
        self.test_get_popular_skills()
        self.test_get_skill_categories()
        self.test_add_user_skill()
        self.test_get_user_skills()
        self.test_update_skill_preferences()
        
        # AI Matching tests
        self.test_find_matches()
        self.test_get_my_matches()
        self.test_get_match_suggestions()
        self.test_get_matching_analytics()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"  • {test['test']}: {test['details']}")
        
        print("\n🎯 KEY FEATURES TESTED:")
        print("  • User Authentication (Register, Login, JWT)")
        print("  • User Profile Management")
        print("  • Skill Management System")
        print("  • AI-Powered Matching Algorithm")
        print("  • Search and Discovery")
        print("  • Analytics and Statistics")
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = SkillSwapTester()
    tester.run_all_tests()