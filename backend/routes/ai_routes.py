from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime

from auth import get_current_user
from models import (
    User, AIConversationType, AIMessageCreate, AIMessageResponse,
    AIConversationResponse, SessionAnalysisCreate, SessionAnalysisResponse,
    LearningInsightResponse, StudyPlanCreate, StudyPlan, SkillLevel
)
from services.ai_companion_service import AICompanionService

router = APIRouter(prefix="/api/ai", tags=["AI Learning Companion"])
ai_service = AICompanionService()


@router.post("/chat", response_model=AIMessageResponse)
async def send_ai_message(
    message_create: AIMessageCreate,
    current_user: User = Depends(get_current_user)
):
    """Send a message to AI learning companion"""
    try:
        response = await ai_service.send_ai_message(message_create, current_user.id)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send AI message: {str(e)}"
        )


@router.get("/conversations", response_model=List[AIConversationResponse])
async def get_user_conversations(
    limit: Optional[int] = 50,
    current_user: User = Depends(get_current_user)
):
    """Get user's AI conversations"""
    try:
        conversations = await ai_service.get_user_conversations(current_user.id, limit)
        
        conversation_responses = []
        for conv in conversations:
            conversation_responses.append(AIConversationResponse(
                id=conv.id,
                conversation_type=conv.conversation_type,
                title=conv.title,
                summary=conv.summary,
                message_count=conv.message_count,
                last_message_at=conv.last_message_at,
                topics_discussed=conv.topics_discussed,
                created_at=conv.created_at,
                is_active=conv.is_active
            ))
        
        return conversation_responses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversations: {str(e)}"
        )


@router.get("/conversations/{conversation_id}/messages", response_model=List[AIMessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get messages from an AI conversation"""
    try:
        messages = await ai_service.get_conversation_messages(conversation_id, current_user.id)
        
        message_responses = []
        for msg in messages:
            message_responses.append(AIMessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role,
                content=msg.content,
                ai_confidence=msg.ai_confidence,
                created_at=msg.created_at,
                conversation_type=msg.conversation_type,
                skill_context=msg.skill_context,
                session_context=msg.session_context
            ))
        
        return message_responses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation messages: {str(e)}"
        )


@router.post("/session-analysis", response_model=SessionAnalysisResponse)
async def create_session_analysis(
    analysis_create: SessionAnalysisCreate,
    current_user: User = Depends(get_current_user)
):
    """Create AI-powered session analysis"""
    try:
        analysis = await ai_service.create_session_analysis(analysis_create, current_user.id)
        
        return SessionAnalysisResponse(
            id=analysis.id,
            session_id=analysis.session_id,
            summary=analysis.summary,
            key_topics_covered=analysis.key_topics_covered,
            learning_objectives_achieved=analysis.learning_objectives_achieved,
            knowledge_gaps_identified=analysis.knowledge_gaps_identified,
            comprehension_score=analysis.comprehension_score,
            engagement_score=analysis.engagement_score,
            strengths_identified=analysis.strengths_identified,
            areas_for_improvement=analysis.areas_for_improvement,
            next_steps_suggested=analysis.next_steps_suggested,
            practice_recommendations=analysis.practice_recommendations,
            homework_suggested=analysis.homework_suggested,
            resources_recommended=analysis.resources_recommended,
            analysis_confidence=analysis.analysis_confidence,
            created_at=analysis.created_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session analysis: {str(e)}"
        )


@router.get("/session-analysis/{session_id}", response_model=Optional[SessionAnalysisResponse])
async def get_session_analysis(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get AI session analysis"""
    try:
        analysis = await ai_service.get_session_analysis(session_id, current_user.id)
        
        if not analysis:
            return None
        
        return SessionAnalysisResponse(
            id=analysis.id,
            session_id=analysis.session_id,
            summary=analysis.summary,
            key_topics_covered=analysis.key_topics_covered,
            learning_objectives_achieved=analysis.learning_objectives_achieved,
            knowledge_gaps_identified=analysis.knowledge_gaps_identified,
            comprehension_score=analysis.comprehension_score,
            engagement_score=analysis.engagement_score,
            strengths_identified=analysis.strengths_identified,
            areas_for_improvement=analysis.areas_for_improvement,
            next_steps_suggested=analysis.next_steps_suggested,
            practice_recommendations=analysis.practice_recommendations,
            homework_suggested=analysis.homework_suggested,
            resources_recommended=analysis.resources_recommended,
            analysis_confidence=analysis.analysis_confidence,
            created_at=analysis.created_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session analysis: {str(e)}"
        )


@router.get("/insights", response_model=List[LearningInsightResponse])
async def get_learning_insights(
    limit: Optional[int] = 20,
    current_user: User = Depends(get_current_user)
):
    """Get user's learning insights"""
    try:
        insights = await ai_service.get_user_insights(current_user.id, limit)
        
        insight_responses = []
        for insight in insights:
            insight_responses.append(LearningInsightResponse(
                id=insight.id,
                insight_type=insight.insight_type,
                title=insight.title,
                description=insight.description,
                action_items=insight.action_items,
                resource_suggestions=insight.resource_suggestions,
                confidence_score=insight.confidence_score,
                created_at=insight.created_at,
                is_viewed=insight.is_viewed
            ))
        
        return insight_responses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get learning insights: {str(e)}"
        )


@router.post("/insights/generate")
async def generate_learning_insights(
    current_user: User = Depends(get_current_user)
):
    """Generate new learning insights for the user"""
    try:
        insights = await ai_service.generate_learning_insights(current_user.id)
        return {"message": f"Generated {len(insights)} new insights", "count": len(insights)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {str(e)}"
        )


@router.post("/study-plan", response_model=StudyPlan)
async def create_study_plan(
    study_plan_create: StudyPlanCreate,
    current_user: User = Depends(get_current_user)
):
    """Create AI-generated study plan"""
    try:
        study_plan = await ai_service.create_study_plan(
            current_user.id,
            study_plan_create.skill_id,
            study_plan_create.target_level,
            study_plan_create.estimated_duration_weeks or 8,
            study_plan_create.weekly_time_commitment or 5
        )
        return study_plan
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create study plan: {str(e)}"
        )


@router.get("/study-plans", response_model=List[StudyPlan])
async def get_study_plans(
    current_user: User = Depends(get_current_user)
):
    """Get user's active study plans"""
    try:
        study_plans = await ai_service.get_user_study_plans(current_user.id)
        return study_plans
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get study plans: {str(e)}"
        )


@router.put("/study-plans/{plan_id}/progress")
async def update_study_plan_progress(
    plan_id: str,
    current_module: Optional[int] = None,
    completion_percentage: Optional[float] = None,
    current_user: User = Depends(get_current_user)
):
    """Update study plan progress"""
    try:
        study_plan = await ai_service.update_study_plan_progress(
            plan_id, current_user.id, current_module, completion_percentage
        )
        return study_plan
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update study plan progress: {str(e)}"
        )


# Quick helper endpoints for specific AI interactions
@router.post("/quick/skill-help")
async def get_quick_skill_help(
    skill_name: str,
    question: str,
    current_user: User = Depends(get_current_user)
):
    """Get quick AI help for a specific skill"""
    message_create = AIMessageCreate(
        conversation_type=AIConversationType.SKILL_GUIDANCE,
        content=question,
        skill_context=skill_name,
        context_data={"skill_name": skill_name}
    )
    
    try:
        response = await ai_service.send_ai_message(message_create, current_user.id)
        return {"response": response.content, "conversation_id": response.conversation_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get skill help: {str(e)}"
        )


@router.post("/quick/practice-feedback")
async def get_practice_feedback(
    skill_name: str,
    practice_description: str,
    current_user: User = Depends(get_current_user)
):
    """Get AI feedback on practice work"""
    message_create = AIMessageCreate(
        conversation_type=AIConversationType.PRACTICE_FEEDBACK,
        content=f"I practiced {skill_name}: {practice_description}. Can you give me feedback?",
        skill_context=skill_name,
        context_data={"skill_name": skill_name, "practice_type": "user_submission"}
    )
    
    try:
        response = await ai_service.send_ai_message(message_create, current_user.id)
        return {"feedback": response.content, "conversation_id": response.conversation_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get practice feedback: {str(e)}"
        )


@router.get("/analytics/summary")
async def get_ai_analytics_summary(
    current_user: User = Depends(get_current_user)
):
    """Get AI analytics summary for dashboard"""
    try:
        # Get conversation count
        conversations = await ai_service.get_user_conversations(current_user.id, 1000)
        
        # Get insights count
        insights = await ai_service.get_user_insights(current_user.id, 1000)
        
        # Get study plans
        study_plans = await ai_service.get_user_study_plans(current_user.id)
        
        return {
            "total_conversations": len(conversations),
            "active_conversations": len([c for c in conversations if c.is_active]),
            "total_insights": len(insights),
            "unviewed_insights": len([i for i in insights if not i.is_viewed]),
            "active_study_plans": len(study_plans),
            "conversation_types": {
                "learning_assistance": len([c for c in conversations if c.conversation_type == AIConversationType.LEARNING_ASSISTANCE]),
                "skill_guidance": len([c for c in conversations if c.conversation_type == AIConversationType.SKILL_GUIDANCE]),
                "session_analysis": len([c for c in conversations if c.conversation_type == AIConversationType.SESSION_ANALYSIS]),
                "practice_feedback": len([c for c in conversations if c.conversation_type == AIConversationType.PRACTICE_FEEDBACK]),
                "career_advice": len([c for c in conversations if c.conversation_type == AIConversationType.CAREER_ADVICE]),
                "general_help": len([c for c in conversations if c.conversation_type == AIConversationType.GENERAL_HELP])
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI analytics: {str(e)}"
        )