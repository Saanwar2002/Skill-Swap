import React, { useState, useEffect } from 'react';
import { 
  CalendarDaysIcon, 
  ClockIcon, 
  UserIcon, 
  MapPinIcon,
  StarIcon,
  PlusIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  EyeIcon,
  PencilIcon,
  XMarkIcon,
  CheckIcon,
  PlayIcon,
  StopIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const Sessions = () => {
  const { user } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [upcomingSessions, setUpcomingSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('upcoming');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterRole, setFilterRole] = useState('all');
  const [selectedSession, setSelectedSession] = useState(null);
  const [showSessionModal, setShowSessionModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedback, setFeedback] = useState({ rating: 5, comment: '' });

  const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  // Fetch sessions
  useEffect(() => {
    const loadSessions = async () => {
      setLoading(true);
      try {
        await Promise.all([fetchSessions(), fetchUpcomingSessions()]);
      } catch (err) {
        console.error('Error loading sessions:', err);
      } finally {
        setLoading(false);
      }
    };
    
    loadSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/sessions`, {
        params: {
          role: filterRole,
          status: filterStatus,
          limit: 50
        }
      });
      setSessions(response.data);
    } catch (err) {
      setError('Failed to fetch sessions');
      console.error('Error fetching sessions:', err);
    }
  };

  const fetchUpcomingSessions = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/sessions/upcoming`, {
        params: { limit: 10 }
      });
      setUpcomingSessions(response.data);
    } catch (err) {
      console.error('Error fetching upcoming sessions:', err);
    }
  };

  // Filter sessions based on search and filters
  const filteredSessions = sessions.filter(session => {
    const matchesSearch = session.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         session.skill_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         session.description?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = filterStatus === 'all' || session.status === filterStatus;
    const matchesRole = filterRole === 'all' || 
                       (filterRole === 'teacher' && session.teacher_id === user?.id) ||
                       (filterRole === 'learner' && session.learner_id === user?.id);
    
    return matchesSearch && matchesStatus && matchesRole;
  });

  const handleSessionAction = async (sessionId, action, data = {}) => {
    try {
      await axios.post(`${API_BASE}/api/sessions/${sessionId}/${action}`, data);
      fetchSessions();
      fetchUpcomingSessions();
      
      if (action === 'start') {
        alert('Session started successfully!');
      } else if (action === 'end') {
        alert('Session ended successfully!');
      } else if (action === 'cancel') {
        alert('Session cancelled successfully!');
      }
    } catch (err) {
      console.error(`Error ${action} session:`, err);
      alert(`Failed to ${action} session`);
    }
  };

  const handleFeedbackSubmit = async () => {
    try {
      await axios.post(`${API_BASE}/api/sessions/${selectedSession.id}/feedback`, null, {
        params: {
          rating: feedback.rating,
          feedback: feedback.comment
        }
      });
      setShowFeedbackModal(false);
      setFeedback({ rating: 5, comment: '' });
      fetchSessions();
      alert('Feedback submitted successfully!');
    } catch (err) {
      console.error('Error submitting feedback:', err);
      alert('Failed to submit feedback');
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'scheduled': return 'bg-blue-100 text-blue-800';
      case 'in_progress': return 'bg-green-100 text-green-800';
      case 'completed': return 'bg-gray-100 text-gray-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'scheduled': return <CalendarDaysIcon className="h-4 w-4" />;
      case 'in_progress': return <PlayIcon className="h-4 w-4" />;
      case 'completed': return <CheckIcon className="h-4 w-4" />;
      case 'cancelled': return <XMarkIcon className="h-4 w-4" />;
      default: return <ClockIcon className="h-4 w-4" />;
    }
  };

  const canStartSession = (session) => {
    const now = new Date();
    const startTime = new Date(session.scheduled_start);
    const timeDiff = startTime - now;
    return session.status === 'scheduled' && timeDiff <= 15 * 60 * 1000; // 15 minutes before
  };

  const canEndSession = (session) => {
    return session.status === 'in_progress';
  };

  const canCancelSession = (session) => {
    return session.status === 'scheduled';
  };

  const needsFeedback = (session) => {
    const isTeacher = session.teacher_id === user?.id;
    const isLearner = session.learner_id === user?.id;
    
    return session.status === 'completed' && 
           ((isTeacher && !session.teacher_rating) || 
            (isLearner && !session.learner_rating));
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">My Sessions</h1>
            <p className="text-gray-600 mt-2">
              Manage your skill-sharing sessions
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 flex items-center space-x-2"
          >
            <PlusIcon className="h-5 w-5" />
            <span>Book Session</span>
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center">
            <CalendarDaysIcon className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm text-gray-500">Total Sessions</p>
              <p className="text-2xl font-bold text-gray-900">{sessions.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center">
            <PlayIcon className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm text-gray-500">Upcoming</p>
              <p className="text-2xl font-bold text-gray-900">{upcomingSessions.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center">
            <CheckIcon className="h-8 w-8 text-purple-600" />
            <div className="ml-4">
              <p className="text-sm text-gray-500">Completed</p>
              <p className="text-2xl font-bold text-gray-900">
                {sessions.filter(s => s.status === 'completed').length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center">
            <StarIcon className="h-8 w-8 text-yellow-600" />
            <div className="ml-4">
              <p className="text-sm text-gray-500">Avg Rating</p>
              <p className="text-2xl font-bold text-gray-900">{user?.average_rating || 'N/A'}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-6">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('upcoming')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'upcoming'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Upcoming ({upcomingSessions.length})
          </button>
          <button
            onClick={() => setActiveTab('all')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'all'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            All Sessions ({sessions.length})
          </button>
        </nav>
      </div>

      {/* Search and Filters */}
      {activeTab === 'all' && (
        <div className="mb-6 bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search sessions..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <select
              className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="all">All Status</option>
              <option value="scheduled">Scheduled</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
            <select
              className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={filterRole}
              onChange={(e) => setFilterRole(e.target.value)}
            >
              <option value="all">All Roles</option>
              <option value="teacher">As Teacher</option>
              <option value="learner">As Learner</option>
            </select>
          </div>
        </div>
      )}

      {/* Sessions List */}
      <div className="space-y-4">
        {(activeTab === 'upcoming' ? upcomingSessions : filteredSessions).map((session) => (
          <div
            key={session.id}
            className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
          >
            <div className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-3">
                    <h3 className="text-lg font-semibold text-gray-900">{session.title}</h3>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(session.status)}`}>
                      {getStatusIcon(session.status)}
                      <span className="ml-1 capitalize">{session.status.replace('_', ' ')}</span>
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600 mb-4">
                    <div className="flex items-center space-x-2">
                      <CalendarDaysIcon className="h-4 w-4" />
                      <span>{formatDate(session.scheduled_start)}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <ClockIcon className="h-4 w-4" />
                      <span>{formatTime(session.scheduled_start)} - {formatTime(session.scheduled_end)}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <StarIcon className="h-4 w-4" />
                      <span>{session.skill_name}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <UserIcon className="h-4 w-4" />
                      <span>
                        {session.teacher_id === user?.id ? 'Teaching' : 'Learning'}
                      </span>
                    </div>
                  </div>
                  
                  {session.description && (
                    <p className="text-gray-700 mb-4">{session.description}</p>
                  )}
                  
                  {session.learning_objectives && session.learning_objectives.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-gray-900 mb-2">Learning Objectives:</h4>
                      <ul className="text-sm text-gray-600 space-y-1">
                        {session.learning_objectives.map((objective, index) => (
                          <li key={index} className="flex items-center space-x-2">
                            <span className="w-1.5 h-1.5 bg-blue-500 rounded-full"></span>
                            <span>{objective}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
                
                <div className="flex flex-col space-y-2 ml-4">
                  <button
                    onClick={() => {
                      setSelectedSession(session);
                      setShowSessionModal(true);
                    }}
                    className="text-blue-600 hover:text-blue-800 flex items-center space-x-1"
                  >
                    <EyeIcon className="h-4 w-4" />
                    <span>View</span>
                  </button>
                  
                  {canStartSession(session) && (
                    <button
                      onClick={() => handleSessionAction(session.id, 'start')}
                      className="text-green-600 hover:text-green-800 flex items-center space-x-1"
                    >
                      <PlayIcon className="h-4 w-4" />
                      <span>Start</span>
                    </button>
                  )}
                  
                  {canEndSession(session) && (
                    <button
                      onClick={() => handleSessionAction(session.id, 'end')}
                      className="text-purple-600 hover:text-purple-800 flex items-center space-x-1"
                    >
                      <StopIcon className="h-4 w-4" />
                      <span>End</span>
                    </button>
                  )}
                  
                  {canCancelSession(session) && (
                    <button
                      onClick={() => handleSessionAction(session.id, 'cancel', { reason: 'User request' })}
                      className="text-red-600 hover:text-red-800 flex items-center space-x-1"
                    >
                      <XMarkIcon className="h-4 w-4" />
                      <span>Cancel</span>
                    </button>
                  )}
                  
                  {needsFeedback(session) && (
                    <button
                      onClick={() => {
                        setSelectedSession(session);
                        setShowFeedbackModal(true);
                      }}
                      className="text-yellow-600 hover:text-yellow-800 flex items-center space-x-1"
                    >
                      <StarIcon className="h-4 w-4" />
                      <span>Rate</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
        
        {(activeTab === 'upcoming' ? upcomingSessions : filteredSessions).length === 0 && (
          <div className="text-center py-12">
            <CalendarDaysIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No sessions found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {activeTab === 'upcoming' ? 'No upcoming sessions scheduled.' : 'No sessions match your filters.'}
            </p>
          </div>
        )}
      </div>

      {/* Feedback Modal */}
      {showFeedbackModal && selectedSession && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Rate Session</h3>
              <button
                onClick={() => setShowFeedbackModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Rating (1-5 stars)
                </label>
                <div className="flex space-x-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => setFeedback({ ...feedback, rating: star })}
                      className={`${
                        star <= feedback.rating ? 'text-yellow-400' : 'text-gray-300'
                      } hover:text-yellow-400`}
                    >
                      <StarIcon className="h-6 w-6" />
                    </button>
                  ))}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Feedback
                </label>
                <textarea
                  value={feedback.comment}
                  onChange={(e) => setFeedback({ ...feedback, comment: e.target.value })}
                  rows={4}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Share your experience..."
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowFeedbackModal(false)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  onClick={handleFeedbackSubmit}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Submit
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Sessions;