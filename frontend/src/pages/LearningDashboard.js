import React, { useState, useEffect } from 'react';
import {
  ChartBarIcon,
  AcademicCapIcon,
  TrophyIcon,
  ClockIcon,
  CpuChipIcon as BrainIcon,
  SparklesIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  BookOpenIcon,
  LightBulbIcon,
  RocketLaunchIcon
} from '@heroicons/react/24/outline';
import { useAI } from '../hooks/useAI';

const LearningDashboard = () => {
  const {
    isModelLoaded,
    getLearningInsights,
    generateInsights,
    getAIAnalytics,
    createStudyPlan,
    getStudyPlans
  } = useAI();

  const [insights, setInsights] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [studyPlans, setStudyPlans] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState('insights');

  // Load dashboard data
  useEffect(() => {
    if (isModelLoaded) {
      loadDashboardData();
    }
  }, [isModelLoaded]);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      
      // Load all dashboard data
      const [insightsData, analyticsData, studyPlansData] = await Promise.all([
        getLearningInsights(20),
        getAIAnalytics(),
        getStudyPlans()
      ]);

      setInsights(insightsData);
      setAnalytics(analyticsData);
      setStudyPlans(studyPlansData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateInsights = async () => {
    try {
      setIsLoading(true);
      await generateInsights();
      await loadDashboardData(); // Refresh data
    } catch (error) {
      console.error('Failed to generate insights:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isModelLoaded) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <BrainIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">AI Learning Analytics</h3>
          <p className="text-gray-600">AI model is loading... Please wait.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <BrainIcon className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">AI Learning Analytics</h1>
                <p className="text-gray-600">Personalized insights powered by AI</p>
              </div>
            </div>
            
            <button
              onClick={handleGenerateInsights}
              disabled={isLoading}
              className="px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center space-x-2"
            >
              <SparklesIcon className="w-4 h-4" />
              <span>Generate New Insights</span>
            </button>
          </div>
        </div>
      </div>

      {/* Analytics Overview */}
      {analytics && (
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">AI Conversations</p>
                  <p className="text-2xl font-bold text-gray-900">{analytics.total_conversations}</p>
                  <p className="text-sm text-green-600 flex items-center mt-1">
                    <ArrowUpIcon className="w-4 h-4 mr-1" />
                    {analytics.active_conversations} active
                  </p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <BrainIcon className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Learning Insights</p>
                  <p className="text-2xl font-bold text-gray-900">{analytics.total_insights}</p>
                  <p className="text-sm text-orange-600 flex items-center mt-1">
                    <LightBulbIcon className="w-4 h-4 mr-1" />
                    {analytics.unviewed_insights} new
                  </p>
                </div>
                <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                  <LightBulbIcon className="w-6 h-6 text-orange-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Study Plans</p>
                  <p className="text-2xl font-bold text-gray-900">{analytics.active_study_plans}</p>
                  <p className="text-sm text-purple-600 flex items-center mt-1">
                    <RocketLaunchIcon className="w-4 h-4 mr-1" />
                    Active plans
                  </p>
                </div>
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <BookOpenIcon className="w-6 h-6 text-purple-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Learning Help</p>
                  <p className="text-2xl font-bold text-gray-900">{analytics.conversation_types?.learning_assistance || 0}</p>
                  <p className="text-sm text-green-600 flex items-center mt-1">
                    <AcademicCapIcon className="w-4 h-4 mr-1" />
                    Sessions
                  </p>
                </div>
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <AcademicCapIcon className="w-6 h-6 text-green-600" />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="max-w-7xl mx-auto px-4">
        <div className="bg-white rounded-xl shadow-sm">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {[
                { id: 'insights', name: 'Learning Insights', icon: LightBulbIcon },
                { id: 'plans', name: 'Study Plans', icon: BookOpenIcon },
                { id: 'analytics', name: 'Detailed Analytics', icon: ChartBarIcon }
              ].map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setSelectedTab(tab.id)}
                    className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                      selectedTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{tab.name}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {isLoading ? (
              <div className="text-center py-12">
                <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                <p className="text-gray-600">Loading AI insights...</p>
              </div>
            ) : (
              <>
                {/* Learning Insights Tab */}
                {selectedTab === 'insights' && (
                  <div className="space-y-6">
                    {insights.length === 0 ? (
                      <div className="text-center py-12">
                        <LightBulbIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">No insights yet</h3>
                        <p className="text-gray-600 mb-4">Generate AI-powered insights about your learning journey</p>
                        <button
                          onClick={handleGenerateInsights}
                          className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:opacity-90 transition-opacity"
                        >
                          Generate Insights
                        </button>
                      </div>
                    ) : (
                      <div className="grid gap-6">
                        {insights.map((insight) => (
                          <div key={insight.id} className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-200">
                            <div className="flex items-start justify-between mb-4">
                              <div className="flex-1">
                                <h3 className="text-lg font-semibold text-gray-900 mb-2">{insight.title}</h3>
                                <p className="text-gray-700 mb-4">{insight.description}</p>
                              </div>
                              <div className="ml-4 flex items-center space-x-2">
                                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                                <span className="text-sm text-gray-600">
                                  {Math.round(insight.confidence_score * 100)}% confidence
                                </span>
                              </div>
                            </div>

                            {insight.action_items.length > 0 && (
                              <div className="mb-4">
                                <h4 className="font-medium text-gray-900 mb-2">Recommended Actions:</h4>
                                <ul className="list-disc list-inside space-y-1">
                                  {insight.action_items.map((item, index) => (
                                    <li key={index} className="text-sm text-gray-700">{item}</li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {insight.resource_suggestions.length > 0 && (
                              <div>
                                <h4 className="font-medium text-gray-900 mb-2">Suggested Resources:</h4>
                                <div className="flex flex-wrap gap-2">
                                  {insight.resource_suggestions.map((resource, index) => (
                                    <span key={index} className="px-3 py-1 bg-white border border-blue-200 rounded-full text-sm text-blue-700">
                                      {resource.title || resource}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Study Plans Tab */}
                {selectedTab === 'plans' && (
                  <div className="space-y-6">
                    {studyPlans.length === 0 ? (
                      <div className="text-center py-12">
                        <BookOpenIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">No study plans yet</h3>
                        <p className="text-gray-600">Create AI-generated study plans for your skills</p>
                      </div>
                    ) : (
                      <div className="grid gap-6">
                        {studyPlans.map((plan) => (
                          <div key={plan.id} className="bg-white rounded-xl p-6 border border-gray-200 hover:border-purple-300 transition-colors">
                            <div className="flex items-start justify-between mb-4">
                              <div className="flex-1">
                                <h3 className="text-lg font-semibold text-gray-900 mb-2">{plan.title}</h3>
                                <p className="text-gray-700 mb-2">{plan.description}</p>
                                <div className="flex items-center space-x-4 text-sm text-gray-600">
                                  <span className="flex items-center">
                                    <ClockIcon className="w-4 h-4 mr-1" />
                                    {plan.estimated_duration_weeks} weeks
                                  </span>
                                  <span className="flex items-center">
                                    <TrophyIcon className="w-4 h-4 mr-1" />
                                    {plan.target_level}
                                  </span>
                                </div>
                              </div>
                              <div className="ml-4">
                                <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center">
                                  <span className="text-lg font-bold text-purple-600">
                                    {Math.round(plan.completion_percentage)}%
                                  </span>
                                </div>
                              </div>
                            </div>

                            {/* Progress Bar */}
                            <div className="mb-4">
                              <div className="flex justify-between items-center mb-2">
                                <span className="text-sm font-medium text-gray-700">Progress</span>
                                <span className="text-sm text-gray-600">
                                  Module {plan.current_module + 1} of {plan.modules.length}
                                </span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full transition-all duration-300"
                                  style={{ width: `${plan.completion_percentage}%` }}
                                ></div>
                              </div>
                            </div>

                            {/* Current Module */}
                            {plan.modules[plan.current_module] && (
                              <div className="bg-purple-50 rounded-lg p-4">
                                <h4 className="font-medium text-purple-900 mb-2">
                                  Current: {plan.modules[plan.current_module].title}
                                </h4>
                                <p className="text-sm text-purple-700">
                                  {plan.modules[plan.current_module].description}
                                </p>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Detailed Analytics Tab */}
                {selectedTab === 'analytics' && analytics && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Conversation Types */}
                      <div className="bg-white rounded-lg p-6 border border-gray-200">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Conversation Types</h3>
                        <div className="space-y-3">
                          {Object.entries(analytics.conversation_types || {}).map(([type, count]) => (
                            <div key={type} className="flex justify-between items-center">
                              <span className="text-sm text-gray-600 capitalize">{type.replace('_', ' ')}</span>
                              <span className="font-medium text-gray-900">{count}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Learning Stats */}
                      <div className="bg-white rounded-lg p-6 border border-gray-200">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Learning Statistics</h3>
                        <div className="space-y-4">
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Total Conversations</span>
                            <span className="font-medium text-gray-900">{analytics.total_conversations}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Active Conversations</span>
                            <span className="font-medium text-gray-900">{analytics.active_conversations}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Total Insights</span>
                            <span className="font-medium text-gray-900">{analytics.total_insights}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">New Insights</span>
                            <span className="font-medium text-gray-900">{analytics.unviewed_insights}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LearningDashboard;