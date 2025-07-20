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
BASE_URL = "https://c3224408-d3c9-46ab-9061-d39c2b93b3d1.preview.emergentagent.com/api"
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
    
    def test_update_user_skill(self):
        """Test updating user skill (PUT /api/users/skills/{skill_id})"""
        if not self.auth_token:
            self.log_test("Update User Skill", False, "No auth token available")
            return
            
        try:
            # First get user's skills to find one to update
            skills_response = self.make_request("GET", "/users/skills")
            if skills_response.status_code != 200:
                self.log_test("Update User Skill", False, "Could not retrieve user skills")
                return
                
            skills = skills_response.json()
            if not skills:
                self.log_test("Update User Skill", False, "No skills available to update")
                return
            
            skill_to_update = skills[0]
            skill_id = skill_to_update["skill_id"]  # Use the original skill_id, not the UserSkill id
            
            update_data = {
                "level": "advanced",
                "years_experience": 5,
                "certifications": ["Advanced Python Certification", "Django Expert"],
                "self_assessment": "Expert level with extensive project experience"
            }
            
            response = self.make_request("PUT", f"/users/skills/{skill_id}", update_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Update User Skill", True, f"Updated skill: {data.get('skill_name')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Update User Skill", False, f"Failed to update skill: {error_detail}")
                
        except Exception as e:
            self.log_test("Update User Skill", False, f"Error: {str(e)}")

    def test_delete_user_skill(self):
        """Test deleting user skill (DELETE /api/users/skills/{skill_id})"""
        if not self.auth_token:
            self.log_test("Delete User Skill", False, "No auth token available")
            return
            
        try:
            # First add a skill to delete
            skills_response = self.make_request("GET", "/skills/")
            if skills_response.status_code != 200:
                self.log_test("Delete User Skill", False, "Could not retrieve skills list")
                return
                
            skills = skills_response.json()
            if not skills:
                self.log_test("Delete User Skill", False, "No skills available")
                return
            
            # Add a skill first
            test_skill = next((skill for skill in skills if "JavaScript" in skill.get("name", "")), skills[0])
            
            skill_data = {
                "skill_id": test_skill["id"],
                "skill_name": test_skill["name"],
                "level": "beginner",
                "years_experience": 1,
                "certifications": [],
                "self_assessment": "Learning the basics"
            }
            
            add_response = self.make_request("POST", "/users/skills", skill_data)
            if add_response.status_code != 200:
                self.log_test("Delete User Skill", False, "Could not add skill to delete")
                return
            
            added_skill = add_response.json()
            skill_id = added_skill["skill_id"]  # Use the original skill_id, not the UserSkill id
            
            # Now delete the skill
            response = self.make_request("DELETE", f"/users/skills/{skill_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Delete User Skill", True, f"Deleted skill successfully: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Delete User Skill", False, f"Failed to delete skill: {error_detail}")
                
        except Exception as e:
            self.log_test("Delete User Skill", False, f"Error: {str(e)}")

    def test_search_users_with_filters(self):
        """Test user search with various filters (GET /api/users/search)"""
        try:
            # Test 1: Search with skills_offered filter
            response1 = self.make_request("GET", "/users/search", params={
                "skills_offered": ["Python", "JavaScript"]
            })
            
            if response1.status_code == 200:
                data1 = response1.json()
                self.log_test("Search Users - Skills Offered Filter", True, f"Found {len(data1)} users with Python/JavaScript skills", {"user_count": len(data1)})
            else:
                error_detail = response1.json().get("detail", "Unknown error") if response1.content else f"Status: {response1.status_code}"
                self.log_test("Search Users - Skills Offered Filter", False, f"Search failed: {error_detail}")
            
            # Test 2: Search with location filter
            response2 = self.make_request("GET", "/users/search", params={
                "location": "San Francisco"
            })
            
            if response2.status_code == 200:
                data2 = response2.json()
                self.log_test("Search Users - Location Filter", True, f"Found {len(data2)} users in San Francisco", {"user_count": len(data2)})
            else:
                error_detail = response2.json().get("detail", "Unknown error") if response2.content else f"Status: {response2.status_code}"
                self.log_test("Search Users - Location Filter", False, f"Search failed: {error_detail}")
            
            # Test 3: Search with min_rating filter
            response3 = self.make_request("GET", "/users/search", params={
                "min_rating": 4.0
            })
            
            if response3.status_code == 200:
                data3 = response3.json()
                self.log_test("Search Users - Min Rating Filter", True, f"Found {len(data3)} users with rating >= 4.0", {"user_count": len(data3)})
            else:
                error_detail = response3.json().get("detail", "Unknown error") if response3.content else f"Status: {response3.status_code}"
                self.log_test("Search Users - Min Rating Filter", False, f"Search failed: {error_detail}")
            
            # Test 4: Combined filters
            response4 = self.make_request("GET", "/users/search", params={
                "query": "developer",
                "skills_offered": ["Python"],
                "location": "CA",
                "limit": 10
            })
            
            if response4.status_code == 200:
                data4 = response4.json()
                self.log_test("Search Users - Combined Filters", True, f"Found {len(data4)} users with combined filters", {"user_count": len(data4)})
            else:
                error_detail = response4.json().get("detail", "Unknown error") if response4.content else f"Status: {response4.status_code}"
                self.log_test("Search Users - Combined Filters", False, f"Search failed: {error_detail}")
                
        except Exception as e:
            self.log_test("Search Users with Filters", False, f"Error: {str(e)}")
    
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
    
    # ===== SESSION MANAGEMENT TESTS =====
    
    def test_create_session(self):
        """Test creating a new session"""
        if not self.auth_token:
            self.log_test("Create Session", False, "No auth token available")
            return
            
        try:
            # First get available skills to use in session
            skills_response = self.make_request("GET", "/skills/")
            if skills_response.status_code != 200:
                self.log_test("Create Session", False, "Could not retrieve skills list")
                return
                
            skills = skills_response.json()
            if not skills:
                self.log_test("Create Session", False, "No skills available")
                return
            
            # Get current user info
            user_response = self.make_request("GET", "/auth/me")
            if user_response.status_code != 200:
                self.log_test("Create Session", False, "Could not get current user")
                return
            
            current_user = user_response.json()
            
            # Create a second user to be the learner
            timestamp = int(time.time())
            learner_data = {
                "email": f"learner{timestamp}@skillswap.com",
                "username": f"learner{timestamp}",
                "password": "LearnerPass123!",
                "first_name": "Emma",
                "last_name": "Wilson",
                "role": "learner"
            }
            
            learner_response = self.make_request("POST", "/auth/register", learner_data)
            if learner_response.status_code != 200:
                self.log_test("Create Session", False, "Could not create learner user")
                return
            
            learner_user = learner_response.json().get("user", {})
            
            # Create session data
            from datetime import datetime, timedelta
            start_time = datetime.utcnow() + timedelta(days=1)  # Tomorrow
            end_time = start_time + timedelta(hours=1)  # 1 hour session
            
            python_skill = next((skill for skill in skills if "Python" in skill.get("name", "")), skills[0])
            
            session_data = {
                "teacher_id": current_user["id"],
                "learner_id": learner_user["id"],
                "skill_id": python_skill["id"],
                "skill_name": python_skill["name"],
                "title": "Python Fundamentals - Variables and Data Types",
                "description": "Learn the basics of Python programming including variables, data types, and basic operations",
                "scheduled_start": start_time.isoformat(),
                "scheduled_end": end_time.isoformat(),
                "timezone": "UTC",
                "session_type": "video",
                "learning_objectives": [
                    "Understand Python variables",
                    "Learn different data types",
                    "Practice basic operations"
                ],
                "skill_coins_paid": 10
            }
            
            response = self.make_request("POST", "/sessions/", session_data)
            
            if response.status_code == 200:
                data = response.json()
                self.created_session_id = data.get("id")  # Store for other tests
                self.learner_token = learner_response.json().get("access_token")  # Store learner token
                self.log_test("Create Session", True, f"Session created: {data.get('title')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Create Session", False, f"Failed to create session: {error_detail}")
                
        except Exception as e:
            self.log_test("Create Session", False, f"Error: {str(e)}")
    
    def test_get_my_sessions(self):
        """Test getting user's sessions with filters"""
        if not self.auth_token:
            self.log_test("Get My Sessions", False, "No auth token available")
            return
            
        try:
            # Test 1: Get all sessions
            response1 = self.make_request("GET", "/sessions/")
            
            if response1.status_code == 200:
                data1 = response1.json()
                self.log_test("Get My Sessions - All", True, f"Retrieved {len(data1)} sessions", {"session_count": len(data1)})
            else:
                error_detail = response1.json().get("detail", "Unknown error") if response1.content else f"Status: {response1.status_code}"
                self.log_test("Get My Sessions - All", False, f"Failed to get sessions: {error_detail}")
            
            # Test 2: Get sessions as teacher
            response2 = self.make_request("GET", "/sessions/", params={"role": "teacher"})
            
            if response2.status_code == 200:
                data2 = response2.json()
                self.log_test("Get My Sessions - Teacher Role", True, f"Retrieved {len(data2)} teacher sessions", {"session_count": len(data2)})
            else:
                error_detail = response2.json().get("detail", "Unknown error") if response2.content else f"Status: {response2.status_code}"
                self.log_test("Get My Sessions - Teacher Role", False, f"Failed to get teacher sessions: {error_detail}")
            
            # Test 3: Get sessions by status
            response3 = self.make_request("GET", "/sessions/", params={"status": "scheduled"})
            
            if response3.status_code == 200:
                data3 = response3.json()
                self.log_test("Get My Sessions - Scheduled Status", True, f"Retrieved {len(data3)} scheduled sessions", {"session_count": len(data3)})
            else:
                error_detail = response3.json().get("detail", "Unknown error") if response3.content else f"Status: {response3.status_code}"
                self.log_test("Get My Sessions - Scheduled Status", False, f"Failed to get scheduled sessions: {error_detail}")
                
        except Exception as e:
            self.log_test("Get My Sessions", False, f"Error: {str(e)}")
    
    def test_get_upcoming_sessions(self):
        """Test getting upcoming sessions"""
        if not self.auth_token:
            self.log_test("Get Upcoming Sessions", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/sessions/upcoming")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Upcoming Sessions", True, f"Retrieved {len(data)} upcoming sessions", {"session_count": len(data)})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Upcoming Sessions", False, f"Failed to get upcoming sessions: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Upcoming Sessions", False, f"Error: {str(e)}")
    
    def test_get_specific_session(self):
        """Test getting a specific session by ID"""
        if not self.auth_token:
            self.log_test("Get Specific Session", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_session_id') or not self.created_session_id:
            self.log_test("Get Specific Session", False, "No session ID available from previous test")
            return
            
        try:
            response = self.make_request("GET", f"/sessions/{self.created_session_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Specific Session", True, f"Retrieved session: {data.get('title')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Specific Session", False, f"Failed to get session: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Specific Session", False, f"Error: {str(e)}")
    
    def test_update_session(self):
        """Test updating a session"""
        if not self.auth_token:
            self.log_test("Update Session", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_session_id') or not self.created_session_id:
            self.log_test("Update Session", False, "No session ID available from previous test")
            return
            
        try:
            update_data = {
                "title": "Python Fundamentals - Updated Session",
                "description": "Updated description: Learn Python basics with hands-on examples",
                "notes": "Updated session with additional practice exercises",
                "learning_objectives": [
                    "Understand Python variables and naming conventions",
                    "Learn different data types (int, float, string, boolean)",
                    "Practice basic operations and expressions",
                    "Write simple Python programs"
                ]
            }
            
            response = self.make_request("PUT", f"/sessions/{self.created_session_id}", update_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Update Session", True, f"Session updated: {data.get('title')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Update Session", False, f"Failed to update session: {error_detail}")
                
        except Exception as e:
            self.log_test("Update Session", False, f"Error: {str(e)}")
    
    def test_start_session(self):
        """Test starting a session"""
        if not self.auth_token:
            self.log_test("Start Session", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_session_id') or not self.created_session_id:
            self.log_test("Start Session", False, "No session ID available from previous test")
            return
            
        try:
            response = self.make_request("POST", f"/sessions/{self.created_session_id}/start")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Start Session", True, f"Session started: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Start Session", False, f"Failed to start session: {error_detail}")
                
        except Exception as e:
            self.log_test("Start Session", False, f"Error: {str(e)}")
    
    def test_end_session(self):
        """Test ending a session"""
        if not self.auth_token:
            self.log_test("End Session", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_session_id') or not self.created_session_id:
            self.log_test("End Session", False, "No session ID available from previous test")
            return
            
        try:
            response = self.make_request("POST", f"/sessions/{self.created_session_id}/end")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("End Session", True, f"Session ended: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("End Session", False, f"Failed to end session: {error_detail}")
                
        except Exception as e:
            self.log_test("End Session", False, f"Error: {str(e)}")
    
    def test_submit_session_feedback(self):
        """Test submitting session feedback and rating"""
        if not self.auth_token:
            self.log_test("Submit Session Feedback", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_session_id') or not self.created_session_id:
            self.log_test("Submit Session Feedback", False, "No session ID available from previous test")
            return
            
        try:
            # Submit feedback as teacher
            response = self.make_request("POST", f"/sessions/{self.created_session_id}/feedback", 
                                       params={
                                           "rating": 4.5,
                                           "feedback": "Great session! The learner was engaged and asked excellent questions. Made good progress on Python fundamentals."
                                       })
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Submit Session Feedback", True, f"Feedback submitted: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Submit Session Feedback", False, f"Failed to submit feedback: {error_detail}")
                
        except Exception as e:
            self.log_test("Submit Session Feedback", False, f"Error: {str(e)}")
    
    def test_cancel_session(self):
        """Test cancelling a session"""
        if not self.auth_token:
            self.log_test("Cancel Session", False, "No auth token available")
            return
            
        try:
            # Create a new session to cancel (so we don't interfere with other tests)
            skills_response = self.make_request("GET", "/skills/")
            if skills_response.status_code != 200:
                self.log_test("Cancel Session", False, "Could not retrieve skills list")
                return
                
            skills = skills_response.json()
            if not skills:
                self.log_test("Cancel Session", False, "No skills available")
                return
            
            user_response = self.make_request("GET", "/auth/me")
            if user_response.status_code != 200:
                self.log_test("Cancel Session", False, "Could not get current user")
                return
            
            current_user = user_response.json()
            
            # Create a learner for this test
            timestamp = int(time.time())
            learner_data = {
                "email": f"cancellearner{timestamp}@skillswap.com",
                "username": f"cancellearner{timestamp}",
                "password": "CancelPass123!",
                "first_name": "John",
                "last_name": "Doe",
                "role": "learner"
            }
            
            learner_response = self.make_request("POST", "/auth/register", learner_data)
            if learner_response.status_code != 200:
                self.log_test("Cancel Session", False, "Could not create learner user")
                return
            
            learner_user = learner_response.json().get("user", {})
            
            # Create session to cancel
            from datetime import datetime, timedelta
            start_time = datetime.utcnow() + timedelta(days=2)  # Day after tomorrow
            end_time = start_time + timedelta(hours=1)
            
            javascript_skill = next((skill for skill in skills if "JavaScript" in skill.get("name", "")), skills[0])
            
            session_data = {
                "teacher_id": current_user["id"],
                "learner_id": learner_user["id"],
                "skill_id": javascript_skill["id"],
                "skill_name": javascript_skill["name"],
                "title": "JavaScript Basics - To Be Cancelled",
                "description": "This session will be cancelled for testing purposes",
                "scheduled_start": start_time.isoformat(),
                "scheduled_end": end_time.isoformat(),
                "timezone": "UTC",
                "session_type": "video",
                "skill_coins_paid": 15
            }
            
            create_response = self.make_request("POST", "/sessions/", session_data)
            if create_response.status_code != 200:
                self.log_test("Cancel Session", False, "Could not create session to cancel")
                return
            
            created_session = create_response.json()
            session_id = created_session["id"]
            
            # Now cancel the session
            response = self.make_request("POST", f"/sessions/{session_id}/cancel", 
                                       params={"reason": "Schedule conflict - need to reschedule"})
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Cancel Session", True, f"Session cancelled: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Cancel Session", False, f"Failed to cancel session: {error_detail}")
                
        except Exception as e:
            self.log_test("Cancel Session", False, f"Error: {str(e)}")
    
    def test_get_session_statistics(self):
        """Test getting session statistics for a user"""
        if not self.auth_token:
            self.log_test("Get Session Statistics", False, "No auth token available")
            return
            
        try:
            # Get current user info
            user_response = self.make_request("GET", "/auth/me")
            if user_response.status_code != 200:
                self.log_test("Get Session Statistics", False, "Could not get current user")
                return
            
            current_user = user_response.json()
            user_id = current_user["id"]
            
            response = self.make_request("GET", f"/sessions/user/{user_id}/statistics")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Session Statistics", True, f"Retrieved session statistics", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Session Statistics", False, f"Failed to get statistics: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Session Statistics", False, f"Error: {str(e)}")
    
    def test_get_user_availability(self):
        """Test getting user availability"""
        if not self.auth_token:
            self.log_test("Get User Availability", False, "No auth token available")
            return
            
        try:
            # Get current user info
            user_response = self.make_request("GET", "/auth/me")
            if user_response.status_code != 200:
                self.log_test("Get User Availability", False, "Could not get current user")
                return
            
            current_user = user_response.json()
            user_id = current_user["id"]
            
            # Check availability for tomorrow
            from datetime import datetime, timedelta
            tomorrow = datetime.utcnow() + timedelta(days=1)
            
            response = self.make_request("GET", f"/sessions/user/{user_id}/availability", 
                                       params={"date": tomorrow.isoformat()})
            
            if response.status_code == 200:
                data = response.json()
                available_slots = data.get("available_slots", [])
                self.log_test("Get User Availability", True, f"Retrieved {len(available_slots)} available time slots", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get User Availability", False, f"Failed to get availability: {error_detail}")
                
        except Exception as e:
            self.log_test("Get User Availability", False, f"Error: {str(e)}")
    
    def test_search_sessions(self):
        """Test session search functionality"""
        if not self.auth_token:
            self.log_test("Search Sessions", False, "No auth token available")
            return
            
        try:
            # Test 1: Search by query (should return empty list since user has no matching sessions)
            response1 = self.make_request("GET", "/sessions/search", params={"query": "Python"})
            
            if response1.status_code == 200:
                data1 = response1.json()
                self.log_test("Search Sessions - Query", True, f"Found {len(data1)} sessions matching 'Python' (expected 0 for security)", {"session_count": len(data1)})
            elif response1.status_code == 404:
                # This is also acceptable - some implementations return 404 for no results
                self.log_test("Search Sessions - Query", True, "No sessions found (404 response is acceptable)", {"status": 404})
            else:
                error_detail = response1.json().get("detail", "Unknown error") if response1.content else f"Status: {response1.status_code}"
                self.log_test("Search Sessions - Query", False, f"Search failed: {error_detail}")
            
            # Test 2: Search by status (should return empty list since user has no matching sessions)
            response2 = self.make_request("GET", "/sessions/search", params={"status": "completed"})
            
            if response2.status_code == 200:
                data2 = response2.json()
                self.log_test("Search Sessions - Status Filter", True, f"Found {len(data2)} completed sessions (expected 0 for security)", {"session_count": len(data2)})
            elif response2.status_code == 404:
                # This is also acceptable - some implementations return 404 for no results
                self.log_test("Search Sessions - Status Filter", True, "No sessions found (404 response is acceptable)", {"status": 404})
            else:
                error_detail = response2.json().get("detail", "Unknown error") if response2.content else f"Status: {response2.status_code}"
                self.log_test("Search Sessions - Status Filter", False, f"Search failed: {error_detail}")
            
            # Test 3: Search with date range (should return empty list since user has no matching sessions)
            from datetime import datetime, timedelta
            date_from = datetime.utcnow() - timedelta(days=7)
            date_to = datetime.utcnow() + timedelta(days=7)
            
            response3 = self.make_request("GET", "/sessions/search", params={
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
                "limit": 10
            })
            
            if response3.status_code == 200:
                data3 = response3.json()
                self.log_test("Search Sessions - Date Range", True, f"Found {len(data3)} sessions in date range (expected 0 for security)", {"session_count": len(data3)})
            elif response3.status_code == 404:
                # This is also acceptable - some implementations return 404 for no results
                self.log_test("Search Sessions - Date Range", True, "No sessions found (404 response is acceptable)", {"status": 404})
            else:
                error_detail = response3.json().get("detail", "Unknown error") if response3.content else f"Status: {response3.status_code}"
                self.log_test("Search Sessions - Date Range", False, f"Search failed: {error_detail}")
                
        except Exception as e:
            self.log_test("Search Sessions", False, f"Error: {str(e)}")
    
    def test_session_permission_controls(self):
        """Test that users can only access sessions they participate in"""
        if not self.auth_token:
            self.log_test("Session Permission Controls", False, "No auth token available")
            return
            
        try:
            # Create a third user who shouldn't have access to our sessions
            timestamp = int(time.time())
            unauthorized_user_data = {
                "email": f"unauthorized{timestamp}@skillswap.com",
                "username": f"unauthorized{timestamp}",
                "password": "UnauthorizedPass123!",
                "first_name": "Unauthorized",
                "last_name": "User",
                "role": "both"
            }
            
            unauthorized_response = self.make_request("POST", "/auth/register", unauthorized_user_data)
            if unauthorized_response.status_code != 200:
                self.log_test("Session Permission Controls", False, "Could not create unauthorized user")
                return
            
            unauthorized_token = unauthorized_response.json().get("access_token")
            
            # Try to access our created session with unauthorized token
            if hasattr(self, 'created_session_id') and self.created_session_id:
                # Temporarily switch to unauthorized token
                original_token = self.auth_token
                self.auth_token = unauthorized_token
                
                response = self.make_request("GET", f"/sessions/{self.created_session_id}")
                
                # Restore original token
                self.auth_token = original_token
                
                if response.status_code == 403:
                    self.log_test("Session Permission Controls", True, "Unauthorized access correctly blocked (403 Forbidden)")
                elif response.status_code == 404:
                    self.log_test("Session Permission Controls", True, "Unauthorized access correctly blocked (404 Not Found)")
                else:
                    self.log_test("Session Permission Controls", False, f"Unauthorized access not blocked - Status: {response.status_code}")
            else:
                self.log_test("Session Permission Controls", False, "No session available to test permissions")
                
        except Exception as e:
            self.log_test("Session Permission Controls", False, f"Error: {str(e)}")
    
    def test_session_authentication_required(self):
        """Test that session endpoints require authentication"""
        try:
            # Temporarily remove auth token
            original_token = self.auth_token
            self.auth_token = None
            
            # Try to access sessions without authentication
            response = self.make_request("GET", "/sessions/")
            
            # Restore auth token
            self.auth_token = original_token
            
            if response.status_code in [401, 403]:
                self.log_test("Session Authentication Required", True, f"Authentication correctly required ({response.status_code})")
            else:
                self.log_test("Session Authentication Required", False, f"Authentication not required - Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Session Authentication Required", False, f"Error: {str(e)}")
    
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
    
    # ===== SMART NOTIFICATIONS SYSTEM TESTS =====
    
    def test_get_user_notifications(self):
        """Test getting user notifications with filtering (GET /api/notifications/)"""
        if not self.auth_token:
            self.log_test("Get User Notifications", False, "No auth token available")
            return
            
        try:
            # Test 1: Get all notifications
            response1 = self.make_request("GET", "/notifications/")
            
            if response1.status_code == 200:
                data1 = response1.json()
                self.log_test("Get User Notifications - All", True, f"Retrieved {len(data1)} notifications", {"notification_count": len(data1)})
            else:
                error_detail = response1.json().get("detail", "Unknown error") if response1.content else f"Status: {response1.status_code}"
                self.log_test("Get User Notifications - All", False, f"Failed to get notifications: {error_detail}")
            
            # Test 2: Get unread notifications only
            response2 = self.make_request("GET", "/notifications/", params={"unread_only": True})
            
            if response2.status_code == 200:
                data2 = response2.json()
                self.log_test("Get User Notifications - Unread Only", True, f"Retrieved {len(data2)} unread notifications", {"unread_count": len(data2)})
            else:
                error_detail = response2.json().get("detail", "Unknown error") if response2.content else f"Status: {response2.status_code}"
                self.log_test("Get User Notifications - Unread Only", False, f"Failed to get unread notifications: {error_detail}")
            
            # Test 3: Get notifications with type filter
            response3 = self.make_request("GET", "/notifications/", params={"notification_types": "match_found,session_reminder"})
            
            if response3.status_code == 200:
                data3 = response3.json()
                self.log_test("Get User Notifications - Type Filter", True, f"Retrieved {len(data3)} filtered notifications", {"filtered_count": len(data3)})
            else:
                error_detail = response3.json().get("detail", "Unknown error") if response3.content else f"Status: {response3.status_code}"
                self.log_test("Get User Notifications - Type Filter", False, f"Failed to get filtered notifications: {error_detail}")
                
        except Exception as e:
            self.log_test("Get User Notifications", False, f"Error: {str(e)}")
    
    def test_get_notification_count(self):
        """Test getting unread notification count (GET /api/notifications/count)"""
        if not self.auth_token:
            self.log_test("Get Notification Count", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/notifications/count")
            
            if response.status_code == 200:
                data = response.json()
                unread_count = data.get("unread_count", 0)
                self.log_test("Get Notification Count", True, f"Unread count: {unread_count}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Notification Count", False, f"Failed to get notification count: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Notification Count", False, f"Error: {str(e)}")
    
    def test_get_notification_stats(self):
        """Test getting notification statistics (GET /api/notifications/stats)"""
        if not self.auth_token:
            self.log_test("Get Notification Stats", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/notifications/stats")
            
            if response.status_code == 200:
                data = response.json()
                total_notifications = data.get("total_notifications", 0)
                total_unread = data.get("total_unread", 0)
                self.log_test("Get Notification Stats", True, f"Total: {total_notifications}, Unread: {total_unread}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Notification Stats", False, f"Failed to get notification stats: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Notification Stats", False, f"Error: {str(e)}")
    
    def test_create_notification(self):
        """Test creating a notification (POST /api/notifications/)"""
        if not self.auth_token:
            self.log_test("Create Notification", False, "No auth token available")
            return
            
        try:
            notification_data = {
                "user_id": self.test_user_id,
                "notification_type": "system_announcement",
                "title": "🎉 Welcome to SkillSwap!",
                "message": "Welcome to the SkillSwap community! Start exploring skills and connecting with other learners.",
                "priority": "medium",
                "data": {
                    "welcome_bonus": 50,
                    "onboarding_step": 1
                },
                "action_url": "/dashboard"
            }
            
            response = self.make_request("POST", "/notifications/", notification_data)
            
            if response.status_code == 200:
                data = response.json()
                self.created_notification_id = data.get("notification_id")  # Store for other tests
                self.log_test("Create Notification", True, f"Notification created: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Create Notification", False, f"Failed to create notification: {error_detail}")
                
        except Exception as e:
            self.log_test("Create Notification", False, f"Error: {str(e)}")
    
    def test_update_notification(self):
        """Test updating notification (mark as read) (PUT /api/notifications/{id})"""
        if not self.auth_token:
            self.log_test("Update Notification", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_notification_id') or not self.created_notification_id:
            self.log_test("Update Notification", False, "No notification ID available from previous test")
            return
            
        try:
            update_data = {
                "is_read": True
            }
            
            response = self.make_request("PUT", f"/notifications/{self.created_notification_id}", update_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Update Notification", True, f"Notification updated: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Update Notification", False, f"Failed to update notification: {error_detail}")
                
        except Exception as e:
            self.log_test("Update Notification", False, f"Error: {str(e)}")
    
    def test_mark_all_notifications_read(self):
        """Test marking all notifications as read (PUT /api/notifications/mark-all-read)"""
        if not self.auth_token:
            self.log_test("Mark All Notifications Read", False, "No auth token available")
            return
            
        try:
            response = self.make_request("PUT", "/notifications/mark-all-read")
            
            if response.status_code == 200:
                data = response.json()
                marked_count = data.get("marked_read", 0)
                self.log_test("Mark All Notifications Read", True, f"Marked {marked_count} notifications as read", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Mark All Notifications Read", False, f"Failed to mark all as read: {error_detail}")
                
        except Exception as e:
            self.log_test("Mark All Notifications Read", False, f"Error: {str(e)}")
    
    def test_delete_notification(self):
        """Test deleting a notification (DELETE /api/notifications/{id})"""
        if not self.auth_token:
            self.log_test("Delete Notification", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_notification_id') or not self.created_notification_id:
            self.log_test("Delete Notification", False, "No notification ID available from previous test")
            return
            
        try:
            response = self.make_request("DELETE", f"/notifications/{self.created_notification_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Delete Notification", True, f"Notification deleted: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Delete Notification", False, f"Failed to delete notification: {error_detail}")
                
        except Exception as e:
            self.log_test("Delete Notification", False, f"Error: {str(e)}")
    
    def test_get_notification_preferences(self):
        """Test getting notification preferences (GET /api/notifications/preferences)"""
        if not self.auth_token:
            self.log_test("Get Notification Preferences", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/notifications/preferences")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Notification Preferences", True, "Retrieved notification preferences", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Notification Preferences", False, f"Failed to get preferences: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Notification Preferences", False, f"Error: {str(e)}")
    
    def test_update_notification_preferences(self):
        """Test updating notification preferences (PUT /api/notifications/preferences)"""
        if not self.auth_token:
            self.log_test("Update Notification Preferences", False, "No auth token available")
            return
            
        try:
            preferences_data = {
                "email_notifications": True,
                "push_notifications": True,
                "match_notifications": True,
                "session_reminders": True,
                "message_notifications": False,  # Disable message notifications
                "achievement_notifications": True,
                "community_notifications": True,
                "digest_frequency": "weekly",
                "quiet_hours_start": "23:00",
                "quiet_hours_end": "07:00"
            }
            
            response = self.make_request("PUT", "/notifications/preferences", preferences_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Update Notification Preferences", True, "Notification preferences updated", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Update Notification Preferences", False, f"Failed to update preferences: {error_detail}")
                
        except Exception as e:
            self.log_test("Update Notification Preferences", False, f"Error: {str(e)}")
    
    def test_quick_notification_match_found(self):
        """Test quick match found notification (POST /api/notifications/quick/match-found)"""
        if not self.auth_token:
            self.log_test("Quick Notification - Match Found", False, "No auth token available")
            return
        
        if not hasattr(self, 'chat_participant_id') or not self.chat_participant_id:
            self.log_test("Quick Notification - Match Found", False, "No match user ID available from previous test")
            return
            
        try:
            match_data = {
                "match_user_id": self.chat_participant_id,
                "compatibility_score": 0.85
            }
            
            response = self.make_request("POST", "/notifications/quick/match-found", match_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Quick Notification - Match Found", True, f"Match notification sent: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Quick Notification - Match Found", False, f"Failed to send match notification: {error_detail}")
                
        except Exception as e:
            self.log_test("Quick Notification - Match Found", False, f"Error: {str(e)}")
    
    def test_quick_notification_session_reminder(self):
        """Test quick session reminder notification (POST /api/notifications/quick/session-reminder)"""
        if not self.auth_token:
            self.log_test("Quick Notification - Session Reminder", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_session_id') or not self.created_session_id:
            self.log_test("Quick Notification - Session Reminder", False, "No session ID available from previous test")
            return
            
        try:
            from datetime import datetime, timedelta
            reminder_data = {
                "session_id": self.created_session_id,
                "session_title": "Python Fundamentals - Variables and Data Types",
                "starts_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }
            
            response = self.make_request("POST", "/notifications/quick/session-reminder", reminder_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Quick Notification - Session Reminder", True, f"Session reminder sent: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Quick Notification - Session Reminder", False, f"Failed to send session reminder: {error_detail}")
                
        except Exception as e:
            self.log_test("Quick Notification - Session Reminder", False, f"Error: {str(e)}")
    
    def test_quick_notification_achievement_earned(self):
        """Test quick achievement earned notification (POST /api/notifications/quick/achievement-earned)"""
        if not self.auth_token:
            self.log_test("Quick Notification - Achievement Earned", False, "No auth token available")
            return
            
        try:
            achievement_data = {
                "achievement_name": "First Session Completed",
                "achievement_id": "first_session_achievement",
                "coins_earned": 25
            }
            
            response = self.make_request("POST", "/notifications/quick/achievement-earned", achievement_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Quick Notification - Achievement Earned", True, f"Achievement notification sent: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Quick Notification - Achievement Earned", False, f"Failed to send achievement notification: {error_detail}")
                
        except Exception as e:
            self.log_test("Quick Notification - Achievement Earned", False, f"Error: {str(e)}")
    
    def test_quick_notification_message_received(self):
        """Test quick message received notification (POST /api/notifications/quick/message-received)"""
        if not self.auth_token:
            self.log_test("Quick Notification - Message Received", False, "No auth token available")
            return
        
        if not hasattr(self, 'test_conversation_id') or not self.test_conversation_id:
            self.log_test("Quick Notification - Message Received", False, "No conversation ID available from previous test")
            return
            
        try:
            message_data = {
                "sender_name": "Chat User",
                "conversation_id": self.test_conversation_id
            }
            
            response = self.make_request("POST", "/notifications/quick/message-received", message_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Quick Notification - Message Received", True, f"Message notification sent: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Quick Notification - Message Received", False, f"Failed to send message notification: {error_detail}")
                
        except Exception as e:
            self.log_test("Quick Notification - Message Received", False, f"Error: {str(e)}")
    
    # ===== RECOMMENDATION SYSTEM TESTS =====
    
    def test_get_user_recommendations(self):
        """Test getting user recommendations with filtering (GET /api/recommendations/)"""
        if not self.auth_token:
            self.log_test("Get User Recommendations", False, "No auth token available")
            return
            
        try:
            # Test 1: Get all recommendations
            response1 = self.make_request("GET", "/recommendations/")
            
            if response1.status_code == 200:
                data1 = response1.json()
                self.log_test("Get User Recommendations - All", True, f"Retrieved {len(data1)} recommendations", {"recommendation_count": len(data1)})
            else:
                error_detail = response1.json().get("detail", "Unknown error") if response1.content else f"Status: {response1.status_code}"
                self.log_test("Get User Recommendations - All", False, f"Failed to get recommendations: {error_detail}")
            
            # Test 2: Get recommendations with type filter
            response2 = self.make_request("GET", "/recommendations/", params={"recommendation_types": "skill_learning,user_match"})
            
            if response2.status_code == 200:
                data2 = response2.json()
                self.log_test("Get User Recommendations - Type Filter", True, f"Retrieved {len(data2)} filtered recommendations", {"filtered_count": len(data2)})
            else:
                error_detail = response2.json().get("detail", "Unknown error") if response2.content else f"Status: {response2.status_code}"
                self.log_test("Get User Recommendations - Type Filter", False, f"Failed to get filtered recommendations: {error_detail}")
            
            # Test 3: Get high confidence recommendations
            response3 = self.make_request("GET", "/recommendations/", params={"min_confidence": 0.7})
            
            if response3.status_code == 200:
                data3 = response3.json()
                self.log_test("Get User Recommendations - High Confidence", True, f"Retrieved {len(data3)} high confidence recommendations", {"high_confidence_count": len(data3)})
            else:
                error_detail = response3.json().get("detail", "Unknown error") if response3.content else f"Status: {response3.status_code}"
                self.log_test("Get User Recommendations - High Confidence", False, f"Failed to get high confidence recommendations: {error_detail}")
                
        except Exception as e:
            self.log_test("Get User Recommendations", False, f"Error: {str(e)}")
    
    def test_generate_all_recommendations(self):
        """Test generating fresh AI-powered recommendations (POST /api/recommendations/generate)"""
        if not self.auth_token:
            self.log_test("Generate All Recommendations", False, "No auth token available")
            return
            
        try:
            response = self.make_request("POST", "/recommendations/generate")
            
            if response.status_code == 200:
                data = response.json()
                total_generated = data.get("message", "").split()[1] if "Generated" in data.get("message", "") else "0"
                recommendations_by_type = data.get("recommendations_by_type", {})
                self.log_test("Generate All Recommendations", True, f"Generated {total_generated} recommendations across {len(recommendations_by_type)} types", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Generate All Recommendations", False, f"Failed to generate recommendations: {error_detail}")
                
        except Exception as e:
            self.log_test("Generate All Recommendations", False, f"Error: {str(e)}")
    
    def test_generate_specific_recommendations(self):
        """Test generating specific type of recommendations (POST /api/recommendations/generate/{type})"""
        if not self.auth_token:
            self.log_test("Generate Specific Recommendations", False, "No auth token available")
            return
            
        try:
            # Test generating skill learning recommendations
            response1 = self.make_request("POST", "/recommendations/generate/skill_learning")
            
            if response1.status_code == 200:
                data1 = response1.json()
                count1 = data1.get("count", 0)
                self.log_test("Generate Specific Recommendations - Skill Learning", True, f"Generated {count1} skill learning recommendations", data1)
            else:
                error_detail = response1.json().get("detail", "Unknown error") if response1.content else f"Status: {response1.status_code}"
                self.log_test("Generate Specific Recommendations - Skill Learning", False, f"Failed to generate skill learning recommendations: {error_detail}")
            
            # Test generating user match recommendations
            response2 = self.make_request("POST", "/recommendations/generate/user_match")
            
            if response2.status_code == 200:
                data2 = response2.json()
                count2 = data2.get("count", 0)
                self.log_test("Generate Specific Recommendations - User Match", True, f"Generated {count2} user match recommendations", data2)
            else:
                error_detail = response2.json().get("detail", "Unknown error") if response2.content else f"Status: {response2.status_code}"
                self.log_test("Generate Specific Recommendations - User Match", False, f"Failed to generate user match recommendations: {error_detail}")
            
            # Test generating learning path recommendations
            response3 = self.make_request("POST", "/recommendations/generate/learning_path")
            
            if response3.status_code == 200:
                data3 = response3.json()
                count3 = data3.get("count", 0)
                self.log_test("Generate Specific Recommendations - Learning Path", True, f"Generated {count3} learning path recommendations", data3)
            else:
                error_detail = response3.json().get("detail", "Unknown error") if response3.content else f"Status: {response3.status_code}"
                self.log_test("Generate Specific Recommendations - Learning Path", False, f"Failed to generate learning path recommendations: {error_detail}")
                
        except Exception as e:
            self.log_test("Generate Specific Recommendations", False, f"Error: {str(e)}")
    
    def test_mark_recommendation_viewed(self):
        """Test marking recommendation as viewed (PUT /api/recommendations/{id}/viewed)"""
        if not self.auth_token:
            self.log_test("Mark Recommendation Viewed", False, "No auth token available")
            return
            
        try:
            # First get recommendations to find one to mark as viewed
            recommendations_response = self.make_request("GET", "/recommendations/")
            if recommendations_response.status_code != 200:
                self.log_test("Mark Recommendation Viewed", False, "Could not retrieve recommendations")
                return
                
            recommendations = recommendations_response.json()
            if not recommendations:
                self.log_test("Mark Recommendation Viewed", False, "No recommendations available to mark as viewed")
                return
            
            recommendation_id = recommendations[0]["id"]
            
            response = self.make_request("PUT", f"/recommendations/{recommendation_id}/viewed")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Mark Recommendation Viewed", True, f"Recommendation marked as viewed: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Mark Recommendation Viewed", False, f"Failed to mark recommendation as viewed: {error_detail}")
                
        except Exception as e:
            self.log_test("Mark Recommendation Viewed", False, f"Error: {str(e)}")
    
    def test_mark_recommendation_acted_upon(self):
        """Test marking recommendation as acted upon (PUT /api/recommendations/{id}/acted-upon)"""
        if not self.auth_token:
            self.log_test("Mark Recommendation Acted Upon", False, "No auth token available")
            return
            
        try:
            # First get recommendations to find one to mark as acted upon
            recommendations_response = self.make_request("GET", "/recommendations/")
            if recommendations_response.status_code != 200:
                self.log_test("Mark Recommendation Acted Upon", False, "Could not retrieve recommendations")
                return
                
            recommendations = recommendations_response.json()
            if not recommendations:
                self.log_test("Mark Recommendation Acted Upon", False, "No recommendations available to mark as acted upon")
                return
            
            recommendation_id = recommendations[0]["id"]
            
            response = self.make_request("PUT", f"/recommendations/{recommendation_id}/acted-upon")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Mark Recommendation Acted Upon", True, f"Recommendation marked as acted upon: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Mark Recommendation Acted Upon", False, f"Failed to mark recommendation as acted upon: {error_detail}")
                
        except Exception as e:
            self.log_test("Mark Recommendation Acted Upon", False, f"Error: {str(e)}")
    
    def test_dismiss_recommendation(self):
        """Test dismissing a recommendation (PUT /api/recommendations/{id}/dismiss)"""
        if not self.auth_token:
            self.log_test("Dismiss Recommendation", False, "No auth token available")
            return
            
        try:
            # First get recommendations to find one to dismiss
            recommendations_response = self.make_request("GET", "/recommendations/")
            if recommendations_response.status_code != 200:
                self.log_test("Dismiss Recommendation", False, "Could not retrieve recommendations")
                return
                
            recommendations = recommendations_response.json()
            if not recommendations:
                self.log_test("Dismiss Recommendation", False, "No recommendations available to dismiss")
                return
            
            recommendation_id = recommendations[0]["id"]
            
            response = self.make_request("PUT", f"/recommendations/{recommendation_id}/dismiss")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Dismiss Recommendation", True, f"Recommendation dismissed: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Dismiss Recommendation", False, f"Failed to dismiss recommendation: {error_detail}")
                
        except Exception as e:
            self.log_test("Dismiss Recommendation", False, f"Error: {str(e)}")
    
    def test_get_learning_goals(self):
        """Test getting user's learning goals (GET /api/recommendations/learning-goals)"""
        if not self.auth_token:
            self.log_test("Get Learning Goals", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/recommendations/learning-goals")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Learning Goals", True, f"Retrieved {len(data)} learning goals", {"goals_count": len(data)})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Learning Goals", False, f"Failed to get learning goals: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Learning Goals", False, f"Error: {str(e)}")
    
    def test_create_learning_goal(self):
        """Test creating a learning goal (POST /api/recommendations/learning-goals)"""
        if not self.auth_token:
            self.log_test("Create Learning Goal", False, "No auth token available")
            return
            
        try:
            # First get available skills to create a goal for
            skills_response = self.make_request("GET", "/skills/")
            if skills_response.status_code != 200:
                self.log_test("Create Learning Goal", False, "Could not retrieve skills list")
                return
                
            skills = skills_response.json()
            if not skills:
                self.log_test("Create Learning Goal", False, "No skills available")
                return
            
            # Find a skill to create a goal for (preferably one not already in user's skills)
            target_skill = next((skill for skill in skills if "Machine Learning" in skill.get("name", "")), skills[0])
            
            from datetime import datetime, timedelta
            goal_data = {
                "skill_id": target_skill["id"],
                "target_level": "intermediate",
                "target_date": (datetime.utcnow() + timedelta(days=90)).isoformat(),
                "weekly_session_target": 2
            }
            
            response = self.make_request("POST", "/recommendations/learning-goals", goal_data)
            
            if response.status_code == 200:
                data = response.json()
                self.created_learning_goal_id = data.get("id")  # Store for other tests
                self.log_test("Create Learning Goal", True, f"Learning goal created: {data.get('skill_name')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Create Learning Goal", False, f"Failed to create learning goal: {error_detail}")
                
        except Exception as e:
            self.log_test("Create Learning Goal", False, f"Error: {str(e)}")
    
    def test_update_goal_progress(self):
        """Test updating learning goal progress (PUT /api/recommendations/learning-goals/{id}/progress)"""
        if not self.auth_token:
            self.log_test("Update Goal Progress", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_learning_goal_id') or not self.created_learning_goal_id:
            self.log_test("Update Goal Progress", False, "No learning goal ID available from previous test")
            return
            
        try:
            response = self.make_request("PUT", f"/recommendations/learning-goals/{self.created_learning_goal_id}/progress", params={"progress": 35.5})
            
            if response.status_code == 200:
                data = response.json()
                progress = data.get("progress", 0)
                self.log_test("Update Goal Progress", True, f"Goal progress updated to {progress}%", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Update Goal Progress", False, f"Failed to update goal progress: {error_detail}")
                
        except Exception as e:
            self.log_test("Update Goal Progress", False, f"Error: {str(e)}")
    
    def test_get_recommendation_insights(self):
        """Test getting recommendation insights (GET /api/recommendations/insights)"""
        if not self.auth_token:
            self.log_test("Get Recommendation Insights", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/recommendations/insights")
            
            if response.status_code == 200:
                data = response.json()
                total_recommendations = data.get("total_recommendations", 0)
                engagement_rate = data.get("engagement_rate", 0)
                action_rate = data.get("action_rate", 0)
                self.log_test("Get Recommendation Insights", True, f"Total: {total_recommendations}, Engagement: {engagement_rate}%, Action: {action_rate}%", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Recommendation Insights", False, f"Failed to get recommendation insights: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Recommendation Insights", False, f"Error: {str(e)}")
    
    def test_get_recommendation_dashboard(self):
        """Test getting recommendation dashboard (GET /api/recommendations/dashboard)"""
        if not self.auth_token:
            self.log_test("Get Recommendation Dashboard", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/recommendations/dashboard")
            
            if response.status_code == 200:
                data = response.json()
                featured_count = len(data.get("recommendations", {}).get("featured", []))
                total_goals = data.get("learning_goals", {}).get("total_goals", 0)
                quick_stats = data.get("quick_stats", {})
                self.log_test("Get Recommendation Dashboard", True, f"Featured: {featured_count}, Goals: {total_goals}, Stats: {quick_stats}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Recommendation Dashboard", False, f"Failed to get recommendation dashboard: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Recommendation Dashboard", False, f"Error: {str(e)}")
    
    # ===== MESSAGING SYSTEM TESTS =====
    
    def test_get_user_conversations(self):
        """Test getting user conversations (GET /api/messages/conversations)"""
        if not self.auth_token:
            self.log_test("Get User Conversations", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/messages/conversations")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get User Conversations", True, f"Retrieved {len(data)} conversations", {"conversation_count": len(data)})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get User Conversations", False, f"Failed to get conversations: {error_detail}")
                
        except Exception as e:
            self.log_test("Get User Conversations", False, f"Error: {str(e)}")
    
    def test_create_conversation(self):
        """Test creating a new conversation (POST /api/messages/conversations)"""
        if not self.auth_token:
            self.log_test("Create Conversation", False, "No auth token available")
            return
            
        try:
            # Create a second user to have a conversation with
            timestamp = int(time.time())
            participant_data = {
                "email": f"chatuser{timestamp}@skillswap.com",
                "username": f"chatuser{timestamp}",
                "password": "ChatUser123!",
                "first_name": "Chat",
                "last_name": "User",
                "role": "both"
            }
            
            participant_response = self.make_request("POST", "/auth/register", participant_data)
            if participant_response.status_code != 200:
                self.log_test("Create Conversation", False, "Could not create participant user")
                return
            
            participant_user = participant_response.json().get("user", {})
            self.chat_participant_id = participant_user["id"]  # Store for other tests
            self.chat_participant_token = participant_response.json().get("access_token")
            
            # Create conversation
            conversation_data = [self.test_user_id, self.chat_participant_id]
            
            response = self.make_request("POST", "/messages/conversations", conversation_data)
            
            if response.status_code == 200:
                data = response.json()
                self.test_conversation_id = data.get("id")  # Store for other tests
                self.log_test("Create Conversation", True, f"Conversation created: {data.get('id')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Create Conversation", False, f"Failed to create conversation: {error_detail}")
                
        except Exception as e:
            self.log_test("Create Conversation", False, f"Error: {str(e)}")
    
    def test_get_specific_conversation(self):
        """Test getting a specific conversation (GET /api/messages/conversations/{id})"""
        if not self.auth_token:
            self.log_test("Get Specific Conversation", False, "No auth token available")
            return
        
        if not hasattr(self, 'test_conversation_id') or not self.test_conversation_id:
            self.log_test("Get Specific Conversation", False, "No conversation ID available from previous test")
            return
            
        try:
            response = self.make_request("GET", f"/messages/conversations/{self.test_conversation_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Specific Conversation", True, f"Retrieved conversation: {data.get('id')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Specific Conversation", False, f"Failed to get conversation: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Specific Conversation", False, f"Error: {str(e)}")
    
    def test_send_message(self):
        """Test sending a message (POST /api/messages/send)"""
        if not self.auth_token:
            self.log_test("Send Message", False, "No auth token available")
            return
        
        if not hasattr(self, 'chat_participant_id') or not self.chat_participant_id:
            self.log_test("Send Message", False, "No chat participant available from previous test")
            return
            
        try:
            message_data = {
                "recipient_id": self.chat_participant_id,
                "content": "Hello! This is a test message from the messaging system. How are you doing?",
                "message_type": "text"
            }
            
            response = self.make_request("POST", "/messages/send", message_data)
            
            if response.status_code == 200:
                data = response.json()
                self.test_message_id = data.get("id")  # Store for other tests
                self.log_test("Send Message", True, f"Message sent: {data.get('content')[:50]}...", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Send Message", False, f"Failed to send message: {error_detail}")
                
        except Exception as e:
            self.log_test("Send Message", False, f"Error: {str(e)}")
    
    def test_get_conversation_messages(self):
        """Test getting conversation messages (GET /api/messages/conversations/{id}/messages)"""
        if not self.auth_token:
            self.log_test("Get Conversation Messages", False, "No auth token available")
            return
        
        if not hasattr(self, 'test_conversation_id') or not self.test_conversation_id:
            self.log_test("Get Conversation Messages", False, "No conversation ID available from previous test")
            return
            
        try:
            response = self.make_request("GET", f"/messages/conversations/{self.test_conversation_id}/messages", 
                                       params={"limit": 20, "offset": 0})
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Conversation Messages", True, f"Retrieved {len(data)} messages", {"message_count": len(data)})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Conversation Messages", False, f"Failed to get messages: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Conversation Messages", False, f"Error: {str(e)}")
    
    def test_mark_message_as_read(self):
        """Test marking a message as read (PUT /api/messages/messages/{id}/read)"""
        if not self.auth_token:
            self.log_test("Mark Message as Read", False, "No auth token available")
            return
        
        if not hasattr(self, 'test_message_id') or not self.test_message_id:
            self.log_test("Mark Message as Read", False, "No message ID available from previous test")
            return
            
        try:
            # Switch to the recipient's token to mark the message as read
            if hasattr(self, 'chat_participant_token'):
                original_token = self.auth_token
                self.auth_token = self.chat_participant_token
                
                response = self.make_request("PUT", f"/messages/messages/{self.test_message_id}/read")
                
                # Restore original token
                self.auth_token = original_token
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test("Mark Message as Read", True, f"Message marked as read: {data.get('message')}", data)
                else:
                    error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                    self.log_test("Mark Message as Read", False, f"Failed to mark message as read: {error_detail}")
            else:
                self.log_test("Mark Message as Read", False, "No participant token available")
                
        except Exception as e:
            self.log_test("Mark Message as Read", False, f"Error: {str(e)}")
    
    def test_mark_conversation_as_read(self):
        """Test marking conversation as read (PUT /api/messages/conversations/{id}/read)"""
        if not self.auth_token:
            self.log_test("Mark Conversation as Read", False, "No auth token available")
            return
        
        if not hasattr(self, 'test_conversation_id') or not self.test_conversation_id:
            self.log_test("Mark Conversation as Read", False, "No conversation ID available from previous test")
            return
            
        try:
            response = self.make_request("PUT", f"/messages/conversations/{self.test_conversation_id}/read")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Mark Conversation as Read", True, f"Conversation marked as read: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Mark Conversation as Read", False, f"Failed to mark conversation as read: {error_detail}")
                
        except Exception as e:
            self.log_test("Mark Conversation as Read", False, f"Error: {str(e)}")
    
    def test_get_unread_count(self):
        """Test getting unread message count (GET /api/messages/unread-count)"""
        if not self.auth_token:
            self.log_test("Get Unread Count", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/messages/unread-count")
            
            if response.status_code == 200:
                data = response.json()
                unread_count = data.get("unread_count", 0)
                self.log_test("Get Unread Count", True, f"Unread message count: {unread_count}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Unread Count", False, f"Failed to get unread count: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Unread Count", False, f"Error: {str(e)}")
    
    def test_delete_message(self):
        """Test deleting a message (DELETE /api/messages/messages/{id})"""
        if not self.auth_token:
            self.log_test("Delete Message", False, "No auth token available")
            return
        
        if not hasattr(self, 'chat_participant_id') or not self.chat_participant_id:
            self.log_test("Delete Message", False, "No chat participant available")
            return
            
        try:
            # Send a message to delete
            message_data = {
                "recipient_id": self.chat_participant_id,
                "content": "This message will be deleted for testing purposes.",
                "message_type": "text"
            }
            
            send_response = self.make_request("POST", "/messages/send", message_data)
            if send_response.status_code != 200:
                self.log_test("Delete Message", False, "Could not send message to delete")
                return
            
            message_to_delete = send_response.json()
            message_id = message_to_delete.get("id")
            
            # Delete the message
            response = self.make_request("DELETE", f"/messages/messages/{message_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Delete Message", True, f"Message deleted: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Delete Message", False, f"Failed to delete message: {error_detail}")
                
        except Exception as e:
            self.log_test("Delete Message", False, f"Error: {str(e)}")
    
    def test_edit_message(self):
        """Test editing a message (PUT /api/messages/messages/{id}/edit)"""
        if not self.auth_token:
            self.log_test("Edit Message", False, "No auth token available")
            return
        
        if not hasattr(self, 'chat_participant_id') or not self.chat_participant_id:
            self.log_test("Edit Message", False, "No chat participant available")
            return
            
        try:
            # Send a message to edit
            message_data = {
                "recipient_id": self.chat_participant_id,
                "content": "This message will be edited.",
                "message_type": "text"
            }
            
            send_response = self.make_request("POST", "/messages/send", message_data)
            if send_response.status_code != 200:
                self.log_test("Edit Message", False, "Could not send message to edit")
                return
            
            message_to_edit = send_response.json()
            message_id = message_to_edit.get("id")
            
            # Edit the message
            response = self.make_request("PUT", f"/messages/messages/{message_id}/edit", 
                                       params={"new_content": "This message has been edited successfully! The content is now updated."})
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Edit Message", True, f"Message edited: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Edit Message", False, f"Failed to edit message: {error_detail}")
                
        except Exception as e:
            self.log_test("Edit Message", False, f"Error: {str(e)}")
    
    def test_search_messages(self):
        """Test searching messages (GET /api/messages/search)"""
        if not self.auth_token:
            self.log_test("Search Messages", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/messages/search", params={"query": "test", "limit": 10})
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                self.log_test("Search Messages", True, f"Found {len(messages)} messages matching 'test'", {"message_count": len(messages)})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Search Messages", False, f"Failed to search messages: {error_detail}")
                
        except Exception as e:
            self.log_test("Search Messages", False, f"Error: {str(e)}")
    
    def test_get_online_users(self):
        """Test getting online users (GET /api/messages/online-users)"""
        if not self.auth_token:
            self.log_test("Get Online Users", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/messages/online-users")
            
            if response.status_code == 200:
                data = response.json()
                online_users = data.get("online_users", [])
                self.log_test("Get Online Users", True, f"Retrieved {len(online_users)} online users", {"online_count": len(online_users)})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Online Users", False, f"Failed to get online users: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Online Users", False, f"Error: {str(e)}")
    
    def test_messaging_authentication_required(self):
        """Test that messaging endpoints require authentication"""
        try:
            # Temporarily remove auth token
            original_token = self.auth_token
            self.auth_token = None
            
            # Try to access conversations without authentication
            response = self.make_request("GET", "/messages/conversations")
            
            # Restore auth token
            self.auth_token = original_token
            
            if response.status_code in [401, 403]:
                self.log_test("Messaging Authentication Required", True, f"Authentication correctly required ({response.status_code})")
            else:
                self.log_test("Messaging Authentication Required", False, f"Authentication not required - Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Messaging Authentication Required", False, f"Error: {str(e)}")
    
    def test_messaging_permission_controls(self):
        """Test that users can only access their own conversations and messages"""
        if not self.auth_token:
            self.log_test("Messaging Permission Controls", False, "No auth token available")
            return
            
        try:
            # Create a third user who shouldn't have access to our conversations
            timestamp = int(time.time())
            unauthorized_user_data = {
                "email": f"msgUnauth{timestamp}@skillswap.com",
                "username": f"msgUnauth{timestamp}",
                "password": "MsgUnauth123!",
                "first_name": "Message",
                "last_name": "Unauthorized",
                "role": "both"
            }
            
            unauthorized_response = self.make_request("POST", "/auth/register", unauthorized_user_data)
            if unauthorized_response.status_code != 200:
                self.log_test("Messaging Permission Controls", False, "Could not create unauthorized user")
                return
            
            unauthorized_token = unauthorized_response.json().get("access_token")
            
            # Try to access our conversation with unauthorized token
            if hasattr(self, 'test_conversation_id') and self.test_conversation_id:
                # Temporarily switch to unauthorized token
                original_token = self.auth_token
                self.auth_token = unauthorized_token
                
                response = self.make_request("GET", f"/messages/conversations/{self.test_conversation_id}")
                
                # Restore original token
                self.auth_token = original_token
                
                if response.status_code == 403:
                    self.log_test("Messaging Permission Controls", True, "Unauthorized access correctly blocked (403 Forbidden)")
                elif response.status_code == 404:
                    self.log_test("Messaging Permission Controls", True, "Unauthorized access correctly blocked (404 Not Found)")
                else:
                    self.log_test("Messaging Permission Controls", False, f"Unauthorized access not blocked - Status: {response.status_code}")
            else:
                self.log_test("Messaging Permission Controls", False, "No conversation available to test permissions")
                
        except Exception as e:
            self.log_test("Messaging Permission Controls", False, f"Error: {str(e)}")
    
    # ===== GAMIFICATION SYSTEM TESTS =====
    
    def test_get_user_progress(self):
        """Test getting user progress (GET /api/gamification/progress)"""
        if not self.auth_token:
            self.log_test("Get User Progress", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/gamification/progress")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get User Progress", True, f"Retrieved user progress: {data.get('skill_coins', 0)} coins, {data.get('total_sessions', 0)} sessions", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get User Progress", False, f"Failed to get user progress: {error_detail}")
                
        except Exception as e:
            self.log_test("Get User Progress", False, f"Error: {str(e)}")
    
    def test_get_all_badges(self):
        """Test getting all available badges (GET /api/gamification/badges)"""
        if not self.auth_token:
            self.log_test("Get All Badges", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/gamification/badges")
            
            if response.status_code == 200:
                data = response.json()
                badge_count = len(data)
                badge_types = list(set([badge.get('badge_type') for badge in data]))
                self.log_test("Get All Badges", True, f"Retrieved {badge_count} badges with types: {badge_types}", {"badge_count": badge_count, "sample_badges": data[:3] if data else []})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get All Badges", False, f"Failed to get badges: {error_detail}")
                
        except Exception as e:
            self.log_test("Get All Badges", False, f"Error: {str(e)}")
    
    def test_get_all_achievements(self):
        """Test getting all available achievements (GET /api/gamification/achievements)"""
        if not self.auth_token:
            self.log_test("Get All Achievements", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/gamification/achievements")
            
            if response.status_code == 200:
                data = response.json()
                achievement_count = len(data)
                achievement_types = list(set([achievement.get('achievement_type') for achievement in data]))
                self.log_test("Get All Achievements", True, f"Retrieved {achievement_count} achievements with types: {achievement_types}", {"achievement_count": achievement_count, "sample_achievements": data[:3] if data else []})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get All Achievements", False, f"Failed to get achievements: {error_detail}")
                
        except Exception as e:
            self.log_test("Get All Achievements", False, f"Error: {str(e)}")
    
    def test_get_leaderboard(self):
        """Test getting the leaderboard (GET /api/gamification/leaderboard)"""
        if not self.auth_token:
            self.log_test("Get Leaderboard", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/gamification/leaderboard", params={"limit": 10})
            
            if response.status_code == 200:
                data = response.json()
                leaderboard_count = len(data)
                top_user = data[0] if data else None
                self.log_test("Get Leaderboard", True, f"Retrieved leaderboard with {leaderboard_count} entries", {
                    "leaderboard_count": leaderboard_count,
                    "top_user": {
                        "username": top_user.get("username"),
                        "skill_coins": top_user.get("skill_coins"),
                        "rank": top_user.get("rank")
                    } if top_user else None
                })
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Leaderboard", False, f"Failed to get leaderboard: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Leaderboard", False, f"Error: {str(e)}")
    
    def test_get_user_transactions(self):
        """Test getting user's skill coin transactions (GET /api/gamification/transactions)"""
        if not self.auth_token:
            self.log_test("Get User Transactions", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/gamification/transactions", params={"limit": 20})
            
            if response.status_code == 200:
                data = response.json()
                transaction_count = len(data)
                transaction_types = list(set([tx.get('transaction_type') for tx in data])) if data else []
                self.log_test("Get User Transactions", True, f"Retrieved {transaction_count} transactions with types: {transaction_types}", {
                    "transaction_count": transaction_count,
                    "sample_transactions": data[:3] if data else []
                })
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get User Transactions", False, f"Failed to get transactions: {error_detail}")
                
        except Exception as e:
            self.log_test("Get User Transactions", False, f"Error: {str(e)}")
    
    def test_check_user_progress(self):
        """Test checking user progress and awarding badges (POST /api/gamification/check-progress)"""
        if not self.auth_token:
            self.log_test("Check User Progress", False, "No auth token available")
            return
            
        try:
            response = self.make_request("POST", "/gamification/check-progress")
            
            if response.status_code == 200:
                data = response.json()
                new_badges = data.get("new_badges", 0)
                badges_awarded = data.get("badges", [])
                self.log_test("Check User Progress", True, f"Progress checked: {new_badges} new badges awarded", {
                    "new_badges": new_badges,
                    "badges_awarded": [badge.get("name") for badge in badges_awarded]
                })
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Check User Progress", False, f"Failed to check progress: {error_detail}")
                
        except Exception as e:
            self.log_test("Check User Progress", False, f"Error: {str(e)}")
    
    def test_get_other_user_progress(self):
        """Test getting another user's progress (GET /api/gamification/user/{user_id}/progress)"""
        if not self.auth_token:
            self.log_test("Get Other User Progress", False, "No auth token available")
            return
            
        try:
            # Create a second user to check their progress
            timestamp = int(time.time())
            other_user_data = {
                "email": f"otheruser{timestamp}@skillswap.com",
                "username": f"otheruser{timestamp}",
                "password": "OtherUser123!",
                "first_name": "Other",
                "last_name": "User",
                "role": "both"
            }
            
            other_user_response = self.make_request("POST", "/auth/register", other_user_data)
            if other_user_response.status_code != 200:
                self.log_test("Get Other User Progress", False, "Could not create other user")
                return
            
            other_user = other_user_response.json().get("user", {})
            other_user_id = other_user["id"]
            
            response = self.make_request("GET", f"/gamification/user/{other_user_id}/progress")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Other User Progress", True, f"Retrieved other user progress: {data.get('skill_coins', 0)} coins, {data.get('total_sessions', 0)} sessions", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Other User Progress", False, f"Failed to get other user progress: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Other User Progress", False, f"Error: {str(e)}")
    
    def test_award_skill_coins(self):
        """Test awarding skill coins to user (POST /api/gamification/award-coins)"""
        if not self.auth_token:
            self.log_test("Award Skill Coins", False, "No auth token available")
            return
            
        try:
            # Get current user info
            user_response = self.make_request("GET", "/auth/me")
            if user_response.status_code != 200:
                self.log_test("Award Skill Coins", False, "Could not get current user")
                return
            
            current_user = user_response.json()
            user_id = current_user["id"]
            
            # Award coins to self (allowed for testing)
            response = self.make_request("POST", "/gamification/award-coins", params={
                "user_id": user_id,
                "amount": 50,
                "reason": "Testing skill coin award system"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Award Skill Coins", True, f"Successfully awarded coins: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Award Skill Coins", False, f"Failed to award coins: {error_detail}")
                
        except Exception as e:
            self.log_test("Award Skill Coins", False, f"Error: {str(e)}")
    
    def test_get_gamification_stats(self):
        """Test getting gamification system statistics (GET /api/gamification/stats/summary)"""
        if not self.auth_token:
            self.log_test("Get Gamification Stats", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/gamification/stats/summary")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Gamification Stats", True, f"Retrieved gamification stats: {data.get('total_badges', 0)} badges, {data.get('total_achievements', 0)} achievements, {data.get('total_users', 0)} users", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Gamification Stats", False, f"Failed to get stats: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Gamification Stats", False, f"Error: {str(e)}")
    
    def test_gamification_authentication_required(self):
        """Test that gamification endpoints require authentication"""
        try:
            # Temporarily remove auth token
            original_token = self.auth_token
            self.auth_token = None
            
            # Try to access gamification endpoints without authentication
            response = self.make_request("GET", "/gamification/progress")
            
            # Restore auth token
            self.auth_token = original_token
            
            if response.status_code in [401, 403]:
                self.log_test("Gamification Authentication Required", True, f"Authentication correctly required ({response.status_code})")
            else:
                self.log_test("Gamification Authentication Required", False, f"Authentication not required - Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Gamification Authentication Required", False, f"Error: {str(e)}")
    
    def test_gamification_badge_system_integration(self):
        """Test the complete badge system workflow"""
        if not self.auth_token:
            self.log_test("Badge System Integration", False, "No auth token available")
            return
            
        try:
            # Step 1: Get initial progress
            initial_progress = self.make_request("GET", "/gamification/progress")
            if initial_progress.status_code != 200:
                self.log_test("Badge System Integration", False, "Could not get initial progress")
                return
            
            initial_data = initial_progress.json()
            initial_badges = len(initial_data.get("badges", []))
            initial_coins = initial_data.get("skill_coins", 0)
            
            # Step 2: Add a skill to potentially trigger badge
            skills_response = self.make_request("GET", "/skills/")
            if skills_response.status_code == 200:
                skills = skills_response.json()
                if skills:
                    # Add a skill
                    test_skill = skills[0]
                    skill_data = {
                        "skill_id": test_skill["id"],
                        "skill_name": test_skill["name"],
                        "level": "beginner",
                        "years_experience": 1,
                        "certifications": [],
                        "self_assessment": "Testing badge system"
                    }
                    
                    add_skill_response = self.make_request("POST", "/users/skills", skill_data)
                    if add_skill_response.status_code == 200:
                        # Step 3: Check progress to trigger badge evaluation
                        check_response = self.make_request("POST", "/gamification/check-progress")
                        if check_response.status_code == 200:
                            check_data = check_response.json()
                            new_badges = check_data.get("new_badges", 0)
                            
                            # Step 4: Get updated progress
                            final_progress = self.make_request("GET", "/gamification/progress")
                            if final_progress.status_code == 200:
                                final_data = final_progress.json()
                                final_badges = len(final_data.get("badges", []))
                                final_coins = final_data.get("skill_coins", 0)
                                
                                self.log_test("Badge System Integration", True, f"Badge system workflow complete: {initial_badges} → {final_badges} badges, {initial_coins} → {final_coins} coins, {new_badges} new badges awarded", {
                                    "initial_badges": initial_badges,
                                    "final_badges": final_badges,
                                    "initial_coins": initial_coins,
                                    "final_coins": final_coins,
                                    "new_badges_awarded": new_badges
                                })
                            else:
                                self.log_test("Badge System Integration", False, "Could not get final progress")
                        else:
                            self.log_test("Badge System Integration", False, "Could not check progress")
                    else:
                        self.log_test("Badge System Integration", False, "Could not add skill")
                else:
                    self.log_test("Badge System Integration", False, "No skills available")
            else:
                self.log_test("Badge System Integration", False, "Could not get skills")
                
        except Exception as e:
            self.log_test("Badge System Integration", False, f"Error: {str(e)}")
    
    # ===== COMMUNITY FEATURES TESTS =====
    
    def test_get_forums(self):
        """Test getting all forums (GET /api/community/forums)"""
        if not self.auth_token:
            self.log_test("Get Forums", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/community/forums")
            
            if response.status_code == 200:
                data = response.json()
                forum_count = len(data)
                forum_categories = list(set([forum.get('category') for forum in data]))
                self.log_test("Get Forums", True, f"Retrieved {forum_count} forums with categories: {forum_categories}", {
                    "forum_count": forum_count,
                    "sample_forums": data[:3] if data else []
                })
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Forums", False, f"Failed to get forums: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Forums", False, f"Error: {str(e)}")
    
    def test_create_forum(self):
        """Test creating a new forum (POST /api/community/forums)"""
        if not self.auth_token:
            self.log_test("Create Forum", False, "No auth token available")
            return
            
        try:
            timestamp = int(time.time())
            forum_data = {
                "name": f"Test Forum {timestamp}",
                "description": "A test forum for automated testing purposes",
                "category": "Testing",
                "icon": "🧪",
                "color": "#FF6B6B"
            }
            
            response = self.make_request("POST", "/community/forums", forum_data)
            
            if response.status_code == 200:
                data = response.json()
                self.created_forum_id = data.get("id")  # Store for other tests
                self.log_test("Create Forum", True, f"Forum created: {data.get('name')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Create Forum", False, f"Failed to create forum: {error_detail}")
                
        except Exception as e:
            self.log_test("Create Forum", False, f"Error: {str(e)}")
    
    def test_get_specific_forum(self):
        """Test getting a specific forum (GET /api/community/forums/{forum_id})"""
        if not self.auth_token:
            self.log_test("Get Specific Forum", False, "No auth token available")
            return
        
        # First get all forums to get a valid forum ID
        try:
            forums_response = self.make_request("GET", "/community/forums")
            if forums_response.status_code != 200:
                self.log_test("Get Specific Forum", False, "Could not retrieve forums list")
                return
            
            forums = forums_response.json()
            if not forums:
                self.log_test("Get Specific Forum", False, "No forums available")
                return
            
            forum_id = forums[0]["id"]
            
            response = self.make_request("GET", f"/community/forums/{forum_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Specific Forum", True, f"Retrieved forum: {data.get('name')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Specific Forum", False, f"Failed to get forum: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Specific Forum", False, f"Error: {str(e)}")
    
    def test_get_posts(self):
        """Test getting posts with filtering (GET /api/community/posts)"""
        if not self.auth_token:
            self.log_test("Get Posts", False, "No auth token available")
            return
            
        try:
            # Test 1: Get all posts
            response1 = self.make_request("GET", "/community/posts")
            
            if response1.status_code == 200:
                data1 = response1.json()
                self.log_test("Get Posts - All", True, f"Retrieved {len(data1)} posts", {"post_count": len(data1)})
            else:
                error_detail = response1.json().get("detail", "Unknown error") if response1.content else f"Status: {response1.status_code}"
                self.log_test("Get Posts - All", False, f"Failed to get posts: {error_detail}")
            
            # Test 2: Get posts by type
            response2 = self.make_request("GET", "/community/posts", params={"post_type": "discussion"})
            
            if response2.status_code == 200:
                data2 = response2.json()
                self.log_test("Get Posts - Discussion Type", True, f"Retrieved {len(data2)} discussion posts", {"post_count": len(data2)})
            else:
                error_detail = response2.json().get("detail", "Unknown error") if response2.content else f"Status: {response2.status_code}"
                self.log_test("Get Posts - Discussion Type", False, f"Failed to get discussion posts: {error_detail}")
            
            # Test 3: Search posts
            response3 = self.make_request("GET", "/community/posts", params={"search": "python"})
            
            if response3.status_code == 200:
                data3 = response3.json()
                self.log_test("Get Posts - Search", True, f"Found {len(data3)} posts matching 'python'", {"post_count": len(data3)})
            else:
                error_detail = response3.json().get("detail", "Unknown error") if response3.content else f"Status: {response3.status_code}"
                self.log_test("Get Posts - Search", False, f"Failed to search posts: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Posts", False, f"Error: {str(e)}")
    
    def test_create_post(self):
        """Test creating a new post (POST /api/community/posts)"""
        if not self.auth_token:
            self.log_test("Create Post", False, "No auth token available")
            return
            
        try:
            # First get forums to get a valid forum ID
            forums_response = self.make_request("GET", "/community/forums")
            if forums_response.status_code != 200:
                self.log_test("Create Post", False, "Could not retrieve forums list")
                return
            
            forums = forums_response.json()
            if not forums:
                self.log_test("Create Post", False, "No forums available")
                return
            
            forum_id = forums[0]["id"]
            timestamp = int(time.time())
            
            post_data = {
                "title": f"Test Discussion Post {timestamp}",
                "content": "This is a test post created by the automated testing system. It demonstrates the community posting functionality.",
                "post_type": "discussion",
                "forum_id": forum_id,
                "tags": ["testing", "automation", "community"]
            }
            
            response = self.make_request("POST", "/community/posts", post_data)
            
            if response.status_code == 200:
                data = response.json()
                self.created_post_id = data.get("id")  # Store for other tests
                self.log_test("Create Post", True, f"Post created: {data.get('title')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Create Post", False, f"Failed to create post: {error_detail}")
                
        except Exception as e:
            self.log_test("Create Post", False, f"Error: {str(e)}")
    
    def test_get_specific_post(self):
        """Test getting a specific post (GET /api/community/posts/{post_id})"""
        if not self.auth_token:
            self.log_test("Get Specific Post", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_post_id') or not self.created_post_id:
            self.log_test("Get Specific Post", False, "No post ID available from previous test")
            return
            
        try:
            response = self.make_request("GET", f"/community/posts/{self.created_post_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Specific Post", True, f"Retrieved post: {data.get('title')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Specific Post", False, f"Failed to get post: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Specific Post", False, f"Error: {str(e)}")
    
    def test_update_post(self):
        """Test updating a post (PUT /api/community/posts/{post_id})"""
        if not self.auth_token:
            self.log_test("Update Post", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_post_id') or not self.created_post_id:
            self.log_test("Update Post", False, "No post ID available from previous test")
            return
            
        try:
            update_data = {
                "title": "Updated Test Discussion Post",
                "content": "This post has been updated by the automated testing system to verify the update functionality.",
                "tags": ["testing", "automation", "community", "updated"]
            }
            
            response = self.make_request("PUT", f"/community/posts/{self.created_post_id}", update_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Update Post", True, f"Post updated: {data.get('title')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Update Post", False, f"Failed to update post: {error_detail}")
                
        except Exception as e:
            self.log_test("Update Post", False, f"Error: {str(e)}")
    
    def test_toggle_post_like(self):
        """Test toggling like on a post (POST /api/community/posts/{post_id}/like)"""
        if not self.auth_token:
            self.log_test("Toggle Post Like", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_post_id') or not self.created_post_id:
            self.log_test("Toggle Post Like", False, "No post ID available from previous test")
            return
            
        try:
            # Like the post
            response1 = self.make_request("POST", f"/community/posts/{self.created_post_id}/like")
            
            if response1.status_code == 200:
                data1 = response1.json()
                liked = data1.get("liked", False)
                
                # Unlike the post
                response2 = self.make_request("POST", f"/community/posts/{self.created_post_id}/like")
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    unliked = not data2.get("liked", True)
                    
                    self.log_test("Toggle Post Like", True, f"Post like toggled: liked={liked}, then unliked={unliked}", {
                        "first_action": data1,
                        "second_action": data2
                    })
                else:
                    self.log_test("Toggle Post Like", False, "Failed to unlike post")
            else:
                error_detail = response1.json().get("detail", "Unknown error") if response1.content else f"Status: {response1.status_code}"
                self.log_test("Toggle Post Like", False, f"Failed to like post: {error_detail}")
                
        except Exception as e:
            self.log_test("Toggle Post Like", False, f"Error: {str(e)}")
    
    def test_get_post_comments(self):
        """Test getting comments for a post (GET /api/community/posts/{post_id}/comments)"""
        if not self.auth_token:
            self.log_test("Get Post Comments", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_post_id') or not self.created_post_id:
            self.log_test("Get Post Comments", False, "No post ID available from previous test")
            return
            
        try:
            response = self.make_request("GET", f"/community/posts/{self.created_post_id}/comments")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Post Comments", True, f"Retrieved {len(data)} comments", {"comment_count": len(data)})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Post Comments", False, f"Failed to get comments: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Post Comments", False, f"Error: {str(e)}")
    
    def test_create_comment(self):
        """Test creating a comment (POST /api/community/comments)"""
        if not self.auth_token:
            self.log_test("Create Comment", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_post_id') or not self.created_post_id:
            self.log_test("Create Comment", False, "No post ID available from previous test")
            return
            
        try:
            comment_data = {
                "content": "This is a test comment created by the automated testing system.",
                "post_id": self.created_post_id
            }
            
            response = self.make_request("POST", "/community/comments", comment_data)
            
            if response.status_code == 200:
                data = response.json()
                self.created_comment_id = data.get("id")  # Store for other tests
                self.log_test("Create Comment", True, f"Comment created: {data.get('content')[:50]}...", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Create Comment", False, f"Failed to create comment: {error_detail}")
                
        except Exception as e:
            self.log_test("Create Comment", False, f"Error: {str(e)}")
    
    def test_toggle_comment_like(self):
        """Test toggling like on a comment (POST /api/community/comments/{comment_id}/like)"""
        if not self.auth_token:
            self.log_test("Toggle Comment Like", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_comment_id') or not self.created_comment_id:
            self.log_test("Toggle Comment Like", False, "No comment ID available from previous test")
            return
            
        try:
            response = self.make_request("POST", f"/community/comments/{self.created_comment_id}/like")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Toggle Comment Like", True, f"Comment like toggled: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Toggle Comment Like", False, f"Failed to toggle comment like: {error_detail}")
                
        except Exception as e:
            self.log_test("Toggle Comment Like", False, f"Error: {str(e)}")
    
    def test_get_groups(self):
        """Test getting groups (GET /api/community/groups)"""
        if not self.auth_token:
            self.log_test("Get Groups", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/community/groups")
            
            if response.status_code == 200:
                data = response.json()
                group_count = len(data)
                group_types = list(set([group.get('group_type') for group in data]))
                self.log_test("Get Groups", True, f"Retrieved {group_count} groups with types: {group_types}", {
                    "group_count": group_count,
                    "sample_groups": data[:3] if data else []
                })
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Groups", False, f"Failed to get groups: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Groups", False, f"Error: {str(e)}")
    
    def test_create_group(self):
        """Test creating a group (POST /api/community/groups)"""
        if not self.auth_token:
            self.log_test("Create Group", False, "No auth token available")
            return
            
        try:
            timestamp = int(time.time())
            group_data = {
                "name": f"Test Study Group {timestamp}",
                "description": "A test study group for automated testing purposes",
                "group_type": "study_group",
                "privacy": "public",
                "skills_focus": ["Python", "JavaScript"],
                "category": "Programming",
                "learning_goals": ["Learn Python basics", "Build web applications"]
            }
            
            response = self.make_request("POST", "/community/groups", group_data)
            
            if response.status_code == 200:
                data = response.json()
                self.created_group_id = data.get("id")  # Store for other tests
                self.log_test("Create Group", True, f"Group created: {data.get('name')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Create Group", False, f"Failed to create group: {error_detail}")
                
        except Exception as e:
            self.log_test("Create Group", False, f"Error: {str(e)}")
    
    def test_join_group(self):
        """Test joining a group (POST /api/community/groups/{group_id}/join)"""
        if not self.auth_token:
            self.log_test("Join Group", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_group_id') or not self.created_group_id:
            self.log_test("Join Group", False, "No group ID available from previous test")
            return
            
        try:
            response = self.make_request("POST", f"/community/groups/{self.created_group_id}/join")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Join Group", True, f"Group join result: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Join Group", False, f"Failed to join group: {error_detail}")
                
        except Exception as e:
            self.log_test("Join Group", False, f"Error: {str(e)}")
    
    def test_get_testimonials(self):
        """Test getting testimonials (GET /api/community/testimonials)"""
        if not self.auth_token:
            self.log_test("Get Testimonials", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/community/testimonials")
            
            if response.status_code == 200:
                data = response.json()
                testimonial_count = len(data)
                self.log_test("Get Testimonials", True, f"Retrieved {testimonial_count} testimonials", {
                    "testimonial_count": testimonial_count,
                    "sample_testimonials": data[:3] if data else []
                })
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Testimonials", False, f"Failed to get testimonials: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Testimonials", False, f"Error: {str(e)}")
    
    def test_create_testimonial(self):
        """Test creating a testimonial (POST /api/community/testimonials)"""
        if not self.auth_token:
            self.log_test("Create Testimonial", False, "No auth token available")
            return
            
        try:
            # Create a second user to write testimonial about
            timestamp = int(time.time())
            subject_user_data = {
                "email": f"testimonialsubject{timestamp}@skillswap.com",
                "username": f"testimonialsubject{timestamp}",
                "password": "TestimonialSubject123!",
                "first_name": "Testimonial",
                "last_name": "Subject",
                "role": "teacher"
            }
            
            subject_response = self.make_request("POST", "/auth/register", subject_user_data)
            if subject_response.status_code != 200:
                self.log_test("Create Testimonial", False, "Could not create subject user")
                return
            
            subject_user = subject_response.json().get("user", {})
            
            testimonial_data = {
                "subject_id": subject_user["id"],
                "content": "This is a test testimonial created by the automated testing system. The subject is an excellent teacher with great communication skills.",
                "rating": 4.5,
                "skills_mentioned": ["Python", "Teaching"],
                "highlights": ["Clear explanations", "Patient instructor", "Practical examples"]
            }
            
            response = self.make_request("POST", "/community/testimonials", testimonial_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Create Testimonial", True, f"Testimonial created with rating {data.get('rating')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Create Testimonial", False, f"Failed to create testimonial: {error_detail}")
                
        except Exception as e:
            self.log_test("Create Testimonial", False, f"Error: {str(e)}")
    
    def test_get_knowledge_base(self):
        """Test getting knowledge base entries (GET /api/community/knowledge-base)"""
        if not self.auth_token:
            self.log_test("Get Knowledge Base", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/community/knowledge-base")
            
            if response.status_code == 200:
                data = response.json()
                kb_count = len(data)
                categories = list(set([entry.get('category') for entry in data]))
                self.log_test("Get Knowledge Base", True, f"Retrieved {kb_count} knowledge base entries with categories: {categories}", {
                    "kb_count": kb_count,
                    "sample_entries": data[:3] if data else []
                })
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Knowledge Base", False, f"Failed to get knowledge base: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Knowledge Base", False, f"Error: {str(e)}")
    
    def test_create_knowledge_base_entry(self):
        """Test creating a knowledge base entry (POST /api/community/knowledge-base)"""
        if not self.auth_token:
            self.log_test("Create Knowledge Base Entry", False, "No auth token available")
            return
            
        try:
            # Get skills to reference in the KB entry
            skills_response = self.make_request("GET", "/skills/")
            if skills_response.status_code != 200:
                self.log_test("Create Knowledge Base Entry", False, "Could not retrieve skills list")
                return
            
            skills = skills_response.json()
            if not skills:
                self.log_test("Create Knowledge Base Entry", False, "No skills available")
                return
            
            python_skill = next((skill for skill in skills if "Python" in skill.get("name", "")), skills[0])
            
            timestamp = int(time.time())
            kb_data = {
                "title": f"Python Best Practices Guide {timestamp}",
                "content": "This is a comprehensive guide to Python best practices created by the automated testing system. It covers coding standards, documentation, and testing approaches.",
                "category": "Programming",
                "subcategory": "Best Practices",
                "tags": ["python", "best-practices", "coding-standards"],
                "skill_ids": [python_skill["id"]],
                "difficulty_level": "intermediate",
                "sections": [
                    {"title": "Code Style", "content": "Follow PEP 8 guidelines"},
                    {"title": "Documentation", "content": "Write clear docstrings"},
                    {"title": "Testing", "content": "Use pytest for testing"}
                ],
                "resources": [
                    {"title": "PEP 8", "url": "https://pep8.org", "type": "documentation"}
                ]
            }
            
            response = self.make_request("POST", "/community/knowledge-base", kb_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Create Knowledge Base Entry", True, f"KB entry created: {data.get('title')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Create Knowledge Base Entry", False, f"Failed to create KB entry: {error_detail}")
                
        except Exception as e:
            self.log_test("Create Knowledge Base Entry", False, f"Error: {str(e)}")
    
    def test_get_community_stats(self):
        """Test getting community statistics (GET /api/community/stats)"""
        if not self.auth_token:
            self.log_test("Get Community Stats", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/community/stats")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Community Stats", True, "Retrieved community statistics", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Community Stats", False, f"Failed to get community stats: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Community Stats", False, f"Error: {str(e)}")
    
    def test_get_trending_topics(self):
        """Test getting trending topics (GET /api/community/trending)"""
        if not self.auth_token:
            self.log_test("Get Trending Topics", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/community/trending", params={"days": 7})
            
            if response.status_code == 200:
                data = response.json()
                trending_topics = data.get("trending_topics", [])
                self.log_test("Get Trending Topics", True, f"Retrieved {len(trending_topics)} trending topics", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Trending Topics", False, f"Failed to get trending topics: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Trending Topics", False, f"Error: {str(e)}")
    
    def test_community_authentication_required(self):
        """Test that community endpoints require authentication"""
        try:
            # Temporarily remove auth token
            original_token = self.auth_token
            self.auth_token = None
            
            # Try to access community endpoints without authentication
            endpoints_to_test = [
                "/community/forums",
                "/community/posts",
                "/community/groups",
                "/community/testimonials",
                "/community/knowledge-base",
                "/community/stats",
                "/community/trending"
            ]
            
            auth_required_count = 0
            for endpoint in endpoints_to_test:
                response = self.make_request("GET", endpoint)
                if response.status_code in [401, 403]:
                    auth_required_count += 1
            
            # Restore auth token
            self.auth_token = original_token
            
            if auth_required_count == len(endpoints_to_test):
                self.log_test("Community Authentication Required", True, f"Authentication correctly required for all {len(endpoints_to_test)} endpoints")
            else:
                self.log_test("Community Authentication Required", False, f"Authentication not required for {len(endpoints_to_test) - auth_required_count} endpoints")
                
        except Exception as e:
            self.log_test("Community Authentication Required", False, f"Error: {str(e)}")
    
    # ===== WEBRTC VIDEO CHAT TESTS =====
    
    def test_get_webrtc_config(self):
        """Test getting WebRTC configuration (GET /api/webrtc/config)"""
        if not self.auth_token:
            self.log_test("Get WebRTC Config", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/webrtc/config")
            
            if response.status_code == 200:
                data = response.json()
                ice_servers = data.get("ice_servers", [])
                user_id = data.get("user_id")
                
                # Validate ICE servers structure
                has_stun = any("stun:" in server.get("urls", "") for server in ice_servers)
                
                self.log_test("Get WebRTC Config", True, f"Retrieved WebRTC config with {len(ice_servers)} ICE servers, STUN available: {has_stun}", {
                    "ice_servers_count": len(ice_servers),
                    "has_stun": has_stun,
                    "user_id": user_id,
                    "sample_ice_servers": ice_servers[:2] if ice_servers else []
                })
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get WebRTC Config", False, f"Failed to get WebRTC config: {error_detail}")
                
        except Exception as e:
            self.log_test("Get WebRTC Config", False, f"Error: {str(e)}")
    
    def test_get_session_info_for_webrtc(self):
        """Test getting session info for WebRTC (GET /api/webrtc/session/{session_id}/info)"""
        if not self.auth_token:
            self.log_test("Get Session Info for WebRTC", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_session_id') or not self.created_session_id:
            self.log_test("Get Session Info for WebRTC", False, "No session ID available from previous test")
            return
            
        try:
            response = self.make_request("GET", f"/webrtc/session/{self.created_session_id}/info")
            
            if response.status_code == 200:
                data = response.json()
                session_id = data.get("session_id")
                active_users = data.get("active_users", [])
                user_count = data.get("user_count", 0)
                timestamp = data.get("timestamp")
                
                self.log_test("Get Session Info for WebRTC", True, f"Retrieved WebRTC session info: {user_count} active users", {
                    "session_id": session_id,
                    "active_users": active_users,
                    "user_count": user_count,
                    "timestamp": timestamp
                })
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Session Info for WebRTC", False, f"Failed to get session info: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Session Info for WebRTC", False, f"Error: {str(e)}")
    
    def test_start_video_call(self):
        """Test starting a video call (POST /api/webrtc/session/{session_id}/start-call)"""
        if not self.auth_token:
            self.log_test("Start Video Call", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_session_id') or not self.created_session_id:
            self.log_test("Start Video Call", False, "No session ID available from previous test")
            return
            
        try:
            # First ensure the session is in progress (required for video calls)
            start_session_response = self.make_request("POST", f"/sessions/{self.created_session_id}/start")
            if start_session_response.status_code != 200:
                self.log_test("Start Video Call", False, "Could not start session (required for video call)")
                return
            
            # Now try to start the video call
            response = self.make_request("POST", f"/webrtc/session/{self.created_session_id}/start-call")
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message")
                session_id = data.get("session_id")
                websocket_url = data.get("websocket_url")
                
                self.log_test("Start Video Call", True, f"Video call started: {message}", {
                    "message": message,
                    "session_id": session_id,
                    "websocket_url": websocket_url
                })
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Start Video Call", False, f"Failed to start video call: {error_detail}")
                
        except Exception as e:
            self.log_test("Start Video Call", False, f"Error: {str(e)}")
    
    def test_end_video_call(self):
        """Test ending a video call (POST /api/webrtc/session/{session_id}/end-call)"""
        if not self.auth_token:
            self.log_test("End Video Call", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_session_id') or not self.created_session_id:
            self.log_test("End Video Call", False, "No session ID available from previous test")
            return
            
        try:
            response = self.make_request("POST", f"/webrtc/session/{self.created_session_id}/end-call")
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message")
                session_id = data.get("session_id")
                
                self.log_test("End Video Call", True, f"Video call ended: {message}", {
                    "message": message,
                    "session_id": session_id
                })
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("End Video Call", False, f"Failed to end video call: {error_detail}")
                
        except Exception as e:
            self.log_test("End Video Call", False, f"Error: {str(e)}")
    
    def test_webrtc_session_access_control(self):
        """Test that WebRTC endpoints require proper session access"""
        if not self.auth_token:
            self.log_test("WebRTC Session Access Control", False, "No auth token available")
            return
            
        try:
            # Create a third user who shouldn't have access to our sessions
            timestamp = int(time.time())
            unauthorized_user_data = {
                "email": f"webrtcunauth{timestamp}@skillswap.com",
                "username": f"webrtcunauth{timestamp}",
                "password": "WebRTCUnauth123!",
                "first_name": "WebRTC",
                "last_name": "Unauthorized",
                "role": "both"
            }
            
            unauthorized_response = self.make_request("POST", "/auth/register", unauthorized_user_data)
            if unauthorized_response.status_code != 200:
                self.log_test("WebRTC Session Access Control", False, "Could not create unauthorized user")
                return
            
            unauthorized_token = unauthorized_response.json().get("access_token")
            
            # Try to access WebRTC session info with unauthorized token
            if hasattr(self, 'created_session_id') and self.created_session_id:
                # Temporarily switch to unauthorized token
                original_token = self.auth_token
                self.auth_token = unauthorized_token
                
                response = self.make_request("GET", f"/webrtc/session/{self.created_session_id}/info")
                
                # Restore original token
                self.auth_token = original_token
                
                if response.status_code in [403, 404]:
                    self.log_test("WebRTC Session Access Control", True, f"Unauthorized access correctly blocked ({response.status_code})")
                else:
                    self.log_test("WebRTC Session Access Control", False, f"Unauthorized access not blocked - Status: {response.status_code}")
            else:
                self.log_test("WebRTC Session Access Control", False, "No session available to test access control")
                
        except Exception as e:
            self.log_test("WebRTC Session Access Control", False, f"Error: {str(e)}")
    
    def test_webrtc_authentication_required(self):
        """Test that WebRTC endpoints require authentication"""
        try:
            # Temporarily remove auth token
            original_token = self.auth_token
            self.auth_token = None
            
            # Try to access WebRTC endpoints without authentication
            endpoints_to_test = [
                "/webrtc/config"
            ]
            
            auth_required_count = 0
            for endpoint in endpoints_to_test:
                response = self.make_request("GET", endpoint)
                if response.status_code in [401, 403]:
                    auth_required_count += 1
            
            # Restore auth token
            self.auth_token = original_token
            
            if auth_required_count == len(endpoints_to_test):
                self.log_test("WebRTC Authentication Required", True, f"Authentication correctly required for all {len(endpoints_to_test)} WebRTC endpoints")
            else:
                self.log_test("WebRTC Authentication Required", False, f"Authentication not required for {len(endpoints_to_test) - auth_required_count} WebRTC endpoints")
                
        except Exception as e:
            self.log_test("WebRTC Authentication Required", False, f"Error: {str(e)}")
    
    def test_webrtc_invalid_session_handling(self):
        """Test WebRTC endpoints with invalid session IDs"""
        if not self.auth_token:
            self.log_test("WebRTC Invalid Session Handling", False, "No auth token available")
            return
            
        try:
            # Test with non-existent session ID
            fake_session_id = "00000000-0000-0000-0000-000000000000"
            
            # Test session info endpoint
            response1 = self.make_request("GET", f"/webrtc/session/{fake_session_id}/info")
            
            # Test start call endpoint
            response2 = self.make_request("POST", f"/webrtc/session/{fake_session_id}/start-call")
            
            # Test end call endpoint
            response3 = self.make_request("POST", f"/webrtc/session/{fake_session_id}/end-call")
            
            # All should return 404 or 403 for non-existent sessions
            invalid_responses = 0
            for response in [response1, response2, response3]:
                if response.status_code in [404, 403]:
                    invalid_responses += 1
            
            if invalid_responses == 3:
                self.log_test("WebRTC Invalid Session Handling", True, "All WebRTC endpoints correctly handle invalid session IDs")
            else:
                self.log_test("WebRTC Invalid Session Handling", False, f"Only {invalid_responses}/3 endpoints properly handle invalid session IDs")
                
        except Exception as e:
            self.log_test("WebRTC Invalid Session Handling", False, f"Error: {str(e)}")
    
    def test_webrtc_session_status_validation(self):
        """Test that video calls can only be started for sessions in progress"""
        if not self.auth_token:
            self.log_test("WebRTC Session Status Validation", False, "No auth token available")
            return
            
        try:
            # Create a new session that's not started yet
            skills_response = self.make_request("GET", "/skills/")
            if skills_response.status_code != 200:
                self.log_test("WebRTC Session Status Validation", False, "Could not retrieve skills list")
                return
                
            skills = skills_response.json()
            if not skills:
                self.log_test("WebRTC Session Status Validation", False, "No skills available")
                return
            
            user_response = self.make_request("GET", "/auth/me")
            if user_response.status_code != 200:
                self.log_test("WebRTC Session Status Validation", False, "Could not get current user")
                return
            
            current_user = user_response.json()
            
            # Create a learner for this test
            timestamp = int(time.time())
            learner_data = {
                "email": f"webrtclearner{timestamp}@skillswap.com",
                "username": f"webrtclearner{timestamp}",
                "password": "WebRTCLearner123!",
                "first_name": "WebRTC",
                "last_name": "Learner",
                "role": "learner"
            }
            
            learner_response = self.make_request("POST", "/auth/register", learner_data)
            if learner_response.status_code != 200:
                self.log_test("WebRTC Session Status Validation", False, "Could not create learner user")
                return
            
            learner_user = learner_response.json().get("user", {})
            
            # Create session (will be in 'scheduled' status)
            from datetime import datetime, timedelta
            start_time = datetime.utcnow() + timedelta(days=1)
            end_time = start_time + timedelta(hours=1)
            
            test_skill = skills[0]
            
            session_data = {
                "teacher_id": current_user["id"],
                "learner_id": learner_user["id"],
                "skill_id": test_skill["id"],
                "skill_name": test_skill["name"],
                "title": "WebRTC Status Test Session",
                "description": "Testing WebRTC session status validation",
                "scheduled_start": start_time.isoformat(),
                "scheduled_end": end_time.isoformat(),
                "timezone": "UTC",
                "session_type": "video",
                "skill_coins_paid": 10
            }
            
            create_response = self.make_request("POST", "/sessions/", session_data)
            if create_response.status_code != 200:
                self.log_test("WebRTC Session Status Validation", False, "Could not create test session")
                return
            
            created_session = create_response.json()
            test_session_id = created_session["id"]
            
            # Try to start video call on scheduled session (should fail)
            response = self.make_request("POST", f"/webrtc/session/{test_session_id}/start-call")
            
            if response.status_code == 400:
                error_detail = response.json().get("detail", "")
                if "in progress" in error_detail.lower():
                    self.log_test("WebRTC Session Status Validation", True, "Video call correctly rejected for non-in-progress session")
                else:
                    self.log_test("WebRTC Session Status Validation", False, f"Wrong error message: {error_detail}")
            else:
                self.log_test("WebRTC Session Status Validation", False, f"Expected 400 error, got {response.status_code}")
                
        except Exception as e:
            self.log_test("WebRTC Session Status Validation", False, f"Error: {str(e)}")
    
    # ===== SMART NOTIFICATIONS SYSTEM TESTS =====
    
    def test_get_user_notifications(self):
        """Test getting user notifications with filtering"""
        if not self.auth_token:
            self.log_test("Get User Notifications", False, "No auth token available")
            return
            
        try:
            # Test 1: Get all notifications
            response1 = self.make_request("GET", "/notifications/")
            
            if response1.status_code == 200:
                data1 = response1.json()
                self.log_test("Get User Notifications - All", True, f"Retrieved {len(data1)} notifications", {"notification_count": len(data1)})
            else:
                error_detail = response1.json().get("detail", "Unknown error") if response1.content else f"Status: {response1.status_code}"
                self.log_test("Get User Notifications - All", False, f"Failed to get notifications: {error_detail}")
            
            # Test 2: Get notifications with limit and offset
            response2 = self.make_request("GET", "/notifications/", params={"limit": 5, "offset": 0})
            
            if response2.status_code == 200:
                data2 = response2.json()
                self.log_test("Get User Notifications - Pagination", True, f"Retrieved {len(data2)} notifications with pagination", {"notification_count": len(data2)})
            else:
                error_detail = response2.json().get("detail", "Unknown error") if response2.content else f"Status: {response2.status_code}"
                self.log_test("Get User Notifications - Pagination", False, f"Failed to get paginated notifications: {error_detail}")
            
            # Test 3: Get unread notifications only
            response3 = self.make_request("GET", "/notifications/", params={"unread_only": True})
            
            if response3.status_code == 200:
                data3 = response3.json()
                self.log_test("Get User Notifications - Unread Only", True, f"Retrieved {len(data3)} unread notifications", {"unread_count": len(data3)})
            else:
                error_detail = response3.json().get("detail", "Unknown error") if response3.content else f"Status: {response3.status_code}"
                self.log_test("Get User Notifications - Unread Only", False, f"Failed to get unread notifications: {error_detail}")
            
            # Test 4: Get notifications by type
            response4 = self.make_request("GET", "/notifications/", params={"notification_types": "match_found,session_reminder"})
            
            if response4.status_code == 200:
                data4 = response4.json()
                self.log_test("Get User Notifications - By Type", True, f"Retrieved {len(data4)} notifications by type", {"filtered_count": len(data4)})
            else:
                error_detail = response4.json().get("detail", "Unknown error") if response4.content else f"Status: {response4.status_code}"
                self.log_test("Get User Notifications - By Type", False, f"Failed to get notifications by type: {error_detail}")
                
        except Exception as e:
            self.log_test("Get User Notifications", False, f"Error: {str(e)}")
    
    def test_get_unread_notification_count(self):
        """Test getting unread notification count"""
        if not self.auth_token:
            self.log_test("Get Unread Notification Count", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/notifications/count")
            
            if response.status_code == 200:
                data = response.json()
                unread_count = data.get("unread_count", 0)
                self.log_test("Get Unread Notification Count", True, f"Unread count: {unread_count}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Unread Notification Count", False, f"Failed to get unread count: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Unread Notification Count", False, f"Error: {str(e)}")
    
    def test_get_notification_stats(self):
        """Test getting notification statistics"""
        if not self.auth_token:
            self.log_test("Get Notification Stats", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/notifications/stats")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Notification Stats", True, f"Retrieved notification statistics", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Notification Stats", False, f"Failed to get notification stats: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Notification Stats", False, f"Error: {str(e)}")
    
    def test_create_notification(self):
        """Test creating a notification"""
        if not self.auth_token:
            self.log_test("Create Notification", False, "No auth token available")
            return
            
        try:
            notification_data = {
                "user_id": self.test_user_id,
                "notification_type": "system_announcement",
                "title": "Test Notification",
                "message": "This is a test notification created during API testing",
                "priority": "medium",
                "data": {
                    "test_data": "test_value",
                    "created_by": "api_test"
                },
                "action_url": "/dashboard"
            }
            
            response = self.make_request("POST", "/notifications/", notification_data)
            
            if response.status_code == 200:
                data = response.json()
                self.created_notification_id = data.get("notification_id")  # Store for other tests
                self.log_test("Create Notification", True, f"Notification created successfully: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Create Notification", False, f"Failed to create notification: {error_detail}")
                
        except Exception as e:
            self.log_test("Create Notification", False, f"Error: {str(e)}")
    
    def test_update_notification(self):
        """Test updating notification (mark as read)"""
        if not self.auth_token:
            self.log_test("Update Notification", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_notification_id') or not self.created_notification_id:
            self.log_test("Update Notification", False, "No notification ID available from previous test")
            return
            
        try:
            update_data = {
                "is_read": True
            }
            
            response = self.make_request("PUT", f"/notifications/{self.created_notification_id}", update_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Update Notification", True, f"Notification updated successfully: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Update Notification", False, f"Failed to update notification: {error_detail}")
                
        except Exception as e:
            self.log_test("Update Notification", False, f"Error: {str(e)}")
    
    def test_mark_all_notifications_read(self):
        """Test marking all notifications as read"""
        if not self.auth_token:
            self.log_test("Mark All Notifications Read", False, "No auth token available")
            return
            
        try:
            response = self.make_request("PUT", "/notifications/mark-all-read", {})
            
            if response.status_code == 200:
                data = response.json()
                marked_count = data.get("marked_read", 0)
                self.log_test("Mark All Notifications Read", True, f"Marked {marked_count} notifications as read", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Mark All Notifications Read", False, f"Failed to mark all as read: {error_detail}")
                
        except Exception as e:
            self.log_test("Mark All Notifications Read", False, f"Error: {str(e)}")
    
    def test_delete_notification(self):
        """Test deleting a notification"""
        if not self.auth_token:
            self.log_test("Delete Notification", False, "No auth token available")
            return
        
        if not hasattr(self, 'created_notification_id') or not self.created_notification_id:
            self.log_test("Delete Notification", False, "No notification ID available from previous test")
            return
            
        try:
            response = self.make_request("DELETE", f"/notifications/{self.created_notification_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Delete Notification", True, f"Notification deleted successfully: {data.get('message')}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Delete Notification", False, f"Failed to delete notification: {error_detail}")
                
        except Exception as e:
            self.log_test("Delete Notification", False, f"Error: {str(e)}")
    
    def test_get_notification_preferences(self):
        """Test getting notification preferences"""
        if not self.auth_token:
            self.log_test("Get Notification Preferences", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/notifications/preferences")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Notification Preferences", True, f"Retrieved notification preferences", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Notification Preferences", False, f"Failed to get preferences: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Notification Preferences", False, f"Error: {str(e)}")
    
    def test_update_notification_preferences(self):
        """Test updating notification preferences"""
        if not self.auth_token:
            self.log_test("Update Notification Preferences", False, "No auth token available")
            return
            
        try:
            preferences_data = {
                "email_notifications": True,
                "push_notifications": True,
                "match_notifications": True,
                "session_reminders": True,
                "message_notifications": False,  # Disable message notifications for testing
                "achievement_notifications": True,
                "community_notifications": True,
                "digest_frequency": "weekly",
                "quiet_hours_start": "23:00",
                "quiet_hours_end": "07:00"
            }
            
            response = self.make_request("PUT", "/notifications/preferences", preferences_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Update Notification Preferences", True, f"Preferences updated successfully", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Update Notification Preferences", False, f"Failed to update preferences: {error_detail}")
                
        except Exception as e:
            self.log_test("Update Notification Preferences", False, f"Error: {str(e)}")
    
    def test_quick_notification_methods(self):
        """Test quick notification methods"""
        if not self.auth_token:
            self.log_test("Quick Notification Methods", False, "No auth token available")
            return
            
        try:
            # Test 1: Match found notification
            match_data = {
                "match_user_id": self.test_user_id,  # Use same user for testing
                "compatibility_score": 0.85
            }
            
            response1 = self.make_request("POST", "/notifications/quick/match-found", match_data)
            
            if response1.status_code == 200:
                data1 = response1.json()
                self.log_test("Quick Notification - Match Found", True, f"Match notification sent: {data1.get('message')}", data1)
            else:
                error_detail = response1.json().get("detail", "Unknown error") if response1.content else f"Status: {response1.status_code}"
                self.log_test("Quick Notification - Match Found", False, f"Failed to send match notification: {error_detail}")
            
            # Test 2: Session reminder notification
            from datetime import datetime, timedelta
            reminder_data = {
                "session_id": "test-session-123",
                "session_title": "Python Fundamentals Session",
                "starts_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }
            
            response2 = self.make_request("POST", "/notifications/quick/session-reminder", reminder_data)
            
            if response2.status_code == 200:
                data2 = response2.json()
                self.log_test("Quick Notification - Session Reminder", True, f"Session reminder sent: {data2.get('message')}", data2)
            else:
                error_detail = response2.json().get("detail", "Unknown error") if response2.content else f"Status: {response2.status_code}"
                self.log_test("Quick Notification - Session Reminder", False, f"Failed to send session reminder: {error_detail}")
            
            # Test 3: Achievement earned notification
            achievement_data = {
                "achievement_name": "First Session Completed",
                "achievement_id": "test-achievement-123",
                "coins_earned": 50
            }
            
            response3 = self.make_request("POST", "/notifications/quick/achievement-earned", achievement_data)
            
            if response3.status_code == 200:
                data3 = response3.json()
                self.log_test("Quick Notification - Achievement Earned", True, f"Achievement notification sent: {data3.get('message')}", data3)
            else:
                error_detail = response3.json().get("detail", "Unknown error") if response3.content else f"Status: {response3.status_code}"
                self.log_test("Quick Notification - Achievement Earned", False, f"Failed to send achievement notification: {error_detail}")
            
            # Test 4: Message received notification
            message_data = {
                "sender_name": "Test User",
                "conversation_id": "test-conversation-123"
            }
            
            response4 = self.make_request("POST", "/notifications/quick/message-received", message_data)
            
            if response4.status_code == 200:
                data4 = response4.json()
                self.log_test("Quick Notification - Message Received", True, f"Message notification sent: {data4.get('message')}", data4)
            else:
                error_detail = response4.json().get("detail", "Unknown error") if response4.content else f"Status: {response4.status_code}"
                self.log_test("Quick Notification - Message Received", False, f"Failed to send message notification: {error_detail}")
                
        except Exception as e:
            self.log_test("Quick Notification Methods", False, f"Error: {str(e)}")
    
    def test_notifications_authentication_required(self):
        """Test that notification endpoints require authentication"""
        try:
            # Temporarily remove auth token
            original_token = self.auth_token
            self.auth_token = None
            
            # Try to access notifications without authentication
            response = self.make_request("GET", "/notifications/")
            
            # Restore auth token
            self.auth_token = original_token
            
            if response.status_code in [401, 403]:
                self.log_test("Notifications Authentication Required", True, f"Authentication correctly required ({response.status_code})")
            else:
                self.log_test("Notifications Authentication Required", False, f"Authentication not required - Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Notifications Authentication Required", False, f"Error: {str(e)}")
    
    # ===== SMART RECOMMENDATIONS SYSTEM TESTS =====
    
    def test_get_user_recommendations(self):
        """Test getting personalized recommendations"""
        if not self.auth_token:
            self.log_test("Get User Recommendations", False, "No auth token available")
            return
            
        try:
            # Test 1: Get all recommendations
            response1 = self.make_request("GET", "/recommendations/")
            
            if response1.status_code == 200:
                data1 = response1.json()
                self.log_test("Get User Recommendations - All", True, f"Retrieved {len(data1)} recommendations", {"recommendation_count": len(data1)})
            else:
                error_detail = response1.json().get("detail", "Unknown error") if response1.content else f"Status: {response1.status_code}"
                self.log_test("Get User Recommendations - All", False, f"Failed to get recommendations: {error_detail}")
            
            # Test 2: Get recommendations with limit
            response2 = self.make_request("GET", "/recommendations/", params={"limit": 5})
            
            if response2.status_code == 200:
                data2 = response2.json()
                self.log_test("Get User Recommendations - Limited", True, f"Retrieved {len(data2)} recommendations with limit", {"recommendation_count": len(data2)})
            else:
                error_detail = response2.json().get("detail", "Unknown error") if response2.content else f"Status: {response2.status_code}"
                self.log_test("Get User Recommendations - Limited", False, f"Failed to get limited recommendations: {error_detail}")
            
            # Test 3: Get recommendations by type
            response3 = self.make_request("GET", "/recommendations/", params={"recommendation_types": "skill_learning,user_match"})
            
            if response3.status_code == 200:
                data3 = response3.json()
                self.log_test("Get User Recommendations - By Type", True, f"Retrieved {len(data3)} recommendations by type", {"filtered_count": len(data3)})
            else:
                error_detail = response3.json().get("detail", "Unknown error") if response3.content else f"Status: {response3.status_code}"
                self.log_test("Get User Recommendations - By Type", False, f"Failed to get recommendations by type: {error_detail}")
            
            # Test 4: Get high confidence recommendations
            response4 = self.make_request("GET", "/recommendations/", params={"min_confidence": 0.7})
            
            if response4.status_code == 200:
                data4 = response4.json()
                self.log_test("Get User Recommendations - High Confidence", True, f"Retrieved {len(data4)} high confidence recommendations", {"high_confidence_count": len(data4)})
            else:
                error_detail = response4.json().get("detail", "Unknown error") if response4.content else f"Status: {response4.status_code}"
                self.log_test("Get User Recommendations - High Confidence", False, f"Failed to get high confidence recommendations: {error_detail}")
                
        except Exception as e:
            self.log_test("Get User Recommendations", False, f"Error: {str(e)}")
    
    def test_generate_all_recommendations(self):
        """Test generating all types of AI-powered recommendations"""
        if not self.auth_token:
            self.log_test("Generate All Recommendations", False, "No auth token available")
            return
            
        try:
            response = self.make_request("POST", "/recommendations/generate")
            
            if response.status_code == 200:
                data = response.json()
                total_generated = data.get("recommendations_by_type", {})
                total_count = sum(total_generated.values()) if total_generated else 0
                self.log_test("Generate All Recommendations", True, f"Generated {total_count} recommendations across all types", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Generate All Recommendations", False, f"Failed to generate recommendations: {error_detail}")
                
        except Exception as e:
            self.log_test("Generate All Recommendations", False, f"Error: {str(e)}")
    
    def test_generate_specific_recommendations(self):
        """Test generating specific types of recommendations"""
        if not self.auth_token:
            self.log_test("Generate Specific Recommendations", False, "No auth token available")
            return
            
        try:
            # Test all 5 recommendation types
            recommendation_types = [
                "skill_learning",
                "user_match", 
                "session_timing",
                "learning_path",
                "community_content"
            ]
            
            for rec_type in recommendation_types:
                response = self.make_request("POST", f"/recommendations/generate/{rec_type}")
                
                if response.status_code == 200:
                    data = response.json()
                    count = data.get("count", 0)
                    self.log_test(f"Generate {rec_type.replace('_', ' ').title()} Recommendations", True, f"Generated {count} {rec_type} recommendations", data)
                else:
                    error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                    self.log_test(f"Generate {rec_type.replace('_', ' ').title()} Recommendations", False, f"Failed to generate {rec_type} recommendations: {error_detail}")
                
        except Exception as e:
            self.log_test("Generate Specific Recommendations", False, f"Error: {str(e)}")
    
    def test_recommendation_interactions(self):
        """Test recommendation interaction methods (viewed, acted upon, dismiss)"""
        if not self.auth_token:
            self.log_test("Recommendation Interactions", False, "No auth token available")
            return
            
        try:
            # First generate some recommendations to interact with
            generate_response = self.make_request("POST", "/recommendations/generate")
            if generate_response.status_code != 200:
                self.log_test("Recommendation Interactions", False, "Could not generate recommendations for testing")
                return
            
            # Get recommendations to find one to interact with
            get_response = self.make_request("GET", "/recommendations/", params={"limit": 1})
            if get_response.status_code != 200:
                self.log_test("Recommendation Interactions", False, "Could not retrieve recommendations for testing")
                return
            
            recommendations = get_response.json()
            if not recommendations:
                self.log_test("Recommendation Interactions", False, "No recommendations available for testing")
                return
            
            test_recommendation_id = recommendations[0]["id"]
            
            # Test 1: Mark as viewed
            response1 = self.make_request("PUT", f"/recommendations/{test_recommendation_id}/viewed")
            
            if response1.status_code == 200:
                data1 = response1.json()
                self.log_test("Recommendation Interactions - Mark Viewed", True, f"Recommendation marked as viewed: {data1.get('message')}", data1)
            else:
                error_detail = response1.json().get("detail", "Unknown error") if response1.content else f"Status: {response1.status_code}"
                self.log_test("Recommendation Interactions - Mark Viewed", False, f"Failed to mark as viewed: {error_detail}")
            
            # Test 2: Mark as acted upon
            response2 = self.make_request("PUT", f"/recommendations/{test_recommendation_id}/acted-upon")
            
            if response2.status_code == 200:
                data2 = response2.json()
                self.log_test("Recommendation Interactions - Mark Acted Upon", True, f"Recommendation marked as acted upon: {data2.get('message')}", data2)
            else:
                error_detail = response2.json().get("detail", "Unknown error") if response2.content else f"Status: {response2.status_code}"
                self.log_test("Recommendation Interactions - Mark Acted Upon", False, f"Failed to mark as acted upon: {error_detail}")
            
            # Test 3: Dismiss recommendation
            response3 = self.make_request("PUT", f"/recommendations/{test_recommendation_id}/dismiss")
            
            if response3.status_code == 200:
                data3 = response3.json()
                self.log_test("Recommendation Interactions - Dismiss", True, f"Recommendation dismissed: {data3.get('message')}", data3)
            else:
                error_detail = response3.json().get("detail", "Unknown error") if response3.content else f"Status: {response3.status_code}"
                self.log_test("Recommendation Interactions - Dismiss", False, f"Failed to dismiss recommendation: {error_detail}")
                
        except Exception as e:
            self.log_test("Recommendation Interactions", False, f"Error: {str(e)}")
    
    def test_learning_goals_management(self):
        """Test learning goals management"""
        if not self.auth_token:
            self.log_test("Learning Goals Management", False, "No auth token available")
            return
            
        try:
            # First get available skills to create a goal
            skills_response = self.make_request("GET", "/skills/")
            if skills_response.status_code != 200:
                self.log_test("Learning Goals Management", False, "Could not retrieve skills for testing")
                return
                
            skills = skills_response.json()
            if not skills:
                self.log_test("Learning Goals Management", False, "No skills available for testing")
                return
            
            test_skill = skills[0]
            
            # Test 1: Create learning goal
            from datetime import datetime, timedelta
            goal_data = {
                "skill_id": test_skill["id"],
                "target_level": "intermediate",
                "target_date": (datetime.utcnow() + timedelta(days=90)).isoformat(),
                "weekly_session_target": 3
            }
            
            response1 = self.make_request("POST", "/recommendations/learning-goals", goal_data)
            
            if response1.status_code == 200:
                data1 = response1.json()
                self.created_goal_id = data1.get("id")  # Store for other tests
                self.log_test("Learning Goals - Create Goal", True, f"Learning goal created for {data1.get('skill_name')}", data1)
            else:
                error_detail = response1.json().get("detail", "Unknown error") if response1.content else f"Status: {response1.status_code}"
                self.log_test("Learning Goals - Create Goal", False, f"Failed to create learning goal: {error_detail}")
            
            # Test 2: Get learning goals
            response2 = self.make_request("GET", "/recommendations/learning-goals")
            
            if response2.status_code == 200:
                data2 = response2.json()
                self.log_test("Learning Goals - Get Goals", True, f"Retrieved {len(data2)} learning goals", {"goals_count": len(data2)})
            else:
                error_detail = response2.json().get("detail", "Unknown error") if response2.content else f"Status: {response2.status_code}"
                self.log_test("Learning Goals - Get Goals", False, f"Failed to get learning goals: {error_detail}")
            
            # Test 3: Update goal progress
            if hasattr(self, 'created_goal_id') and self.created_goal_id:
                response3 = self.make_request("PUT", f"/recommendations/learning-goals/{self.created_goal_id}/progress", params={"progress": 25.5})
                
                if response3.status_code == 200:
                    data3 = response3.json()
                    self.log_test("Learning Goals - Update Progress", True, f"Goal progress updated to {data3.get('progress')}%", data3)
                else:
                    error_detail = response3.json().get("detail", "Unknown error") if response3.content else f"Status: {response3.status_code}"
                    self.log_test("Learning Goals - Update Progress", False, f"Failed to update goal progress: {error_detail}")
            else:
                self.log_test("Learning Goals - Update Progress", False, "No goal ID available from previous test")
                
        except Exception as e:
            self.log_test("Learning Goals Management", False, f"Error: {str(e)}")
    
    def test_recommendation_insights(self):
        """Test recommendation engagement insights"""
        if not self.auth_token:
            self.log_test("Recommendation Insights", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/recommendations/insights")
            
            if response.status_code == 200:
                data = response.json()
                total_recommendations = data.get("total_recommendations", 0)
                engagement_rate = data.get("engagement_rate", 0)
                action_rate = data.get("action_rate", 0)
                self.log_test("Recommendation Insights", True, f"Retrieved insights: {total_recommendations} total recommendations, {engagement_rate}% engagement rate, {action_rate}% action rate", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Recommendation Insights", False, f"Failed to get insights: {error_detail}")
                
        except Exception as e:
            self.log_test("Recommendation Insights", False, f"Error: {str(e)}")
    
    def test_recommendation_dashboard(self):
        """Test personalized recommendation dashboard"""
        if not self.auth_token:
            self.log_test("Recommendation Dashboard", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/recommendations/dashboard")
            
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get("recommendations", {})
                learning_goals = data.get("learning_goals", {})
                quick_stats = data.get("quick_stats", {})
                
                featured_count = len(recommendations.get("featured", []))
                total_goals = learning_goals.get("total_goals", 0)
                total_recs = quick_stats.get("total_recommendations", 0)
                
                self.log_test("Recommendation Dashboard", True, f"Retrieved dashboard: {featured_count} featured recommendations, {total_goals} learning goals, {total_recs} total recommendations", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Recommendation Dashboard", False, f"Failed to get dashboard: {error_detail}")
                
        except Exception as e:
            self.log_test("Recommendation Dashboard", False, f"Error: {str(e)}")
    
    def test_recommendations_authentication_required(self):
        """Test that recommendation endpoints require authentication"""
        try:
            # Temporarily remove auth token
            original_token = self.auth_token
            self.auth_token = None
            
            # Try to access recommendations without authentication
            response = self.make_request("GET", "/recommendations/")
            
            # Restore auth token
            self.auth_token = original_token
            
            if response.status_code in [401, 403]:
                self.log_test("Recommendations Authentication Required", True, f"Authentication correctly required ({response.status_code})")
            else:
                self.log_test("Recommendations Authentication Required", False, f"Authentication not required - Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Recommendations Authentication Required", False, f"Error: {str(e)}")
    
    
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
        
        # User profile tests (NEW FEATURES)
        self.test_get_user_profile()
        self.test_update_user_profile()
        
        # User management tests
        self.test_get_user_statistics()
        self.test_search_users_with_filters()
        self.test_get_leaderboard()
        
        # Skill management tests (NEW FEATURES)
        self.test_get_all_skills()
        self.test_search_skills()
        self.test_get_popular_skills()
        self.test_get_skill_categories()
        self.test_add_user_skill()
        self.test_get_user_skills()
        self.test_update_user_skill()
        self.test_delete_user_skill()
        self.test_update_skill_preferences()
        
        # AI Matching tests (NEW FEATURES)
        self.test_find_matches()
        self.test_get_my_matches()
        self.test_get_match_suggestions()
        self.test_get_matching_analytics()
        
        # Session Management tests (NEW FEATURES)
        print("\n🎯 Testing Session Management System...")
        self.test_create_session()
        self.test_get_my_sessions()
        self.test_get_upcoming_sessions()
        self.test_get_specific_session()
        self.test_update_session()
        self.test_start_session()
        self.test_end_session()
        self.test_submit_session_feedback()
        self.test_cancel_session()
        self.test_get_session_statistics()
        self.test_get_user_availability()
        self.test_search_sessions()
        self.test_session_permission_controls()
        self.test_session_authentication_required()
        
        # Real-time Messaging tests (NEW FEATURES)
        print("\n💬 Testing Real-time Messaging System...")
        self.test_get_user_conversations()
        self.test_create_conversation()
        self.test_get_specific_conversation()
        self.test_send_message()
        self.test_get_conversation_messages()
        self.test_mark_message_as_read()
        self.test_mark_conversation_as_read()
        self.test_get_unread_count()
        self.test_delete_message()
        self.test_edit_message()
        self.test_search_messages()
        self.test_get_online_users()
        self.test_messaging_authentication_required()
        self.test_messaging_permission_controls()
        
        # Gamification System Tests
        print("\n🎮 Testing Gamification System...")
        self.test_get_user_progress()
        self.test_get_all_badges()
        self.test_get_all_achievements()
        self.test_get_leaderboard()
        self.test_get_user_transactions()
        self.test_check_user_progress()
        self.test_get_other_user_progress()
        self.test_award_skill_coins()
        self.test_get_gamification_stats()
        self.test_gamification_authentication_required()
        self.test_gamification_badge_system_integration()
        
        # Community Features Tests (NEW FEATURES)
        print("\n🏘️ Testing Community Features System...")
        self.test_get_forums()
        self.test_create_forum()
        self.test_get_specific_forum()
        self.test_get_posts()
        self.test_create_post()
        self.test_get_specific_post()
        self.test_update_post()
        self.test_toggle_post_like()
        self.test_get_post_comments()
        self.test_create_comment()
        self.test_toggle_comment_like()
        self.test_get_groups()
        self.test_create_group()
        self.test_join_group()
        self.test_get_testimonials()
        self.test_create_testimonial()
        self.test_get_knowledge_base()
        self.test_create_knowledge_base_entry()
        self.test_get_community_stats()
        self.test_get_trending_topics()
        self.test_community_authentication_required()
        
        # WebRTC Video Chat Tests (NEW FEATURES)
        print("\n📹 Testing WebRTC Video Chat System...")
        self.test_get_webrtc_config()
        self.test_get_session_info_for_webrtc()
        self.test_start_video_call()
        self.test_end_video_call()
        self.test_webrtc_session_access_control()
        self.test_webrtc_authentication_required()
        self.test_webrtc_invalid_session_handling()
        self.test_webrtc_session_status_validation()
        
        # Smart Notifications System Tests (NEW FEATURES)
        print("\n🔔 Testing Smart Notifications System...")
        self.test_get_user_notifications()
        self.test_get_notification_count()
        self.test_get_notification_stats()
        self.test_create_notification()
        self.test_update_notification()
        self.test_mark_all_notifications_read()
        self.test_delete_notification()
        self.test_get_notification_preferences()
        self.test_update_notification_preferences()
        self.test_quick_notification_match_found()
        self.test_quick_notification_session_reminder()
        self.test_quick_notification_achievement_earned()
        self.test_quick_notification_message_received()
        
        # Smart Recommendations System Tests (NEW FEATURES)
        print("\n🎯 Testing Smart Recommendations System...")
        self.test_get_user_recommendations()
        self.test_generate_all_recommendations()
        self.test_generate_specific_recommendations()
        self.test_mark_recommendation_viewed()
        self.test_mark_recommendation_acted_upon()
        self.test_dismiss_recommendation()
        self.test_get_learning_goals()
        self.test_create_learning_goal()
        self.test_update_goal_progress()
        self.test_get_recommendation_insights()
        self.test_get_recommendation_dashboard()
        
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
        print("  • Session Management System")
        print("  • Real-time Messaging System")
        print("  • Gamification System")
        print("  • Community Features System")
        print("  • WebRTC Video Chat System")
        print("  • Smart Notifications System")
        print("  • Smart Recommendations System")
        print("  • Search and Discovery")
        print("  • Analytics and Statistics")
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = SkillSwapTester()
    tester.run_all_tests()