// frontend/src/context/WebSocketContext.js
import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAuth } from './AuthContext';

const WebSocketContext = createContext({});

export const useWS = () => {
  const ctx = useContext(WebSocketContext);
  if (!ctx) throw new Error('useWS must be used within WebSocketProvider');
  return ctx;
};

export const WebSocketProvider = ({ 
  children, 
  url = (import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/trading/') 
}) => {
  const { user, isAuthenticated } = useAuth();
  const [messages, setMessages] = useState([]);
  const [subscriptions, setSubscriptions] = useState(new Set());
  const messageHandlers = useRef(new Map());

  const handleIncomingMessage = useCallback((msg) => {
    try {
      const parsedMsg = typeof msg === 'string' ? JSON.parse(msg) : msg;
      
      setMessages(prev => {
        // Keep a small ring buffer (last 200 messages)
        const next = [...prev, {
          ...parsedMsg,
          timestamp: new Date().toISOString(),
          id: Date.now() + Math.random()
        }].slice(-200);
        return next;
      });

      // Call specific handlers for this message type
      const handlers = messageHandlers.current.get(parsedMsg.type);
      if (handlers) {
        handlers.forEach(handler => handler(parsedMsg));
      }
    } catch (error) {
      console.error('Error processing WebSocket message:', error);
    }
  }, []);

  const { sendMessage, isConnected, reconnect } = useWebSocket(url, handleIncomingMessage);

  // Auto-reconnect when user authenticates
  useEffect(() => {
    if (isAuthenticated && !isConnected) {
      reconnect();
    }
  }, [isAuthenticated, isConnected, reconnect]);

  // Clear messages on logout
  useEffect(() => {
    if (!user) {
      setMessages([]);
      setSubscriptions(new Set());
    }
  }, [user]);

  const publish = useCallback(async (type, payload) => {
    if (!isConnected) {
      console.warn('WebSocket not connected, cannot publish message');
      return false;
    }
    
    try {
      const message = {
        type,
        payload,
        timestamp: new Date().toISOString(),
      };
      sendMessage(message);
      return true;
    } catch (error) {
      console.error('WebSocket publish failed:', error);
      return false;
    }
  }, [isConnected, sendMessage]);

  const subscribe = useCallback((channel) => {
    if (!channel || !isConnected) return false;
    
    if (!subscriptions.has(channel)) {
      publish('subscribe', { channel });
      setSubscriptions(prev => new Set(prev).add(channel));
      return true;
    }
    return false;
  }, [isConnected, subscriptions, publish]);

  const unsubscribe = useCallback((channel) => {
    if (!channel || !isConnected) return false;
    
    if (subscriptions.has(channel)) {
      publish('unsubscribe', { channel });
      setSubscriptions(prev => {
        const next = new Set(prev);
        next.delete(channel);
        return next;
      });
      return true;
    }
    return false;
  }, [isConnected, subscriptions, publish]);

  const onMessage = useCallback((messageType, handler) => {
    if (!messageHandlers.current.has(messageType)) {
      messageHandlers.current.set(messageType, new Set());
    }
    messageHandlers.current.get(messageType).add(handler);

    // Return cleanup function
    return () => {
      const handlers = messageHandlers.current.get(messageType);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          messageHandlers.current.delete(messageType);
        }
      }
    };
  }, []);

  const value = {
    sendMessage: publish,
    isConnected,
    messages,
    subscribe,
    unsubscribe,
    subscriptions: Array.from(subscriptions),
    onMessage,
    clearMessages: () => setMessages([]),
    reconnect,
    lastMessage: messages.length > 0 ? messages[messages.length - 1] : null,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export default WebSocketContext;