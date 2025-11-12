// frontend/src/components/settings/ApiKeys/ApiKeys.jsx
import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Tag,
  Space,
  Typography,
  Alert,
  Card,
  Popconfirm,
  message,
  Tooltip,
  Dropdown,
  Menu
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  MoreOutlined,
  CheckOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { userService } from '../../../services/api/userService';
import './ApiKeys.css';

const { Title, Text } = Typography;
const { Option } = Select;

const ApiKeys = ({ onSettingsChange }) => {
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState({});
  const [error, setError] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingKey, setEditingKey] = useState(null);
  const [form] = Form.useForm();
  const [showSecrets, setShowSecrets] = useState({});

  const EXCHANGE_OPTIONS = [
    { value: 'binance', label: 'Binance' },
    { value: 'coinbase', label: 'Coinbase' },
    { value: 'kraken', label: 'Kraken' },
    { value: 'kucoin', label: 'KuCoin' },
    { value: 'okx', label: 'OKX' },
    { value: 'huobi', label: 'Huobi' },
    { value: 'bybit', label: 'Bybit' }
  ];

  // Exchange-specific requirements
  const EXCHANGE_REQUIREMENTS = {
    okx: { requiresPassphrase: true },
    coinbase: { requiresPassphrase: true },
    kucoin: { requiresPassphrase: true }
  };

  useEffect(() => {
    loadApiKeys();
  }, []);

  const loadApiKeys = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await userService.getApiKeys();
      console.log('API Keys Response:', response);
      
      // Handle different response structures
      let keysArray = [];
      if (Array.isArray(response)) {
        keysArray = response;
      } else if (response && Array.isArray(response.api_keys)) {
        keysArray = response.api_keys;
      } else if (response && Array.isArray(response.data)) {
        keysArray = response.data;
      } else if (response && typeof response === 'object') {
        // Try to extract keys from various possible structures
        keysArray = response.api_keys || response.data || [];
      }
      
      // Ensure we always have an array and format consistently
      const formattedKeys = Array.isArray(keysArray) ? keysArray.map(key => ({
        id: key.id,
        exchange: key.exchange,
        label: key.label || '',
        api_key: key.api_key || '',
        secret_key: key.secret_key || '',
        passphrase: key.passphrase || '',
        is_active: key.is_active !== undefined ? key.is_active : true,
        is_validated: key.is_validated !== undefined ? key.is_validated : false,
        created_at: key.created_at,
        last_used: key.last_used,
        last_validated: key.last_validated
      })) : [];
      
      console.log(`✅ Loaded ${formattedKeys.length} API keys`);
      setApiKeys(formattedKeys);
      
    } catch (error) {
      console.error('Failed to load API keys:', error);
      setError('Failed to load API keys: ' + error.message);
      setApiKeys([]); // Fallback to empty array
    } finally {
      setLoading(false);
    }
  };

  const handleAddKey = () => {
    setEditingKey(null);
    form.resetFields();
    setModalVisible(true);
    onSettingsChange(true);
  };

  const handleEditKey = (key) => {
    setEditingKey(key);
    form.setFieldsValue({
      exchange: key.exchange,
      label: key.label,
      api_key: key.api_key,
      secret_key: key.secret_key,
      passphrase: key.passphrase,
      is_active: key.is_active
    });
    setModalVisible(true);
    onSettingsChange(true);
  };

  const handleDeleteKey = async (keyId) => {
    try {
      await userService.deleteApiKey(keyId);
      message.success('API key deleted successfully');
      loadApiKeys();
    } catch (error) {
      message.error('Failed to delete API key: ' + error.message);
    }
  };

  const handleValidateKey = async (keyId) => {
    setValidating(prev => ({ ...prev, [keyId]: true }));
    try {
      // Call the actual validation endpoint
      const result = await userService.validateApiKey(keyId);
      
      if (result.valid) {
        // Update the key validation status locally
        setApiKeys(prev => prev.map(key => 
          key.id === keyId 
            ? { 
                ...key, 
                is_validated: true, 
                last_validated: new Date().toISOString(),
                permissions: result.permissions || key.permissions
              }
            : key
        ));
        message.success(`API key validated successfully for ${result.exchange}`);
      } else {
        // Update as invalidated
        setApiKeys(prev => prev.map(key => 
          key.id === keyId 
            ? { 
                ...key, 
                is_validated: false,
                last_validated: new Date().toISOString()
              }
            : key
        ));
        message.error(`API key validation failed: ${result.message || 'Unknown error'}`);
      }
      
      return result;
    } catch (error) {
      console.error('❌ API key validation error:', error);
      message.error('Failed to validate API key: ' + (error.message || 'Unknown error'));
      throw error;
    } finally {
      setValidating(prev => ({ ...prev, [keyId]: false }));
    }
  };

  const handleSubmit = async (values) => {
    try {
      // Enhanced validation for exchanges that require passphrase
      const exchange = values.exchange?.toLowerCase();
      const requirements = EXCHANGE_REQUIREMENTS[exchange];
      
      if (requirements?.requiresPassphrase && !values.passphrase?.trim()) {
        message.error(`${exchange.toUpperCase()} requires a passphrase for API authentication`);
        return;
      }

      if (editingKey) {
        await userService.updateApiKey(editingKey.id, values);
        message.success('API key updated successfully');
      } else {
        await userService.addApiKey(values);
        message.success('API key added successfully');
      }
      setModalVisible(false);
      form.resetFields();
      loadApiKeys();
      onSettingsChange(false);
    } catch (error) {
      console.error('❌ Failed to save API key:', error);
      message.error('Failed to save API key: ' + error.message);
    }
  };

  const toggleSecretVisibility = (keyId, field) => {
    setShowSecrets(prev => ({
      ...prev,
      [keyId]: {
        ...prev[keyId],
        [field]: !prev[keyId]?.[field]
      }
    }));
  };

  const maskSecret = (secret, show = false) => {
    if (!secret) return '';
    if (show) return secret;
    return '•'.repeat(Math.min(secret.length, 12));
  };

  const getValidationStatus = (key) => {
    if (!key.is_validated) {
      return { status: 'error', text: 'Not Validated', icon: <CloseCircleOutlined /> };
    }
    
    // Check if validation is recent (within 7 days)
    if (key.last_validated) {
      const lastValidated = new Date(key.last_validated);
      const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
      if (lastValidated < sevenDaysAgo) {
        return { status: 'warning', text: 'Needs Revalidation', icon: <CloseCircleOutlined /> };
      }
    }
    
    return { status: 'success', text: 'Validated', icon: <CheckCircleOutlined /> };
  };

  const createActionMenu = (record) => {
    const validationStatus = getValidationStatus(record);
    const isCurrentlyValidating = validating[record.id];
    
    return (
      <Menu>
        <Menu.Item 
          key="edit" 
          icon={<EditOutlined />}
          onClick={() => handleEditKey(record)}
        >
          Edit
        </Menu.Item>
        
        <Menu.Item 
          key="validate" 
          icon={isCurrentlyValidating ? <ReloadOutlined spin /> : validationStatus.icon}
          onClick={() => handleValidateKey(record.id)}
          disabled={isCurrentlyValidating}
        >
          {isCurrentlyValidating ? 'Validating...' : `Validate ${validationStatus.text}`}
        </Menu.Item>
        
        <Menu.Divider />
        
        <Menu.Item 
          key="delete" 
          icon={<DeleteOutlined />}
          danger
        >
          <Popconfirm
            title="Delete API Key"
            description="Are you sure you want to delete this API key?"
            onConfirm={() => handleDeleteKey(record.id)}
            okText="Yes"
            cancelText="No"
          >
            Delete
          </Popconfirm>
        </Menu.Item>
      </Menu>
    );
  };

  const getPassphraseTooltip = (exchange) => {
    const requirements = EXCHANGE_REQUIREMENTS[exchange?.toLowerCase()];
    if (requirements?.requiresPassphrase) {
      return `Required for ${exchange.toUpperCase()}`;
    }
    return 'Optional passphrase for exchanges that require it';
  };

  const isPassphraseRequired = (exchange) => {
    return EXCHANGE_REQUIREMENTS[exchange?.toLowerCase()]?.requiresPassphrase || false;
  };

  const columns = [
    {
      title: 'Exchange',
      dataIndex: 'exchange',
      key: 'exchange',
      width: 120,
      render: (exchange) => {
        const exchangeInfo = EXCHANGE_OPTIONS.find(e => e.value === exchange);
        return exchangeInfo ? exchangeInfo.label : exchange;
      }
    },
    {
      title: 'Label',
      dataIndex: 'label',
      key: 'label',
      width: 150,
      render: (label) => label || <Text type="secondary">No Label</Text>
    },
    {
      title: 'API Key',
      dataIndex: 'api_key',
      key: 'api_key',
      width: 200,
      render: (apiKey, record) => (
        <Space>
          <Text code style={{ fontSize: '12px', maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {maskSecret(apiKey, showSecrets[record.id]?.api_key)}
          </Text>
          <Tooltip title={showSecrets[record.id]?.api_key ? 'Hide API Key' : 'Show API Key'}>
            <Button
              type="text"
              size="small"
              icon={showSecrets[record.id]?.api_key ? <EyeInvisibleOutlined /> : <EyeOutlined />}
              onClick={() => toggleSecretVisibility(record.id, 'api_key')}
            />
          </Tooltip>
        </Space>
      )
    },
    {
      title: 'Secret Key',
      dataIndex: 'secret_key',
      key: 'secret_key',
      width: 200,
      render: (secretKey, record) => (
        <Space>
          <Text code style={{ fontSize: '12px', maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {maskSecret(secretKey, showSecrets[record.id]?.secret_key)}
          </Text>
          <Tooltip title={showSecrets[record.id]?.secret_key ? 'Hide Secret Key' : 'Show Secret Key'}>
            <Button
              type="text"
              size="small"
              icon={showSecrets[record.id]?.secret_key ? <EyeInvisibleOutlined /> : <EyeOutlined />}
              onClick={() => toggleSecretVisibility(record.id, 'secret_key')}
            />
          </Tooltip>
        </Space>
      )
    },
    {
      title: 'Passphrase',
      dataIndex: 'passphrase',
      key: 'passphrase',
      width: 150,
      render: (passphrase, record) => {
        if (!passphrase) return <Text type="secondary">None</Text>;
        
        return (
          <Space>
            <Text code style={{ fontSize: '12px', maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {maskSecret(passphrase, showSecrets[record.id]?.passphrase)}
            </Text>
            <Tooltip title={showSecrets[record.id]?.passphrase ? 'Hide Passphrase' : 'Show Passphrase'}>
              <Button
                type="text"
                size="small"
                icon={showSecrets[record.id]?.passphrase ? <EyeInvisibleOutlined /> : <EyeOutlined />}
                onClick={() => toggleSecretVisibility(record.id, 'passphrase')}
              />
            </Tooltip>
          </Space>
        );
      }
    },
    {
      title: 'Validation',
      key: 'validation',
      width: 140,
      render: (_, record) => {
        const { status, text, icon } = getValidationStatus(record);
        return (
          <Tooltip title={record.last_validated ? `Last validated: ${new Date(record.last_validated).toLocaleDateString()}` : 'Never validated'}>
            <Tag 
              color={
                status === 'success' ? 'green' : 
                status === 'warning' ? 'orange' : 'red'
              } 
              icon={icon}
            >
              {text}
            </Tag>
          </Tooltip>
        );
      }
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? 'ACTIVE' : 'INACTIVE'}
        </Tag>
      )
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date) => date ? new Date(date).toLocaleDateString() : 'N/A'
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 80,
      fixed: 'right',
      render: (_, record) => (
        <Dropdown 
          overlay={createActionMenu(record)} 
          trigger={['click']}
          placement="bottomRight"
        >
          <Button 
            type="text" 
            icon={<MoreOutlined />} 
            size="small"
            loading={validating[record.id]}
          />
        </Dropdown>
      )
    }
  ];

  return (
    <div className="api-keys-container">
      <div className="api-keys-header">
        <Title level={3}>API Keys Management</Title>
        <Text type="secondary">
          Add and manage your exchange API keys for automated trading
        </Text>
      </div>

      {error && (
        <Alert
          message="Error Loading API Keys"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
          closable
          onClose={() => setError(null)}
        />
      )}

      <Alert
        message="Security Notice"
        description="Your API keys are encrypted and stored securely. Never share your secret keys or passphrases."
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Card
        title="Your API Keys"
        extra={
          <Space>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={loadApiKeys}
              loading={loading}
            >
              Refresh
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAddKey}>
              Add API Key
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={apiKeys}
          loading={loading}
          rowKey="id"
          pagination={{ 
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} items`
          }}
          scroll={{ x: 1200 }}
          locale={{ 
            emptyText: loading ? 'Loading API keys...' : 'No API keys found. Click "Add API Key" to get started.' 
          }}
        />
      </Card>

      <Modal
        title={editingKey ? 'Edit API Key' : 'Add New API Key'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          onSettingsChange(false);
        }}
        footer={null}
        width={600}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          onValuesChange={(changedValues) => {
            // Update passphrase requirement when exchange changes
            if (changedValues.exchange) {
              const isRequired = isPassphraseRequired(changedValues.exchange);
              if (isRequired) {
                form.setFields([{
                  name: 'passphrase',
                  errors: []
                }]);
              }
            }
          }}
        >
          <Form.Item
            name="exchange"
            label="Exchange"
            rules={[{ required: true, message: 'Please select an exchange' }]}
          >
            <Select placeholder="Select exchange" showSearch>
              {EXCHANGE_OPTIONS.map(exchange => (
                <Option key={exchange.value} value={exchange.value}>
                  {exchange.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="label"
            label="Label (Optional)"
            tooltip="A friendly name to identify this API key"
          >
            <Input placeholder="e.g., Main Binance Account" />
          </Form.Item>

          <Form.Item
            name="api_key"
            label="API Key"
            rules={[{ required: true, message: 'Please enter your API key' }]}
          >
            <Input.Password 
              placeholder="Enter your API key" 
              visibilityToggle={false}
            />
          </Form.Item>

          <Form.Item
            name="secret_key"
            label="Secret Key"
            rules={[{ required: true, message: 'Please enter your secret key' }]}
          >
            <Input.Password 
              placeholder="Enter your secret key" 
              visibilityToggle={false}
            />
          </Form.Item>

          <Form.Item
            name="passphrase"
            label="Passphrase"
            tooltip={getPassphraseTooltip(form.getFieldValue('exchange'))}
            rules={[
              ({ getFieldValue }) => ({
                validator(_, value) {
                  const exchange = getFieldValue('exchange');
                  if (isPassphraseRequired(exchange) && !value?.trim()) {
                    return Promise.reject(new Error(`${exchange.toUpperCase()} requires a passphrase`));
                  }
                  return Promise.resolve();
                },
              }),
            ]}
          >
            <Input.Password 
              placeholder="Enter passphrase if required" 
              visibilityToggle={false}
            />
          </Form.Item>

          <Form.Item
            name="is_active"
            label="Status"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch checkedChildren="Active" unCheckedChildren="Inactive" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingKey ? 'Update' : 'Add'} API Key
              </Button>
              <Button onClick={() => {
                setModalVisible(false);
                form.resetFields();
                onSettingsChange(false);
              }}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ApiKeys;