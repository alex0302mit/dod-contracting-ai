import { useEffect, useState } from 'react';
import { notificationsApi, type Notification } from '@/services/api';

export function useNotifications(userId: string | null) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!userId) {
      setNotifications([]);
      setUnreadCount(0);
      setLoading(false);
      return;
    }

    fetchNotifications();

    // Poll for updates every 30 seconds (replacing Supabase real-time subscription)
    const intervalId = setInterval(fetchNotifications, 30000);

    return () => {
      clearInterval(intervalId);
    };
  }, [userId]);

  const fetchNotifications = async () => {
    if (!userId) return;

    try {
      setLoading(true);
      const response = await notificationsApi.list();
      setNotifications(response.notifications || []);
      setUnreadCount((response.notifications || []).filter((n) => !n.is_read).length);
    } catch (err) {
      console.error('Error fetching notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (notificationId: string) => {
    try {
      await notificationsApi.markAsRead(notificationId);
      await fetchNotifications();
    } catch (error) {
      console.error('Error marking notification as read:', error);
      throw error;
    }
  };

  const markAllAsRead = async () => {
    if (!userId) return;

    try {
      await notificationsApi.markAllAsRead();
      await fetchNotifications();
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
      throw error;
    }
  };

  const deleteNotification = async (notificationId: string) => {
    try {
      await notificationsApi.delete(notificationId);
      await fetchNotifications();
    } catch (error) {
      console.error('Error deleting notification:', error);
      throw error;
    }
  };

  return {
    notifications,
    unreadCount,
    loading,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    refresh: fetchNotifications,
  };
}
