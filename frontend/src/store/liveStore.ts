import { create } from 'zustand';

interface LiveState {
  dashboardCache: Record<string, any>;
  mlCache: Record<string, any>;
  anomalyCache: Record<string, any>;
  simulatorCache: Record<string, any>;
  lastRowCount: number | null;
  setDashboardCache: (key: string, data: any) => void;
  getDashboardCache: (key: string) => any | null;
  setMlCache: (key: string, data: any) => void;
  getMlCache: (key: string) => any | null;
  setAnomalyCache: (key: string, data: any) => void;
  getAnomalyCache: (key: string) => any | null;
  setSimulatorCache: (key: string, data: any) => void;
  getSimulatorCache: (key: string) => any | null;
  setLastRowCount: (count: number) => void;
  clearCache: () => void;
  clearSimulatorCache: () => void;
}

export const useLiveStore = create<LiveState>((set, get) => ({
  dashboardCache: {},
  mlCache: {},
  anomalyCache: {},
  simulatorCache: {},
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

  setSimulatorCache: (key, data) => set((state) => ({
    simulatorCache: { ...state.simulatorCache, [key]: data }
  })),
  
  getSimulatorCache: (key) => get().simulatorCache[key] || null,
  
  setLastRowCount: (count) => set({ lastRowCount: count }),
  
  clearCache: () => set({ dashboardCache: {}, mlCache: {}, anomalyCache: {}, simulatorCache: {}, lastRowCount: null }),
  clearSimulatorCache: () => set({ simulatorCache: {} }),
}));
