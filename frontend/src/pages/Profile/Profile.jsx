// frontend/src/pages/Profile/Profile.jsx
import React, { useState, useEffect } from 'react';
import {
  Card,
  Typography,
  Avatar,
  Button,
  Form,
  Input,
  Select,
  Row,
  Col,
  Divider,
  Tag,
  Skeleton,
  Alert,
  Space,
  Modal,
  message
} from 'antd';
import {
  UserOutlined,
  MailOutlined,
  PhoneOutlined,
  SafetyOutlined,
  EditOutlined,
  SaveOutlined,
  CloseOutlined,
  KeyOutlined,
  HistoryOutlined,
  SettingOutlined
} from '@ant-design/icons';
import { userService } from '../../services/api/userService';
import { authService } from '../../services/api/authService';
import './Profile.css';

const { Title, Text } = Typography;
const { Option } = Select;

const Profile = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [form] = Form.useForm();
  const [saveLoading, setSaveLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadUserProfile();
  }, []);

  const loadUserProfile = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Try to get profile from backend first
      try {
        const profileData = await userService.getUserProfile();
        setUser(profileData);
      } catch (profileError) {
        console.warn('Profile endpoint not available, using auth service:', profileError);
        // Fallback to auth service
        const currentUser = authService.getCurrentUser();
        if (currentUser) {
          setUser({
            ...currentUser,
            phone: currentUser.phone || 'Not provided',
            user_type: currentUser.user_type || 'trader',
            date_joined: currentUser.date_joined || new Date().toISOString()
          });
        }
      }
    } catch (error) {
      console.error('Failed to load user profile:', error);
      setError('Failed to load profile data');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    if (user) {
      form.setFieldsValue({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        phone: user.phone || '',
        username: user.username || ''
      });
      setEditing(true);
      setError('');
      setSuccess('');
    }
  };

  const handleCancel = () => {
    setEditing(false);
    form.resetFields();
    setError('');
    setSuccess('');
  };

  const handleSave = async (values) => {
    try {
      setSaveLoading(true);
      setError('');
      setSuccess('');

      // Update profile via service
      await userService.updateUserProfile(values);
      
      // Update local state
      setUser(prev => ({
        ...prev,
        ...values
      }));
      
      setSuccess('Profile updated successfully');
      setEditing(false);
      
      // Show success message
      message.success('Profile updated successfully');
      
    } catch (error) {
      console.error('Failed to update profile:', error);
      setError(error.message || 'Failed to update profile');
      message.error(error.message || 'Failed to update profile');
    } finally {
      setSaveLoading(false);
    }
  };

  const handleChangePassword = () => {
    Modal.info({
      title: 'Change Password',
      content: 'Password change functionality will be implemented soon.',
      okText: 'OK'
    });
  };

  const getInitials = (user) => {
    if (!user) return 'U';
    const first = user.first_name?.[0] || '';
    const last = user.last_name?.[0] || '';
    return (first + last).toUpperCase() || user.username?.[0]?.toUpperCase() || 'U';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="profile-page">
        <div className="profile-header">
          <Skeleton active paragraph={{ rows: 1 }} />
        </div>
        <Card className="profile-card">
          <Skeleton active />
        </Card>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="profile-page">
        <Alert
          message="Profile Not Available"
          description="Unable to load user profile. Please try again later."
          type="error"
          showIcon
        />
      </div>
    );
  }

  return (
    <div className="profile-page">
      <div className="profile-header">
        <Title level={2}>User Profile</Title>
        <div className="profile-subtitle">
          Manage your account information and preferences
        </div>
      </div>

      {error && (
        <Alert
          message="Error"
          description={error}
          type="error"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {success && (
        <Alert
          message="Success"
          description={success}
          type="success"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      <Card className="profile-card">
        <div className="profile-avatar-section">
          <div className="profile-avatar">
            {getInitials(user)}
          </div>
          <div className="profile-info">
            <div className="profile-name">
              {user.first_name && user.last_name 
                ? `${user.first_name} ${user.last_name}`
                : user.username
              }
            </div>
            <div className="profile-email">{user.email}</div>
            <div>
              <Tag color="blue" className="profile-badge profile-tag-trader">
                {user.user_type?.toUpperCase() || 'TRADER'}
              </Tag>
              <Tag 
                color={user.is_verified ? 'green' : 'orange'} 
                className={`profile-badge ${user.is_verified ? 'profile-tag-verified' : 'profile-tag-unverified'}`}
              >
                {user.is_verified ? 'Verified' : 'Unverified'}
              </Tag>
            </div>
          </div>
          {!editing && (
            <Button 
              type="primary" 
              icon={<EditOutlined />}
              onClick={handleEdit}
            >
              Edit Profile
            </Button>
          )}
        </div>

        <Divider className="profile-divider" />

        <div className="profile-content">
          {editing ? (
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSave}
              className="profile-form"
            >
              <Row gutter={16}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="First Name"
                    name="first_name"
                    rules={[
                      { required: true, message: 'Please enter your first name' }
                    ]}
                  >
                    <Input prefix={<UserOutlined />} placeholder="Enter first name" />
                  </Form.Item>
                </Col>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="Last Name"
                    name="last_name"
                    rules={[
                      { required: true, message: 'Please enter your last name' }
                    ]}
                  >
                    <Input prefix={<UserOutlined />} placeholder="Enter last name" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                label="Email"
                name="email"
                rules={[
                  { required: true, message: 'Please enter your email' },
                  { type: 'email', message: 'Please enter a valid email' }
                ]}
              >
                <Input prefix={<MailOutlined />} placeholder="Enter email" />
              </Form.Item>

              <Form.Item
                label="Phone"
                name="phone"
              >
                <Input prefix={<PhoneOutlined />} placeholder="Enter phone number" />
              </Form.Item>

              <Form.Item
                label="Username"
                name="username"
                rules={[
                  { required: true, message: 'Please enter your username' }
                ]}
              >
                <Input prefix={<UserOutlined />} placeholder="Enter username" />
              </Form.Item>

              <div className="profile-action-buttons">
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  icon={<SaveOutlined />}
                  loading={saveLoading}
                >
                  Save Changes
                </Button>
                <Button 
                  icon={<CloseOutlined />}
                  onClick={handleCancel}
                  disabled={saveLoading}
                >
                  Cancel
                </Button>
              </div>
            </Form>
          ) : (
            <>
              <div className="profile-section">
                <div className="profile-section-title">
                  <UserOutlined />
                  Personal Information
                </div>
                <div className="profile-info-grid">
                  <div className="profile-info-item">
                    <div className="profile-info-label">Username</div>
                    <div className="profile-info-value">{user.username}</div>
                  </div>
                  <div className="profile-info-item">
                    <div className="profile-info-label">Email</div>
                    <div className="profile-info-value">{user.email}</div>
                  </div>
                  <div className="profile-info-item">
                    <div className="profile-info-label">Phone</div>
                    <div className="profile-info-value">{user.phone || 'Not provided'}</div>
                  </div>
                  <div className="profile-info-item">
                    <div className="profile-info-label">User Type</div>
                    <div className="profile-info-value">
                      <Tag color="blue" className="profile-tag-trader">{user.user_type || 'trader'}</Tag>
                    </div>
                  </div>
                  <div className="profile-info-item">
                    <div className="profile-info-label">Account Status</div>
                    <div className="profile-info-value">
                      <Tag 
                        className={user.is_verified ? 'profile-tag-verified' : 'profile-tag-unverified'}
                      >
                        {user.is_verified ? 'Verified' : 'Unverified'}
                      </Tag>
                    </div>
                  </div>
                  <div className="profile-info-item">
                    <div className="profile-info-label">Member Since</div>
                    <div className="profile-info-value">{formatDate(user.date_joined)}</div>
                  </div>
                </div>
              </div>

              <Divider className="profile-divider" />

              <div className="profile-section">
                <div className="profile-section-title">
                  <SettingOutlined />
                  Quick Actions
                </div>
                <div className="profile-action-buttons">
                  <Button 
                    type="primary" 
                    icon={<EditOutlined />}
                    onClick={handleEdit}
                  >
                    Edit Profile
                  </Button>
                  <Button 
                    icon={<KeyOutlined />}
                    onClick={handleChangePassword}
                  >
                    Change Password
                  </Button>
                  <Button 
                    icon={<SafetyOutlined />}
                    onClick={() => message.info('Security settings coming soon')}
                  >
                    Security Settings
                  </Button>
                  <Button 
                    icon={<HistoryOutlined />}
                    onClick={() => message.info('Activity log coming soon')}
                  >
                    View Activity
                  </Button>
                </div>
              </div>

              <Divider className="profile-divider" />

              <div className="profile-section">
                <div className="profile-section-title">
                  <SafetyOutlined />
                  Account Statistics
                </div>
                <div className="profile-stats-grid">
                  <div className="profile-stat-card">
                    <div className="profile-stat-value">0</div>
                    <div className="profile-stat-label">API Keys</div>
                  </div>
                  <div className="profile-stat-card">
                    <div className="profile-stat-value">0</div>
                    <div className="profile-stat-label">Active Trades</div>
                  </div>
                  <div className="profile-stat-card">
                    <div className="profile-stat-value">0</div>
                    <div className="profile-stat-label">Total Trades</div>
                  </div>
                  <div className="profile-stat-card">
                    <div className="profile-stat-value">-</div>
                    <div className="profile-stat-label">Success Rate</div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </Card>
    </div>
  );
};

export default Profile;