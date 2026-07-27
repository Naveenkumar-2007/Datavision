import os
import zipfile
import json
import numpy as np
import cv2
from pathlib import Path

out_dir = Path("sample_cv_test_datasets")
out_dir.mkdir(exist_ok=True)

def create_sample_img(filename, color=(0, 200, 100)):
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.rectangle(img, (50, 50), (250, 250), color, -1)
    cv2.putText(img, "TEST DATASET", (60, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imwrite(filename, img)

# 1. Instance Segmentation ZIP Dataset
seg_dir = out_dir / "sample_instance_segmentation"
seg_dir.mkdir(exist_ok=True)
create_sample_img(str(seg_dir / "car_sample.jpg"), (220, 50, 50))
coco_seg = {
    "images": [{"id": 1, "file_name": "car_sample.jpg", "height": 300, "width": 300}],
    "categories": [{"id": 1, "name": "vehicle_segmentation"}],
    "annotations": [{
        "id": 1, "image_id": 1, "category_id": 1,
        "segmentation": [[50, 50, 250, 50, 250, 250, 50, 250]],
        "bbox": [50, 50, 200, 200], "area": 40000, "iscrowd": 0
    }]
}
with open(seg_dir / "_annotations.coco.json", "w") as f:
    json.dump(coco_seg, f, indent=2)

with zipfile.ZipFile(out_dir / "Instance_Segmentation_Test_Dataset.zip", "w") as z:
    z.write(seg_dir / "car_sample.jpg", "car_sample.jpg")
    z.write(seg_dir / "_annotations.coco.json", "_annotations.coco.json")

# 2. Keypoint Detection ZIP Dataset
pose_dir = out_dir / "sample_keypoint_pose"
pose_dir.mkdir(exist_ok=True)
create_sample_img(str(pose_dir / "person_pose.jpg"), (50, 100, 250))
coco_pose = {
    "images": [{"id": 1, "file_name": "person_pose.jpg", "height": 300, "width": 300}],
    "categories": [{"id": 1, "name": "human_pose", "keypoints": ["nose", "left_eye", "right_eye", "left_shoulder", "right_shoulder"]}],
    "annotations": [{
        "id": 1, "image_id": 1, "category_id": 1,
        "keypoints": [150, 100, 2, 140, 90, 2, 160, 90, 2, 100, 180, 2, 200, 180, 2],
        "bbox": [50, 50, 200, 200], "num_keypoints": 5, "area": 40000, "iscrowd": 0
    }]
}
with open(pose_dir / "_annotations.coco.json", "w") as f:
    json.dump(coco_pose, f, indent=2)

with zipfile.ZipFile(out_dir / "Keypoint_Detection_Test_Dataset.zip", "w") as z:
    z.write(pose_dir / "person_pose.jpg", "person_pose.jpg")
    z.write(pose_dir / "_annotations.coco.json", "_annotations.coco.json")

# 3. OCR Text Extraction ZIP Dataset
ocr_dir = out_dir / "sample_ocr_dataset"
ocr_dir.mkdir(exist_ok=True)
create_sample_img(str(ocr_dir / "ocr_text.jpg"), (10, 180, 220))
coco_ocr = {
    "images": [{"id": 1, "file_name": "ocr_text.jpg", "height": 300, "width": 300}],
    "categories": [{"id": 1, "name": "text_block"}],
    "annotations": [{
        "id": 1, "image_id": 1, "category_id": 1,
        "text": "TEST DATASET",
        "bbox": [60, 140, 180, 40], "area": 7200, "iscrowd": 0
    }]
}
with open(ocr_dir / "_annotations.coco.json", "w") as f:
    json.dump(coco_ocr, f, indent=2)

with zipfile.ZipFile(out_dir / "OCR_Text_Test_Dataset.zip", "w") as z:
    z.write(ocr_dir / "ocr_text.jpg", "ocr_text.jpg")
    z.write(ocr_dir / "_annotations.coco.json", "_annotations.coco.json")

print("Generated sample benchmark test datasets cleanly.")
