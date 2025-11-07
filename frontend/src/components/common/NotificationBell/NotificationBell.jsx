// frontend/src/components/common/NotificationBell/NotificationBell.jsx
import React, { useState, useEffect } from 'react';
import { Badge, Dropdown, List, Button, Typography, Empty, message } from 'antd';
import { BellOutlined, NotificationOutlined, CheckOutlined, ExclamationOutlined } from '@ant-design/icons';
import { notificationService } from '../../../services/api/notificationService';
import './NotificationBell.css';

const { Text } = Typography;

const NotificationBell = () => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadNotifications();
    
    // Set up real-time updates if available
    const unsubscribe = notificationService.subscribeToNotifications((newNotification) => {
      setNotifications(prev => {
        // Ensure prev is always an array
        const currentNotifications = Array.isArray(prev) ? prev : [];
        // Avoid duplicates
        const exists = currentNotifications.find(n => n.id === newNotification.id);
        if (!exists) {
          return [newNotification, ...currentNotifications];
        }
        return currentNotifications;
      });
      setUnreadCount(prev => prev + 1);
    });

    return unsubscribe;
  }, []);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const data = await notificationService.getNotifications();
      
      // Handle different response formats safely
      let notificationsArray = [];
      let calculatedUnreadCount = 0;
      
      if (Array.isArray(data)) {
        notificationsArray = data;
        calculatedUnreadCount = data.filter(n => !n.read).length;
      } else if (data && Array.isArray(data.results)) {
        notificationsArray = data.results;
        calculatedUnreadCount = data.results.filter(n => !n.read).length;
      } else if (data && data.results) {
        // Handle case where results might be an object instead of array
        notificationsArray = Object.values(data.results);
        calculatedUnreadCount = Object.values(data.results).filter(n => !n.read).length;
      } else {
        // Fallback to empty array
        notificationsArray = [];
        calculatedUnreadCount = 0;
      }
      
      setNotifications(notificationsArray);
      setUnreadCount(calculatedUnreadCount);
    } catch (error) {
      console.error('Failed to load notifications:', error);
      // Set empty state on error
      setNotifications([]);
      setUnreadCount(0);
      message.error('Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await notificationService.markAsRead(notificationId);
      setNotifications(prev => {
        const currentNotifications = Array.isArray(prev) ? prev : [];
        return currentNotifications.map(n => n.id === notificationId ? { ...n, read: true } : n);
      });
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
      message.error('Failed to mark notification as read');
    }
  };

  const markAllAsRead = async () => {
    try {
      await notificationService.markAllAsRead();
      setNotifications(prev => {
        const currentNotifications = Array.isArray(prev) ? prev : [];
        return currentNotifications.map(n => ({ ...n, read: true }));
      });
      setUnreadCount(0);
      message.success('All notifications marked as read');
    } catch (error) {
      console.error('Failed to mark all as read:', error);
      message.error('Failed to mark all notifications as read');
    }
  };

  // Ensure notifications is always an array for rendering
  const safeNotifications = Array.isArray(notifications) ? notifications : [];

  const notificationItems = [
    {
      key: 'header',
      label: (
        <div className="notification-header">
          <Text strong>Notifications</Text>
          {unreadCount > 0 && (
            <Button 
              type="link" 
              size="small" 
              icon={<CheckOutlined />}
              onClick={markAllAsRead}
            >
              Mark all as read
            </Button>
          )}
        </div>
      ),
    },
    {
      key: 'notifications',
      label: (
        <div className="notification-list">
          <List
            dataSource={safeNotifications.slice(0, 10)}
            loading={loading}
            locale={{ 
              emptyText: (
                <Empty 
                  image={<ExclamationOutlined style={{ fontSize: '24px', color: '#d9d9d9' }} />}
                  description="No notifications"
                />
              )
            }}
            renderItem={(notification) => (
              <List.Item 
                className={`notification-item ${notification.read ? 'read' : 'unread'}`}
                onClick={() => !notification.read && markAsRead(notification.id)}
                style={{ cursor: notification.read ? 'default' : 'pointer' }}
              >
                <List.Item.Meta
                  avatar={
                    <div className={`notification-avatar ${notification.read ? 'read' : 'unread'}`}>
                      <NotificationOutlined />
                    </div>
                  }
                  title={
                    <div className="notification-title">
                      {notification.title}
                      {!notification.read && <span className="unread-dot" />}
                    </div>
                  }
                  description={
                    <div>
                      <Text type="secondary" className="notification-message">
                        {notification.message}
                      </Text>
                      <div className="notification-time">
                        {notification.created_at ? (
                          <>
                            {new Date(notification.created_at).toLocaleDateString()} at{' '}
                            {new Date(notification.created_at).toLocaleTimeString([], { 
                              hour: '2-digit', 
                              minute: '2-digit' 
                            })}
                          </>
                        ) : (
                          'Just now'
                        )}
                      </div>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        </div>
      ),
    },
  ];

  return (
    <Dropdown
      menu={{ items: notificationItems }}
      trigger={['click']}
      placement="bottomRight"
      overlayClassName="notification-dropdown"
      onOpenChange={(open) => {
        if (open) {
          loadNotifications(); // Refresh when dropdown opens
        }
      }}
    >
      <Badge count={unreadCount} size="small" offset={[-5, 5]}>
        <Button 
          type="text" 
          icon={<BellOutlined />} 
          className="notification-bell"
          title="Notifications"
        />
      </Badge>
    </Dropdown>
  );
};

export default NotificationBell;