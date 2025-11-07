//frontend/src/store/slices/tradingSlice.js
import { createSlice } from '@reduxjs/toolkit';

const tradingSlice = createSlice({
  name: 'trading',
  initialState: {
    opportunities: [],
    activeTrades: [],
    tradeHistory: [],
    autoTrading: false,
    loading: false,
    error: null,
  },
  reducers: {
    setOpportunities: (state, action) => {
      state.opportunities = action.payload;
    },
    setActiveTrades: (state, action) => {
      state.activeTrades = action.payload;
    },
    setTradeHistory: (state, action) => {
      state.tradeHistory = action.payload;
    },
    setAutoTrading: (state, action) => {
      state.autoTrading = action.payload;
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
    },
  },
});

export const {
  setOpportunities,
  setActiveTrades,
  setTradeHistory,
  setAutoTrading,
  setLoading,
  setError,
} = tradingSlice.actions;

export default tradingSlice.reducer;