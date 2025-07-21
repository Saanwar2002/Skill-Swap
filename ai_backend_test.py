#!/usr/bin/env python3
"""
Comprehensive AI Learning Companion Backend Testing
Tests all AI-powered features including chat system, conversation management,
quick helpers, session analysis, learning insights, study plans, and analytics.
"""

import requests
import json
import time
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://4f055f89-6ced-4357-ab0a-a1d5329feb6c.preview.emergentagent.com/api"
TIMEOUT = 30

class AILearningCompanionTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.auth_token = None
        self.test_user_id = None
        self.test_results = []
        
        # Test data storage
        self.created_conversation_id = None
        self.created_session_id = None
        self.created_study_plan_id = None
        self.created_session_analysis_id = None
        
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
                return self.session.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                return self.session.post(url, json=data, headers=headers, params=params)
            elif method.upper() == "PUT":
                return self.session.put(url, json=data, headers=headers, params=params)
            elif method.upper() == "DELETE":
                return self.session.delete(url, headers=headers, params=params)
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            raise
    
    def setup_test_user(self):
        """Create and authenticate a test user"""
        timestamp = int(time.time())
        user_data = {
            "email": f"ailearner{timestamp}@skillswap.com",
            "username": f"ailearner{timestamp}",
            "password": "AILearner123!",
            "first_name": "AI",
            "last_name": "Learner",
            "bio": "Testing AI Learning Companion features",
            "role": "both"
        }
        
        try:
            # Register user
            response = self.make_request("POST", "/auth/register", user_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                user_info = data.get("user", {})
                self.test_user_id = user_info.get("id")
                self.log_test("Setup Test User", True, f"User created: {user_info.get('username')}")
                return True
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Setup Test User", False, f"Registration failed: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("Setup Test User", False, f"Error: {str(e)}")
            return False
    
    def create_test_session(self):
        """Create a test session for analysis testing"""
        try:
            # First get available skills
            skills_response = self.make_request("GET", "/skills/")
            if skills_response.status_code != 200:
                return None
                
            skills = skills_response.json()
            if not skills:
                return None
            
            # Use Python skill if available, otherwise first skill
            python_skill = next((skill for skill in skills if "Python" in skill.get("name", "")), skills[0])
            
            # Create a session
            session_data = {
                "teacher_id": self.test_user_id,
                "learner_id": self.test_user_id,  # Self-session for testing
                "skill_id": python_skill["id"],
                "skill_name": python_skill["name"],
                "title": "Python Fundamentals - Variables and Data Types",
                "description": "Learning basic Python concepts including variables, data types, and basic operations",
                "scheduled_start": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                "scheduled_end": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
                "timezone": "UTC",
                "session_type": "video",
                "learning_objectives": [
                    "Understand Python variables",
                    "Learn different data types",
                    "Practice basic operations"
                ],
                "skill_coins_paid": 50
            }
            
            response = self.make_request("POST", "/sessions/", session_data)
            
            if response.status_code == 200:
                session = response.json()
                self.created_session_id = session.get("id")
                return session
            
            return None
            
        except Exception as e:
            print(f"Error creating test session: {str(e)}")
            return None
    
    # ===== AI CHAT SYSTEM TESTS =====
    
    def test_ai_chat_learning_assistance(self):
        """Test AI chat with learning assistance conversation type"""
        if not self.auth_token:
            self.log_test("AI Chat - Learning Assistance", False, "No auth token available")
            return
            
        try:
            message_data = {
                "conversation_type": "learning_assistance",
                "content": "I'm struggling to understand Python variables. Can you help me understand the difference between strings and integers?",
                "skill_context": "Python",
                "context_data": {
                    "skill_name": "Python",
                    "difficulty_level": "beginner",
                    "specific_topic": "variables and data types"
                }
            }
            
            response = self.make_request("POST", "/ai/chat", message_data)
            
            if response.status_code == 200:
                data = response.json()
                self.created_conversation_id = data.get("conversation_id")
                ai_response = data.get("content", "")
                confidence = data.get("ai_confidence", 0)
                self.log_test("AI Chat - Learning Assistance", True, 
                             f"AI responded with {len(ai_response)} characters, confidence: {confidence}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("AI Chat - Learning Assistance", False, f"Chat failed: {error_detail}")
                
        except Exception as e:
            self.log_test("AI Chat - Learning Assistance", False, f"Error: {str(e)}")
    
    def test_ai_chat_skill_guidance(self):
        """Test AI chat with skill guidance conversation type"""
        if not self.auth_token:
            self.log_test("AI Chat - Skill Guidance", False, "No auth token available")
            return
            
        try:
            message_data = {
                "conversation_type": "skill_guidance",
                "content": "I want to become proficient in machine learning. What learning path would you recommend?",
                "skill_context": "Machine Learning",
                "context_data": {
                    "skill_name": "Machine Learning",
                    "current_level": "beginner",
                    "goal_level": "intermediate",
                    "time_commitment": "10 hours per week"
                }
            }
            
            response = self.make_request("POST", "/ai/chat", message_data)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("content", "")
                confidence = data.get("ai_confidence", 0)
                self.log_test("AI Chat - Skill Guidance", True, 
                             f"AI provided guidance with {len(ai_response)} characters, confidence: {confidence}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("AI Chat - Skill Guidance", False, f"Skill guidance failed: {error_detail}")
                
        except Exception as e:
            self.log_test("AI Chat - Skill Guidance", False, f"Error: {str(e)}")
    
    def test_ai_chat_practice_feedback(self):
        """Test AI chat with practice feedback conversation type"""
        if not self.auth_token:
            self.log_test("AI Chat - Practice Feedback", False, "No auth token available")
            return
            
        try:
            message_data = {
                "conversation_type": "practice_feedback",
                "content": "I just wrote my first Python function to calculate the area of a rectangle. Here's my code: def area(length, width): return length * width. How did I do?",
                "skill_context": "Python",
                "context_data": {
                    "skill_name": "Python",
                    "practice_type": "coding_exercise",
                    "code_submitted": "def area(length, width): return length * width"
                }
            }
            
            response = self.make_request("POST", "/ai/chat", message_data)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("content", "")
                confidence = data.get("ai_confidence", 0)
                self.log_test("AI Chat - Practice Feedback", True, 
                             f"AI provided feedback with {len(ai_response)} characters, confidence: {confidence}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("AI Chat - Practice Feedback", False, f"Practice feedback failed: {error_detail}")
                
        except Exception as e:
            self.log_test("AI Chat - Practice Feedback", False, f"Error: {str(e)}")
    
    def test_ai_chat_career_advice(self):
        """Test AI chat with career advice conversation type"""
        if not self.auth_token:
            self.log_test("AI Chat - Career Advice", False, "No auth token available")
            return
            
        try:
            message_data = {
                "conversation_type": "career_advice",
                "content": "I'm a beginner programmer and want to transition into a data science career. What skills should I focus on and what's a realistic timeline?",
                "context_data": {
                    "current_role": "beginner programmer",
                    "target_role": "data scientist",
                    "experience_level": "beginner",
                    "available_time": "15 hours per week"
                }
            }
            
            response = self.make_request("POST", "/ai/chat", message_data)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("content", "")
                confidence = data.get("ai_confidence", 0)
                self.log_test("AI Chat - Career Advice", True, 
                             f"AI provided career advice with {len(ai_response)} characters, confidence: {confidence}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("AI Chat - Career Advice", False, f"Career advice failed: {error_detail}")
                
        except Exception as e:
            self.log_test("AI Chat - Career Advice", False, f"Error: {str(e)}")
    
    def test_ai_chat_general_help(self):
        """Test AI chat with general help conversation type"""
        if not self.auth_token:
            self.log_test("AI Chat - General Help", False, "No auth token available")
            return
            
        try:
            message_data = {
                "conversation_type": "general_help",
                "content": "How does the SkillSwap platform work? I'm new here and want to understand how to get the most out of it.",
                "context_data": {
                    "user_type": "new_user",
                    "platform_experience": "none"
                }
            }
            
            response = self.make_request("POST", "/ai/chat", message_data)
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("content", "")
                confidence = data.get("ai_confidence", 0)
                self.log_test("AI Chat - General Help", True, 
                             f"AI provided general help with {len(ai_response)} characters, confidence: {confidence}", data)
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("AI Chat - General Help", False, f"General help failed: {error_detail}")
                
        except Exception as e:
            self.log_test("AI Chat - General Help", False, f"Error: {str(e)}")
    
    # ===== CONVERSATION MANAGEMENT TESTS =====
    
    def test_get_user_conversations(self):
        """Test getting user's AI conversations"""
        if not self.auth_token:
            self.log_test("Get User Conversations", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/ai/conversations", params={"limit": 20})
            
            if response.status_code == 200:
                data = response.json()
                conversation_count = len(data)
                self.log_test("Get User Conversations", True, 
                             f"Retrieved {conversation_count} AI conversations", 
                             {"conversation_count": conversation_count, "conversations": data})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get User Conversations", False, f"Failed to get conversations: {error_detail}")
                
        except Exception as e:
            self.log_test("Get User Conversations", False, f"Error: {str(e)}")
    
    def test_get_conversation_messages(self):
        """Test getting messages from a specific AI conversation"""
        if not self.auth_token:
            self.log_test("Get Conversation Messages", False, "No auth token available")
            return
        
        if not self.created_conversation_id:
            self.log_test("Get Conversation Messages", False, "No conversation ID available from previous tests")
            return
            
        try:
            response = self.make_request("GET", f"/ai/conversations/{self.created_conversation_id}/messages")
            
            if response.status_code == 200:
                data = response.json()
                message_count = len(data)
                self.log_test("Get Conversation Messages", True, 
                             f"Retrieved {message_count} messages from conversation", 
                             {"message_count": message_count, "messages": data})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Conversation Messages", False, f"Failed to get conversation messages: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Conversation Messages", False, f"Error: {str(e)}")
    
    # ===== QUICK AI HELPERS TESTS =====
    
    def test_quick_skill_help(self):
        """Test quick skill help endpoint"""
        if not self.auth_token:
            self.log_test("Quick Skill Help", False, "No auth token available")
            return
            
        try:
            response = self.make_request("POST", "/ai/quick/skill-help", params={
                "skill_name": "JavaScript",
                "question": "What's the difference between let, const, and var in JavaScript?"
            })
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("response", "")
                conversation_id = data.get("conversation_id")
                self.log_test("Quick Skill Help", True, 
                             f"AI provided quick help with {len(ai_response)} characters", 
                             {"response_length": len(ai_response), "conversation_id": conversation_id})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Quick Skill Help", False, f"Quick skill help failed: {error_detail}")
                
        except Exception as e:
            self.log_test("Quick Skill Help", False, f"Error: {str(e)}")
    
    def test_quick_practice_feedback(self):
        """Test quick practice feedback endpoint"""
        if not self.auth_token:
            self.log_test("Quick Practice Feedback", False, "No auth token available")
            return
            
        try:
            response = self.make_request("POST", "/ai/quick/practice-feedback", params={
                "skill_name": "React",
                "practice_description": "I built a simple todo app with React hooks. I used useState for managing the todo list and useEffect for localStorage persistence. The app allows adding, deleting, and marking todos as complete."
            })
            
            if response.status_code == 200:
                data = response.json()
                feedback = data.get("feedback", "")
                conversation_id = data.get("conversation_id")
                self.log_test("Quick Practice Feedback", True, 
                             f"AI provided practice feedback with {len(feedback)} characters", 
                             {"feedback_length": len(feedback), "conversation_id": conversation_id})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Quick Practice Feedback", False, f"Quick practice feedback failed: {error_detail}")
                
        except Exception as e:
            self.log_test("Quick Practice Feedback", False, f"Error: {str(e)}")
    
    # ===== SESSION ANALYSIS TESTS =====
    
    def test_create_session_analysis(self):
        """Test creating AI-powered session analysis"""
        if not self.auth_token:
            self.log_test("Create Session Analysis", False, "No auth token available")
            return
        
        # Create a test session if we don't have one
        if not self.created_session_id:
            session = self.create_test_session()
            if not session:
                self.log_test("Create Session Analysis", False, "Could not create test session")
                return
            
        try:
            analysis_data = {
                "session_id": self.created_session_id,
                "transcript": "Teacher: Today we're learning about Python variables. A variable is like a container that holds data. Student: So it's like a box? Teacher: Exactly! You can put different types of data in these boxes - numbers, text, lists. Student: How do I create a variable? Teacher: You just assign a value like this: name = 'John'. Student: That's simple! Teacher: Yes, Python makes it easy. Let's try with numbers too. age = 25. Student: I understand now!",
                "additional_context": {
                    "session_duration": 60,
                    "skill_level": "beginner",
                    "learning_objectives": ["Understand variables", "Learn data types", "Practice assignments"]
                }
            }
            
            response = self.make_request("POST", "/ai/session-analysis", analysis_data)
            
            if response.status_code == 200:
                data = response.json()
                self.created_session_analysis_id = data.get("id")
                summary = data.get("summary", "")
                comprehension_score = data.get("comprehension_score", 0)
                engagement_score = data.get("engagement_score", 0)
                key_topics = data.get("key_topics_covered", [])
                
                self.log_test("Create Session Analysis", True, 
                             f"Analysis created - Comprehension: {comprehension_score}%, Engagement: {engagement_score}%, Topics: {len(key_topics)}", 
                             {
                                 "analysis_id": self.created_session_analysis_id,
                                 "summary_length": len(summary),
                                 "comprehension_score": comprehension_score,
                                 "engagement_score": engagement_score,
                                 "topics_count": len(key_topics)
                             })
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Create Session Analysis", False, f"Session analysis creation failed: {error_detail}")
                
        except Exception as e:
            self.log_test("Create Session Analysis", False, f"Error: {str(e)}")
    
    def test_get_session_analysis(self):
        """Test retrieving session analysis"""
        if not self.auth_token:
            self.log_test("Get Session Analysis", False, "No auth token available")
            return
        
        if not self.created_session_id:
            self.log_test("Get Session Analysis", False, "No session ID available")
            return
            
        try:
            response = self.make_request("GET", f"/ai/session-analysis/{self.created_session_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data:  # Analysis exists
                    summary = data.get("summary", "")
                    recommendations = data.get("practice_recommendations", [])
                    next_steps = data.get("next_steps_suggested", [])
                    
                    self.log_test("Get Session Analysis", True, 
                                 f"Retrieved analysis - Summary: {len(summary)} chars, Recommendations: {len(recommendations)}, Next steps: {len(next_steps)}", 
                                 {
                                     "has_analysis": True,
                                     "summary_length": len(summary),
                                     "recommendations_count": len(recommendations),
                                     "next_steps_count": len(next_steps)
                                 })
                else:  # No analysis found
                    self.log_test("Get Session Analysis", True, "No analysis found for session (expected for new session)", {"has_analysis": False})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Session Analysis", False, f"Failed to get session analysis: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Session Analysis", False, f"Error: {str(e)}")
    
    # ===== LEARNING INSIGHTS TESTS =====
    
    def test_get_learning_insights(self):
        """Test getting user's learning insights"""
        if not self.auth_token:
            self.log_test("Get Learning Insights", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/ai/insights", params={"limit": 10})
            
            if response.status_code == 200:
                data = response.json()
                insights_count = len(data)
                
                if insights_count > 0:
                    insight_types = [insight.get("insight_type") for insight in data]
                    viewed_count = sum(1 for insight in data if insight.get("is_viewed", False))
                    
                    self.log_test("Get Learning Insights", True, 
                                 f"Retrieved {insights_count} insights, {viewed_count} viewed, types: {set(insight_types)}", 
                                 {
                                     "insights_count": insights_count,
                                     "viewed_count": viewed_count,
                                     "insight_types": list(set(insight_types))
                                 })
                else:
                    self.log_test("Get Learning Insights", True, "No insights found (expected for new user)", {"insights_count": 0})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Learning Insights", False, f"Failed to get learning insights: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Learning Insights", False, f"Error: {str(e)}")
    
    def test_generate_learning_insights(self):
        """Test generating new learning insights"""
        if not self.auth_token:
            self.log_test("Generate Learning Insights", False, "No auth token available")
            return
            
        try:
            response = self.make_request("POST", "/ai/insights/generate")
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", "")
                count = data.get("count", 0)
                
                self.log_test("Generate Learning Insights", True, 
                             f"Generated {count} new insights: {message}", 
                             {"generated_count": count, "message": message})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Generate Learning Insights", False, f"Failed to generate insights: {error_detail}")
                
        except Exception as e:
            self.log_test("Generate Learning Insights", False, f"Error: {str(e)}")
    
    # ===== STUDY PLANS TESTS =====
    
    def test_create_study_plan(self):
        """Test creating AI-generated study plan"""
        if not self.auth_token:
            self.log_test("Create Study Plan", False, "No auth token available")
            return
            
        try:
            # First get available skills
            skills_response = self.make_request("GET", "/skills/")
            if skills_response.status_code != 200:
                self.log_test("Create Study Plan", False, "Could not retrieve skills")
                return
                
            skills = skills_response.json()
            if not skills:
                self.log_test("Create Study Plan", False, "No skills available")
                return
            
            # Find a skill for the study plan (prefer Machine Learning or Python)
            target_skill = next((skill for skill in skills if "Machine Learning" in skill.get("name", "")), 
                              next((skill for skill in skills if "Python" in skill.get("name", "")), skills[0]))
            
            study_plan_data = {
                "skill_id": target_skill["id"],
                "target_level": "intermediate",
                "estimated_duration_weeks": 12,
                "weekly_time_commitment": 8
            }
            
            response = self.make_request("POST", "/ai/study-plan", study_plan_data)
            
            if response.status_code == 200:
                data = response.json()
                self.created_study_plan_id = data.get("id")
                skill_name = data.get("skill_name", "")
                modules_count = len(data.get("modules", []))
                milestones_count = len(data.get("milestones", []))
                duration = data.get("estimated_duration_weeks", 0)
                
                self.log_test("Create Study Plan", True, 
                             f"Study plan created for {skill_name} - {duration} weeks, {modules_count} modules, {milestones_count} milestones", 
                             {
                                 "plan_id": self.created_study_plan_id,
                                 "skill_name": skill_name,
                                 "duration_weeks": duration,
                                 "modules_count": modules_count,
                                 "milestones_count": milestones_count
                             })
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Create Study Plan", False, f"Study plan creation failed: {error_detail}")
                
        except Exception as e:
            self.log_test("Create Study Plan", False, f"Error: {str(e)}")
    
    def test_get_study_plans(self):
        """Test getting user's study plans"""
        if not self.auth_token:
            self.log_test("Get Study Plans", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/ai/study-plans")
            
            if response.status_code == 200:
                data = response.json()
                plans_count = len(data)
                
                if plans_count > 0:
                    active_plans = [plan for plan in data if plan.get("is_active", False)]
                    skills_covered = [plan.get("skill_name") for plan in data]
                    
                    self.log_test("Get Study Plans", True, 
                                 f"Retrieved {plans_count} study plans, {len(active_plans)} active, skills: {skills_covered}", 
                                 {
                                     "total_plans": plans_count,
                                     "active_plans": len(active_plans),
                                     "skills_covered": skills_covered
                                 })
                else:
                    self.log_test("Get Study Plans", True, "No study plans found", {"plans_count": 0})
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Get Study Plans", False, f"Failed to get study plans: {error_detail}")
                
        except Exception as e:
            self.log_test("Get Study Plans", False, f"Error: {str(e)}")
    
    def test_update_study_plan_progress(self):
        """Test updating study plan progress"""
        if not self.auth_token:
            self.log_test("Update Study Plan Progress", False, "No auth token available")
            return
        
        if not self.created_study_plan_id:
            self.log_test("Update Study Plan Progress", False, "No study plan ID available")
            return
            
        try:
            response = self.make_request("PUT", f"/ai/study-plans/{self.created_study_plan_id}/progress", 
                                       params={
                                           "current_module": 2,
                                           "completion_percentage": 25.5
                                       })
            
            if response.status_code == 200:
                data = response.json()
                current_module = data.get("current_module", 0)
                completion = data.get("completion_percentage", 0)
                
                self.log_test("Update Study Plan Progress", True, 
                             f"Progress updated - Module: {current_module}, Completion: {completion}%", 
                             {
                                 "current_module": current_module,
                                 "completion_percentage": completion
                             })
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("Update Study Plan Progress", False, f"Failed to update progress: {error_detail}")
                
        except Exception as e:
            self.log_test("Update Study Plan Progress", False, f"Error: {str(e)}")
    
    # ===== ANALYTICS TESTS =====
    
    def test_ai_analytics_summary(self):
        """Test AI analytics summary endpoint"""
        if not self.auth_token:
            self.log_test("AI Analytics Summary", False, "No auth token available")
            return
            
        try:
            response = self.make_request("GET", "/ai/analytics/summary")
            
            if response.status_code == 200:
                data = response.json()
                total_conversations = data.get("total_conversations", 0)
                active_conversations = data.get("active_conversations", 0)
                total_insights = data.get("total_insights", 0)
                unviewed_insights = data.get("unviewed_insights", 0)
                active_study_plans = data.get("active_study_plans", 0)
                conversation_types = data.get("conversation_types", {})
                
                self.log_test("AI Analytics Summary", True, 
                             f"Conversations: {total_conversations} ({active_conversations} active), Insights: {total_insights} ({unviewed_insights} unviewed), Study plans: {active_study_plans}", 
                             {
                                 "total_conversations": total_conversations,
                                 "active_conversations": active_conversations,
                                 "total_insights": total_insights,
                                 "unviewed_insights": unviewed_insights,
                                 "active_study_plans": active_study_plans,
                                 "conversation_types": conversation_types
                             })
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else f"Status: {response.status_code}"
                self.log_test("AI Analytics Summary", False, f"Failed to get analytics summary: {error_detail}")
                
        except Exception as e:
            self.log_test("AI Analytics Summary", False, f"Error: {str(e)}")
    
    # ===== AUTHENTICATION TESTS =====
    
    def test_ai_endpoints_require_authentication(self):
        """Test that AI endpoints require authentication"""
        try:
            # Temporarily remove auth token
            original_token = self.auth_token
            self.auth_token = None
            
            # Test various AI endpoints without authentication
            endpoints_to_test = [
                ("/ai/chat", "POST"),
                ("/ai/conversations", "GET"),
                ("/ai/insights", "GET"),
                ("/ai/study-plans", "GET"),
                ("/ai/analytics/summary", "GET")
            ]
            
            unauthorized_count = 0
            for endpoint, method in endpoints_to_test:
                try:
                    if method == "POST":
                        response = self.make_request(method, endpoint, {"content": "test"})
                    else:
                        response = self.make_request(method, endpoint)
                    
                    if response.status_code in [401, 403]:
                        unauthorized_count += 1
                except:
                    unauthorized_count += 1  # Request failed, which is expected
            
            # Restore auth token
            self.auth_token = original_token
            
            if unauthorized_count == len(endpoints_to_test):
                self.log_test("AI Endpoints Require Authentication", True, 
                             f"All {len(endpoints_to_test)} AI endpoints correctly require authentication")
            else:
                self.log_test("AI Endpoints Require Authentication", False, 
                             f"Only {unauthorized_count}/{len(endpoints_to_test)} endpoints require authentication")
                
        except Exception as e:
            # Restore auth token in case of error
            if 'original_token' in locals():
                self.auth_token = original_token
            self.log_test("AI Endpoints Require Authentication", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all AI Learning Companion tests"""
        print("🤖 Starting AI Learning Companion Backend Testing...")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user. Aborting tests.")
            return
        
        print("\n🎯 Testing AI Chat System...")
        self.test_ai_chat_learning_assistance()
        self.test_ai_chat_skill_guidance()
        self.test_ai_chat_practice_feedback()
        self.test_ai_chat_career_advice()
        self.test_ai_chat_general_help()
        
        print("\n💬 Testing Conversation Management...")
        self.test_get_user_conversations()
        self.test_get_conversation_messages()
        
        print("\n⚡ Testing Quick AI Helpers...")
        self.test_quick_skill_help()
        self.test_quick_practice_feedback()
        
        print("\n📊 Testing Session Analysis...")
        self.test_create_session_analysis()
        self.test_get_session_analysis()
        
        print("\n💡 Testing Learning Insights...")
        self.test_get_learning_insights()
        self.test_generate_learning_insights()
        
        print("\n📚 Testing Study Plans...")
        self.test_create_study_plan()
        self.test_get_study_plans()
        self.test_update_study_plan_progress()
        
        print("\n📈 Testing Analytics...")
        self.test_ai_analytics_summary()
        
        print("\n🔒 Testing Authentication...")
        self.test_ai_endpoints_require_authentication()
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 AI LEARNING COMPANION TESTING COMPLETE!")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 RESULTS SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n🎯 AI LEARNING COMPANION SYSTEM STATUS: {'✅ FULLY FUNCTIONAL' if success_rate >= 90 else '⚠️ NEEDS ATTENTION' if success_rate >= 70 else '❌ CRITICAL ISSUES'}")
        
        return self.test_results

if __name__ == "__main__":
    tester = AILearningCompanionTester()
    results = tester.run_all_tests()