import React, { useState } from 'react';
import { Settings, Zap, Crown, Target, Cpu, CheckCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { useUserStore } from '@/store/userStore';
import { useCVStore } from '@/store/cvStore';
import { TrainingMode, CVTrainingConfig } from '@/types/cv';

interface Props {
  onStartTraining: (mode: TrainingMode, config: CVTrainingConfig, taskType?: string) => void;
  disabled?: boolean;
  selectedTaskType?: string;
}

const CVTrainingConfigPanel: React.FC<Props> = ({ onStartTraining, disabled, selectedTaskType }) => {
  const { isDark } = useUserStore();
  const { trainingMode, setTrainingMode, activeDatasetId, datasets } = useCVStore();
  
  const dataset = datasets.find(d => d.id === activeDatasetId);
  const effectiveTaskType = selectedTaskType || dataset?.taskType || 'object_detection';
  
  const [config, setConfig] = useState<CVTrainingConfig>({
    model: effectiveTaskType === 'classification' ? 'resnet50' : 
           effectiveTaskType === 'pose_estimation' ? 'yolov8s-pose' :
           effectiveTaskType === 'ocr' ? 'trocr' :
           (effectiveTaskType === 'instance_segmentation' || effectiveTaskType === 'semantic_segmentation') ? 'yolov8s-seg' : 'yolov8s',
    epochs: 50,
    batchSize: 16,
    learningRate: 0.001,
    imageSize: 640,
    optimizer: 'AdamW',
    weightDecay: 0.0005,
    augmentations: ['mosaic', 'mixup'],
  });

  const handleStart = () => {
    onStartTraining(trainingMode, config, effectiveTaskType);
  };

  const modeTabs = [
    { id: 'fast', label: 'Fast Mode', icon: Zap, desc: 'Quick prototyping, 10-20 epochs, basic augmentations' },
    { id: 'ultra', label: 'Ultra Mode', icon: Crown, desc: 'State-of-the-art accuracy, heavy augmentations, 100+ epochs' },
    { id: 'expert', label: 'Expert Mode', icon: Settings, desc: 'Full manual hyperparameter control' }
  ];

  // Advanced model definitions matching AutoML's deep selection
  const detectionModels = [
    { category: 'YOLOv11 (State of the Art)', models: [
      { id: 'yolo11n', name: 'YOLO11 Nano', desc: 'Ultra-fast edge deployment', params: '2.6M' },
      { id: 'yolo11s', name: 'YOLO11 Small', desc: 'Balanced speed/accuracy', params: '9.4M' },
      { id: 'yolo11m', name: 'YOLO11 Medium', desc: 'Standard use cases', params: '20.1M' },
      { id: 'yolo11l', name: 'YOLO11 Large', desc: 'High accuracy', params: '25.3M' },
      { id: 'yolo11x', name: 'YOLO11 Extra', desc: 'Max performance', params: '56.9M' }
    ]},
    { category: 'YOLOv10 / v9', models: [
      { id: 'yolov10n', name: 'YOLOv10 Nano', desc: 'NMS-free end-to-end', params: '2.7M' },
      { id: 'yolov10x', name: 'YOLOv10 Extra', desc: 'Max NMS-free perf', params: '31.6M' },
      { id: 'yolov9c', name: 'YOLOv9 Compact', desc: 'PGI architecture', params: '25.3M' },
      { id: 'yolov9e', name: 'YOLOv9 Extended', desc: 'GELAN heavy', params: '58.1M' }
    ]},
    { category: 'YOLOv8 (Industry Standard)', models: [
      { id: 'yolov8n', name: 'YOLOv8 Nano', desc: 'Extremely fast', params: '3.2M' },
      { id: 'yolov8s', name: 'YOLOv8 Small', desc: 'Good baseline', params: '11.2M' },
      { id: 'yolov8x', name: 'YOLOv8 Extra', desc: 'Heavy but precise', params: '68.2M' }
    ]},
    { category: 'Transformers & Other', models: [
      { id: 'rtdetr-l', name: 'RT-DETR Large', desc: 'Real-time Transformer', params: '32M' },
      { id: 'rtdetr-x', name: 'RT-DETR Extra', desc: 'SOTA Transformer', params: '67M' },
      { id: 'faster_rcnn', name: 'Faster R-CNN', desc: 'Classic two-stage', params: '41M' },
      { id: 'ssd_mobilenet', name: 'SSD MobileNet', desc: 'Lightweight mobile', params: '4M' },
      { id: 'retinanet', name: 'RetinaNet', desc: 'Focal loss pioneer', params: '38M' },
      { id: 'efficientdet_d0', name: 'EfficientDet-D0', desc: 'BiFPN architecture', params: '4M' }
    ]}
  ];

  const classificationModels = [
    { category: 'Transformers (SOTA)', models: [
      { id: 'vit_b_16', name: 'ViT Base 16', desc: 'Vision Transformer', params: '86M' },
      { id: 'vit_l_16', name: 'ViT Large 16', desc: 'Heavy Transformer', params: '304M' },
      { id: 'swin_t', name: 'Swin-T', desc: 'Hierarchical ViT', params: '28M' },
      { id: 'deit_base', name: 'DeiT Base', desc: 'Data-efficient ViT', params: '86M' }
    ]},
    { category: 'EfficientNet (Balanced)', models: [
      { id: 'efficientnet_b0', name: 'EfficientNet-B0', desc: 'Fast baseline', params: '5M' },
      { id: 'efficientnet_b4', name: 'EfficientNet-B4', desc: 'High accuracy', params: '19M' },
      { id: 'efficientnet_v2_s', name: 'EfficientNetV2-S', desc: 'Faster training', params: '21M' },
      { id: 'convnext_tiny', name: 'ConvNeXt Tiny', desc: 'Modern ConvNet', params: '28M' }
    ]},
    { category: 'Classic ResNet', models: [
      { id: 'resnet18', name: 'ResNet-18', desc: 'Lightweight classic', params: '11M' },
      { id: 'resnet50', name: 'ResNet-50', desc: 'Industry standard', params: '25M' },
      { id: 'resnet101', name: 'ResNet-101', desc: 'Deeper network', params: '44M' }
    ]},
    { category: 'Mobile & Edge', models: [
      { id: 'mobilenet_v3_small', name: 'MobileNetV3 S', desc: 'Ultra-light', params: '2.5M' },
      { id: 'mobilenet_v3_large', name: 'MobileNetV3 L', desc: 'Mobile standard', params: '5.4M' },
      { id: 'shufflenet_v2_x1_0', name: 'ShuffleNet V2', desc: 'Efficient edge', params: '2.3M' }
    ]}
  ];

  const segmentationModels = [
    { category: 'Foundation Models', models: [
      { id: 'sam_b', name: 'SAM Base', desc: 'Segment Anything', params: '91M' },
      { id: 'sam2_t', name: 'SAM 2 Tiny', desc: 'Video/Image SOTA', params: '38M' }
    ]},
    { category: 'YOLO Segmentation', models: [
      { id: 'yolo11n-seg', name: 'YOLO11n-Seg', desc: 'Fast instance seg', params: '2.8M' },
      { id: 'yolov8s-seg', name: 'YOLOv8s-Seg', desc: 'Standard instance', params: '11.8M' }
    ]},
    { category: 'Classic', models: [
      { id: 'mask_rcnn', name: 'Mask R-CNN', desc: 'Standard two-stage', params: '44M' },
      { id: 'deeplabv3', name: 'DeepLabV3', desc: 'Semantic seg', params: '39M' }
    ]}
  ];

  const poseModels = [
    { category: 'YOLO Pose Estimation', models: [
      { id: 'yolo11n-pose', name: 'YOLO11n-Pose', desc: 'Fast pose tracking', params: '2.9M' },
      { id: 'yolov8s-pose', name: 'YOLOv8s-Pose', desc: 'Standard keypoints', params: '11.6M' },
      { id: 'yolov8x-pose', name: 'YOLOv8x-Pose', desc: 'SOTA pose accuracy', params: '69.4M' }
    ]},
    { category: 'Classic Keypoints', models: [
      { id: 'hrnet_w32', name: 'HRNet-W32', desc: 'High-resolution keypoints', params: '28.5M' },
      { id: 'openpose', name: 'OpenPose Multi-Person', desc: 'Real-time multi-person', params: '26M' }
    ]}
  ];

  const ocrModels = [
    { category: 'Text Recognition & Detection', models: [
      { id: 'trocr', name: 'TrOCR (Transformer OCR)', desc: 'Encoder-decoder text OCR', params: '62M' },
      { id: 'paddle_ocr', name: 'PaddleOCR Engine', desc: 'Multilingual document OCR', params: '15M' },
      { id: 'easy_ocr', name: 'EasyOCR Text Pipeline', desc: 'Fast multi-language text', params: '12M' }
    ]}
  ];

  const currentModels = effectiveTaskType === 'classification' ? classificationModels :
                        effectiveTaskType === 'pose_estimation' ? poseModels :
                        effectiveTaskType === 'ocr' ? ocrModels :
                        (effectiveTaskType === 'instance_segmentation' || effectiveTaskType === 'semantic_segmentation') ? segmentationModels :
                        detectionModels;

  const renderModelGrid = (categories: {category: string, models: any[]}[]) => (
    <div className="space-y-6">
      {categories.map((group, idx) => (
        <div key={idx}>
          <h4 className="text-sm font-semibold mb-3 px-1" style={{ color: 'var(--text-muted)' }}>{group.category}</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {group.models.map(m => (
              <div 
                key={m.id}
                onClick={() => setConfig({...config, model: m.id})}
                className={`relative p-4 rounded-xl border cursor-pointer transition-all ${
                  config.model === m.id 
                    ? 'border-emerald-500 bg-emerald-500/10 shadow-[0_0_15px_rgba(16,185,129,0.1)]' 
                    : 'hover:border-emerald-500/50 hover:bg-black/5 dark:hover:bg-white/5'
                }`}
                style={{ borderColor: config.model === m.id ? '' : 'var(--border-color)' }}
              >
                {config.model === m.id && (
                  <div className="absolute top-2 right-2 text-emerald-500">
                    <CheckCircle className="w-4 h-4" />
                  </div>
                )}
                <div className="font-bold mb-1" style={{ color: 'var(--text-primary)' }}>{m.name}</div>
                <div className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>{m.desc}</div>
                <div className="text-[10px] font-mono px-2 py-1 bg-black/10 dark:bg-white/10 rounded w-fit text-slate-500">
                  {m.params} Params
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <div className="space-y-8">
      {/* Mode Selector - Uses AutoML pill pattern */}
      <div className="flex p-1 rounded-xl bg-black/5 dark:bg-white/5 border w-fit" style={{ borderColor: 'var(--border-color)' }}>
        {modeTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setTrainingMode(tab.id as TrainingMode)}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-medium transition-all ${
              trainingMode === tab.id 
                ? 'bg-white dark:bg-slate-800 shadow-sm text-emerald-500' 
                : 'hover:bg-black/5 dark:hover:bg-white/5'
            }`}
            style={{ color: trainingMode === tab.id ? '' : 'var(--text-muted)' }}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      <div className="p-4 rounded-xl border bg-emerald-500/5" style={{ borderColor: 'var(--border-color)' }}>
        <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
          {modeTabs.find(t => t.id === trainingMode)?.desc}
        </p>
        {trainingMode === 'fast' && (
          <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
            Note: Fast Mode will automatically select a lightweight model ({effectiveTaskType === 'classification' ? 'ResNet-18' : 'YOLO11n'}) and train for 20 epochs. Model architecture selection is disabled in Fast Mode.
          </p>
        )}
      </div>

      {/* Model Selection (Visible in Ultra and Expert) */}
      {trainingMode !== 'fast' && (
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4 p-5 rounded-2xl border"
          style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
        >
          <div className="flex items-center gap-2 mb-6 border-b pb-4" style={{ borderColor: 'var(--border-color)' }}>
            <Cpu className="w-6 h-6 text-emerald-500" />
            <div>
              <h3 className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>Model Architecture</h3>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Select a foundation model to fine-tune on your dataset.</p>
            </div>
          </div>
          
          {renderModelGrid(currentModels)}
          
        </motion.div>
      )}

      {/* Expert Settings */}
      {trainingMode === 'expert' && (
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4 p-5 rounded-2xl border"
          style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
        >
          <div className="flex items-center gap-2 mb-6 border-b pb-4" style={{ borderColor: 'var(--border-color)' }}>
            <Settings className="w-6 h-6 text-emerald-500" />
            <div>
              <h3 className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>Advanced Hyperparameters</h3>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Fine-tune the training process manually.</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>Epochs</label>
              <input 
                type="number" 
                value={config.epochs} 
                onChange={(e) => setConfig({...config, epochs: parseInt(e.target.value)})}
                className="w-full p-2.5 rounded-xl border outline-none bg-transparent focus:border-emerald-500"
                style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>Batch Size</label>
              <input 
                type="number" 
                value={config.batchSize} 
                onChange={(e) => setConfig({...config, batchSize: parseInt(e.target.value)})}
                className="w-full p-2.5 rounded-xl border outline-none bg-transparent focus:border-emerald-500"
                style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>Learning Rate</label>
              <input 
                type="number" 
                step="0.0001"
                value={config.learningRate} 
                onChange={(e) => setConfig({...config, learningRate: parseFloat(e.target.value)})}
                className="w-full p-2.5 rounded-xl border outline-none bg-transparent focus:border-emerald-500"
                style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>Image Size</label>
              <input 
                type="number" 
                value={config.imageSize} 
                onChange={(e) => setConfig({...config, imageSize: parseInt(e.target.value)})}
                className="w-full p-2.5 rounded-xl border outline-none bg-transparent focus:border-emerald-500"
                style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>Optimizer</label>
              <select 
                value={config.optimizer} 
                onChange={(e) => setConfig({...config, optimizer: e.target.value})}
                className="w-full p-2.5 rounded-xl border outline-none bg-transparent focus:border-emerald-500"
                style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
              >
                <option value="AdamW" style={{ backgroundColor: isDark ? '#1e293b' : '#fff' }}>AdamW</option>
                <option value="SGD" style={{ backgroundColor: isDark ? '#1e293b' : '#fff' }}>SGD</option>
                <option value="Adam" style={{ backgroundColor: isDark ? '#1e293b' : '#fff' }}>Adam</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>Weight Decay</label>
              <input 
                type="number" 
                step="0.0001"
                value={config.weightDecay} 
                onChange={(e) => setConfig({...config, weightDecay: parseFloat(e.target.value)})}
                className="w-full p-2.5 rounded-xl border outline-none bg-transparent focus:border-emerald-500"
                style={{ borderColor: 'var(--border-color)', color: 'var(--text-primary)' }}
              />
            </div>
          </div>
          
          <div className="mt-6 border-t pt-6" style={{ borderColor: 'var(--border-color)' }}>
            <h4 className="font-bold text-sm mb-4" style={{ color: 'var(--text-primary)' }}>Data Augmentation</h4>
            <div className="flex flex-wrap gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={config.augmentations?.includes('mosaic') || false}
                  onChange={(e) => {
                    const augs = config.augmentations || [];
                    setConfig({
                      ...config, 
                      augmentations: e.target.checked ? [...augs, 'mosaic'] : augs.filter(a => a !== 'mosaic')
                    });
                  }}
                  className="w-4 h-4 text-emerald-500 rounded focus:ring-emerald-500/20"
                />
                <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>Mosaic</span>
              </label>
              
              <label className="flex items-center gap-2 cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={config.augmentations?.includes('mixup') || false}
                  onChange={(e) => {
                    const augs = config.augmentations || [];
                    setConfig({
                      ...config, 
                      augmentations: e.target.checked ? [...augs, 'mixup'] : augs.filter(a => a !== 'mixup')
                    });
                  }}
                  className="w-4 h-4 text-emerald-500 rounded focus:ring-emerald-500/20"
                />
                <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>MixUp</span>
              </label>
              
              <label className="flex items-center gap-2 cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={config.augmentations?.includes('hflip') || false}
                  onChange={(e) => {
                    const augs = config.augmentations || [];
                    setConfig({
                      ...config, 
                      augmentations: e.target.checked ? [...augs, 'hflip'] : augs.filter(a => a !== 'hflip')
                    });
                  }}
                  className="w-4 h-4 text-emerald-500 rounded focus:ring-emerald-500/20"
                />
                <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>Horizontal Flip</span>
              </label>
            </div>
          </div>
        </motion.div>
      )}

      {/* Start Button */}
      <button
        onClick={handleStart}
        disabled={disabled || !activeDatasetId}
        className="w-full md:w-auto px-12 py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-2 text-white bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/40 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
      >
        <Target className="w-5 h-5" />
        Start {trainingMode === 'expert' ? 'Custom' : trainingMode === 'ultra' ? 'Ultra' : 'Fast'} Training
      </button>
    </div>
  );
};

export default CVTrainingConfigPanel;
