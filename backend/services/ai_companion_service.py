import os
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from bson import ObjectId
import asyncio

from models import (
    AIConversationType, AIMessage, AIConversation, SessionAnalysis,
    LearningInsight, SkillAssessment, StudyPlan, LearningAnalytics,
    AIMessageCreate, AIMessageResponse, SessionAnalysisCreate,
    SkillLevel, Session, User, Skill, UserSkill
)


class AICompanionService:
    def __init__(self):
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.db_name = os.environ.get('DB_NAME', 'test_database')
        self.client = MongoClient(self.mongo_url)
        self.db = self.client[self.db_name]
        
        # Collections
        self.ai_conversations = self.db.ai_conversations
        self.ai_messages = self.db.ai_messages
        self.session_analyses = self.db.session_analyses
        self.learning_insights = self.db.learning_insights
        self.skill_assessments = self.db.skill_assessments
        self.study_plans = self.db.study_plans
        self.learning_analytics = self.db.learning_analytics
        
        # Other collections for context
        self.users = self.db.users
        self.sessions = self.db.sessions
        self.skills = self.db.skills
        self.user_skills = self.db.user_skills


    async def create_ai_conversation(self, user_id: str, conversation_type: AIConversationType, 
                                   title: str, skill_context: str = None, session_context: str = None) -> AIConversation:
        """Create a new AI conversation"""
        conversation = AIConversation(
            user_id=user_id,
            conversation_type=conversation_type,
            title=title,
            skill_context=skill_context,
            session_context=session_context
        )
        
        conversation_dict = conversation.dict()
        conversation_dict['_id'] = conversation_dict['id']
        del conversation_dict['id']
        
        result = self.ai_conversations.insert_one(conversation_dict)
        conversation_dict['id'] = str(result.inserted_id)
        
        return AIConversation(**conversation_dict)


    async def send_ai_message(self, message_create: AIMessageCreate, user_id: str) -> AIMessageResponse:
        """Send a message to AI companion and get response"""
        
        # Get or create conversation
        conversation = None
        if message_create.conversation_id:
            conv_data = self.ai_conversations.find_one({"_id": message_create.conversation_id})
            if conv_data:
                conv_data['id'] = str(conv_data['_id'])
                conversation = AIConversation(**conv_data)
        
        if not conversation:
            # Create new conversation
            title = self._generate_conversation_title(message_create.content, message_create.conversation_type)
            conversation = await self.create_ai_conversation(
                user_id=user_id,
                conversation_type=message_create.conversation_type,
                title=title,
                skill_context=message_create.skill_context,
                session_context=message_create.session_context
            )
        
        # Save user message
        user_message = AIMessage(
            conversation_id=conversation.id,
            user_id=user_id,
            role="user",
            content=message_create.content,
            context_data=message_create.context_data,
            conversation_type=message_create.conversation_type,
            skill_context=message_create.skill_context,
            session_context=message_create.session_context
        )
        
        user_msg_dict = user_message.dict()
        user_msg_dict['_id'] = user_msg_dict['id']
        del user_msg_dict['id']
        
        self.ai_messages.insert_one(user_msg_dict)
        
        # Generate AI response
        ai_response_content = await self._generate_ai_response(
            conversation=conversation,
            user_message=message_create.content,
            context_data=message_create.context_data,
            user_id=user_id
        )
        
        # Save AI response
        ai_message = AIMessage(
            conversation_id=conversation.id,
            user_id=user_id,
            role="assistant",
            content=ai_response_content,
            context_data=message_create.context_data,
            conversation_type=message_create.conversation_type,
            skill_context=message_create.skill_context,
            session_context=message_create.session_context,
            ai_confidence=0.85  # This would come from actual AI model
        )
        
        ai_msg_dict = ai_message.dict()
        ai_msg_dict['_id'] = ai_msg_dict['id']
        del ai_msg_dict['id']
        
        result = self.ai_messages.insert_one(ai_msg_dict)
        ai_msg_dict['id'] = str(result.inserted_id)
        
        # Update conversation
        self.ai_conversations.update_one(
            {"_id": conversation.id},
            {
                "$set": {
                    "last_message_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                "$inc": {"message_count": 2}  # User message + AI response
            }
        )
        
        return AIMessageResponse(
            id=ai_message.id,
            conversation_id=conversation.id,
            role="assistant",
            content=ai_response_content,
            ai_confidence=0.85,
            created_at=ai_message.created_at,
            conversation_type=message_create.conversation_type,
            skill_context=message_create.skill_context,
            session_context=message_create.session_context
        )


    async def _generate_ai_response(self, conversation: AIConversation, user_message: str, 
                                  context_data: Dict[str, Any], user_id: str) -> str:
        """Generate AI response using WebLLM (this will be handled on frontend)"""
        
        # For now, we'll create intelligent response templates based on conversation type
        # The actual AI generation will happen on the frontend using WebLLM
        
        user_data = self.users.find_one({"_id": user_id})
        user_name = user_data.get('first_name', 'there') if user_data else 'there'
        
        if conversation.conversation_type == AIConversationType.LEARNING_ASSISTANCE:
            return self._generate_learning_assistance_response(user_message, user_name, context_data)
        elif conversation.conversation_type == AIConversationType.SESSION_ANALYSIS:
            return self._generate_session_analysis_response(user_message, user_name, context_data)
        elif conversation.conversation_type == AIConversationType.SKILL_GUIDANCE:
            return self._generate_skill_guidance_response(user_message, user_name, context_data)
        elif conversation.conversation_type == AIConversationType.PRACTICE_FEEDBACK:
            return self._generate_practice_feedback_response(user_message, user_name, context_data)
        elif conversation.conversation_type == AIConversationType.CAREER_ADVICE:
            return self._generate_career_advice_response(user_message, user_name, context_data)
        else:
            return self._generate_general_help_response(user_message, user_name, context_data)


    def _generate_learning_assistance_response(self, user_message: str, user_name: str, context_data: Dict[str, Any]) -> str:
        """Generate learning assistance response"""
        skill_context = context_data.get('skill_name', 'your skill')
        
        responses = [
            f"Hi {user_name}! I'd be happy to help you with {skill_context}. Could you tell me more specifically what you're struggling with?",
            f"Great question about {skill_context}, {user_name}! Let me break this down into simpler concepts for you.",
            f"I understand you're working on {skill_context}. Here's a step-by-step approach that might help:",
            f"That's an excellent question, {user_name}! For {skill_context}, I recommend starting with the fundamentals."
        ]
        
        # Simple response selection based on message content
        if any(word in user_message.lower() for word in ['help', 'confused', 'stuck', 'don\'t understand']):
            return responses[0]
        elif any(word in user_message.lower() for word in ['how', 'what', 'why']):
            return responses[1]
        elif any(word in user_message.lower() for word in ['step', 'process', 'method']):
            return responses[2]
        else:
            return responses[3]


    def _generate_session_analysis_response(self, user_message: str, user_name: str, context_data: Dict[str, Any]) -> str:
        """Generate session analysis response"""
        return f"Hi {user_name}! I've analyzed your recent learning session. Based on the content covered, here are my insights and recommendations for your next steps in learning."


    def _generate_skill_guidance_response(self, user_message: str, user_name: str, context_data: Dict[str, Any]) -> str:
        """Generate skill guidance response"""
        return f"Hello {user_name}! I'm here to guide you on your skill development journey. What specific area would you like to focus on improving?"


    def _generate_practice_feedback_response(self, user_message: str, user_name: str, context_data: Dict[str, Any]) -> str:
        """Generate practice feedback response"""
        return f"Great work, {user_name}! I've reviewed your practice attempt. Let me give you some constructive feedback and suggestions for improvement."


    def _generate_career_advice_response(self, user_message: str, user_name: str, context_data: Dict[str, Any]) -> str:
        """Generate career advice response"""
        return f"Hi {user_name}! I'm here to help with your career development. Based on your skills and goals, I can provide personalized advice for your professional growth."


    def _generate_general_help_response(self, user_message: str, user_name: str, context_data: Dict[str, Any]) -> str:
        """Generate general help response"""
        return f"Hello {user_name}! I'm your AI learning companion. I'm here to help you with any questions about your learning journey, skills, or the platform. How can I assist you today?"


    def _generate_conversation_title(self, first_message: str, conversation_type: AIConversationType) -> str:
        """Generate a conversation title based on the first message"""
        if len(first_message) > 50:
            base_title = first_message[:47] + "..."
        else:
            base_title = first_message
        
        type_prefixes = {
            AIConversationType.LEARNING_ASSISTANCE: "Learning Help: ",
            AIConversationType.SESSION_ANALYSIS: "Session Analysis: ",
            AIConversationType.SKILL_GUIDANCE: "Skill Guidance: ",
            AIConversationType.PRACTICE_FEEDBACK: "Practice Review: ",
            AIConversationType.CAREER_ADVICE: "Career Advice: ",
            AIConversationType.GENERAL_HELP: "AI Chat: "
        }
        
        return type_prefixes.get(conversation_type, "AI Chat: ") + base_title


    async def get_user_conversations(self, user_id: str, limit: int = 50) -> List[AIConversation]:
        """Get user's AI conversations"""
        conversations_data = list(self.ai_conversations.find(
            {"user_id": user_id}
        ).sort("last_message_at", -1).limit(limit))
        
        conversations = []
        for conv_data in conversations_data:
            conv_data['id'] = str(conv_data['_id'])
            conversations.append(AIConversation(**conv_data))
        
        return conversations


    async def get_conversation_messages(self, conversation_id: str, user_id: str) -> List[AIMessage]:
        """Get messages from a conversation"""
        # Verify user owns the conversation
        conversation = self.ai_conversations.find_one({"_id": conversation_id, "user_id": user_id})
        if not conversation:
            return []
        
        messages_data = list(self.ai_messages.find(
            {"conversation_id": conversation_id}
        ).sort("created_at", 1))
        
        messages = []
        for msg_data in messages_data:
            msg_data['id'] = str(msg_data['_id'])
            messages.append(AIMessage(**msg_data))
        
        return messages


    async def create_session_analysis(self, session_analysis_create: SessionAnalysisCreate, user_id: str) -> SessionAnalysis:
        """Create AI-powered session analysis"""
        
        # Get session data
        session_data = self.sessions.find_one({"_id": session_analysis_create.session_id})
        if not session_data:
            raise ValueError("Session not found")
        
        # Verify user is participant
        if user_id not in [session_data.get('teacher_id'), session_data.get('learner_id')]:
            raise ValueError("User not authorized for this session")
        
        # Generate AI analysis (this would use WebLLM on frontend)
        analysis = await self._generate_session_analysis(session_data, session_analysis_create.transcript, user_id)
        
        analysis_dict = analysis.dict()
        analysis_dict['_id'] = analysis_dict['id']
        del analysis_dict['id']
        
        result = self.session_analyses.insert_one(analysis_dict)
        analysis_dict['id'] = str(result.inserted_id)
        
        return SessionAnalysis(**analysis_dict)


    async def _generate_session_analysis(self, session_data: Dict[str, Any], transcript: str, user_id: str) -> SessionAnalysis:
        """Generate comprehensive session analysis"""
        
        skill_name = session_data.get('skill_name', 'Unknown Skill')
        session_duration = 60  # Default duration in minutes
        
        # This would be enhanced with actual AI analysis
        analysis = SessionAnalysis(
            session_id=session_data['_id'],
            user_id=user_id,
            transcript=transcript,
            summary=f"Session focused on {skill_name} with comprehensive coverage of key concepts and practical exercises.",
            key_topics_covered=[
                f"{skill_name} fundamentals",
                "Practical applications",
                "Best practices",
                "Common challenges"
            ],
            learning_objectives_achieved=[
                f"Understanding core {skill_name} concepts",
                "Ability to apply learned techniques",
                "Confidence in practical usage"
            ],
            knowledge_gaps_identified=[
                "Advanced techniques need more practice",
                "Real-world applications could be explored further"
            ],
            comprehension_score=85.0,
            engagement_score=90.0,
            participation_score=88.0,
            strengths_identified=[
                "Quick grasp of fundamental concepts",
                "Active participation and engagement",
                "Good questions that show deep thinking"
            ],
            areas_for_improvement=[
                "Practice with more complex scenarios",
                "Build confidence in independent problem-solving"
            ],
            next_steps_suggested=[
                f"Schedule follow-up session for advanced {skill_name}",
                "Practice with provided exercises",
                "Join community discussions on this topic"
            ],
            practice_recommendations=[
                f"Complete 3-5 {skill_name} practice problems",
                "Work on a small personal project",
                "Review session materials within 24 hours"
            ],
            homework_suggested=f"Create a simple project using {skill_name} concepts covered in today's session",
            resources_recommended=[
                {"title": f"Advanced {skill_name} Guide", "url": "#", "type": "article"},
                {"title": f"{skill_name} Practice Exercises", "url": "#", "type": "interactive"},
                {"title": f"{skill_name} Community Forum", "url": "#", "type": "community"}
            ],
            ai_model_used="webllm",
            analysis_confidence=0.85
        )
        
        return analysis


    async def generate_learning_insights(self, user_id: str) -> List[LearningInsight]:
        """Generate personalized learning insights for a user"""
        
        # Get user data and learning history
        user_data = self.users.find_one({"_id": user_id})
        if not user_data:
            return []
        
        # Get recent sessions and progress
        recent_sessions = list(self.sessions.find({
            "$or": [{"teacher_id": user_id}, {"learner_id": user_id}],
            "status": "completed",
            "created_at": {"$gte": datetime.utcnow() - timedelta(days=30)}
        }))
        
        # Get user skills
        user_skills = list(self.user_skills.find({"user_id": user_id}))
        
        insights = []
        
        # Learning Velocity Insight
        if len(recent_sessions) >= 3:
            avg_sessions_per_week = len(recent_sessions) / 4.0  # Last 4 weeks
            insights.append(LearningInsight(
                user_id=user_id,
                insight_type="learning_velocity",
                title="Learning Velocity Analysis",
                description=f"You've been averaging {avg_sessions_per_week:.1f} sessions per week. " + 
                           ("Great consistency!" if avg_sessions_per_week >= 2 else "Consider increasing your session frequency for better progress."),
                time_period="last_month",
                data_points={"avg_sessions_per_week": avg_sessions_per_week, "total_sessions": len(recent_sessions)},
                action_items=[
                    "Maintain current learning pace" if avg_sessions_per_week >= 2 else "Try to schedule 2-3 sessions per week",
                    "Focus on consistent practice between sessions"
                ],
                confidence_score=0.9
            ))
        
        # Skill Diversification Insight
        skills_practiced = set([session.get('skill_name') for session in recent_sessions if session.get('skill_name')])
        if len(skills_practiced) >= 2:
            insights.append(LearningInsight(
                user_id=user_id,
                insight_type="skill_diversification",
                title="Skill Diversification",
                description=f"You've been learning {len(skills_practiced)} different skills recently. This diverse approach helps build a well-rounded skill set.",
                time_period="last_month",
                data_points={"skills_count": len(skills_practiced), "skills": list(skills_practiced)},
                action_items=[
                    "Consider deepening expertise in your strongest skills",
                    "Look for connections between different skills you're learning"
                ],
                confidence_score=0.8
            ))
        
        # Goal Achievement Insight
        completed_objectives = []
        for session in recent_sessions:
            completed_objectives.extend(session.get('objectives_completed', []))
        
        if completed_objectives:
            insights.append(LearningInsight(
                user_id=user_id,
                insight_type="goal_achievement",
                title="Learning Objectives Progress",
                description=f"You've completed {len(completed_objectives)} learning objectives recently. Keep up the excellent progress!",
                time_period="last_month",
                data_points={"completed_objectives": len(completed_objectives)},
                action_items=[
                    "Celebrate your achievements",
                    "Set more challenging goals for continued growth",
                    "Share your progress with the community"
                ],
                confidence_score=0.9
            ))
        
        # Save insights to database
        for insight in insights:
            insight_dict = insight.dict()
            insight_dict['_id'] = insight_dict['id']
            del insight_dict['id']
            self.learning_insights.insert_one(insight_dict)
        
        return insights


    async def get_user_insights(self, user_id: str, limit: int = 20) -> List[LearningInsight]:
        """Get user's learning insights"""
        insights_data = list(self.learning_insights.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(limit))
        
        insights = []
        for insight_data in insights_data:
            insight_data['id'] = str(insight_data['_id'])
            insights.append(LearningInsight(**insight_data))
        
        return insights


    async def get_session_analysis(self, session_id: str, user_id: str) -> Optional[SessionAnalysis]:
        """Get session analysis for a user"""
        analysis_data = self.session_analyses.find_one({
            "session_id": session_id,
            "user_id": user_id
        })
        
        if not analysis_data:
            return None
        
        analysis_data['id'] = str(analysis_data['_id'])
        return SessionAnalysis(**analysis_data)


    async def create_study_plan(self, user_id: str, skill_id: str, target_level: SkillLevel, 
                              estimated_duration_weeks: int = 8, weekly_time_commitment: int = 5) -> StudyPlan:
        """Create AI-generated study plan"""
        
        # Get skill information
        skill_data = self.skills.find_one({"_id": skill_id})
        if not skill_data:
            raise ValueError("Skill not found")
        
        skill_name = skill_data.get('name', 'Unknown Skill')
        
        # Get user's current skill level
        user_skill_data = self.user_skills.find_one({"user_id": user_id, "skill_id": skill_id})
        current_level = SkillLevel.BEGINNER
        if user_skill_data:
            current_level = SkillLevel(user_skill_data.get('level', 'beginner'))
        
        # Generate study plan
        study_plan = await self._generate_study_plan(
            user_id, skill_id, skill_name, current_level, target_level, 
            estimated_duration_weeks, weekly_time_commitment
        )
        
        plan_dict = study_plan.dict()
        plan_dict['_id'] = plan_dict['id']
        del plan_dict['id']
        
        result = self.study_plans.insert_one(plan_dict)
        plan_dict['id'] = str(result.inserted_id)
        
        return StudyPlan(**plan_dict)


    async def _generate_study_plan(self, user_id: str, skill_id: str, skill_name: str, 
                                 current_level: SkillLevel, target_level: SkillLevel,
                                 duration_weeks: int, weekly_hours: int) -> StudyPlan:
        """Generate comprehensive study plan"""
        
        # Create structured learning modules
        modules = []
        if current_level == SkillLevel.BEGINNER and target_level in [SkillLevel.INTERMEDIATE, SkillLevel.ADVANCED]:
            modules = [
                {
                    "id": 1,
                    "title": f"{skill_name} Fundamentals",
                    "description": f"Master the basic concepts and principles of {skill_name}",
                    "estimated_hours": weekly_hours * 2,
                    "learning_objectives": [
                        f"Understand core {skill_name} concepts",
                        "Learn basic terminology and tools",
                        "Complete introductory exercises"
                    ]
                },
                {
                    "id": 2,
                    "title": f"Intermediate {skill_name}",
                    "description": f"Build on fundamentals with more complex {skill_name} techniques",
                    "estimated_hours": weekly_hours * 3,
                    "learning_objectives": [
                        f"Apply {skill_name} in practical scenarios",
                        "Understand advanced concepts",
                        "Work on intermediate projects"
                    ]
                },
                {
                    "id": 3,
                    "title": f"Advanced {skill_name}",
                    "description": f"Master advanced {skill_name} techniques and best practices",
                    "estimated_hours": weekly_hours * 3,
                    "learning_objectives": [
                        f"Master complex {skill_name} patterns",
                        "Optimize and refactor existing work",
                        "Mentor others in {skill_name}"
                    ]
                }
            ]
        
        # Create milestones
        milestones = [
            {
                "week": 2,
                "title": "Foundation Complete",
                "description": f"Basic {skill_name} concepts mastered",
                "criteria": ["Complete Module 1", "Pass fundamental assessment"]
            },
            {
                "week": 5,
                "title": "Intermediate Proficiency",
                "description": f"Comfortable with intermediate {skill_name}",
                "criteria": ["Complete Module 2", "Build intermediate project"]
            },
            {
                "week": 8,
                "title": "Advanced Competency",
                "description": f"Advanced {skill_name} skills achieved",
                "criteria": ["Complete Module 3", "Demonstrate advanced techniques"]
            }
        ]
        
        return StudyPlan(
            user_id=user_id,
            skill_id=skill_id,
            skill_name=skill_name,
            target_level=target_level,
            current_level=current_level,
            title=f"{skill_name} Learning Path: {current_level.value} → {target_level.value}",
            description=f"Comprehensive {duration_weeks}-week study plan to advance from {current_level.value} to {target_level.value} in {skill_name}",
            estimated_duration_weeks=duration_weeks,
            modules=modules,
            milestones=milestones,
            weekly_time_commitment=weekly_hours,
            resources=[
                {"title": f"{skill_name} Documentation", "url": "#", "type": "documentation"},
                {"title": f"{skill_name} Video Tutorials", "url": "#", "type": "video"},
                {"title": f"{skill_name} Practice Exercises", "url": "#", "type": "interactive"}
            ]
        )


    async def get_user_study_plans(self, user_id: str) -> List[StudyPlan]:
        """Get user's active study plans"""
        plans_data = list(self.study_plans.find(
            {"user_id": user_id, "is_active": True}
        ).sort("created_at", -1))
        
        plans = []
        for plan_data in plans_data:
            plan_data['id'] = str(plan_data['_id'])
            plans.append(StudyPlan(**plan_data))
        
        return plans


    async def update_study_plan_progress(self, plan_id: str, user_id: str, 
                                       current_module: int = None, completion_percentage: float = None) -> StudyPlan:
        """Update study plan progress"""
        update_data = {"updated_at": datetime.utcnow()}
        
        if current_module is not None:
            update_data["current_module"] = current_module
        
        if completion_percentage is not None:
            update_data["completion_percentage"] = completion_percentage
        
        result = self.study_plans.update_one(
            {"_id": plan_id, "user_id": user_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise ValueError("Study plan not found or unauthorized")
        
        # Return updated plan
        plan_data = self.study_plans.find_one({"_id": plan_id})
        plan_data['id'] = str(plan_data['_id'])
        return StudyPlan(**plan_data)