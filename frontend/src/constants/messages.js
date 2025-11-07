// frontend/src/constants/messages.js

export const MESSAGES = {
  // Generic Messages
  GENERIC_ERROR: 'Something went wrong. Please try again.',
  NETWORK_ERROR: 'Unable to reach the server. Check your network connection.',
  AUTH_REQUIRED: 'Please log in to continue.',
  PERMISSION_DENIED: 'You do not have permission to perform this action.',
  
  // Success Messages
  SAVE_SUCCESS: 'Settings saved successfully.',
  DELETE_SUCCESS: 'Item deleted successfully.',
  UPDATE_SUCCESS: 'Update successful.',
  OPERATION_SUCCESS: 'Operation completed successfully.',
  
  // Failure Messages
  SAVE_FAILURE: 'Failed to save settings.',
  DELETE_FAILURE: 'Failed to delete item.',
  UPDATE_FAILURE: 'Failed to update.',
  OPERATION_FAILURE: 'Operation failed.',
  
  // API Key Messages
  APIKEY_ADD_SUCCESS: 'API key added successfully.',
  APIKEY_ADD_FAILURE: 'Failed to add API key.',
  APIKEY_UPDATE_SUCCESS: 'API key updated successfully.',
  APIKEY_UPDATE_FAILURE: 'Failed to update API key.',
  APIKEY_DELETE_SUCCESS: 'API key deleted successfully.',
  APIKEY_DELETE_FAILURE: 'Failed to delete API key.',
  CONFIRM_DELETE_APIKEY: 'Are you sure you want to delete this API key?',
  
  // Validation Messages
  VALIDATION_IN_PROGRESS: 'Validation in progress...',
  VALIDATION_SUCCESS: 'Validation successful.',
  VALIDATION_FAILED: 'Validation failed. Check credentials and permissions.',
  INVALID_CREDENTIALS: 'Invalid credentials provided.',
  
  // Trading Messages
  TRADE_EXECUTED_SUCCESS: 'Trade executed successfully.',
  TRADE_EXECUTED_FAILED: 'Trade execution failed.',
  TRADE_CANCELLED_SUCCESS: 'Trade cancelled successfully.',
  TRADE_CANCELLED_FAILED: 'Failed to cancel trade.',
  INSUFFICIENT_BALANCE: 'Insufficient balance for this trade.',
  
  // Exchange Messages
  EXCHANGE_CONNECTED: 'Exchange connected successfully.',
  EXCHANGE_DISCONNECTED: 'Exchange disconnected.',
  EXCHANGE_CONNECTION_FAILED: 'Failed to connect to exchange.',
  
  // Form Messages
  FORM_VALIDATION_ERROR: 'Please fix the errors in the form.',
  REQUIRED_FIELD: 'This field is required.',
  INVALID_EMAIL: 'Please enter a valid email address.',
  PASSWORD_TOO_WEAK: 'Password is too weak.',
  PASSWORDS_DONT_MATCH: 'Passwords do not match.',
};

export const getMessage = (key, fallback = MESSAGES.GENERIC_ERROR) => {
  return MESSAGES[key] || fallback;
};

export default MESSAGES;