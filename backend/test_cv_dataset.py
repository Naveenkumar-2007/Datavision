import os
import zipfile
import tempfile
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.mode_engines.cv_dataset_service import CVDatasetService

def create_dummy_zip():
    zip_path = "dummy_dataset.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        # Create a root folder like archive (1)
        zf.writestr('archive (1)/', '')
        zf.writestr('archive (1)/images/', '')
        zf.writestr('archive (1)/images/test1.jpg', 'fake image content')
        zf.writestr('archive (1)/annotations/', '')
        zf.writestr('archive (1)/annotations/test1.xml', 'fake annotation')
    return zip_path

if __name__ == "__main__":
    service = CVDatasetService(base_dir="test_cv_datasets")
    zip_path = create_dummy_zip()
    
    result = service.prepare_dataset(zip_path, "user_123", "archive (1).zip")
    print(result)
    
    os.unlink(zip_path)
