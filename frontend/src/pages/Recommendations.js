import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import {
  LightBulbIcon,
  UserIcon,
  ClockIcon,
  BookOpenIcon,
  UserGroupIcon,
  StarIcon,
  TrophyIcon,
  ArrowPathIcon,
  EyeIcon,
  CheckIcon,
  XMarkIcon,
  ChartBarIcon,
  AcademicCapIcon,
  CalendarIcon
} from '@heroicons/react/24/outline';

const Recommendations = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [dashboardData, setDashboardData] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [learningGoals, setLearningGoals] = useState([]);
  const [insights, setInsights] = useState(null);
  const [filterType, setFilterType] = useState('all');

  useEffect(() => {
    if (user) {
      if (activeTab === 'dashboard') {
        fetchDashboard();
      } else if (activeTab === 'all') {
        fetchRecommendations();
      } else if (activeTab === 'goals') {
        fetchLearningGoals();
      } else if (activeTab === 'insights') {
        fetchInsights();
      }
    }
  }, [user, activeTab, filterType]);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/recommendations/dashboard`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterType !== 'all') {
        params.recommendation_types = filterType;
      }
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/recommendations/`, {
        params: { limit: 20, min_confidence: 0.2, ...params }
      });
      setRecommendations(response.data);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchLearningGoals = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/recommendations/learning-goals`);
      setLearningGoals(response.data);
    } catch (error) {
      console.error('Error fetching learning goals:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchInsights = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/recommendations/insights`);
      setInsights(response.data);
    } catch (error) {
      console.error('Error fetching insights:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateRecommendations = async () => {
    try {
      setLoading(true);
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/recommendations/generate`);
      
      // Refresh current view
      if (activeTab === 'dashboard') {
        await fetchDashboard();
      } else if (activeTab === 'all') {
        await fetchRecommendations();
      }
    } catch (error) {
      console.error('Error generating recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  const markRecommendationViewed = async (recommendationId) => {
    try {
      await axios.put(`${process.env.REACT_APP_BACKEND_URL}/api/recommendations/${recommendationId}/viewed`);
      
      // Update local state
      if (activeTab === 'all') {
        setRecommendations(recommendations.map(r => 
          r.id === recommendationId ? { ...r, is_viewed: true } : r
        ));
      }
    } catch (error) {
      console.error('Error marking as viewed:', error);
    }
  };

  const markRecommendationActedUpon = async (recommendationId) => {
    try {
      await axios.put(`${process.env.REACT_APP_BACKEND_URL}/api/recommendations/${recommendationId}/acted-upon`);
      
      // Update local state
      if (activeTab === 'all') {
        setRecommendations(recommendations.map(r => 
          r.id === recommendationId ? { ...r, is_acted_upon: true } : r
        ));
      }
    } catch (error) {
      console.error('Error marking as acted upon:', error);
    }
  };

  const dismissRecommendation = async (recommendationId) => {
    try {
      await axios.put(`${process.env.REACT_APP_BACKEND_URL}/api/recommendations/${recommendationId}/dismiss`);
      
      // Remove from local state
      if (activeTab === 'all') {
        setRecommendations(recommendations.filter(r => r.id !== recommendationId));
      }
    } catch (error) {
      console.error('Error dismissing recommendation:', error);
    }
  };

  const createLearningGoal = async () => {
    // This would open a modal or form to create a learning goal
    console.log('Create learning goal - would open modal');
  };

  const getRecommendationIcon = (type) => {
    const iconMap = {
      skill_learning: BookOpenIcon,
      skill_teaching: AcademicCapIcon,
      user_match: UserIcon,
      session_timing: ClockIcon,
      learning_path: TargetIcon,
      community_content: UserGroupIcon,
      goal_suggestion: StarIcon
    };
    return iconMap[type] || LightBulbIcon;
  };

  const getRecommendationTypeColor = (type) => {
    const colorMap = {
      skill_learning: 'bg-blue-50 text-blue-700 border-blue-200',
      skill_teaching: 'bg-green-50 text-green-700 border-green-200',
      user_match: 'bg-purple-50 text-purple-700 border-purple-200',
      session_timing: 'bg-orange-50 text-orange-700 border-orange-200',
      learning_path: 'bg-indigo-50 text-indigo-700 border-indigo-200',
      community_content: 'bg-pink-50 text-pink-700 border-pink-200',
      goal_suggestion: 'bg-yellow-50 text-yellow-700 border-yellow-200'
    };
    return colorMap[type] || 'bg-gray-50 text-gray-700 border-gray-200';
  };

  const tabs = [
    { id: 'dashboard', name: 'Dashboard', icon: ChartBarIcon },
    { id: 'all', name: 'All Recommendations', icon: LightBulbIcon },
    { id: 'goals', name: 'Learning Goals', icon: TargetIcon },
    { id: 'insights', name: 'Insights', icon: ChartBarIcon }
  ];

  const recommendationTypes = [
    { id: 'all', name: 'All Types' },
    { id: 'skill_learning', name: 'Skill Learning' },
    { id: 'user_match', name: 'User Matches' },
    { id: 'learning_path', name: 'Learning Paths' },
    { id: 'community_content', name: 'Community Content' }
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Smart Recommendations
            </h1>
            <p className="text-gray-600 mt-2">
              AI-powered personalized learning recommendations and insights
            </p>
          </div>
          
          <button
            onClick={generateRecommendations}
            disabled={loading}
            className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            <ArrowPathIcon className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
            <span>Generate Fresh Recommendations</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-8">
        <nav className="flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-5 w-5" />
                <span>{tab.name}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
        </div>
      )}

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && dashboardData && !loading && (
        <div className="space-y-8">
          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="bg-blue-50 rounded-lg p-3">
                  <LightBulbIcon className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-2xl font-semibold text-gray-900">
                    {dashboardData.quick_stats?.total_recommendations || 0}
                  </p>
                  <p className="text-sm text-gray-600">Active Recommendations</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="bg-green-50 rounded-lg p-3">
                  <TargetIcon className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-2xl font-semibold text-gray-900">
                    {dashboardData.learning_goals?.active_goals || 0}
                  </p>
                  <p className="text-sm text-gray-600">Active Goals</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="bg-yellow-50 rounded-lg p-3">
                  <TrophyIcon className="h-6 w-6 text-yellow-600" />
                </div>
                <div className="ml-4">
                  <p className="text-2xl font-semibold text-gray-900">
                    {dashboardData.learning_goals?.average_progress || 0}%
                  </p>
                  <p className="text-sm text-gray-600">Average Progress</p>
                </div>
              </div>
            </div>
          </div>

          {/* Featured Recommendations */}
          {dashboardData.recommendations?.featured?.length > 0 && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Featured Recommendations</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {dashboardData.recommendations.featured.map((rec) => {
                  const Icon = getRecommendationIcon(rec.recommendation_type);
                  const typeColor = getRecommendationTypeColor(rec.recommendation_type);
                  
                  return (
                    <div key={rec.id} className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
                      <div className="flex items-start space-x-4">
                        <div className={`p-2 rounded-lg ${typeColor} border`}>
                          <Icon className="h-5 w-5" />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-medium text-gray-900 mb-2">{rec.title}</h3>
                          <p className="text-sm text-gray-600 mb-3">{rec.description}</p>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-blue-600 font-medium">
                              {(rec.confidence_score * 100).toFixed(0)}% match
                            </span>
                            <div className="flex space-x-2">
                              <button
                                onClick={() => markRecommendationViewed(rec.id)}
                                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                              >
                                View
                              </button>
                              <button
                                onClick={() => markRecommendationActedUpon(rec.id)}
                                className="text-sm text-green-600 hover:text-green-800 font-medium"
                              >
                                Act
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Recent Learning Goals */}
          {dashboardData.learning_goals?.recent_goals?.length > 0 && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Learning Goals</h2>
              <div className="bg-white rounded-lg shadow overflow-hidden">
                {dashboardData.learning_goals.recent_goals.map((goal) => (
                  <div key={goal.id} className="p-4 border-b border-gray-100 last:border-b-0">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900">{goal.skill_name}</h3>
                        <p className="text-sm text-gray-600">Target: {goal.target_level}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-semibold text-blue-600">
                          {goal.current_progress.toFixed(1)}%
                        </div>
                        <div className="w-24 bg-gray-200 rounded-full h-2 mt-1">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${Math.min(100, goal.current_progress)}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* All Recommendations Tab */}
      {activeTab === 'all' && !loading && (
        <div>
          {/* Filter */}
          <div className="flex flex-wrap gap-2 mb-6">
            {recommendationTypes.map((type) => (
              <button
                key={type.id}
                onClick={() => setFilterType(type.id)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  filterType === type.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {type.name}
              </button>
            ))}
          </div>

          {/* Recommendations List */}
          <div className="space-y-4">
            {recommendations.length === 0 ? (
              <div className="text-center py-12">
                <LightBulbIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 mb-2">No recommendations yet</p>
                <button
                  onClick={generateRecommendations}
                  className="text-blue-600 hover:text-blue-800 font-medium"
                >
                  Generate your first recommendations
                </button>
              </div>
            ) : (
              recommendations.map((rec) => {
                const Icon = getRecommendationIcon(rec.recommendation_type);
                const typeColor = getRecommendationTypeColor(rec.recommendation_type);
                
                return (
                  <div key={rec.id} className={`bg-white rounded-lg shadow p-6 transition-all ${
                    rec.is_viewed ? 'opacity-75' : ''
                  }`}>
                    <div className="flex items-start space-x-4">
                      <div className={`p-3 rounded-lg ${typeColor} border flex-shrink-0`}>
                        <Icon className="h-6 w-6" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h3 className="font-semibold text-gray-900 mb-2">{rec.title}</h3>
                            <p className="text-gray-600 mb-4">{rec.description}</p>
                            
                            <div className="flex items-center space-x-4 text-sm">
                              <span className="text-blue-600 font-medium">
                                {(rec.confidence_score * 100).toFixed(0)}% confidence
                              </span>
                              <span className="text-gray-500">{rec.time_ago}</span>
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${typeColor}`}>
                                {rec.recommendation_type.replace('_', ' ')}
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center space-x-2 ml-4">
                            {!rec.is_viewed && (
                              <button
                                onClick={() => markRecommendationViewed(rec.id)}
                                className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                title="Mark as viewed"
                              >
                                <EyeIcon className="h-4 w-4" />
                              </button>
                            )}
                            
                            {!rec.is_acted_upon && (
                              <button
                                onClick={() => markRecommendationActedUpon(rec.id)}
                                className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                                title="Mark as acted upon"
                              >
                                <CheckIcon className="h-4 w-4" />
                              </button>
                            )}
                            
                            <button
                              onClick={() => dismissRecommendation(rec.id)}
                              className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                              title="Dismiss"
                            >
                              <XMarkIcon className="h-4 w-4" />
                            </button>
                          </div>
                        </div>

                        {rec.is_acted_upon && (
                          <div className="mt-3 p-2 bg-green-50 border border-green-200 rounded text-sm text-green-700">
                            ✅ You acted on this recommendation
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* Learning Goals Tab */}
      {activeTab === 'goals' && !loading && (
        <div>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-gray-900">Learning Goals</h2>
            <button
              onClick={createLearningGoal}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              + New Goal
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {learningGoals.length === 0 ? (
              <div className="col-span-2 text-center py-12">
                <TargetIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 mb-2">No learning goals yet</p>
                <button
                  onClick={createLearningGoal}
                  className="text-blue-600 hover:text-blue-800 font-medium"
                >
                  Create your first goal
                </button>
              </div>
            ) : (
              learningGoals.map((goal) => (
                <div key={goal.id} className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-gray-900">{goal.skill_name}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      goal.is_active ? 'bg-green-50 text-green-700' : 'bg-gray-50 text-gray-500'
                    }`}>
                      {goal.is_active ? 'Active' : 'Completed'}
                    </span>
                  </div>
                  
                  <div className="mb-4">
                    <div className="flex justify-between text-sm mb-1">
                      <span>Progress</span>
                      <span>{goal.current_progress.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${Math.min(100, goal.current_progress)}%` }}
                      />
                    </div>
                  </div>
                  
                  <div className="text-sm text-gray-600 space-y-1">
                    <div className="flex items-center space-x-2">
                      <TargetIcon className="h-4 w-4" />
                      <span>Target: {goal.target_level}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CalendarIcon className="h-4 w-4" />
                      <span>Sessions/week: {goal.weekly_session_target}</span>
                    </div>
                    {goal.target_date && (
                      <div className="flex items-center space-x-2">
                        <ClockIcon className="h-4 w-4" />
                        <span>Target date: {new Date(goal.target_date).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Insights Tab */}
      {activeTab === 'insights' && insights && !loading && (
        <div className="space-y-8">
          {/* Overall Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <div className="text-3xl font-bold text-blue-600 mb-2">
                {insights.total_recommendations}
              </div>
              <div className="text-sm text-gray-600">Total Recommendations</div>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <div className="text-3xl font-bold text-green-600 mb-2">
                {insights.engagement_rate}%
              </div>
              <div className="text-sm text-gray-600">Engagement Rate</div>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <div className="text-3xl font-bold text-purple-600 mb-2">
                {insights.action_rate}%
              </div>
              <div className="text-sm text-gray-600">Action Rate</div>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <div className="text-3xl font-bold text-orange-600 mb-2">
                {insights.total_acted_upon}
              </div>
              <div className="text-sm text-gray-600">Actions Taken</div>
            </div>
          </div>

          {/* Breakdown by Type */}
          {insights.by_type && Object.keys(insights.by_type).length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Performance by Type</h2>
              <div className="space-y-4">
                {Object.entries(insights.by_type).map(([type, stats]) => (
                  <div key={type} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-lg ${getRecommendationTypeColor(type)} border`}>
                        {React.createElement(getRecommendationIcon(type), { className: "h-4 w-4" })}
                      </div>
                      <div>
                        <div className="font-medium text-gray-900 capitalize">
                          {type.replace('_', ' ')}
                        </div>
                        <div className="text-sm text-gray-600">
                          {stats.total} recommendations
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-semibold text-gray-900">
                        {stats.engagement_rate}%
                      </div>
                      <div className="text-sm text-gray-600">engagement</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Recommendations;