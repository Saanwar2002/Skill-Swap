import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import {
  BellIcon,
  XMarkIcon,
  CheckIcon,
  TrashIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  StarIcon,
  ChatBubbleLeftRightIcon,
  TrophyIcon,
  UserGroupIcon,
  CalendarIcon
} from '@heroicons/react/24/outline';

const NotificationCenter = ({ isOpen, onClose }) => {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('all'); // all, unread, read

  useEffect(() => {
    if (isOpen && user) {
      fetchNotifications();
      fetchUnreadCount();
    }
  }, [isOpen, user, filter]);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const params = filter === 'unread' ? { unread_only: true } : {};
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/notifications/`, {
        params: { limit: 20, ...params }
      });
      setNotifications(response.data);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUnreadCount = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/notifications/count`);
      setUnreadCount(response.data.unread_count);
    } catch (error) {
      console.error('Error fetching unread count:', error);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await axios.put(`${process.env.REACT_APP_BACKEND_URL}/api/notifications/${notificationId}`, {
        is_read: true
      });
      
      // Update local state
      setNotifications(notifications.map(n => 
        n.id === notificationId ? { ...n, is_read: true } : n
      ));
      setUnreadCount(Math.max(0, unreadCount - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await axios.put(`${process.env.REACT_APP_BACKEND_URL}/api/notifications/mark-all-read`);
      
      // Update local state
      setNotifications(notifications.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('Error marking all as read:', error);
    }
  };

  const deleteNotification = async (notificationId) => {
    try {
      await axios.delete(`${process.env.REACT_APP_BACKEND_URL}/api/notifications/${notificationId}`);
      
      // Remove from local state
      const deletedNotification = notifications.find(n => n.id === notificationId);
      setNotifications(notifications.filter(n => n.id !== notificationId));
      
      // Update unread count if the deleted notification was unread
      if (deletedNotification && !deletedNotification.is_read) {
        setUnreadCount(Math.max(0, unreadCount - 1));
      }
    } catch (error) {
      console.error('Error deleting notification:', error);
    }
  };

  const getNotificationIcon = (type) => {
    const iconMap = {
      match_found: StarIcon,
      session_reminder: CalendarIcon,
      session_started: CalendarIcon,
      message_received: ChatBubbleLeftRightIcon,
      achievement_earned: TrophyIcon,
      badge_earned: TrophyIcon,
      community_post_like: UserGroupIcon,
      community_post_comment: UserGroupIcon,
      system_announcement: InformationCircleIcon,
      skill_recommendation: StarIcon,
      goal_reminder: ClockIcon
    };
    return iconMap[type] || InformationCircleIcon;
  };

  const getPriorityColor = (priority) => {
    const colorMap = {
      urgent: 'text-red-500 bg-red-50',
      high: 'text-orange-500 bg-orange-50',
      medium: 'text-blue-500 bg-blue-50',
      low: 'text-gray-500 bg-gray-50'
    };
    return colorMap[priority] || colorMap.medium;
  };

  const handleNotificationClick = async (notification) => {
    // Mark as read if unread
    if (!notification.is_read) {
      await markAsRead(notification.id);
    }

    // Navigate to action URL if available
    if (notification.action_url) {
      window.location.href = notification.action_url;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black bg-opacity-25" onClick={onClose} />
      
      {/* Notification Panel */}
      <div className="absolute right-0 top-0 h-full w-full max-w-md bg-white shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
          <div className="flex items-center space-x-2">
            <BellIcon className="h-6 w-6" />
            <h2 className="text-lg font-semibold">Notifications</h2>
            {unreadCount > 0 && (
              <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                {unreadCount}
              </span>
            )}
          </div>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-white hover:bg-opacity-20">
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Filter Tabs */}
        <div className="flex border-b border-gray-200 bg-gray-50">
          {['all', 'unread'].map((filterOption) => (
            <button
              key={filterOption}
              onClick={() => setFilter(filterOption)}
              className={`flex-1 px-4 py-2 text-sm font-medium capitalize transition-colors ${
                filter === filterOption
                  ? 'bg-white text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              {filterOption} {filterOption === 'unread' && unreadCount > 0 && `(${unreadCount})`}
            </button>
          ))}
        </div>

        {/* Actions */}
        {unreadCount > 0 && (
          <div className="p-3 border-b border-gray-100 bg-gray-50">
            <button
              onClick={markAllAsRead}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              Mark all as read
            </button>
          </div>
        )}

        {/* Notifications List */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center p-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            </div>
          ) : notifications.length === 0 ? (
            <div className="text-center p-8 text-gray-500">
              <BellIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No notifications yet</p>
              <p className="text-sm">We'll notify you when something happens!</p>
            </div>
          ) : (
            notifications.map((notification) => {
              const IconComponent = getNotificationIcon(notification.notification_type);
              const priorityColors = getPriorityColor(notification.priority);
              
              return (
                <div
                  key={notification.id}
                  className={`border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                    !notification.is_read ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                  }`}
                >
                  <div className="p-4">
                    <div className="flex items-start space-x-3">
                      {/* Icon */}
                      <div className={`p-2 rounded-full ${priorityColors} flex-shrink-0`}>
                        <IconComponent className="h-4 w-4" />
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <h4 className="text-sm font-medium text-gray-900 truncate">
                            {notification.title}
                          </h4>
                          <div className="flex items-center space-x-1">
                            <span className="text-xs text-gray-500">
                              {notification.time_ago}
                            </span>
                            {!notification.is_read && (
                              <span className="h-2 w-2 bg-blue-500 rounded-full" />
                            )}
                          </div>
                        </div>
                        
                        <p className="text-sm text-gray-600 mt-1">
                          {notification.message}
                        </p>

                        {/* Action Buttons */}
                        <div className="flex items-center space-x-3 mt-2">
                          {notification.action_url && (
                            <button
                              onClick={() => handleNotificationClick(notification)}
                              className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                            >
                              View
                            </button>
                          )}
                          
                          {!notification.is_read && (
                            <button
                              onClick={() => markAsRead(notification.id)}
                              className="text-xs text-green-600 hover:text-green-800 font-medium flex items-center space-x-1"
                            >
                              <CheckIcon className="h-3 w-3" />
                              <span>Mark Read</span>
                            </button>
                          )}
                          
                          <button
                            onClick={() => deleteNotification(notification.id)}
                            className="text-xs text-red-600 hover:text-red-800 font-medium flex items-center space-x-1"
                          >
                            <TrashIcon className="h-3 w-3" />
                            <span>Delete</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={() => {
              window.location.href = '/recommendations';
            }}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-2 px-4 rounded-lg text-sm font-medium hover:from-blue-700 hover:to-purple-700 transition-colors"
          >
            View Recommendations Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};

export default NotificationCenter;