import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import toast from 'react-hot-toast';
import {
  MagnifyingGlassIcon,
  AdjustmentsHorizontalIcon,
  UserGroupIcon,
  StarIcon,
  MapPinIcon,
  ClockIcon,
  HeartIcon,
  ChatBubbleLeftRightIcon,
  VideoCameraIcon,
  AcademicCapIcon,
  BookOpenIcon,
  SparklesIcon,
  GlobeAltIcon,
  FunnelIcon,
  XMarkIcon,
  CheckIcon,
  ArrowRightIcon,
  UserCircleIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid, HeartIcon as HeartIconSolid } from '@heroicons/react/24/solid';

const Marketplace = () => {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilters, setSelectedFilters] = useState({
    skills_offered: [],
    skills_wanted: [],
    location: '',
    min_rating: 0,
    role: '',
    availability: ''
  });
  const [availableSkills, setAvailableSkills] = useState([]);
  const [showFilters, setShowFilters] = useState(false);
  const [activeTab, setActiveTab] = useState('browse'); // 'browse', 'matches', 'favorites'
  const [favorites, setFavorites] = useState([]);
  const [view, setView] = useState('grid'); // 'grid', 'list'

  const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    handleSearch();
  }, [searchQuery, selectedFilters]);

  const fetchInitialData = async () => {
    try {
      const [skillsResponse, matchesResponse] = await Promise.all([
        axios.get(`${API_BASE}/api/skills/`),
        axios.get(`${API_BASE}/api/matching/my-matches?limit=20`)
      ]);

      setAvailableSkills(skillsResponse.data);
      setMatches(matchesResponse.data);
      
      // Fetch all users initially
      await handleSearch();
    } catch (error) {
      console.error('Error fetching initial data:', error);
      toast.error('Failed to load marketplace data');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('query', searchQuery);
      if (selectedFilters.skills_offered.length > 0) {
        selectedFilters.skills_offered.forEach(skill => params.append('skills_offered', skill));
      }
      if (selectedFilters.skills_wanted.length > 0) {
        selectedFilters.skills_wanted.forEach(skill => params.append('skills_wanted', skill));
      }
      if (selectedFilters.location) params.append('location', selectedFilters.location);
      if (selectedFilters.min_rating > 0) params.append('min_rating', selectedFilters.min_rating.toString());
      params.append('limit', '50');

      const response = await axios.get(`${API_BASE}/api/users/search?${params.toString()}`);
      setUsers(response.data);
    } catch (error) {
      console.error('Error searching users:', error);
      toast.error('Failed to search users');
    }
  };

  const handleSkillToggle = (skill, filterType) => {
    setSelectedFilters(prev => ({
      ...prev,
      [filterType]: prev[filterType].includes(skill)
        ? prev[filterType].filter(s => s !== skill)
        : [...prev[filterType], skill]
    }));
  };

  const clearFilters = () => {
    setSelectedFilters({
      skills_offered: [],
      skills_wanted: [],
      location: '',
      min_rating: 0,
      role: '',
      availability: ''
    });
    setSearchQuery('');
  };

  const handleConnect = async (userId) => {
    try {
      // This would typically create a connection request
      toast.success('Connection request sent!');
    } catch (error) {
      console.error('Error connecting:', error);
      toast.error('Failed to send connection request');
    }
  };

  const toggleFavorite = (userId) => {
    setFavorites(prev => 
      prev.includes(userId) 
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    );
  };

  const renderStars = (rating) => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <StarIconSolid
          key={i}
          className={`h-4 w-4 ${i <= rating ? 'text-yellow-400' : 'text-gray-300'}`}
        />
      );
    }
    return stars;
  };

  const UserCard = ({ user: userProfile, isMatch = false }) => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start space-x-4">
        {/* Profile Image */}
        <div className="flex-shrink-0">
          {userProfile.profile_image ? (
            <img 
              src={userProfile.profile_image} 
              alt={userProfile.username}
              className="w-16 h-16 rounded-full object-cover"
            />
          ) : (
            <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center">
              <UserCircleIcon className="h-10 w-10 text-gray-400" />
            </div>
          )}
        </div>

        {/* User Info */}
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">
              {userProfile.first_name} {userProfile.last_name}
            </h3>
            <button
              onClick={() => toggleFavorite(userProfile.id)}
              className="text-gray-400 hover:text-red-500 transition-colors"
            >
              {favorites.includes(userProfile.id) ? (
                <HeartIconSolid className="h-5 w-5 text-red-500" />
              ) : (
                <HeartIcon className="h-5 w-5" />
              )}
            </button>
          </div>
          
          <p className="text-gray-600 text-sm">@{userProfile.username}</p>
          
          {/* Rating and Level */}
          <div className="flex items-center space-x-4 mt-2">
            <div className="flex items-center space-x-1">
              {renderStars(Math.floor(userProfile.average_rating || 0))}
              <span className="text-sm text-gray-500">({userProfile.rating_count || 0})</span>
            </div>
            <span className="text-sm text-gray-500">Level {userProfile.level}</span>
          </div>

          {/* Location */}
          {userProfile.location && (
            <div className="flex items-center space-x-1 mt-2">
              <MapPinIcon className="h-4 w-4 text-gray-400" />
              <span className="text-sm text-gray-600">{userProfile.location}</span>
            </div>
          )}

          {/* Bio */}
          {userProfile.bio && (
            <p className="text-gray-700 text-sm mt-2 line-clamp-2">
              {userProfile.bio}
            </p>
          )}

          {/* Skills */}
          <div className="mt-3">
            <div className="flex flex-wrap gap-2">
              {userProfile.skills_offered?.slice(0, 3).map((skill, index) => (
                <span
                  key={index}
                  className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full"
                >
                  {skill}
                </span>
              ))}
              {userProfile.skills_offered?.length > 3 && (
                <span className="text-xs text-gray-500 self-center">
                  +{userProfile.skills_offered.length - 3} more
                </span>
              )}
            </div>
          </div>

          {/* Match Score */}
          {isMatch && (
            <div className="mt-3">
              <div className="flex items-center space-x-2">
                <SparklesIcon className="h-4 w-4 text-purple-500" />
                <span className="text-sm text-purple-600 font-medium">
                  {Math.round((userProfile.match_score || 0) * 100)}% match
                </span>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex space-x-3 mt-4">
            <button
              onClick={() => handleConnect(userProfile.id)}
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              Connect
            </button>
            <button className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors text-sm">
              <ChatBubbleLeftRightIcon className="h-4 w-4" />
            </button>
            <button className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors text-sm">
              <VideoCameraIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const UserListItem = ({ user: userProfile, isMatch = false }) => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-center space-x-4">
        {/* Profile Image */}
        <div className="flex-shrink-0">
          {userProfile.profile_image ? (
            <img 
              src={userProfile.profile_image} 
              alt={userProfile.username}
              className="w-12 h-12 rounded-full object-cover"
            />
          ) : (
            <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
              <UserCircleIcon className="h-8 w-8 text-gray-400" />
            </div>
          )}
        </div>

        {/* User Info */}
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-gray-900">
                {userProfile.first_name} {userProfile.last_name}
              </h3>
              <p className="text-sm text-gray-600">@{userProfile.username}</p>
            </div>
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-1">
                {renderStars(Math.floor(userProfile.average_rating || 0))}
                <span className="text-sm text-gray-500">({userProfile.rating_count || 0})</span>
              </div>
              <button
                onClick={() => toggleFavorite(userProfile.id)}
                className="text-gray-400 hover:text-red-500 transition-colors"
              >
                {favorites.includes(userProfile.id) ? (
                  <HeartIconSolid className="h-5 w-5 text-red-500" />
                ) : (
                  <HeartIcon className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>
          
          <div className="flex items-center space-x-4 mt-2">
            <div className="flex flex-wrap gap-1">
              {userProfile.skills_offered?.slice(0, 3).map((skill, index) => (
                <span
                  key={index}
                  className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full"
                >
                  {skill}
                </span>
              ))}
            </div>
            {isMatch && (
              <span className="text-sm text-purple-600 font-medium">
                {Math.round((userProfile.match_score || 0) * 100)}% match
              </span>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-2">
          <button
            onClick={() => handleConnect(userProfile.id)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            Connect
          </button>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Skill Marketplace</h1>
            <p className="text-gray-600 mt-1">Discover talented people and share your skills</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setView('grid')}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                  view === 'grid' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'
                }`}
              >
                Grid
              </button>
              <button
                onClick={() => setView('list')}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                  view === 'list' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'
                }`}
              >
                List
              </button>
            </div>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by name, skills, or location..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center space-x-2 px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <FunnelIcon className="h-5 w-5" />
            <span>Filters</span>
          </button>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium text-gray-900">Filters</h3>
              <button
                onClick={clearFilters}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                Clear all
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Skills Offered */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Skills Offered
                </label>
                <div className="max-h-40 overflow-y-auto">
                  {availableSkills.slice(0, 20).map((skill) => (
                    <label key={skill.id} className="flex items-center space-x-2 py-1">
                      <input
                        type="checkbox"
                        checked={selectedFilters.skills_offered.includes(skill.name)}
                        onChange={() => handleSkillToggle(skill.name, 'skills_offered')}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">{skill.name}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Location */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Location
                </label>
                <input
                  type="text"
                  placeholder="City, Country"
                  value={selectedFilters.location}
                  onChange={(e) => setSelectedFilters(prev => ({ ...prev, location: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Minimum Rating */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Minimum Rating
                </label>
                <select
                  value={selectedFilters.min_rating}
                  onChange={(e) => setSelectedFilters(prev => ({ ...prev, min_rating: Number(e.target.value) }))}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value={0}>Any rating</option>
                  <option value={1}>1+ stars</option>
                  <option value={2}>2+ stars</option>
                  <option value={3}>3+ stars</option>
                  <option value={4}>4+ stars</option>
                  <option value={5}>5 stars</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('browse')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'browse'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Browse All ({users.length})
            </button>
            <button
              onClick={() => setActiveTab('matches')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'matches'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              AI Matches ({matches.length})
            </button>
            <button
              onClick={() => setActiveTab('favorites')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'favorites'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Favorites ({favorites.length})
            </button>
          </nav>
        </div>

        {/* Content */}
        <div className="p-6">
          {activeTab === 'browse' && (
            <div>
              {users.length > 0 ? (
                <div className={view === 'grid' ? 'grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6' : 'space-y-4'}>
                  {users.map((userProfile) => (
                    <div key={userProfile.id}>
                      {view === 'grid' ? (
                        <UserCard user={userProfile} />
                      ) : (
                        <UserListItem user={userProfile} />
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <UserGroupIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500 mb-4">No users found matching your criteria</p>
                  <button
                    onClick={clearFilters}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Clear Filters
                  </button>
                </div>
              )}
            </div>
          )}

          {activeTab === 'matches' && (
            <div>
              {matches.length > 0 ? (
                <div className={view === 'grid' ? 'grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6' : 'space-y-4'}>
                  {matches.map((match) => (
                    <div key={match.user.id}>
                      {view === 'grid' ? (
                        <UserCard user={{...match.user, match_score: match.match?.compatibility_score}} isMatch={true} />
                      ) : (
                        <UserListItem user={{...match.user, match_score: match.match?.compatibility_score}} isMatch={true} />
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <SparklesIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500 mb-4">No AI matches found yet</p>
                  <p className="text-gray-400 text-sm">Complete your profile to get better matches</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'favorites' && (
            <div>
              {favorites.length > 0 ? (
                <div className={view === 'grid' ? 'grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6' : 'space-y-4'}>
                  {users.filter(u => favorites.includes(u.id)).map((userProfile) => (
                    <div key={userProfile.id}>
                      {view === 'grid' ? (
                        <UserCard user={userProfile} />
                      ) : (
                        <UserListItem user={userProfile} />
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <HeartIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500 mb-4">No favorites yet</p>
                  <p className="text-gray-400 text-sm">Click the heart icon on user cards to add them to favorites</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Marketplace;