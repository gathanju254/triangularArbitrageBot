// frontend/src/pages/Register/Register.jsx
import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, message, Divider } from 'antd';
import { 
  UserOutlined, 
  LockOutlined, 
  MailOutlined, 
  PhoneOutlined,
  RocketOutlined,
  EyeTwoTone,
  EyeInvisibleOutlined 
} from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { TradingLoader } from '../../components/common/LoadingSpinner/LoadingSpinner';
import { ROUTES } from '../../constants/routes';
import './Register.css';

const { Title, Text } = Typography;

const Register = () => {
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { register } = useAuth();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      await register(values);
      message.success('Registration successful! Welcome to TAB Trading.');
      navigate(ROUTES.DASHBOARD);
    } catch (error) {
      message.error(error.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const validateConfirmPassword = ({ getFieldValue }) => ({
    validator(_, value) {
      if (!value || getFieldValue('password') === value) {
        return Promise.resolve();
      }
      return Promise.reject(new Error('The two passwords do not match!'));
    },
  });

  if (loading) {
    return (
      <div className="register-container">
        <TradingLoader text="Creating your account..." fullScreen={false} />
      </div>
    );
  }

  return (
    <div className="register-container">
      <Card className="register-card">
        <div className="register-header">
          <RocketOutlined className="register-logo" />
          <Title level={2} className="register-title">
            Create Your Account
          </Title>
          <Text type="secondary" className="register-subtitle">
            Start your triangular arbitrage journey
          </Text>
        </div>

        <Form
          form={form}
          name="register"
          onFinish={onFinish}
          autoComplete="off"
          className="register-form"
          size="large"
        >

          {/* Username */}
          <Form.Item
            name="username"
            rules={[
              { required: true, message: 'Please input your username!' },
              { min: 3, message: 'Username must be at least 3 characters!' },
              { max: 20, message: 'Username must be less than 20 characters!' }
            ]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="Username" 
              disabled={loading}
            />
          </Form.Item>

          {/* Email */}
          <Form.Item
            name="email"
            rules={[
              { required: true, message: 'Please input your email!' },
              { type: 'email', message: 'Please enter a valid email!' }
            ]}
          >
            <Input 
              prefix={<MailOutlined />} 
              placeholder="Email" 
              disabled={loading}
            />
          </Form.Item>

          {/* Phone Number */}
          <Form.Item
            name="phone"
            rules={[
              { required: true, message: 'Phone number is required!' },
              { min: 10, message: 'Phone number must be valid!' },
              { max: 15, message: 'Phone number is too long!' }
            ]}
          >
            <Input 
              prefix={<PhoneOutlined />} 
              placeholder="Phone Number (e.g., +1234567890)" 
              disabled={loading}
            />
          </Form.Item>

          {/* First Name */}
          <Form.Item
            name="firstName"
            rules={[
              { required: true, message: 'Please input your first name!' },
              { min: 2, message: 'First name must be at least 2 characters!' }
            ]}
          >
            <Input 
              placeholder="First Name" 
              disabled={loading}
            />
          </Form.Item>

          {/* Last Name */}
          <Form.Item
            name="lastName"
            rules={[
              { required: true, message: 'Please input your last name!' },
              { min: 2, message: 'Last name must be at least 2 characters!' }
            ]}
          >
            <Input 
              placeholder="Last Name" 
              disabled={loading}
            />
          </Form.Item>

          {/* Password */}
          <Form.Item
            name="password"
            rules={[
              { required: true, message: 'Please input your password!' },
              { min: 6, message: 'Password must be at least 6 characters!' },
              { pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, message: 'Password must contain uppercase, lowercase, and number!' }
            ]}
          >
            <Input.Password 
              prefix={<LockOutlined />} 
              placeholder="Password" 
              disabled={loading}
              iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
            />
          </Form.Item>

          {/* Confirm Password */}
          <Form.Item
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: 'Please confirm your password!' },
              validateConfirmPassword
            ]}
          >
            <Input.Password 
              prefix={<LockOutlined />} 
              placeholder="Confirm Password" 
              disabled={loading}
              iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
            />
          </Form.Item>

          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading} 
              block 
              className="register-button"
            >
              {loading ? 'Creating Account...' : 'Create Account'}
            </Button>
          </Form.Item>
        </Form>

        <Divider plain>Or</Divider>

        <div className="register-footer">
          <Text type="secondary">
            Already have an account?{' '}
            <Link to={ROUTES.LOGIN} className="login-link">
              Sign in here
            </Link>
          </Text>
        </div>
      </Card>
    </div>
  );
};

export default Register;