import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import io from 'socket.io-client';

const useNotifications = () => {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);

  // Initialize WebSocket connection for real-time notifications
  useEffect(() => {
    if (user) {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const socketUrl = backendUrl.replace('http', 'ws').replace('https', 'wss');
      
      const newSocket = io(socketUrl, {
        auth: {
          token: localStorage.getItem('token')
        },
        transports: ['websocket']
      });

      newSocket.on('connect', () => {
        console.log('Connected to notification service');
        setConnected(true);
      });

      newSocket.on('disconnect', () => {
        console.log('Disconnected from notification service');
        setConnected(false);
      });

      // Listen for real-time notifications
      newSocket.on('notification', (notificationData) => {
        console.log('Real-time notification received:', notificationData);
        
        // Add to notifications list if it's a full notification object
        if (notificationData.data) {
          setNotifications(prev => [notificationData.data, ...prev]);
          setUnreadCount(prev => prev + 1);
        }
      });

      setSocket(newSocket);

      return () => {
        newSocket.close();
        setSocket(null);
        setConnected(false);
      };
    }
  }, [user]);

  // Fetch notifications
  const fetchNotifications = useCallback(async (options = {}) => {
    if (!user) return;

    try {
      setLoading(true);
      const params = {
        limit: options.limit || 20,
        offset: options.offset || 0,
        ...options
      };

      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/notifications/`,
        { params }
      );

      if (options.offset === 0) {
        setNotifications(response.data);
      } else {
        setNotifications(prev => [...prev, ...response.data]);
      }
    } catch (error) {
      console.error('Error fetching notifications:', error);
    } finally {
      setLoading(false);
    }
  }, [user]);

  // Fetch unread count
  const fetchUnreadCount = useCallback(async () => {
    if (!user) return;

    try {
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/notifications/count`
      );
      setUnreadCount(response.data.unread_count);
    } catch (error) {
      console.error('Error fetching unread count:', error);
    }
  }, [user]);

  // Mark notification as read
  const markAsRead = async (notificationId) => {
    try {
      await axios.put(
        `${process.env.REACT_APP_BACKEND_URL}/api/notifications/${notificationId}`,
        { is_read: true }
      );

      // Update local state
      setNotifications(prev =>
        prev.map(n =>
          n.id === notificationId ? { ...n, is_read: true } : n
        )
      );
      
      // Update unread count
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  // Mark all as read
  const markAllAsRead = async () => {
    try {
      await axios.put(
        `${process.env.REACT_APP_BACKEND_URL}/api/notifications/mark-all-read`
      );

      // Update local state
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('Error marking all as read:', error);
    }
  };

  // Delete notification
  const deleteNotification = async (notificationId) => {
    try {
      await axios.delete(
        `${process.env.REACT_APP_BACKEND_URL}/api/notifications/${notificationId}`
      );

      // Update local state
      const deletedNotification = notifications.find(n => n.id === notificationId);
      setNotifications(prev => prev.filter(n => n.id !== notificationId));
      
      // Update unread count if deleted notification was unread
      if (deletedNotification && !deletedNotification.is_read) {
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (error) {
      console.error('Error deleting notification:', error);
    }
  };

  // Create notification (for testing or admin use)
  const createNotification = async (notificationData) => {
    try {
      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/api/notifications/`,
        notificationData
      );
      return response.data;
    } catch (error) {
      console.error('Error creating notification:', error);
      throw error;
    }
  };

  // Send quick notifications
  const sendMatchFoundNotification = async (matchData) => {
    try {
      await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/api/notifications/quick/match-found`,
        matchData
      );
    } catch (error) {
      console.error('Error sending match notification:', error);
    }
  };

  const sendSessionReminderNotification = async (sessionData) => {
    try {
      await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/api/notifications/quick/session-reminder`,
        sessionData
      );
    } catch (error) {
      console.error('Error sending session reminder:', error);
    }
  };

  const sendAchievementNotification = async (achievementData) => {
    try {
      await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/api/notifications/quick/achievement-earned`,
        achievementData
      );
    } catch (error) {
      console.error('Error sending achievement notification:', error);
    }
  };

  const sendMessageNotification = async (messageData) => {
    try {
      await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/api/notifications/quick/message-received`,
        messageData
      );
    } catch (error) {
      console.error('Error sending message notification:', error);
    }
  };

  // Initialize data on mount
  useEffect(() => {
    if (user) {
      fetchNotifications();
      fetchUnreadCount();
    }
  }, [user, fetchNotifications, fetchUnreadCount]);

  return {
    // State
    notifications,
    unreadCount,
    loading,
    connected,

    // Actions
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    createNotification,

    // Quick notifications
    sendMatchFoundNotification,
    sendSessionReminderNotification,
    sendAchievementNotification,
    sendMessageNotification,

    // Utilities
    refresh: () => {
      fetchNotifications();
      fetchUnreadCount();
    }
  };
};

export default useNotifications;