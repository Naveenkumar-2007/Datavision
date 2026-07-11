import os
import shutil
from typing import Optional

# Base storage directory
STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "user-files")
os.makedirs(STORAGE_DIR, exist_ok=True)

class LocalStorage:
    def __init__(self):
        self.available = True
    
    def _get_user_dir(self, user_id: str) -> str:
        d = os.path.join(STORAGE_DIR, user_id)
        os.makedirs(d, exist_ok=True)
        return d

    def upload_file(self, user_id: str, filename: str, file_data: bytes, content_type: str = "application/octet-stream") -> dict:
        user_dir = self._get_user_dir(user_id)
        filepath = os.path.join(user_dir, filename)
        try:
            with open(filepath, "wb") as f:
                f.write(file_data)
            return {"success": True, "path": f"{user_id}/{filename}", "response": {}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def download_file(self, user_id: str, filename: str) -> bytes:
        filepath = os.path.join(self._get_user_dir(user_id), filename)
        with open(filepath, "rb") as f:
            return f.read()

    def delete_file(self, user_id: str, filename: str) -> dict:
        filepath = os.path.join(self._get_user_dir(user_id), filename)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
            return {"success": True, "response": {}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_files(self, user_id: str) -> list:
        user_dir = self._get_user_dir(user_id)
        try:
            return [{"name": f} for f in os.listdir(user_dir) if os.path.isfile(os.path.join(user_dir, f))]
        except:
            return []

    def get_public_url(self, user_id: str, filename: str) -> str:
        return f"/api/v1/files/download/{user_id}/{filename}"

    def get_signed_url(self, user_id: str, filename: str, expires_in: int = 3600) -> str:
        return self.get_public_url(user_id, filename)

def get_storage() -> LocalStorage:
    return LocalStorage()
