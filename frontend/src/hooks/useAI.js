import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { CreateMLCEngine } from '@mlc-ai/web-llm';

// AI Conversation Types
export const AI_CONVERSATION_TYPES = {
  LEARNING_ASSISTANCE: 'learning_assistance',
  SESSION_ANALYSIS: 'session_analysis',
  SKILL_GUIDANCE: 'skill_guidance',
  PRACTICE_FEEDBACK: 'practice_feedback',
  CAREER_ADVICE: 'career_advice',
  GENERAL_HELP: 'general_help'
};

// Available WebLLM models
const AVAILABLE_MODELS = [
  'Llama-3.2-1B-Instruct-q4f32_1-MLC',
  'Llama-3.2-3B-Instruct-q4f32_1-MLC',
  'Phi-3.5-mini-instruct-q4f16_1-MLC',
  'TinyLlama-1.1B-Chat-v0.4-q4f16_1-MLC'
];

export function useAI() {
  const [isModelLoaded, setIsModelLoaded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [error, setError] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  
  const engineRef = useRef(null);
  const selectedModel = 'Phi-3.5-mini-instruct-q4f16_1-MLC'; // Lightweight, fast model

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  // Initialize WebLLM engine
  const initializeAI = useCallback(async () => {
    if (engineRef.current || isLoading) return;

    try {
      setIsLoading(true);
      setError(null);

      console.log('🤖 Initializing WebLLM AI engine...');
      
      const engine = await CreateMLCEngine(selectedModel, {
        initProgressCallback: (report) => {
          console.log('AI Loading:', report.text);
          setLoadingProgress(report.progress || 0);
        },
      });

      engineRef.current = engine;
      setIsModelLoaded(true);
      setLoadingProgress(100);
      console.log('🎉 AI engine initialized successfully!');
    } catch (err) {
      console.error('Failed to initialize AI engine:', err);
      setError('Failed to load AI model. Please refresh and try again.');
    } finally {
      setIsLoading(false);
    }
  }, [selectedModel, isLoading]);

  // Generate AI response using WebLLM
  const generateAIResponse = useCallback(async (userMessage, context = {}) => {
    if (!engineRef.current) {
      throw new Error('AI engine not initialized');
    }

    const systemPrompt = getSystemPrompt(context.conversationType, context.skillContext);
    const contextPrompt = buildContextPrompt(context);
    const fullPrompt = `${systemPrompt}\n\n${contextPrompt}\n\nUser: ${userMessage}\n\nAssistant:`;

    try {
      const response = await engineRef.current.chat.completions.create({
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: `${contextPrompt}\n\n${userMessage}` }
        ],
        temperature: 0.7,
        max_tokens: 512
      });

      return response.choices[0].message.content;
    } catch (error) {
      console.error('AI generation error:', error);
      throw new Error('Failed to generate AI response');
    }
  }, []);

  // Send message to AI (combines backend storage + AI generation)
  const sendAIMessage = useCallback(async (messageData) => {
    try {
      setIsLoading(true);

      // Generate AI response using WebLLM
      const aiResponse = await generateAIResponse(messageData.content, messageData.context_data);

      // Prepare message for backend
      const messagePayload = {
        conversation_id: messageData.conversation_id,
        conversation_type: messageData.conversation_type || AI_CONVERSATION_TYPES.GENERAL_HELP,
        content: messageData.content,
        context_data: messageData.context_data || {},
        skill_context: messageData.skill_context,
        session_context: messageData.session_context
      };

      // Send to backend and get conversation metadata
      const response = await axios.post(`${backendUrl}/api/ai/chat`, messagePayload);
      
      // Override AI response from backend with our WebLLM response
      const enhancedResponse = {
        ...response.data,
        content: aiResponse,
        ai_confidence: 0.85,
        generated_by: 'webllm'
      };

      return enhancedResponse;
    } catch (error) {
      console.error('Failed to send AI message:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [generateAIResponse, backendUrl]);

  // Get user conversations
  const getConversations = useCallback(async (limit = 50) => {
    try {
      const response = await axios.get(`${backendUrl}/api/ai/conversations?limit=${limit}`);
      setConversations(response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to get conversations:', error);
      throw error;
    }
  }, [backendUrl]);

  // Get conversation messages
  const getConversationMessages = useCallback(async (conversationId) => {
    try {
      const response = await axios.get(`${backendUrl}/api/ai/conversations/${conversationId}/messages`);
      setMessages(response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to get conversation messages:', error);
      throw error;
    }
  }, [backendUrl]);

  // Quick AI interactions
  const getQuickSkillHelp = useCallback(async (skillName, question) => {
    try {
      const response = await axios.post(`${backendUrl}/api/ai/quick/skill-help`, {
        skill_name: skillName,
        question: question
      });
      return response.data;
    } catch (error) {
      console.error('Failed to get skill help:', error);
      throw error;
    }
  }, [backendUrl]);

  const getPracticeFeedback = useCallback(async (skillName, practiceDescription) => {
    try {
      const response = await axios.post(`${backendUrl}/api/ai/quick/practice-feedback`, {
        skill_name: skillName,
        practice_description: practiceDescription
      });
      return response.data;
    } catch (error) {
      console.error('Failed to get practice feedback:', error);
      throw error;
    }
  }, [backendUrl]);

  // Session analysis
  const createSessionAnalysis = useCallback(async (sessionId, transcript) => {
    try {
      const response = await axios.post(`${backendUrl}/api/ai/session-analysis`, {
        session_id: sessionId,
        transcript: transcript,
        additional_context: {}
      });
      return response.data;
    } catch (error) {
      console.error('Failed to create session analysis:', error);
      throw error;
    }
  }, [backendUrl]);

  const getSessionAnalysis = useCallback(async (sessionId) => {
    try {
      const response = await axios.get(`${backendUrl}/api/ai/session-analysis/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get session analysis:', error);
      throw error;
    }
  }, [backendUrl]);

  // Learning insights
  const getLearningInsights = useCallback(async (limit = 20) => {
    try {
      const response = await axios.get(`${backendUrl}/api/ai/insights?limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get learning insights:', error);
      throw error;
    }
  }, [backendUrl]);

  const generateInsights = useCallback(async () => {
    try {
      const response = await axios.post(`${backendUrl}/api/ai/insights/generate`);
      return response.data;
    } catch (error) {
      console.error('Failed to generate insights:', error);
      throw error;
    }
  }, [backendUrl]);

  // Study plans
  const createStudyPlan = useCallback(async (skillId, targetLevel, options = {}) => {
    try {
      const response = await axios.post(`${backendUrl}/api/ai/study-plan`, {
        skill_id: skillId,
        target_level: targetLevel,
        estimated_duration_weeks: options.duration || 8,
        weekly_time_commitment: options.weeklyHours || 5,
        preferred_session_length: options.sessionLength || 60,
        flexibility_level: options.flexibility || 'medium'
      });
      return response.data;
    } catch (error) {
      console.error('Failed to create study plan:', error);
      throw error;
    }
  }, [backendUrl]);

  const getStudyPlans = useCallback(async () => {
    try {
      const response = await axios.get(`${backendUrl}/api/ai/study-plans`);
      return response.data;
    } catch (error) {
      console.error('Failed to get study plans:', error);
      throw error;
    }
  }, [backendUrl]);

  // Analytics
  const getAIAnalytics = useCallback(async () => {
    try {
      const response = await axios.get(`${backendUrl}/api/ai/analytics/summary`);
      return response.data;
    } catch (error) {
      console.error('Failed to get AI analytics:', error);
      throw error;
    }
  }, [backendUrl]);

  // Initialize AI on mount
  useEffect(() => {
    // Only initialize if user is authenticated and in a browser environment
    if (typeof window !== 'undefined' && localStorage.getItem('token')) {
      initializeAI();
    }
  }, [initializeAI]);

  return {
    // State
    isModelLoaded,
    isLoading,
    loadingProgress,
    error,
    conversations,
    currentConversation,
    messages,
    selectedModel,

    // Actions
    initializeAI,
    sendAIMessage,
    getConversations,
    getConversationMessages,
    setCurrentConversation,

    // Quick interactions
    getQuickSkillHelp,
    getPracticeFeedback,

    // Session analysis
    createSessionAnalysis,
    getSessionAnalysis,

    // Learning insights
    getLearningInsights,
    generateInsights,

    // Study plans
    createStudyPlan,
    getStudyPlans,

    // Analytics
    getAIAnalytics
  };
}

// Helper functions for AI prompts
function getSystemPrompt(conversationType, skillContext) {
  const basePrompt = "You are an intelligent learning companion for SkillSwap, a peer-to-peer learning platform. You help users learn new skills, provide guidance, and offer personalized insights.";
  
  const typePrompts = {
    [AI_CONVERSATION_TYPES.LEARNING_ASSISTANCE]: `${basePrompt} Your role is to provide learning assistance and help users understand concepts. Be encouraging, break down complex topics into simple steps, and provide practical examples.`,
    [AI_CONVERSATION_TYPES.SESSION_ANALYSIS]: `${basePrompt} You analyze learning sessions and provide insights. Focus on what was learned, areas for improvement, and next steps for continued learning.`,
    [AI_CONVERSATION_TYPES.SKILL_GUIDANCE]: `${basePrompt} You provide guidance on skill development paths. Help users understand how to progress from their current level to their goals.`,
    [AI_CONVERSATION_TYPES.PRACTICE_FEEDBACK]: `${basePrompt} You provide constructive feedback on practice work. Be specific, encouraging, and suggest concrete improvements.`,
    [AI_CONVERSATION_TYPES.CAREER_ADVICE]: `${basePrompt} You provide career guidance related to skill development. Connect learning to career opportunities and professional growth.`,
    [AI_CONVERSATION_TYPES.GENERAL_HELP]: `${basePrompt} You assist with general questions about learning, the platform, and skill development. Be helpful and friendly.`
  };

  let prompt = typePrompts[conversationType] || typePrompts[AI_CONVERSATION_TYPES.GENERAL_HELP];
  
  if (skillContext) {
    prompt += ` The current skill context is: ${skillContext}. Tailor your responses to this skill area.`;
  }

  prompt += ` Keep responses concise (under 200 words), practical, and encouraging. Use a friendly, supportive tone.`;

  return prompt;
}

function buildContextPrompt(context) {
  let prompt = "";
  
  if (context.skillContext) {
    prompt += `Skill being discussed: ${context.skillContext}\n`;
  }
  
  if (context.userLevel) {
    prompt += `User's current level: ${context.userLevel}\n`;
  }
  
  if (context.learningGoals) {
    prompt += `Learning goals: ${context.learningGoals.join(', ')}\n`;
  }
  
  if (context.sessionContext) {
    prompt += `Related to session: ${context.sessionContext}\n`;
  }
  
  if (context.recentActivity) {
    prompt += `Recent activity: ${context.recentActivity}\n`;
  }

  return prompt.trim();
}