import axios from 'axios';
import { supabase } from '../lib/supabase';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * 🔐 ENTERPRISE AUTH INTERCEPTOR
 * 
 * Automatically adds JWT token to ALL requests.
 * Backend extracts user_id from the verified token - NOT from request body.
 * This prevents users from manipulating user_id to access other users' data.
 */
api.interceptors.request.use(async (config) => {
  try {
    // Get current session from Supabase
    const { data: { session } } = await supabase.auth.getSession();

    if (session?.access_token) {
      // 🔐 Send JWT token - Backend validates this cryptographically
      config.headers['Authorization'] = `Bearer ${session.access_token}`;
      // Also send user ID header for backward compatibility during migration
      config.headers['X-User-ID'] = session.user.id;
    } else {
      // Guest user - send guest ID in header (backend generates consistent guest ID)
      const guestId = localStorage.getItem('guestUserId');
      if (guestId) {
        config.headers['X-User-ID'] = guestId;
      }
    }
  } catch (error) {
    console.warn('Auth interceptor error:', error);
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

// Import user ID helper
import { getUserIdSync } from '../utils/userId';

// Get current user ID helper - uses unique ID per user/guest
const getUserId = (): string => {
  return getUserIdSync();
};

// API Service Methods
export const apiService = {
  // File operations
  uploadFiles: async (files: File[], signal?: AbortSignal) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    const userId = getUserId();
    return api.post(`/api/v1/files/upload/${userId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      signal, // Pass abort signal to axios
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
        data_transformer: true,
        data_validator: true,
        alert_engine: true,
        insight_engine: true,
        forecast_engine: true,
      },
    });
  },

  // Streaming chat - word-by-word like ChatGPT
  streamMessage: async (
    message: string,
    model: string = 'deepseek',
    onChunk: (chunk: string) => void,
    onDone: () => void,
    onError: (error: string) => void
  ) => {
    const userId = getUserId();
    const baseUrl = import.meta.env.VITE_API_URL || '';

    try {
      const response = await fetch(`${baseUrl}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId,
        },
        body: JSON.stringify({
          message,
          model,
          userId,
        }),
      });

      if (!response.ok) {
        onError(`HTTP error: ${response.status}`);
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        onError('No response body');
        return;
      }

      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value, { stream: true });
        const lines = text.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              onDone();
              return;
            }
            try {
              const parsed = JSON.parse(data);
              if (parsed.content) {
                onChunk(parsed.content);
              }
              if (parsed.error) {
                onError(parsed.error);
                return;
              }
            } catch {
              // Ignore parse errors for incomplete chunks
            }
          }
        }
      }

      onDone();
    } catch (error: any) {
      onError(error.message || 'Stream error');
    }
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

  // Schema-driven smart overview (Power BI style - works with ANY data)
  getSmartOverview: async () => {
    const userId = getUserId();
    return api.get(`/api/v1/analytics/smart-overview/${userId}`);
  },

  // Power BI-style unified analytics - single source of truth
  getUnifiedAnalytics: async (filterParams: string = '') => {
    const userId = getUserId();
    return api.get(`/api/v1/analytics/unified/${userId}${filterParams}`);
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

  // Enterprise Smart Analytics
  getInsights: async () => {
    const userId = getUserId();
    return api.get(`/api/v1/analytics/insights/${userId}`);
  },

  getDataProfile: async () => {
    const userId = getUserId();
    return api.get(`/api/v1/analytics/data-profile/${userId}`);
  },

  // $500K Enterprise Dashboard Stats
  getDashboardStats: async () => {
    const userId = getUserId();
    return api.get('/api/v1/analytics/dashboard-stats', {
      params: { user_id: userId },
    });
  },

  // Report operations
  generateReport: async (reportType: string, dateRange?: { start: string; end: string }, fallbackModel?: any) => {
    const userId = getUserId();
    return api.post('/api/v1/reports/generate', {
      userId: userId,
      reportType: reportType,
      dateRange: dateRange || 'all',
      format: 'json',
      // Pass local model metadata as fallback if backend session is lost
      fallbackModel: fallbackModel || null
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

  // Real-time Exchange Rates
  getExchangeRates: async (baseCurrency: string = 'USD') => {
    return api.get('/api/v1/analytics/exchange-rates', {
      params: { base: baseCurrency },
    });
  },

  convertCurrency: async (amount: number, fromCurrency: string, toCurrency: string) => {
    return api.get('/api/v1/analytics/convert-currency', {
      params: { amount, from_currency: fromCurrency, to_currency: toCurrency },
    });
  },

  // Google Sheets Import
  importGoogleSheet: async (sheetUrl: string, sheetName?: string) => {
    const userId = getUserId();
    return api.post(`/api/v1/files/${userId}/import-google-sheet`, null, {
      params: { sheet_url: sheetUrl, sheet_name: sheetName },
    });
  },

  previewGoogleSheet: async (sheetUrl: string) => {
    const userId = getUserId();
    return api.get(`/api/v1/files/${userId}/preview-google-sheet`, {
      params: { sheet_url: sheetUrl },
    });
  },

  // AI Providers
  getAIProviders: async () => {
    return api.get('/api/v1/analytics/ai-providers');
  },

  // Charts - Plotly Generation
  generateChart: async (chartType: string, dataSource: string = 'revenue') => {
    const userId = getUserId();
    return api.post('/api/v1/charts/generate', {
      user_id: userId,
      chart_type: chartType,
      data_source: dataSource,
    });
  },

  getChartTypes: async () => {
    return api.get('/api/v1/charts/available-types');
  },

  // ===== SCHEMA-DRIVEN ANALYTICS API =====
  // Single source of truth for frontend schema consumption

  // Get full schema intelligence (domain, metrics, dimensions, time_column, etc.)
  getSchema: async (refresh: boolean = false) => {
    const userId = getUserId();
    return api.get(`/api/v1/schema/${userId}`, {
      params: { refresh },
    });
  },

  // Get only metric columns (optimized for dropdowns)
  getSchemaMetrics: async () => {
    const userId = getUserId();
    return api.get(`/api/v1/schema/${userId}/metrics`);
  },

  // Get only dimension columns (optimized for dropdowns)
  getSchemaDimensions: async () => {
    const userId = getUserId();
    return api.get(`/api/v1/schema/${userId}/dimensions`);
  },

  // Get chart-ready data based on selected columns
  getChartData: async (params: {
    chartType: 'line' | 'bar' | 'pie' | 'histogram' | 'scatter';
    xColumn: string;
    yColumn?: string;
    groupBy?: string;
    startDate?: string;
    endDate?: string;
    limit?: number;
  }) => {
    const userId = getUserId();
    return api.get(`/api/v1/schema/${userId}/chart-data`, {
      params: {
        chart_type: params.chartType,
        x_column: params.xColumn,
        y_column: params.yColumn,
        group_by: params.groupBy,
        start_date: params.startDate,
        end_date: params.endDate,
        limit: params.limit || 20,
      },
    });
  },
};

export default apiService;
