// frontend/src/components/common/ErrorBoundary/ErrorBoundary.jsx
import React from 'react';
import { Result, Button, Space, Typography } from 'antd';
import { HomeOutlined, ReloadOutlined, BugOutlined } from '@ant-design/icons';

const { Text } = Typography;

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null,
      errorInfo: null 
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    this.setState({ errorInfo });
    
    // You could also send this to an error reporting service
    // this.logErrorToService(error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  handleGoHome = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.href = '/';
  };

  // Optional: Log errors to external service
  logErrorToService = (error, errorInfo) => {
    // Example: Send to Sentry, LogRocket, etc.
    // console.log('Would send to error service:', error, errorInfo);
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ 
          padding: '50px', 
          minHeight: '100vh', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          backgroundColor: '#f5f5f5'
        }}>
          <Result
            status="500"
            title="Something went wrong"
            subTitle={
              <Space direction="vertical">
                <Text>Sorry, something went wrong. Please try again.</Text>
                {this.props.showDetails && this.state.error && (
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    Error: {this.state.error.toString()}
                  </Text>
                )}
              </Space>
            }
            extra={[
              <Button type="primary" key="home" icon={<HomeOutlined />} onClick={this.handleGoHome}>
                Back Home
              </Button>,
              <Button key="reset" icon={<ReloadOutlined />} onClick={this.handleReset}>
                Reload Page
              </Button>,
            ]}
          />
        </div>
      );
    }

    return this.props.children;
  }
}

// Default props
ErrorBoundary.defaultProps = {
  showDetails: false
};

export default ErrorBoundary;