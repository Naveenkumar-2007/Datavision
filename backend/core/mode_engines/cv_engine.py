import logging
from typing import Dict, Any, List, Optional
import base64
import numpy as np
try:
    import cv2
except ImportError:
    cv2 = None
import os
from pathlib import Path

from core.mode_engines.cv_dataset_service import CVDatasetService
from core.mode_engines.cv_trainer import CVTrainer
from core.mode_engines.cv_export_service import CVExportService

logger = logging.getLogger(__name__)

class CVAutoMLEngine:
    """Enhanced Computer Vision AutoML Engine supporting Classification, Detection, Segmentation, Keypoints, and OCR."""

    def __init__(self):
        self.model = None
        self.model_type = None
        self._model_cache_key = None  # (model_path, task_type) tuple for caching
        self.models_dir = Path("cv_models")
        self.datasets_dir = Path("cv_datasets")
        self.models_dir.mkdir(exist_ok=True)
        self.datasets_dir.mkdir(exist_ok=True)
        
        # Sub-services
        self.dataset_service = CVDatasetService(base_dir=str(self.datasets_dir))
        self.trainer = CVTrainer(models_dir=str(self.models_dir))
        self.export_service = CVExportService()

    # ─────────────────────────────────────────────────────
    # DATASET DELEGATION
    # ─────────────────────────────────────────────────────
    def prepare_dataset(self, zip_path: str, user_id: str, original_filename: str) -> Dict[str, Any]:
        return self.dataset_service.prepare_dataset(zip_path, user_id, original_filename)

    def list_datasets(self, user_id: str) -> List[Dict]:
        return self.dataset_service.list_datasets(user_id)
        
    def get_dataset(self, dataset_id: str) -> Optional[Dict]:
        return self.dataset_service.get_dataset(dataset_id)
        
    def get_dataset_image(self, dataset_id: str, index: int) -> Optional[str]:
        return self.dataset_service.get_dataset_image(dataset_id, index)
        
    def delete_dataset(self, dataset_id: str) -> bool:
        return self.dataset_service.delete_dataset(dataset_id)

    # ─────────────────────────────────────────────────────
    # TRAINING & MODEL MANAGEMENT
    # ─────────────────────────────────────────────────────
    def train_model(self, dataset_id: str, config: Dict, task_id: str, mode: str = 'fast', user_id: str = 'anonymous', task_type: Optional[str] = None) -> str:
        dataset_meta = self.get_dataset(dataset_id)
        dataset_path = dataset_meta.get('path') if dataset_meta else None
        resolved_task_type = task_type or (dataset_meta.get('taskType', 'object_detection') if dataset_meta else 'object_detection')
        classes = dataset_meta.get('classes', []) if dataset_meta else []
        
        return self.trainer.start_training(dataset_id, user_id, mode, config, dataset_path=dataset_path, task_type=resolved_task_type, classes=classes)

    def get_training_progress(self, job_id: str) -> Dict:
        progress = self.trainer.get_progress(job_id)
        if not progress:
            return {'status': 'not_found'}
        return progress

    def stop_training(self, job_id: str) -> bool:
        return self.trainer.stop_training(job_id)
        
    def pause_training(self, job_id: str) -> bool:
        return self.trainer.pause_training(job_id)
        
    def resume_training(self, job_id: str) -> bool:
        return self.trainer.resume_training(job_id)

    def list_models(self) -> List[Dict[str, Any]]:
        """Lists all trained models with real performance metrics for Model Hub."""
        models = []
        if self.models_dir.exists():
            for d in self.models_dir.iterdir():
                if d.is_dir() and (d / 'train' / 'weights' / 'best.pt').exists():
                    job_progress = self.trainer.get_progress(d.name) or {}
                    meta = job_progress.get('metrics', {})
                    task_type = job_progress.get('task_type') or job_progress.get('config', {}).get('task_type') or meta.get('task_type', 'object_detection')
                    models.append({
                        'id': d.name,
                        'name': f"{job_progress.get('config', {}).get('model', 'yolov8n').upper()} - {task_type.replace('_', ' ').title()}",
                        'task': task_type.replace('_', ' ').title(),
                        'mAP50': meta.get('mAP50', 0.0),
                        'accuracy': meta.get('accuracy', 0.0),
                        'size_mb': meta.get('modelSizeMB', 0.0),
                        'status': 'ready',
                        'task_type': task_type,
                        'classes': job_progress.get('classes', []),
                        'createdAt': job_progress.get('started_at', '')
                    })
        return models

    def export_model(self, job_id: str, formats: List[str]) -> Dict[str, Any]:
        """Generates downloadable model ZIP package."""
        job = self.trainer.get_progress(job_id) or {'id': job_id}
        return self.export_service.generate_export_package(job, formats)

    def find_latest_trained_model(self, user_id: str = None) -> tuple:
        """Find the most recent best.pt trained model for this user.
        Returns (model_path, task_type) or (None, None) if no trained model exists."""
        try:
            best_models = list(self.models_dir.glob('*/train/weights/best.pt'))
            if not best_models:
                best_models = list(self.models_dir.glob('*/train/weights/last.pt'))
            if not best_models:
                return None, None
            
            # Sort by modification time, newest first
            latest = max(best_models, key=lambda p: p.stat().st_mtime)
            job_id = latest.parent.parent.parent.name
            
            # Get task type — check multiple locations for backwards compatibility
            progress = self.trainer.get_progress(job_id)
            task_type = None
            if progress:
                # Priority: job-level > config > metrics
                task_type = (
                    progress.get('task_type') or 
                    progress.get('config', {}).get('task_type') or 
                    progress.get('metrics', {}).get('task_type')
                )
                # If user_id specified, only match models trained by this user
                if user_id and progress.get('user_id') and progress.get('user_id') != user_id:
                    for m in sorted(best_models, key=lambda p: p.stat().st_mtime, reverse=True):
                        jid = m.parent.parent.parent.name
                        prog = self.trainer.get_progress(jid)
                        if prog and prog.get('user_id') == user_id:
                            latest = m
                            task_type = (
                                prog.get('task_type') or 
                                prog.get('config', {}).get('task_type') or 
                                prog.get('metrics', {}).get('task_type')
                            )
                            break
            
            logger.info(f"Auto-discovered trained model: {latest} (task: {task_type})")
            return str(latest), task_type
        except Exception as e:
            logger.warning(f"Could not auto-discover trained model: {e}")
            return None, None

    # ─────────────────────────────────────────────────────
    # REAL-WORLD ENTERPRISE COMPUTER VISION INFERENCE ENGINE
    # ─────────────────────────────────────────────────────
    def initialize_model(self, model_path: Optional[str] = None, task_type: Optional[str] = None):
        """Load the YOLO model with caching. Selects the correct architecture based on task_type.
        Custom model_path always takes priority over pretrained.
        Models are cached by (model_path, task_type) to avoid reload on every prediction."""
        cache_key = (model_path, task_type)
        
        # Return cached model if same path and task
        if self._model_cache_key == cache_key and self.model is not None:
            logger.debug(f"Using cached model: {cache_key}")
            return True
        
        try:
            from ultralytics import YOLO
            
            if model_path and os.path.exists(model_path):
                # Always trust the user's trained custom model
                self.model = YOLO(model_path)
                self.model_type = 'yolo_custom'
                self._model_cache_key = cache_key
                custom_names = getattr(self.model, 'names', {})
                logger.info(f"Loaded custom model: {model_path} with {len(custom_names)} classes: {list(custom_names.values())[:10]}")
                return True
            
            # No custom model — select correct pretrained architecture based on task type
            task_model_map = {
                'classification': 'yolov8s-cls.pt',
                'instance_segmentation': 'yolov8s-seg.pt',
                'semantic_segmentation': 'yolov8s-seg.pt',
                'pose_estimation': 'yolov8s-pose.pt',
                'object_detection': 'yolov8s.pt',
                'ocr': 'yolov8s.pt',
            }
            model_file = task_model_map.get(task_type, 'yolov8s.pt')
            
            try:
                self.model = YOLO(model_file)
            except Exception:
                # Fallback to base detection model if task-specific weights unavailable
                logger.warning(f"Could not load {model_file}, falling back to yolov8s.pt")
                self.model = YOLO('yolov8s.pt')
            
            self.model_type = 'yolo'
            self._model_cache_key = cache_key
            logger.info(f"Loaded pretrained model: {model_file} for task: {task_type or 'general'}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self._model_cache_key = None
            return False

    def predict_image(self, base64_image: str, model_path: Optional[str] = None, task_type: Optional[str] = None, conf: float = 0.25, iou: float = 0.45) -> Dict[str, Any]:
        """
        Runs dynamic inference reading actual model class names with zero hardcoding.
        Selects the correct model architecture based on task_type.
        When a custom model_path is provided, ALWAYS uses it.
        """
        has_custom_model = model_path and os.path.exists(model_path)
        success = self.initialize_model(model_path, task_type=task_type)
        if not success or not self.model:
            if has_custom_model:
                return {"success": False, "error": "Failed to load your trained model. Please retrain."}
            return {"success": False, "error": "YOLO model not available. Install ultralytics: pip install ultralytics"}

        try:
            # Decode base64 image
            img_data = base64.b64decode(base64_image.split(',')[1] if ',' in base64_image else base64_image)
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return {"success": False, "error": "Failed to decode image. Please upload a valid image file."}

            h, w, c = img.shape

            # Detect model architecture task if not explicitly provided
            model_task = getattr(self.model, 'task', None)
            if model_task:
                task_map = {
                    'classify': 'classification',
                    'segment': 'instance_segmentation',
                    'pose': 'pose_estimation',
                    'detect': 'object_detection',
                    'obb': 'oriented_bounding_box'
                }
                if not task_type or task_type in {'general', 'auto', 'cv'}:
                    task_type = task_map.get(model_task, task_type or 'object_detection')

            resolved_task = task_type or 'object_detection'

            # Run inference with confidence threshold & IOU threshold
            # Lower confidence threshold for custom models to ensure detections aren't missed
            effective_conf = conf if not has_custom_model else max(0.1, conf - 0.1)
            results = self.model(img, conf=effective_conf, iou=iou)
            if not results or len(results) == 0:
                if has_custom_model:
                    return {
                        "success": True, "is_low_confidence": True, "task_type": resolved_task,
                        "class": "No Detections", "confidence": 0.0,
                        "predictions": [{"class": "No Detections", "confidence": 0.0}],
                        "processed_image": base64_image, "model": "Custom Trained Model"
                    }
                return {
                    "success": True, "is_low_confidence": True, "task_type": resolved_task,
                    "class": "No Detections", "confidence": 0.0,
                    "predictions": [{"class": "No Detections", "confidence": 0.0}],
                    "processed_image": base64_image, "model": "YOLOv8 Pretrained"
                }

            result = results[0]
            predictions = []

            # Only use dataset classes as fallback for pretrained models, not custom trained
            ds_classes = []
            if self.model_type != 'yolo_custom':
                try:
                    datasets = self.dataset_service.list_datasets('anonymous')
                    ds_classes = datasets[0]['classes'] if datasets and datasets[0].get('classes') else []
                except Exception:
                    pass

            # ─── 1. OBJECT DETECTION, SEGMENTATION, KEYPOINTS, & OCR ───
            if hasattr(result, 'boxes') and result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes
                names = result.names or getattr(self.model, 'names', {})
                
                raw_boxes = []
                confidences = []
                class_ids = []

                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    b_conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    
                    if b_conf >= conf:
                        raw_boxes.append([int(x1), int(y1), int(x2 - x1), int(y2 - y1)])
                        confidences.append(float(b_conf))
                        class_ids.append(cls_id)

                # Perform Non-Maximum Suppression (NMS) to eliminate duplicate overlapping boxes
                indices = []
                if raw_boxes:
                    indices = cv2.dnn.NMSBoxes(raw_boxes, confidences, conf, iou)

                final_boxes = []
                if len(indices) > 0:
                    indices = indices.flatten() if hasattr(indices, 'flatten') else indices
                    for i in indices:
                        x, y, bw, bh = raw_boxes[i]
                        b_conf = confidences[i]
                        cls_id = class_ids[i]
                        raw_name = names.get(cls_id, f"Object_{cls_id}")
                        class_name = str(raw_name).replace('_', ' ').title()

                        # Only use dataset class fallback for pretrained models, never for custom
                        if self.model_type != 'yolo_custom' and class_name.lower() in {'object', 'detected object', 'default class'} and ds_classes:
                            class_name = str(ds_classes[min(cls_id, len(ds_classes)-1)]).replace('_', ' ').title()

                        final_boxes.append({
                            "class": class_name,
                            "confidence": b_conf,
                            "bbox": [x, y, x + bw, y + bh]
                        })

                        # High-Contrast Neon Color Palette for Multi-Object Visualizations (BGR)
                        colors = [
                            (127, 255, 0),   # Neon Emerald
                            (255, 255, 0),   # Neon Cyan
                            (0, 200, 255),   # Neon Yellow-Orange
                            (255, 0, 255),   # Neon Magenta/Pink
                            (255, 128, 0)    # Neon Violet-Blue
                        ]
                        box_color = colors[cls_id % len(colors)]

                        # Draw bold bounding box
                        cv2.rectangle(img, (x, y), (x + bw, y + bh), box_color, 3)

                        # Draw filled background pill for text label for maximum readability
                        label_str = f" {class_name}: {b_conf*100:.1f}% "
                        (text_w, text_h), baseline = cv2.getTextSize(label_str, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                        label_y = max(text_h + 8, y - 6)
                        cv2.rectangle(img, (x, label_y - text_h - 6), (x + text_w, label_y + 4), box_color, -1)
                        cv2.putText(img, label_str, (x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2, cv2.LINE_AA)

                # ─── INSTANCE SEGMENTATION OVERLAY ───
                if hasattr(result, 'masks') and result.masks is not None and len(result.masks) > 0:
                    try:
                        mask_overlay = img.copy()
                        palette = [
                            (255, 255, 0),   # Neon Cyan
                            (255, 0, 255),   # Neon Magenta
                            (0, 255, 255),   # Neon Yellow
                            (0, 255, 128),   # Neon Spring Green
                            (255, 128, 0)    # Neon Blue
                        ]
                        for m_idx, mask_xy in enumerate(result.masks.xy):
                            if len(mask_xy) > 0:
                                pts = np.int32([mask_xy])
                                color = palette[m_idx % len(palette)]
                                cv2.fillPoly(mask_overlay, pts, color)
                                cv2.polylines(img, pts, True, color, 4)
                        cv2.addWeighted(mask_overlay, 0.45, img, 0.55, 0, img)
                    except Exception as me:
                        logger.warning(f"Mask rendering warning: {me}")

                # ─── KEYPOINT POSE SKELETON OVERLAY ───
                if hasattr(result, 'keypoints') and result.keypoints is not None and len(result.keypoints) > 0:
                    try:
                        skeleton_pairs = [
                            (0, 1), (0, 2), (1, 3), (2, 4), (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
                            (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16)
                        ]
                        for kp_person in result.keypoints.xy:
                            pts_dict = {}
                            for idx, pt in enumerate(kp_person):
                                kx, ky = int(pt[0]), int(pt[1])
                                if kx > 0 and ky > 0:
                                    pts_dict[idx] = (kx, ky)
                                    # Large 8px vibrant outer circle + 3px white inner core for maximum visibility
                                    cv2.circle(img, (kx, ky), 8, (255, 0, 255), -1, cv2.LINE_AA) # Neon Pink
                                    cv2.circle(img, (kx, ky), 3, (255, 255, 255), -1, cv2.LINE_AA)
                            for p1, p2 in skeleton_pairs:
                                if p1 in pts_dict and p2 in pts_dict:
                                    # Bold 4px Skeleton connection line in Neon Cyan
                                    cv2.line(img, pts_dict[p1], pts_dict[p2], (255, 255, 0), 4, cv2.LINE_AA)
                    except Exception as ke:
                        logger.warning(f"Keypoint rendering warning: {ke}")

                if not final_boxes:
                    banner_height = 40
                    overlay = img.copy()
                    cv2.rectangle(overlay, (0, 0), (w, banner_height), (100, 116, 139), -1)
                    cv2.addWeighted(overlay, 0.85, img, 0.15, 0, img)
                    cv2.putText(img, "NO TARGET OBJECTS DETECTED", (15, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
                    
                    _, buffer = cv2.imencode('.jpg', img)
                    out_base64 = base64.b64encode(buffer).decode('utf-8')

                    return {
                        "success": True,
                        "is_low_confidence": True,
                        "task_type": task_type or "object_detection",
                        "class": "No Objects Detected",
                        "confidence": 0.0,
                        "predictions": [{"class": "No Objects Detected", "confidence": 0.0}],
                        "processed_image": f"data:image/jpeg;base64,{out_base64}",
                        "model": self.model_type or "YOLOv8"
                    }

                # Sort by confidence
                final_boxes = sorted(final_boxes, key=lambda x: x['confidence'], reverse=True)
                top_pred = final_boxes[0]

                # Determine active task type from actual model output
                detected_task_type = task_type or "object_detection"
                if hasattr(result, 'masks') and result.masks is not None and len(result.masks) > 0:
                    detected_task_type = "instance_segmentation"
                elif hasattr(result, 'keypoints') and result.keypoints is not None and len(result.keypoints) > 0:
                    detected_task_type = "pose_estimation"

                # Draw top prediction banner
                banner_height = 40
                overlay = img.copy()
                banner_col = (16, 185, 129) if detected_task_type != "ocr" else (249, 115, 22)
                cv2.rectangle(overlay, (0, 0), (w, banner_height), banner_col, -1)
                cv2.addWeighted(overlay, 0.85, img, 0.15, 0, img)
                
                banner_text = f"{top_pred['class'].upper()}: {top_pred['confidence']*100:.1f}%"
                cv2.putText(img, banner_text, (15, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

                _, buffer = cv2.imencode('.jpg', img)
                out_base64 = base64.b64encode(buffer).decode('utf-8')

                return {
                    "success": True,
                    "is_low_confidence": False,
                    "task_type": detected_task_type,
                    "class": top_pred["class"],
                    "confidence": top_pred["confidence"],
                    "predictions": final_boxes,
                    "processed_image": f"data:image/jpeg;base64,{out_base64}",
                    "model": f"YOLOv8 Real-World {detected_task_type.replace('_', ' ').title()}"
                }

            # ─── 2. CLASSIFICATION MODEL (result.probs) ───
            elif hasattr(result, 'probs') and result.probs is not None:
                probs = result.probs
                names = result.names or getattr(self.model, 'names', {})
                top1_idx = int(probs.top1)
                top1_conf = float(probs.top1conf)
                raw_top1 = names.get(top1_idx, f"Class_{top1_idx}")
                top1_name = str(raw_top1).replace('_', ' ').title()

                top5_indices = probs.top5 if hasattr(probs, 'top5') else [top1_idx]
                for idx in top5_indices:
                    cls_name = str(names.get(int(idx), f"Class_{idx}")).replace('_', ' ').title()
                    confidence = float(probs.data[int(idx)]) if hasattr(probs, 'data') else top1_conf
                    predictions.append({
                        "class": cls_name,
                        "confidence": float(confidence)
                    })

                # Draw Prediction Banner on top of image
                banner_height = 40
                overlay = img.copy()
                cv2.rectangle(overlay, (0, 0), (w, banner_height), (16, 185, 129), -1)
                cv2.addWeighted(overlay, 0.85, img, 0.15, 0, img)
                
                text = f"{top1_name.upper()}: {top1_conf*100:.1f}%"
                cv2.putText(img, text, (15, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

                _, buffer = cv2.imencode('.jpg', img)
                out_base64 = base64.b64encode(buffer).decode('utf-8')

                return {
                    "success": True,
                    "is_low_confidence": False,
                    "task_type": "classification",
                    "class": top1_name,
                    "confidence": top1_conf,
                    "predictions": predictions,
                    "processed_image": f"data:image/jpeg;base64,{out_base64}",
                    "model": "YOLO Classifier"
                }

            if has_custom_model:
                return {
                    "success": True, "is_low_confidence": True, "task_type": resolved_task,
                    "class": "Unrecognized", "confidence": 0.0,
                    "predictions": [{"class": "Unrecognized", "confidence": 0.0}],
                    "processed_image": base64_image, "model": "Custom Trained Model"
                }
            return {
                "success": True, "is_low_confidence": True, "task_type": resolved_task,
                "class": "Unrecognized", "confidence": 0.0,
                "predictions": [{"class": "Unrecognized", "confidence": 0.0}],
                "processed_image": base64_image, "model": "YOLOv8 Pretrained"
            }

        except Exception as e:
            logger.error(f"CV Engine Error: {str(e)}")
            return {"success": False, "error": f"Prediction failed: {str(e)}"}
            
    def _no_model_response(self, message: str = "No model available") -> Dict[str, Any]:
        """Returns an honest error response when no model is available."""
        return {
            "success": False,
            "error": message,
            "task_type": "unknown",
            "class": "No Model",
            "confidence": 0.0,
            "predictions": [],
            "model": "None"
        }
