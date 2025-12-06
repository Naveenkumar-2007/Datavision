import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add user ID to all requests
api.interceptors.request.use((config) => {
  const userId = localStorage.getItem('userId') || 'user_001';
  config.headers['X-User-ID'] = userId;
  return config;
});

// API Service Methods
export const apiService = {
  // File operations
  uploadFiles: async (files: File[]) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    
    const userId = localStorage.getItem('userId') || 'user_001';
    return api.post(`/api/v1/files/upload/${userId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  listFiles: async () => {
    const userId = localStorage.getItem('userId') || 'user_001';
    return api.get(`/api/v1/files/list/${userId}`);
  },

  deleteFile: async (fileId: string) => {
    const userId = localStorage.getItem('userId') || 'user_001';
    return api.delete(`/api/v1/files/${userId}/${fileId}`);
  },

  deleteAllFiles: async () => {
    const userId = localStorage.getItem('userId') || 'user_001';
    return api.delete(`/api/v1/files/${userId}/all`);
  },

  rebuildIndex: async () => {
    const userId = localStorage.getItem('userId') || 'user_001';
    return api.post(`/api/v1/files/${userId}/rebuild`);
  },

  // Chat operations
  sendMessage: async (
    message: string, 
    mode: string = 'rag', 
    conversationId?: string,
    compareFiles?: string[],
    attachedFiles?: any[]
  ) => {
    const userId = localStorage.getItem('userId') || 'user_001';
    return api.post('/api/v1/chat/message', {
      userId: userId,
      message,
      mode,
      conversationId,
      compareFiles,
      attachedFiles,
    });
  },

  getChatHistory: async () => {
    const userId = localStorage.getItem('userId') || 'user_001';
    return api.get(`/api/v1/chat/history/${userId}`);
  },

  // Analytics operations - REAL DATA
  getAnalyticsOverview: async () => {
    const userId = localStorage.getItem('userId') || 'user_001';
    return api.get(`/api/v1/analytics/overview/${userId}`);
  },

  getRevenueDetails: async (period: string = 'all') => {
    const userId = localStorage.getItem('userId') || 'user_001';
    return api.get(`/api/v1/analytics/revenue/${userId}`, {
      params: { period },
    });
  },

  getCustomerAnalytics: async () => {
    const userId = localStorage.getItem('userId') || 'user_001';
    return api.get(`/api/v1/analytics/customers/${userId}`);
  },

  getProductAnalytics: async () => {
    const userId = localStorage.getItem('userId') || 'user_001';
    return api.get(`/api/v1/analytics/products/${userId}`);
  },

  // Report operations - REAL DATA
  generateReport: async (reportType: string, dateRange?: { start: string; end: string }) => {
    const userId = localStorage.getItem('userId') || 'user_001';
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
