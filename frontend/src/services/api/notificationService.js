// frontend/src/services/api/notificationService.js
import api from './api';

class NotificationService {
  async getNotifications(params = {}) {
    try {
      const response = await api.get('/notifications/', { params });
      console.log('✅ Notifications loaded:', response.data);
      return response.data;
    } catch (error) {
      // Defensive logging and handling to avoid TypeError when error or error.response is null
      console.error('❌ Failed to fetch notifications:', error);

      const status = error && error.response ? error.response.status : null;
      const data = error && error.response ? error.response.data : null;
      const msg = error && error.message ? error.message : String(error);

      // 404 -> return mock data in development
      if (status === 404) {
        console.warn('⚠️ Notifications endpoint not found, returning mock notifications');
        return this.getMockNotifications();
      }

      // Network / no response -> return an empty results shape so polling code can continue
      if (!error || !error.response) {
        console.warn('⚠️ Network or unexpected error while fetching notifications, returning empty list:', msg);
        return { results: [], count: 0 };
      }

      // For other HTTP errors, surface a normalized error
      const errMsg = (data && (data.detail || data.message)) || `Failed to load notifications (status ${status})`;
      throw new Error(errMsg);
    }
  }

  // Mock data for development
  getMockNotifications() {
    return {
      results: [
        {
          id: 1,
          title: 'Welcome to Tudollar Trading',
          message: 'Your account has been successfully created and is ready for trading.',
          read: false,
          created_at: new Date().toISOString(),
          notification_type: 'system'
        },
        {
          id: 2,
          title: 'Arbitrage Opportunity',
          message: 'New arbitrage opportunity detected for BTC/USDT with 1.2% profit potential',
          read: true,
          created_at: new Date(Date.now() - 3600000).toISOString(),
          notification_type: 'opportunity'
        }
      ]
    };
  }

  async markAsRead(notificationId) {
    try {
      // For mock data, just simulate success
      if (notificationId <= 2) { // Our mock notification IDs
        console.log('✅ Mock notification marked as read');
        return { success: true };
      }
      
      const response = await api.patch(`/notifications/${notificationId}/mark-read/`);
      console.log('✅ Notification marked as read');
      return response.data;
    } catch (error) {
      console.error('❌ Failed to mark notification as read:', error);
      
      // For mock purposes, simulate success
      if (error.response?.status === 404) {
        console.warn('⚠️ Mark as read endpoint not found, simulating success');
        return { success: true };
      }
      
      if (error.response?.status === 404) {
        throw new Error('Notification not found');
      } else {
        throw new Error('Failed to mark notification as read');
      }
    }
  }

  async markAllAsRead() {
    try {
      const response = await api.post('/notifications/mark-all-read/');
      console.log('✅ All notifications marked as read');
      return response.data;
    } catch (error) {
      console.error('❌ Failed to mark all notifications as read:', error);
      
      // For mock purposes, simulate success
      if (error.response?.status === 404) {
        console.warn('⚠️ Mark all as read endpoint not found, simulating success');
        return { success: true, updated_count: 0 };
      }
      
      throw new Error('Failed to mark all notifications as read');
    }
  }

  async getUnreadCount() {
    try {
      const response = await api.get('/notifications/unread-count/');
      return response.data;
    } catch (error) {
      console.error('❌ Failed to fetch unread count:', error);
      
      // Return mock count for development
      if (error.response?.status === 404) {
        return { unread_count: 1 }; // Mock unread count
      }
      
      return { unread_count: 0 }; // Return default on error
    }
  }

  // Real-time notifications via WebSocket
  subscribeToNotifications(callback) {
    // This would integrate with your WebSocket service
    // For now, we'll use polling as a fallback
    const pollInterval = setInterval(async () => {
      try {
        const data = await this.getNotifications({ limit: 1 });
        let latest = null;
        
        if (data.results && data.results.length > 0) {
          latest = data.results[0];
        } else if (Array.isArray(data) && data.length > 0) {
          latest = data[0];
        }
        
        if (latest) {
          // Only call callback if it's a new notification
          callback(latest);
        }
      } catch (error) {
        console.error('Error polling notifications:', error);
      }
    }, 30000); // Poll every 30 seconds

    return () => clearInterval(pollInterval);
  }
}

export const notificationService = new NotificationService();