import React, { useState, useEffect, useRef } from 'react';
import { 
  ChatBubbleLeftRightIcon, 
  PaperAirplaneIcon,
  SparklesIcon,
  XMarkIcon,
  AcademicCapIcon,
  LightBulbIcon,
  BrainIcon,
  RocketLaunchIcon,
  DocumentTextIcon,
  QuestionMarkCircleIcon
} from '@heroicons/react/24/outline';
import { useAI, AI_CONVERSATION_TYPES } from '../hooks/useAI';

const AICompanion = ({ isOpen, onToggle, className = '' }) => {
  const {
    isModelLoaded,
    isLoading,
    loadingProgress,
    error,
    conversations,
    currentConversation,
    messages,
    initializeAI,
    sendAIMessage,
    getConversations,
    getConversationMessages,
    setCurrentConversation,
    getQuickSkillHelp,
    getPracticeFeedback
  } = useAI();

  const [inputMessage, setInputMessage] = useState('');
  const [selectedConversationType, setSelectedConversationType] = useState(AI_CONVERSATION_TYPES.GENERAL_HELP);
  const [quickHelpMode, setQuickHelpMode] = useState(null);
  const [skillContext, setSkillContext] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  
  const messagesEndRef = useRef(null);

  // Scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Load conversations on mount
  useEffect(() => {
    if (isModelLoaded) {
      getConversations();
    }
  }, [isModelLoaded, getConversations]);

  // Handle sending messages
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const messageText = inputMessage;
    setInputMessage('');
    setIsTyping(true);

    try {
      const messageData = {
        conversation_id: currentConversation?.id,
        conversation_type: selectedConversationType,
        content: messageText,
        context_data: {
          skill_name: skillContext,
          conversation_type: selectedConversationType
        },
        skill_context: skillContext || null,
        session_context: null
      };

      const response = await sendAIMessage(messageData);
      
      // Refresh messages if we have a conversation
      if (response.conversation_id) {
        await getConversationMessages(response.conversation_id);
      }
      
      // If this was a new conversation, refresh conversations list
      if (!currentConversation) {
        await getConversations();
      }

    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsTyping(false);
    }
  };

  // Handle conversation selection
  const selectConversation = async (conversation) => {
    setCurrentConversation(conversation);
    await getConversationMessages(conversation.id);
  };

  // Handle quick help
  const handleQuickHelp = async (helpType) => {
    if (!skillContext.trim() || !inputMessage.trim()) return;

    setIsTyping(true);
    try {
      let response;
      if (helpType === 'skill_help') {
        response = await getQuickSkillHelp(skillContext, inputMessage);
      } else if (helpType === 'practice_feedback') {
        response = await getPracticeFeedback(skillContext, inputMessage);
      }

      // Create a quick conversation display
      setMessages([
        { role: 'user', content: inputMessage, created_at: new Date() },
        { role: 'assistant', content: response.response || response.feedback, created_at: new Date() }
      ]);
      
      setInputMessage('');
    } catch (error) {
      console.error('Quick help failed:', error);
    } finally {
      setIsTyping(false);
    }
  };

  // Conversation type options
  const conversationTypes = [
    { 
      type: AI_CONVERSATION_TYPES.GENERAL_HELP, 
      label: 'General Help', 
      icon: QuestionMarkCircleIcon, 
      color: 'text-blue-500' 
    },
    { 
      type: AI_CONVERSATION_TYPES.LEARNING_ASSISTANCE, 
      label: 'Learning Help', 
      icon: AcademicCapIcon, 
      color: 'text-green-500' 
    },
    { 
      type: AI_CONVERSATION_TYPES.SKILL_GUIDANCE, 
      label: 'Skill Guidance', 
      icon: RocketLaunchIcon, 
      color: 'text-purple-500' 
    },
    { 
      type: AI_CONVERSATION_TYPES.PRACTICE_FEEDBACK, 
      label: 'Practice Review', 
      icon: DocumentTextIcon, 
      color: 'text-orange-500' 
    },
    { 
      type: AI_CONVERSATION_TYPES.CAREER_ADVICE, 
      label: 'Career Advice', 
      icon: LightBulbIcon, 
      color: 'text-yellow-500' 
    }
  ];

  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className={`fixed bottom-6 right-6 bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4 rounded-full shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 z-50 ${className}`}
      >
        <div className="relative">
          <BrainIcon className="w-6 h-6" />
          {isModelLoaded && (
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
          )}
        </div>
      </button>
    );
  }

  return (
    <div className={`fixed bottom-6 right-6 w-96 h-[32rem] bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col z-50 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-t-2xl">
        <div className="flex items-center space-x-2">
          <BrainIcon className="w-6 h-6" />
          <div>
            <h3 className="font-semibold">AI Learning Companion</h3>
            <div className="flex items-center space-x-1 text-xs">
              {isModelLoaded ? (
                <>
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span>Ready</span>
                </>
              ) : isLoading ? (
                <>
                  <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></div>
                  <span>Loading... {Math.round(loadingProgress)}%</span>
                </>
              ) : (
                <>
                  <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                  <span>Offline</span>
                </>
              )}
            </div>
          </div>
        </div>
        <button
          onClick={onToggle}
          className="text-white hover:text-gray-200 transition-colors"
        >
          <XMarkIcon className="w-5 h-5" />
        </button>
      </div>

      {/* AI Loading State */}
      {isLoading && !isModelLoaded && (
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mb-4 mx-auto">
              <SparklesIcon className="w-6 h-6 text-white animate-spin" />
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">Loading AI Model</h4>
            <div className="w-48 bg-gray-200 rounded-full h-2 mb-2">
              <div 
                className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${loadingProgress}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600">{Math.round(loadingProgress)}% complete</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4 mx-auto">
              <XMarkIcon className="w-6 h-6 text-red-500" />
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">AI Unavailable</h4>
            <p className="text-sm text-gray-600 mb-4">{error}</p>
            <button
              onClick={initializeAI}
              className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:opacity-90 transition-opacity"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Main Interface */}
      {isModelLoaded && !error && (
        <>
          {/* Conversation Type Selector */}
          <div className="p-3 bg-gray-50 border-b">
            <select
              value={selectedConversationType}
              onChange={(e) => setSelectedConversationType(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {conversationTypes.map(({ type, label }) => (
                <option key={type} value={type}>{label}</option>
              ))}
            </select>
            
            {/* Skill Context Input */}
            <input
              type="text"
              placeholder="Skill context (optional)"
              value={skillContext}
              onChange={(e) => setSkillContext(e.target.value)}
              className="w-full mt-2 p-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && !currentConversation && (
              <div className="text-center py-8">
                <BrainIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h4 className="font-semibold text-gray-600 mb-2">AI Learning Companion</h4>
                <p className="text-sm text-gray-500">
                  Ask me anything about learning, skills, or get personalized guidance!
                </p>
              </div>
            )}

            {messages.map((message, index) => (
              <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] p-3 rounded-2xl ${
                  message.role === 'user'
                    ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  <p className={`text-xs mt-1 ${
                    message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                  }`}>
                    {new Date(message.created_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-800 p-3 rounded-2xl">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t bg-gray-50">
            <div className="flex space-x-2">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Ask your AI learning companion..."
                disabled={isLoading}
                className="flex-1 p-3 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading}
                className="p-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <PaperAirplaneIcon className="w-4 h-4" />
              </button>
            </div>

            {/* Quick Actions */}
            <div className="flex space-x-2 mt-2">
              <button
                onClick={() => handleQuickHelp('skill_help')}
                disabled={!skillContext || !inputMessage.trim() || isLoading}
                className="flex-1 py-2 px-3 text-xs bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Quick Help
              </button>
              <button
                onClick={() => handleQuickHelp('practice_feedback')}
                disabled={!skillContext || !inputMessage.trim() || isLoading}
                className="flex-1 py-2 px-3 text-xs bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Get Feedback
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default AICompanion;