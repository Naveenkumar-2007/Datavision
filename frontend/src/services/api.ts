import axios from 'axios';
import { supabase } from '../lib/supabase';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add user ID and auth token to all requests
api.interceptors.request.use(async (config) => {
  // Get current session from Supabase
  const { data: { session } } = await supabase.auth.getSession();

  if (session) {
    // Add user ID header
    config.headers['X-User-ID'] = session.user.id;
    // Add auth token
    config.headers['Authorization'] = `Bearer ${session.access_token}`;
  } else {
    // Fallback to localStorage
    const userId = localStorage.getItem('userId');
    if (userId) {
      config.headers['X-User-ID'] = userId;
    }
  }

  return config;
});

// Handle auth errors - redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login if not already there
      if (window.location.pathname !== '/login' && window.location.pathname !== '/signup' && window.location.pathname !== '/') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Get current user ID helper
const getUserId = (): string => {
  return localStorage.getItem('userId') || 'guest';
};

// API Service Methods
export const apiService = {
  // File operations
  uploadFiles: async (files: File[]) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    const userId = getUserId();
    return api.post(`/api/v1/files/upload/${userId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  listFiles: async () => {
    const userId = getUserId();
    return api.get(`/api/v1/files/list/${userId}`);
  },

  deleteFile: async (fileId: string) => {
    const userId = getUserId();
    return api.delete(`/api/v1/files/${userId}/${fileId}`);
  },

  deleteAllFiles: async () => {
    const userId = getUserId();
    return api.delete(`/api/v1/files/${userId}/all`);
  },

  rebuildIndex: async () => {
    const userId = getUserId();
    return api.post(`/api/v1/files/${userId}/rebuild`);
  },

  // Chat operations - USES AUTHENTICATED USER ID
  sendMessage: async (
    message: string,
    mode: string = 'rag',
    conversationId?: string,
    compareFiles?: string[],
    attachedFiles?: any[],
    enabledMcps?: Record<string, boolean>
  ) => {
    return api.post('/api/v1/chat/message', {
      message,
      mode,
      conversationId,
      compareFiles,
      attachedFiles,
      enabledMcps: enabledMcps || {
        data_cleaner: true,
        vectorizer: true,
        graph_builder: true,
        sql_executor: true,
        vision_ocr: true,
      },
    });
  },

  getChatHistory: async () => {
    const userId = getUserId();
    return api.get(`/api/v1/chat/history/${userId}`);
  },

  getConversation: async (conversationId: string) => {
    const userId = getUserId();
    return api.get(`/api/v1/chat/history/${userId}/${conversationId}`);
  },

  deleteConversation: async (conversationId: string) => {
    const userId = getUserId();
    return api.delete(`/api/v1/chat/history/${userId}/${conversationId}`);
  },

  // Analytics operations
  getAnalyticsOverview: async () => {
    const userId = getUserId();
    return api.get(`/api/v1/analytics/overview/${userId}`);
  },

  getRevenueDetails: async (period: string = 'all') => {
    const userId = getUserId();
    return api.get(`/api/v1/analytics/revenue/${userId}`, {
      params: { period },
    });
  },

  getCustomerAnalytics: async () => {
    const userId = getUserId();
    return api.get(`/api/v1/analytics/customers/${userId}`);
  },

  getProductAnalytics: async () => {
    const userId = getUserId();
    return api.get(`/api/v1/analytics/products/${userId}`);
  },

  // Report operations
  generateReport: async (reportType: string, dateRange?: { start: string; end: string }) => {
    const userId = getUserId();
    return api.post('/api/v1/reports/generate', {
      userId: userId,
      reportType: reportType,
      dateRange: dateRange || 'all',
      format: 'json',
    });
  },

  getReport: async (reportId: string) => {
    return api.get(`/api/v1/reports/${reportId}`);
  },

  exportReportPDF: async (reportId: string) => {
    return api.get(`/api/v1/reports/${reportId}/export/pdf`, {
      responseType: 'blob',
    });
  },
};

export default apiService;
