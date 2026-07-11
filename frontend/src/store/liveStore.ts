import { create } from 'zustand';

interface LiveState {
  dashboardCache: Record<string, any>;
  mlCache: Record<string, any>;
  anomalyCache: Record<string, any>;
  lastRowCount: number | null;
  setDashboardCache: (key: string, data: any) => void;
  getDashboardCache: (key: string) => any | null;
  setMlCache: (key: string, data: any) => void;
  getMlCache: (key: string) => any | null;
  setAnomalyCache: (key: string, data: any) => void;
  getAnomalyCache: (key: string) => any | null;
  setLastRowCount: (count: number) => void;
  clearCache: () => void;
}

export const useLiveStore = create<LiveState>((set, get) => ({
  dashboardCache: {},
  mlCache: {},
  anomalyCache: {},
  lastRowCount: null,
  
  setDashboardCache: (key, data) => set((state) => ({
    dashboardCache: { ...state.dashboardCache, [key]: data }
  })),
  
  getDashboardCache: (key) => get().dashboardCache[key] || null,
  
  setMlCache: (key, data) => set((state) => ({
    mlCache: { ...state.mlCache, [key]: data }
  })),
  
  getMlCache: (key) => get().mlCache[key] || null,
  
  setAnomalyCache: (key, data) => set((state) => ({
    anomalyCache: { ...state.anomalyCache, [key]: data }
  })),
  
  getAnomalyCache: (key) => get().anomalyCache[key] || null,
  
  setLastRowCount: (count) => set({ lastRowCount: count }),
  
  clearCache: () => set({ dashboardCache: {}, mlCache: {}, anomalyCache: {}, lastRowCount: null })
}));
