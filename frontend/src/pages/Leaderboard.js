import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import {
  TrophyIcon,
  CurrencyDollarIcon,
  StarIcon,
  FireIcon,
  UserGroupIcon,
  AcademicCapIcon,
  GiftIcon,
  ChartBarIcon,
  ChevronRightIcon,
  CheckIcon,
  ClockIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import {
  TrophyIcon as TrophySolid,
  CurrencyDollarIcon as CurrencySolid,
  StarIcon as StarSolid,
  FireIcon as FireSolid,
} from '@heroicons/react/24/solid';

const Leaderboard = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('leaderboard');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Data states
  const [userProgress, setUserProgress] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [badges, setBadges] = useState([]);
  const [achievements, setAchievements] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [stats, setStats] = useState(null);

  const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  const tabs = [
    { id: 'leaderboard', name: 'Leaderboard', icon: TrophyIcon },
    { id: 'progress', name: 'My Progress', icon: ChartBarIcon },
    { id: 'badges', name: 'Badges', icon: StarIcon },
    { id: 'achievements', name: 'Achievements', icon: GiftIcon },
    { id: 'coins', name: 'Skill Coins', icon: CurrencyDollarIcon },
  ];

  useEffect(() => {
    loadGamificationData();
  }, []);

  const loadGamificationData = async () => {
    setLoading(true);
    try {
      const [progressRes, leaderboardRes, badgesRes, achievementsRes, transactionsRes, statsRes] = await Promise.all([
        axios.get(`${API_BASE}/api/gamification/progress`),
        axios.get(`${API_BASE}/api/gamification/leaderboard?limit=50`),
        axios.get(`${API_BASE}/api/gamification/badges`),
        axios.get(`${API_BASE}/api/gamification/achievements`),
        axios.get(`${API_BASE}/api/gamification/transactions?limit=20`),
        axios.get(`${API_BASE}/api/gamification/stats/summary`)
      ]);

      setUserProgress(progressRes.data);
      setLeaderboard(leaderboardRes.data);
      setBadges(badgesRes.data);
      setAchievements(achievementsRes.data);
      setTransactions(transactionsRes.data);
      setStats(statsRes.data);
    } catch (err) {
      console.error('Error loading gamification data:', err);
      setError('Failed to load gamification data');
    } finally {
      setLoading(false);
    }
  };

  const checkProgress = async () => {
    try {
      const response = await axios.post(`${API_BASE}/api/gamification/check-progress`);
      if (response.data.new_badges > 0) {
        alert(`Congratulations! You earned ${response.data.new_badges} new badge(s)!`);
        loadGamificationData(); // Refresh data
      } else {
        alert('Progress checked! No new badges earned yet. Keep working on your skills!');
      }
    } catch (err) {
      console.error('Error checking progress:', err);
    }
  };

  const getBadgeIcon = (badgeType) => {
    const iconMap = {
      skill_master: AcademicCapIcon,
      mentor: UserGroupIcon,
      learner: StarIcon,
      social: UserGroupIcon,
      milestone: TrophyIcon,
      special: SparklesIcon
    };
    return iconMap[badgeType] || StarIcon;
  };

  const getAchievementIcon = (achievementType) => {
    const iconMap = {
      sessions_completed: TrophyIcon,
      skill_earned: AcademicCapIcon,
      mentoring_milestone: UserGroupIcon,
      learning_milestone: StarIcon,
      social_milestone: UserGroupIcon,
      rating_milestone: StarIcon,
      streak_milestone: FireIcon
    };
    return iconMap[achievementType] || GiftIcon;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getRankColor = (rank) => {
    if (rank === 1) return 'text-yellow-600 bg-yellow-50';
    if (rank === 2) return 'text-gray-600 bg-gray-50';
    if (rank === 3) return 'text-orange-600 bg-orange-50';
    return 'text-blue-600 bg-blue-50';
  };

  const renderQuickStats = () => {
    if (!userProgress) return null;

    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Skill Coins</p>
              <p className="text-2xl font-bold text-blue-600">{userProgress.skill_coins}</p>
            </div>
            <CurrencySolid className="h-8 w-8 text-blue-500" />
          </div>
        </div>
        
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Sessions</p>
              <p className="text-2xl font-bold text-green-600">{userProgress.total_sessions}</p>
            </div>
            <TrophySolid className="h-8 w-8 text-green-500" />
          </div>
        </div>
        
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Leaderboard Rank</p>
              <p className="text-2xl font-bold text-purple-600">#{userProgress.leaderboard_rank}</p>
            </div>
            <TrophySolid className="h-8 w-8 text-purple-500" />
          </div>
        </div>
        
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Current Streak</p>
              <p className="text-2xl font-bold text-orange-600">{userProgress.current_streak}</p>
            </div>
            <FireSolid className="h-8 w-8 text-orange-500" />
          </div>
        </div>
      </div>
    );
  };

  const renderLeaderboard = () => (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="p-6 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Top Players</h3>
        <p className="text-sm text-gray-600">See how you rank against other learners</p>
      </div>
      
      <div className="divide-y divide-gray-200">
        {leaderboard.map((entry, index) => (
          <div key={entry.user_id} className="p-4 hover:bg-gray-50 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${getRankColor(entry.rank)}`}>
                  {entry.rank}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">{entry.username}</p>
                  <p className="text-xs text-gray-500">
                    {entry.total_sessions} sessions • {entry.skill_coins} coins
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <div className="flex items-center space-x-1">
                  <StarSolid className="h-4 w-4 text-yellow-400" />
                  <span>{entry.average_rating.toFixed(1)}</span>
                </div>
                {entry.current_streak > 0 && (
                  <div className="flex items-center space-x-1">
                    <FireIcon className="h-4 w-4 text-orange-400" />
                    <span>{entry.current_streak}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderProgress = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Your Progress</h3>
          <button
            onClick={checkProgress}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            Check Progress
          </button>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">{userProgress?.badges?.length || 0}</p>
            <p className="text-sm text-gray-600">Badges Earned</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">{userProgress?.achievements?.length || 0}</p>
            <p className="text-sm text-gray-600">Achievements</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-purple-600">{userProgress?.average_rating?.toFixed(1) || '0.0'}</p>
            <p className="text-sm text-gray-600">Average Rating</p>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Session Statistics</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">{userProgress?.teaching_sessions || 0}</p>
            <p className="text-sm text-gray-600">Teaching Sessions</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">{userProgress?.learning_sessions || 0}</p>
            <p className="text-sm text-gray-600">Learning Sessions</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-orange-600">{userProgress?.longest_streak || 0}</p>
            <p className="text-sm text-gray-600">Longest Streak</p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderBadges = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Badges ({userProgress?.badges?.length || 0})</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {userProgress?.badges?.map((userBadge) => {
            const badge = badges.find(b => b.id === userBadge.badge_id);
            if (!badge) return null;
            
            const BadgeIcon = getBadgeIcon(badge.badge_type);
            return (
              <div key={userBadge.id} className="border border-gray-200 rounded-lg p-4 bg-gradient-to-br from-blue-50 to-purple-50">
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-full" style={{ backgroundColor: badge.color + '20' }}>
                    <BadgeIcon className="h-6 w-6" style={{ color: badge.color }} />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{badge.name}</p>
                    <p className="text-sm text-gray-600">{badge.description}</p>
                    <p className="text-xs text-gray-500">Earned {formatDate(userBadge.earned_at)}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">All Available Badges</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {badges.map((badge) => {
            const earned = userProgress?.badges?.some(ub => ub.badge_id === badge.id);
            const BadgeIcon = getBadgeIcon(badge.badge_type);
            
            return (
              <div key={badge.id} className={`border rounded-lg p-4 ${earned ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'}`}>
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-full ${earned ? 'bg-green-100' : 'bg-gray-100'}`}>
                    <BadgeIcon className={`h-6 w-6 ${earned ? 'text-green-600' : 'text-gray-400'}`} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <p className="font-medium text-gray-900">{badge.name}</p>
                      {earned && <CheckIcon className="h-4 w-4 text-green-600" />}
                    </div>
                    <p className="text-sm text-gray-600">{badge.description}</p>
                    {badge.skill_coins_reward > 0 && (
                      <p className="text-xs text-blue-600">+{badge.skill_coins_reward} coins</p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );

  const renderAchievements = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Achievements ({userProgress?.achievements?.length || 0})</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {userProgress?.achievements?.map((userAchievement) => {
            const achievement = achievements.find(a => a.id === userAchievement.achievement_id);
            if (!achievement) return null;
            
            const AchievementIcon = getAchievementIcon(achievement.achievement_type);
            return (
              <div key={userAchievement.id} className="border border-gray-200 rounded-lg p-4 bg-gradient-to-br from-green-50 to-blue-50">
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-full" style={{ backgroundColor: achievement.color + '20' }}>
                    <AchievementIcon className="h-6 w-6" style={{ color: achievement.color }} />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{achievement.name}</p>
                    <p className="text-sm text-gray-600">{achievement.description}</p>
                    <p className="text-xs text-gray-500">Unlocked {formatDate(userAchievement.earned_at)}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">All Achievements</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {achievements.map((achievement) => {
            const earned = userProgress?.achievements?.some(ua => ua.achievement_id === achievement.id);
            const AchievementIcon = getAchievementIcon(achievement.achievement_type);
            
            return (
              <div key={achievement.id} className={`border rounded-lg p-4 ${earned ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'}`}>
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-full ${earned ? 'bg-green-100' : 'bg-gray-100'}`}>
                    <AchievementIcon className={`h-6 w-6 ${earned ? 'text-green-600' : 'text-gray-400'}`} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <p className="font-medium text-gray-900">{achievement.name}</p>
                      {earned && <CheckIcon className="h-4 w-4 text-green-600" />}
                    </div>
                    <p className="text-sm text-gray-600">{achievement.description}</p>
                    {achievement.skill_coins_reward > 0 && (
                      <p className="text-xs text-blue-600">+{achievement.skill_coins_reward} coins</p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );

  const renderCoins = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Skill Coin Balance</h3>
        <div className="text-center p-6 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg">
          <CurrencySolid className="h-16 w-16 text-blue-500 mx-auto mb-4" />
          <p className="text-4xl font-bold text-blue-600 mb-2">{userProgress?.skill_coins || 0}</p>
          <p className="text-gray-600">Skill Coins</p>
        </div>
      </div>
      
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Transactions</h3>
        <div className="space-y-3">
          {transactions.map((transaction) => (
            <div key={transaction.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-full ${transaction.amount > 0 ? 'bg-green-100' : 'bg-red-100'}`}>
                  {transaction.amount > 0 ? (
                    <CurrencyDollarIcon className="h-4 w-4 text-green-600" />
                  ) : (
                    <CurrencyDollarIcon className="h-4 w-4 text-red-600" />
                  )}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">{transaction.description}</p>
                  <p className="text-xs text-gray-500">{formatDate(transaction.created_at)}</p>
                </div>
              </div>
              <div className="text-right">
                <p className={`text-sm font-bold ${transaction.amount > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {transaction.amount > 0 ? '+' : ''}{transaction.amount}
                </p>
                <p className="text-xs text-gray-500">Balance: {transaction.balance_after}</p>
              </div>
            </div>
          ))}
          
          {transactions.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <CurrencyDollarIcon className="h-12 w-12 mx-auto mb-3 text-gray-300" />
              <p>No transactions yet</p>
              <p className="text-sm">Complete sessions to earn skill coins!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'leaderboard':
        return renderLeaderboard();
      case 'progress':
        return renderProgress();
      case 'badges':
        return renderBadges();
      case 'achievements':
        return renderAchievements();
      case 'coins':
        return renderCoins();
      default:
        return renderLeaderboard();
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-600">{error}</p>
          <button
            onClick={loadGamificationData}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Gamification Hub</h1>
        <p className="text-gray-600">
          Track your progress, earn badges, compete on the leaderboard, and manage your skill coins
        </p>
      </div>

      {/* Quick Stats */}
      {renderQuickStats()}

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
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
      </div>

      {/* Content */}
      {renderContent()}
    </div>
  );
};

export default Leaderboard;