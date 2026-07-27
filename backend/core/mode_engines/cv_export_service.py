import os
import shutil
import zipfile
import json
from pathlib import Path
from typing import Dict, Any, List

class CVExportService:
    def __init__(self, export_dir: str = "cv_exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def generate_export_package(self, job: Dict[str, Any], formats: List[str]) -> Dict[str, Any]:
        """Generates a downloadable ZIP package with models, inference scripts, and docs."""
        job_id = job.get('id', 'unknown_job')
        package_dir = self.export_dir / f"export_{job_id}"
        package_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 1. Copy Model Weights
            model_path = job.get('model_path')
            models_out_dir = package_dir / "models"
            models_out_dir.mkdir(exist_ok=True)
            
            if model_path and os.path.exists(model_path):
                # Copy original PT file
                shutil.copy2(model_path, models_out_dir / "best.pt")
                
                # Mock generating other formats based on request
                # In real prod, this would invoke YOLO export functions
                for fmt in formats:
                    if fmt == 'onnx':
                        # Touch a fake ONNX file for demo
                        with open(models_out_dir / "best.onnx", 'w') as f:
                            f.write("MOCK_ONNX_DATA")
                    elif fmt == 'tflite':
                        with open(models_out_dir / "best.tflite", 'w') as f:
                            f.write("MOCK_TFLITE_DATA")
            else:
                # Fallback if no real model exists (e.g. simulation)
                with open(models_out_dir / "best.pt", 'w') as f:
                    f.write("MOCK_PT_WEIGHTS")
                    
            # 2. Generate Inference Script (Python)
            self._generate_inference_script(package_dir, job)
            
            # 3. Generate FastAPI Server
            if 'fastapi' in formats or 'docker' in formats:
                self._generate_fastapi_server(package_dir, job)
                
            # 4. Generate Dockerfile
            if 'docker' in formats:
                self._generate_dockerfile(package_dir)
                
            # 5. Generate Requirements & README
            self._generate_requirements(package_dir)
            self._generate_readme(package_dir, job)
            
            # 6. Save Metrics & Metadata
            with open(package_dir / "metadata.json", 'w') as f:
                json.dump({
                    'job_id': job_id,
                    'config': job.get('config', {}),
                    'metrics': job.get('metrics', {})
                }, f, indent=4)
                
            # 7. Create ZIP Archive
            zip_path = self.export_dir / f"datavision_model_{job_id}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(package_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, package_dir)
                        zipf.write(file_path, arcname)
                        
            # Clean up temp dir
            shutil.rmtree(package_dir, ignore_errors=True)
            
            return {
                'success': True,
                'zip_path': str(zip_path),
                'filename': zip_path.name,
                'size_mb': os.path.getsize(zip_path) / (1024 * 1024)
            }
            
        except Exception as e:
            if package_dir.exists():
                shutil.rmtree(package_dir, ignore_errors=True)
            return {'success': False, 'error': str(e)}

    def _generate_inference_script(self, out_dir: Path, job: Dict[str, Any]):
        script = f"""import cv2
from ultralytics import YOLO

# Load the exported model
model = YOLO('models/best.pt')

def predict_image(image_path):
    # Run inference
    results = model(image_path)
    
    # Process results
    for r in results:
        im_array = r.plot()  # plot a BGR numpy array of predictions
        cv2.imwrite('prediction_result.jpg', im_array)
        
        # Print detected classes and confidences
        for box in r.boxes:
            class_id = int(box.cls[0])
            conf = float(box.conf[0])
            class_name = model.names[class_id]
            print(f"Detected: {{class_name}} ({{conf:.2f}})")

if __name__ == '__main__':
    # Example usage
    # predict_image('test.jpg')
    print("Inference script ready. Run with predict_image('your_image.jpg')")
"""
        with open(out_dir / "inference.py", "w") as f:
            f.write(script)

    def _generate_fastapi_server(self, out_dir: Path, job: Dict[str, Any]):
        script = """from fastapi import FastAPI, UploadFile, File
import cv2
import numpy as np
from ultralytics import YOLO

app = FastAPI(title="DataVision CV Model Server")
model = YOLO('models/best.pt')

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.fromstring(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    results = model(img)
    
    predictions = []
    for r in results:
        for box in r.boxes:
            predictions.append({
                "class": model.names[int(box.cls[0])],
                "confidence": float(box.conf[0]),
                "bbox": box.xyxy[0].tolist()
            })
            
    return {"predictions": predictions}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
        with open(out_dir / "server.py", "w") as f:
            f.write(script)

    def _generate_dockerfile(self, out_dir: Path):
        dockerfile = """FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install OpenCV dependencies
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0

COPY . .

EXPOSE 8000
CMD ["python", "server.py"]
"""
        with open(out_dir / "Dockerfile", "w") as f:
            f.write(dockerfile)

    def _generate_requirements(self, out_dir: Path):
        reqs = """ultralytics>=8.0.0
opencv-python-headless>=4.8.0
fastapi>=0.100.0
uvicorn>=0.23.0
python-multipart>=0.0.6
"""
        with open(out_dir / "requirements.txt", "w") as f:
            f.write(reqs)

    def _generate_readme(self, out_dir: Path, job: Dict[str, Any]):
        metrics = job.get('metrics', {})
        readme = f"""# DataVision CV Model Export

This package contains your trained Computer Vision model and deployment scripts.

## Model Performance
- **mAP50**: {metrics.get('mAP50', 0):.3f}
- **Precision**: {metrics.get('precision', 0):.3f}
- **Recall**: {metrics.get('recall', 0):.3f}

## How to use

### Local Inference
1. Install requirements: `pip install -r requirements.txt`
2. Run script: `python inference.py`

### Run API Server
1. Install requirements
2. Run server: `python server.py`
3. Send POST request to `http://localhost:8000/predict` with an image file.

### Docker Deployment
1. Build: `docker build -t cv-model .`
2. Run: `docker run -p 8000:8000 cv-model`
"""
        with open(out_dir / "README.md", "w") as f:
            f.write(readme)
