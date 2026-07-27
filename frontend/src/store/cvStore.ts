import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { 
  CVProject, 
  CVDataset, 
  CVTrainingJob, 
  CVExperiment, 
  CVPrediction, 
  TrainingMode,
  CVModel
} from '../types/cv';

interface CVState {
  activeProject: CVProject | null;
  datasets: CVDataset[];
  activeDatasetId: string | null;
  trainingJobs: CVTrainingJob[];
  activeJobId: string | null;
  experiments: CVExperiment[];
  models: CVModel[];
  predictions: CVPrediction[];
  activeTab: 'overview' | 'data' | 'vision_tasks' | 'training' | 'live_training' | 'results' | 'prediction' | 'experiments' | 'deploy' | 'hub' | 'model_hub';
  trainingMode: TrainingMode;
  cvCache: Record<string, any>;
  
  // Actions
  setActiveProject: (project: CVProject | null) => void;
  setDatasets: (datasets: CVDataset[]) => void;
  addDataset: (dataset: CVDataset) => void;
  deleteDataset: (id: string) => Promise<void>;
  setActiveDatasetId: (id: string | null) => void;
  
  setTrainingJobs: (jobs: CVTrainingJob[]) => void;
  addTrainingJob: (job: CVTrainingJob) => void;
  updateTrainingJob: (id: string, updates: Partial<CVTrainingJob>) => void;
  setActiveJobId: (id: string | null) => void;
  
  setExperiments: (experiments: CVExperiment[]) => void;
  setModels: (models: CVModel[]) => void;
  setPredictions: (predictions: CVPrediction[]) => void;
  
  setActiveTab: (tab: CVState['activeTab']) => void;
  setTrainingMode: (mode: TrainingMode) => void;
  
  setCvCache: (key: string, data: any) => void;
  clearCvCache: (key?: string) => void;
}

export const useCVStore = create<CVState>()(
  persist(
    (set) => ({
      activeProject: null,
      datasets: [],
      activeDatasetId: null,
      trainingJobs: [],
      activeJobId: null,
      experiments: [],
      models: [],
      predictions: [],
      activeTab: 'overview',
      trainingMode: 'fast',
      cvCache: {},
      
      setActiveProject: (project) => set({ activeProject: project }),
      
      setDatasets: (datasets) => set({ datasets }),
      addDataset: (dataset) => set((state) => ({ 
        datasets: [dataset, ...state.datasets],
        activeDatasetId: dataset.id 
      })),
      deleteDataset: async (id: string) => {
        try {
          const response = await fetch(`/api/v1/cv/datasets/${id}`, { method: 'DELETE' });
          if (response.ok) {
            set((state) => ({
              datasets: state.datasets.filter(d => d.id !== id),
              activeDatasetId: state.activeDatasetId === id ? null : state.activeDatasetId
            }));
          }
        } catch (error) {
          console.error("Failed to delete dataset:", error);
        }
      },
      setActiveDatasetId: (id) => set({ activeDatasetId: id }),
      
      setTrainingJobs: (jobs) => set({ trainingJobs: jobs }),
      addTrainingJob: (job) => set((state) => ({ trainingJobs: [...state.trainingJobs, job] })),
      updateTrainingJob: (id, updates) => set((state) => ({
        trainingJobs: state.trainingJobs.map(job => 
          job.id === id ? { ...job, ...updates } : job
        )
      })),
      setActiveJobId: (id) => set({ activeJobId: id }),
      
      setExperiments: (experiments) => set({ experiments }),
      setModels: (models) => set({ models }),
      setPredictions: (predictions) => set({ predictions }),
      
      setActiveTab: (tab) => set({ activeTab: tab }),
      setTrainingMode: (mode) => set({ trainingMode: mode }),
      
      setCvCache: (key, data) => set((state) => ({
        cvCache: { ...state.cvCache, [key]: data }
      })),
      clearCvCache: (key) => set((state) => {
        if (key) {
          const newCache = { ...state.cvCache };
          delete newCache[key];
          return { cvCache: newCache };
        }
        return { cvCache: {} };
      }),
    }),
    {
      name: 'datavision-cv-store',
      partialize: (state) => ({ 
        activeProject: state.activeProject,
        activeTab: state.activeTab,
        trainingMode: state.trainingMode,
        cvCache: state.cvCache,
        activeDatasetId: state.activeDatasetId,
        activeJobId: state.activeJobId
      }), // Persist specific fields
    }
  )
);
