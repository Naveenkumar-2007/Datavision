export type VisionTask = 
  | 'classification'
  | 'object_detection'
  | 'semantic_segmentation'
  | 'instance_segmentation'
  | 'ocr'
  | 'pose_estimation'
  | 'face_recognition'
  | 'medical_imaging'
  | 'anomaly_detection'
  | 'unknown';

export type TrainingMode = 'fast' | 'ultra' | 'expert';
export type JobStatus = 'pending' | 'starting' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';

export interface CVProject {
  id: string;
  userId: string;
  name: string;
  description?: string;
  taskType: VisionTask;
  createdAt: string;
  updatedAt: string;
}

export interface CVDatasetHealth {
  score: number; // 0-100
  goodImages: number;
  blurredImages: number;
  corruptedImages: number;
  lowLightImages: number;
  duplicates: number;
  resolutionAvg: string;
  aspectRatio: string;
  formats: string[];
  sizeAvg: string;
  recommendations: string[];
}

export interface CVDataset {
  id: string;
  projectId?: string;
  userId: string;
  name: string;
  format: string; // 'yolo', 'coco', 'voc', 'csv', 'folder'
  taskType?: VisionTask;
  numImages: number;
  numClasses: number;
  classes: string[];
  path: string;
  healthScore?: CVDatasetHealth;
  createdAt: string;
}

export interface CVTrainingConfig {
  model: string;
  epochs: number;
  batchSize: number;
  learningRate: number;
  imageSize: number;
  optimizer?: string;
  scheduler?: string;
  loss?: string;
  augmentations?: string[];
  transferLearning?: boolean;
  freezeLayers?: number;
  mixedPrecision?: boolean;
  momentum?: number;
  weightDecay?: number;
  seed?: number;
}

export interface CVTrainingMetrics {
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1?: number;
  mAP50?: number;
  mAP50_95?: number;
  inferenceTime?: number;
  fps?: number;
  modelSizeMB?: number;
}

export interface CVTrainingProgress {
  status: JobStatus;
  epoch: number;
  totalEpochs: number;
  loss: number;
  valLoss: number;
  metrics: CVTrainingMetrics;
  logs: string[];
  systemStats: {
    gpuUsage: number;
    vramUsage: string;
    cpuUsage: number;
    ramUsage: string;
  };
  startedAt: string;
  completedAt?: string;
  error?: string;
  modelPath?: string;
}

export interface CVTrainingJob {
  id: string;
  projectId?: string;
  datasetId: string;
  userId: string;
  mode: TrainingMode;
  config: CVTrainingConfig;
  status: JobStatus;
  progress: CVTrainingProgress;
  metrics?: CVTrainingMetrics;
  modelPath?: string;
  startedAt: string;
  completedAt?: string;
  error?: string;
}

export interface CVExperiment {
  id: string;
  trainingJobId: string;
  userId: string;
  version: number;
  modelName: string;
  hyperparams: CVTrainingConfig;
  metrics: CVTrainingMetrics;
  createdAt: string;
}

export interface CVModel {
  id: string;
  experimentId: string;
  userId: string;
  name: string;
  taskType: VisionTask;
  architecture: string;
  metrics: CVTrainingMetrics;
  modelPath: string;
  sizeMb: number;
  isActive: boolean;
  createdAt: string;
}

export interface CVPredictionResult {
  class?: string;
  confidence: number;
  bbox?: [number, number, number, number]; // [x1, y1, x2, y2]
  mask?: any; // polygon or mask data
}

export interface CVPrediction {
  id: string;
  modelId: string;
  userId: string;
  inputType: 'single' | 'batch' | 'video' | 'stream';
  numImages: number;
  results: CVPredictionResult[];
  processedImageUrl?: string;
  createdAt: string;
}
