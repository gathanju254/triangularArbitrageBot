// frontend/src/components/common/ErrorBoundary/ErrorBoundary.jsx
import React from 'react';
import { Result, Button, Space, Typography, Alert, Collapse } from 'antd';
import { HomeOutlined, ReloadOutlined, BugOutlined, CodeOutlined } from '@ant-design/icons';

const { Text } = Typography;
const { Panel } = Collapse;

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null,
      errorInfo: null,
      errorType: null
    };
  }

  static getDerivedStateFromError(error) {
    return { 
      hasError: true, 
      error,
      errorType: this.classifyError(error)
    };
  }

  static classifyError(error) {
    if (!error) return 'unknown';
    
    const errorMessage = error.toString();
    
    // Common error patterns
    if (errorMessage.includes('rawData.some is not a function')) {
      return 'table_data_error';
    } else if (errorMessage.includes('Cannot read properties') || errorMessage.includes('Cannot read')) {
      return 'null_reference';
    } else if (errorMessage.includes('Network Error') || errorMessage.includes('Failed to fetch')) {
      return 'network_error';
    } else if (errorMessage.includes('Unexpected token') || errorMessage.includes('SyntaxError')) {
      return 'syntax_error';
    } else if (errorMessage.includes('is not a function')) {
      return 'type_error';
    } else if (errorMessage.includes('Maximum update depth exceeded')) {
      return 'infinite_loop';
    }
    
    return 'unknown';
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    
    const errorType = ErrorBoundary.classifyError(error);
    
    this.setState({ 
      errorInfo,
      errorType 
    });
    
    // Handle specific error types
    this.handleSpecificErrors(error, errorType);
    
    // You could also send this to an error reporting service
    // this.logErrorToService(error, errorInfo, errorType);
  }

  handleSpecificErrors(error, errorType) {
    switch (errorType) {
      case 'table_data_error':
        console.error('Table data error - likely non-array data passed to table component');
        console.error('Suggested fix: Ensure dataSource prop is always an array');
        break;
      case 'null_reference':
        console.error('Null reference error - accessing property of null/undefined');
        console.error('Suggested fix: Add null checks before accessing properties');
        break;
      case 'network_error':
        console.error('Network error - API call failed or server unreachable');
        console.error('Suggested fix: Check internet connection and server status');
        break;
      case 'syntax_error':
        console.error('Syntax error - invalid JavaScript syntax');
        console.error('Suggested fix: Check for syntax errors in recent changes');
        break;
      case 'infinite_loop':
        console.error('Infinite loop detected - component re-rendering excessively');
        console.error('Suggested fix: Check useEffect dependencies and state updates');
        break;
      default:
        console.error('Unknown error type - check browser console for details');
    }
  }

  handleReset = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null,
      errorType: null 
    });
    window.location.reload();
  };

  handleGoHome = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null,
      errorType: null 
    });
    window.location.href = '/';
  };

  handleClearStorage = () => {
    // Clear problematic data that might be causing issues
    localStorage.removeItem('apiKeys');
    localStorage.removeItem('userData');
    sessionStorage.clear();
    this.handleReset();
  };

  // Optional: Log errors to external service
  logErrorToService = (error, errorInfo, errorType) => {
    // Example: Send to Sentry, LogRocket, etc.
    const errorData = {
      error: error.toString(),
      errorType,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent
    };
    
    console.log('Would send to error service:', errorData);
    // Your error reporting service integration here
  };

  getErrorDescription() {
    const { errorType, error } = this.state;
    
    const descriptions = {
      table_data_error: {
        title: 'Data Format Error',
        description: 'There was an issue with the data format in a table component. This usually happens when non-array data is passed where an array is expected.',
        suggestion: 'Try reloading the page. If the problem persists, clear your browser data for this site.'
      },
      null_reference: {
        title: 'Reference Error',
        description: 'The application tried to access a property that doesn\'t exist.',
        suggestion: 'This might be due to incomplete data loading. Try reloading the page.'
      },
      network_error: {
        title: 'Network Connection Issue',
        description: 'Unable to connect to the server or fetch required data.',
        suggestion: 'Check your internet connection and try again. If the problem continues, the server might be temporarily unavailable.'
      },
      syntax_error: {
        title: 'Syntax Error',
        description: 'There\'s a syntax error in the application code.',
        suggestion: 'This is likely a development issue. Try clearing your browser cache or contact support if the problem persists.'
      },
      type_error: {
        title: 'Type Error',
        description: 'A function was called on an incompatible type.',
        suggestion: 'Try reloading the application. If the error continues, clear your browser storage.'
      },
      infinite_loop: {
        title: 'Application Loop',
        description: 'The application entered an infinite rendering loop.',
        suggestion: 'The page has been stopped to prevent browser freezing. Try reloading with cleared cache.'
      },
      unknown: {
        title: 'Unexpected Error',
        description: 'An unexpected error occurred in the application.',
        suggestion: 'Try reloading the page. If the problem continues, contact support.'
      }
    };

    return descriptions[errorType] || descriptions.unknown;
  }

  renderErrorDetails() {
    const { error, errorInfo, errorType } = this.state;
    const errorDesc = this.getErrorDescription();

    return (
      <Space direction="vertical" style={{ width: '100%', maxWidth: '800px' }}>
        <Alert
          message={errorDesc.title}
          description={errorDesc.description}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
        
        <Text strong>Suggested Solution:</Text>
        <Text type="secondary">{errorDesc.suggestion}</Text>

        {this.props.showDetails && (
          <Collapse size="small" style={{ marginTop: 16 }}>
            <Panel header="Technical Details" key="1" icon={<CodeOutlined />}>
              <div style={{ fontFamily: 'monospace', fontSize: '12px' }}>
                <Text strong>Error Type: </Text>
                <Text type="secondary">{errorType}</Text>
                <br />
                <Text strong>Error Message: </Text>
                <Text type="secondary">{error?.toString()}</Text>
                <br />
                <Text strong>Component Stack: </Text>
                <pre style={{ fontSize: '10px', whiteSpace: 'pre-wrap' }}>
                  {errorInfo?.componentStack}
                </pre>
              </div>
            </Panel>
          </Collapse>
        )}
      </Space>
    );
  }

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
            subTitle={this.renderErrorDetails()}
            extra={[
              <Button type="primary" key="home" icon={<HomeOutlined />} onClick={this.handleGoHome}>
                Back Home
              </Button>,
              <Button key="reset" icon={<ReloadOutlined />} onClick={this.handleReset}>
                Reload Page
              </Button>,
              <Button 
                key="clear" 
                icon={<BugOutlined />} 
                onClick={this.handleClearStorage}
                danger
              >
                Clear Data & Reload
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
  showDetails: process.env.NODE_ENV === 'development' // Show details in development by default
};

export default ErrorBoundary;