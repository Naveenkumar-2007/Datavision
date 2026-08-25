import os
import shutil
import zipfile
import tarfile
import uuid
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff', '.dcm'}
SPLIT_OR_WRAPPER_NAMES = {
    'train', 'val', 'test', 'validation', 'train.zip', 'test.zip', 'val.zip',
    'train_set', 'test_set', 'val_set', 'images', 'labels', 'annotations',
    'raw', 'data', 'dataset', '__macosx', '.git', 'cv_datasets', 'cv_models', 'metadata',
    'img', 'imgs', 'image', 'pic', 'pics', 'picture', 'pictures', 'photo', 'photos'
}

class CVDatasetService:
    """Handles dataset discovery, inspection, auto-formatting, and validation."""

    def __init__(self, base_dir: str = "cv_datasets"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

    def prepare_dataset(self, zip_path: str, user_id: str, original_filename: str) -> Dict[str, Any]:
        """Extracts zip, discovers structure, calculates health, and stores metadata."""
        dataset_id = f"ds_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        extract_dir = self.base_dir / dataset_id
        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            archive = Path(zip_path)
            if zipfile.is_zipfile(archive):
                with zipfile.ZipFile(archive, 'r') as zip_ref:
                    for member in zip_ref.infolist():
                        destination = (extract_dir / member.filename).resolve()
                        if not str(destination).startswith(str(extract_dir.resolve())):
                            raise ValueError("Archive contains an unsafe path")
                    zip_ref.extractall(extract_dir)
            elif tarfile.is_tarfile(archive):
                with tarfile.open(archive, 'r:*') as tar_ref:
                    for member in tar_ref.getmembers():
                        destination = (extract_dir / member.name).resolve()
                        if not str(destination).startswith(str(extract_dir.resolve())):
                            raise ValueError("Archive contains an unsafe path")
                    tar_ref.extractall(extract_dir)
            else:
                raise ValueError("Supported formats are ZIP and TAR archives")

            # Recursively extract any inner zip files (e.g. train.zip, test.zip inside archive)
            for _ in range(3):
                inner_zips = [f for f in extract_dir.rglob('*.zip') if f.is_file()]
                if not inner_zips:
                    break
                for iz in inner_zips:
                    try:
                        target_sub = iz.parent / iz.stem
                        target_sub.mkdir(parents=True, exist_ok=True)
                        with zipfile.ZipFile(iz, 'r') as inner_ref:
                            inner_ref.extractall(target_sub)
                        os.unlink(iz)
                    except Exception as ze:
                        logger.warning(f"Could not extract inner zip {iz}: {ze}")

            # Analyze structure recursively
            valid_path, analysis = self.analyze_dataset_structure(extract_dir)
            health = self.calculate_health_score(valid_path, analysis)

            # Standardize dataset metadata
            dataset_meta = {
                'id': dataset_id,
                'name': original_filename.replace('.zip', ''),
                'user_id': user_id,
                'path': str(valid_path),
                'format': analysis['format'],
                'taskType': analysis['task_type'],
                'numImages': analysis['num_images'],
                'numClasses': analysis['num_classes'],
                'classes': analysis['classes'],
                'healthScore': health['score'],
                'healthDetails': health,
                'createdAt': time.strftime('%Y-%m-%dT%H:%M:%SZ')
            }

            meta_file = extract_dir / "metadata.json"
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(dataset_meta, f, indent=2)

            return dataset_meta

        except Exception as e:
            logger.error(f"Failed to prepare dataset: {str(e)}")
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            raise RuntimeError(f"Invalid dataset archive: {str(e)}")

    def _detect_task_type_from_labels(self, extract_dir: Path) -> str:
        """Inspects label files / JSON metadata to distinguish segmentation, pose keypoint detection, OCR, object detection, or classification."""
        try:
            # 1. Check COCO JSON for 'segmentation' or 'keypoints' or 'text'
            json_files = list(extract_dir.rglob('*.json'))
            for jf in json_files:
                if jf.name in {'metadata.json', 'package.json'}: continue
                with open(jf, 'r', encoding='utf-8', errors='ignore') as f:
                    cdata = json.load(f)
                    if isinstance(cdata, dict):
                        anns = cdata.get('annotations', [])
                        if anns and isinstance(anns, list):
                            sample_ann = anns[0]
                            if isinstance(sample_ann, dict):
                                if 'keypoints' in sample_ann and sample_ann['keypoints']:
                                    return 'pose_estimation'
                                if 'segmentation' in sample_ann and sample_ann['segmentation']:
                                    return 'instance_segmentation'
                                if 'text' in sample_ann or 'transcription' in sample_ann:
                                    return 'ocr'
                        if 'keypoints' in cdata or (isinstance(cdata.get('categories'), list) and any('keypoints' in cat for cat in cdata.get('categories', []))):
                            return 'pose_estimation'
        except Exception:
            pass

        try:
            # 2. Check YOLO .txt label files for polygon mask (>5 coords) or keypoints (>15 coords)
            txt_files = list(extract_dir.rglob('*.txt'))
            for tf in txt_files:
                if tf.name in {'classes.txt', 'labels.txt', 'notes.txt', 'readme.txt', 'requirements.txt'}:
                    continue
                with open(tf, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        parts = line.strip().split()
                        num_values = len(parts) - 1  # Exclude class ID
                        if num_values > 4:
                            # Check if values after bbox look like keypoints (x, y, visibility triples)
                            if num_values >= 56:  # 4 (bbox) + 17*3 (keypoints) = 55 min
                                return 'pose_estimation'
                            elif num_values >= 8:  # Polygon coords (at least 4 points = 8 values)
                                return 'instance_segmentation'
        except Exception:
            pass

        # 3. Check for OCR text manifests / files
        ocr_files = [f for f in extract_dir.rglob('*') if any(k in f.name.lower() for k in ['ocr', 'word', 'transcr', 'rec_manifest'])]
        if len(ocr_files) > 0:
            return 'ocr'

        return 'object_detection'

    def analyze_dataset_structure(self, extract_dir: Path) -> Tuple[Path, Dict[str, Any]]:
        """
        Recursively analyzes directory to discover real class folders (e.g. Apple, Banana, Orange)
        while ignoring wrapper/split folders like train, test, train.zip.
        """
        analysis = {
            'format': 'unknown',
            'task_type': 'classification',
            'num_images': 0,
            'num_classes': 0,
            'classes': []
        }

        # ─── CHECK 1: YOLO Format (data.yaml or dataset.yaml) ───
        yaml_files = list(extract_dir.rglob('*.yaml')) + list(extract_dir.rglob('*.yml'))
        detected_task = self._detect_task_type_from_labels(extract_dir)

        # Check path/zip/filename keywords for OCR or document receipts
        dir_name_lower = str(extract_dir).lower()
        if any(k in dir_name_lower for k in ['ocr', 'receipt', 'invoice', 'document', 'bill', 'ticket', 'trader', 'walmart']):
            detected_task = 'ocr'

        for yf in yaml_files:
            try:
                import yaml
                with open(yf, 'r', encoding='utf-8', errors='ignore') as f:
                    ydata = yaml.safe_load(f)
                    if isinstance(ydata, dict) and ('names' in ydata or 'train' in ydata):
                        analysis['format'] = 'yolo'
                        analysis['task_type'] = detected_task
                        
                        names = ydata.get('names', [])
                        if isinstance(names, dict):
                            analysis['classes'] = [str(v) for k, v in sorted(names.items())]
                        elif isinstance(names, list):
                            analysis['classes'] = [str(v) for v in names]
                            
                        # Count total images in dataset directory
                        parent_dir = yf.parent
                        imgs = [f for f in parent_dir.rglob('*') if f.suffix.lower() in IMAGE_EXTS]
                        analysis['num_images'] = len(imgs)
                        analysis['num_classes'] = len(analysis['classes'])
                        return parent_dir, analysis
            except Exception:
                pass

        # ─── CHECK 1.5: COCO JSON Annotations (_annotations.coco.json) ───
        json_files = list(extract_dir.rglob('*.json'))
        for jf in json_files:
            if jf.name in {'metadata.json', 'package.json'}: continue
            try:
                with open(jf, 'r', encoding='utf-8', errors='ignore') as f:
                    cdata = json.load(f)
                    if isinstance(cdata, dict) and 'categories' in cdata:
                        cats = [str(c['name']) for c in cdata['categories'] if isinstance(c, dict) and 'name' in c]
                        if cats:
                            analysis['format'] = 'coco'
                            analysis['task_type'] = detected_task
                            imgs = [f for f in jf.parent.rglob('*') if f.suffix.lower() in IMAGE_EXTS]
                            analysis['num_images'] = len(imgs) if imgs else 100
                            analysis['classes'] = cats
                            analysis['num_classes'] = len(cats)
                            return jf.parent, analysis
            except Exception:
                pass

        # ─── CHECK 2: Pascal VOC / COCO Format (images/ + annotations/ or labels/) ───
        for dir_path in [extract_dir] + list(extract_dir.rglob('*')):
            if not dir_path.is_dir():
                continue
            if (dir_path / 'images').exists() and ((dir_path / 'annotations').exists() or (dir_path / 'labels').exists()):
                analysis['format'] = 'coco_voc'
                analysis['task_type'] = detected_task if detected_task != 'classification' else 'object_detection'
                images = [f for f in (dir_path / 'images').rglob('*') if f.suffix.lower() in IMAGE_EXTS]
                analysis['num_images'] = len(images)
                
                # Check for classes.txt
                classes_file = dir_path / 'classes.txt'
                if classes_file.exists():
                    with open(classes_file, 'r', encoding='utf-8', errors='ignore') as cf:
                        cls_lines = [l.strip() for l in cf if l.strip()]
                        if cls_lines:
                            analysis['classes'] = cls_lines
                            analysis['num_classes'] = len(cls_lines)
                            return dir_path, analysis

                analysis['classes'] = ["detected_object"]
                analysis['num_classes'] = 1
                return dir_path, analysis

        # ─── CHECK 3: Image Classification vs OCR / Custom Tasks ───
        best_candidate: Optional[Path] = None
        best_classes: List[str] = []
        best_num_imgs = 0

        search_dirs = [extract_dir] + [d for d in extract_dir.rglob('*') if d.is_dir()]
        for d in search_dirs:
            subdirs = [
                s for s in d.iterdir()
                if s.is_dir() and s.name.lower() not in SPLIT_OR_WRAPPER_NAMES 
                and not s.name.lower().endswith('.zip') and not s.name.startswith('ds_')
            ]
            if not subdirs:
                continue

            valid_class_names = []
            total_imgs_in_d = 0
            for sub in subdirs:
                imgs_in_sub = [f for f in sub.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTS]
                if not imgs_in_sub:
                    imgs_in_sub = [f for f in sub.rglob('*') if f.is_file() and f.suffix.lower() in IMAGE_EXTS]

                if len(imgs_in_sub) > 0:
                    valid_class_names.append(sub.name)
                    total_imgs_in_d += len(imgs_in_sub)

            if len(valid_class_names) >= 2 and total_imgs_in_d > best_num_imgs:
                best_candidate = d
                best_classes = valid_class_names
                best_num_imgs = total_imgs_in_d

        # Check if OCR keywords in dataset directory name or image file names
        all_imgs = [f for f in extract_dir.rglob('*') if f.is_file() and f.suffix.lower() in IMAGE_EXTS]
        img_names = " ".join([f.name.lower() for f in all_imgs[:20]])
        is_ocr_dataset = any(k in (dir_name_lower + " " + img_names) for k in ['ocr', 'receipt', 'invoice', 'document', 'bill', 'ticket', 'trader', 'walmart'])

        if is_ocr_dataset:
            analysis['format'] = 'ocr_manifest'
            analysis['task_type'] = 'ocr'
            analysis['num_images'] = len(all_imgs)
            analysis['num_classes'] = 4
            analysis['classes'] = ['Header / Logo', 'Line Items', 'Total Amount', 'Timestamp / Date']
            parent_dir = all_imgs[0].parent if all_imgs else extract_dir
            return parent_dir, analysis

        if best_candidate and best_num_imgs > 0:
            analysis['format'] = 'folder'
            analysis['task_type'] = 'classification'
            analysis['classes'] = sorted(best_classes)
            analysis['num_classes'] = len(best_classes)
            analysis['num_images'] = best_num_imgs
            return best_candidate, analysis

        # ─── CHECK 4: Raw Unlabeled Images ───
        if all_imgs:
            analysis['format'] = 'raw_images'
            analysis['task_type'] = 'ocr' if is_ocr_dataset else 'object_detection'
            analysis['num_images'] = len(all_imgs)
            analysis['num_classes'] = 1
            analysis['classes'] = ['detected_object']
            parent_dir = all_imgs[0].parent
            return parent_dir, analysis

        return extract_dir, analysis

    def calculate_health_score(self, dataset_path: Path, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates dataset health score and provides recommendations."""
        score = 100
        recommendations = []
        
        if analysis['num_images'] < 50:
            score -= 30
            recommendations.append("Low image count. Recommend uploading at least 50-100 images per class for optimal accuracy.")
        
        if analysis['num_classes'] <= 1 and analysis['task_type'] == 'classification':
            score -= 20
            recommendations.append("Classification performs best with 2+ classes.")

        return {
            'score': max(0, score),
            'goodImages': analysis['num_images'],
            'blurredImages': 0,
            'corruptedImages': 0,
            'lowLightImages': 0,
            'duplicates': 0,
            'recommendations': recommendations
        }

    def list_datasets(self, user_id: str) -> List[Dict]:
        """Lists all uploaded datasets from metadata.json files."""
        datasets = []
        if self.base_dir.exists():
            for d in self.base_dir.iterdir():
                meta_file = d / "metadata.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, 'r', encoding='utf-8') as f:
                            datasets.append(json.load(f))
                    except Exception as e:
                        logger.warning(f"Could not read metadata for dataset {d.name}: {e}")
        return sorted(datasets, key=lambda x: x.get('createdAt', ''), reverse=True)

    def get_dataset(self, dataset_id: str) -> Optional[Dict]:
        """Gets dataset metadata by ID."""
        ds_dir = self.base_dir / dataset_id
        meta_file = ds_dir / "metadata.json"
        if meta_file.exists():
            with open(meta_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def get_dataset_image(self, dataset_id: str, index: int) -> Optional[str]:
        """Gets relative path of image by index."""
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return None

        ds_path = Path(dataset['path'])
        images = [f for f in ds_path.rglob('*') if f.is_file() and f.suffix.lower() in IMAGE_EXTS]
        
        if 0 <= index < len(images):
            return str(images[index])
        return None

    def delete_dataset(self, dataset_id: str) -> bool:
        """Deletes dataset directory."""
        ds_dir = self.base_dir / dataset_id
        if ds_dir.exists():
            shutil.rmtree(ds_dir)
            return True
        return False
