"""
Real Files Management - NO FAKE DATA
Everything based on actual uploaded files
Enterprise-grade with auto currency detection
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import List
import shutil
import traceback
from datetime import datetime
import pandas as pd

from ingestion.pipeline import IngestionPipeline
from config.settings import Settings
from utils.paths import get_user_paths, STORAGE_BASE
from utils.currency import (
    detect_currency,
    detect_currency_from_files,
    save_currency_metadata,
    CURRENCY_CONFIG
)

router = APIRouter()


def detect_and_save_currency(user_id: str, files_path):
    """Detect currency from uploaded files and save to metadata."""
    try:
        detected_currencies = []
        
        for file in files_path.glob('*'):
            if file.is_file():
                ext = file.suffix.lower()
                df = None
                
                try:
                    if ext == '.csv':
                        df = pd.read_csv(file, nrows=100)
                    elif ext in ['.xlsx', '.xls']:
                        df = pd.read_excel(file, nrows=100)
                    
                    if df is not None and not df.empty:
                        currency = detect_currency(df=df, filename=file.name)
                        detected_currencies.append(currency)
                        print(f"💰 Detected {currency} from {file.name}")
                except Exception as e:
                    print(f"⚠️ Error detecting currency from {file.name}: {e}")
        
        if detected_currencies:
            from collections import Counter
            most_common = Counter(detected_currencies).most_common(1)[0][0]
            save_currency_metadata(user_id, most_common, STORAGE_BASE)
            print(f"✅ Saved currency {most_common} for user {user_id}")
            return most_common
        
        return 'USD'
    except Exception as e:
        print(f"Error in currency detection: {e}")
        return 'USD'


@router.post("/upload/{user_id}")
async def upload_files(
    user_id: str,
    files: List[UploadFile] = File(...)
):
    """Upload and process files with REAL ingestion pipeline"""
    try:
        paths = get_user_paths(user_id)
        uploaded_files = []
        
        # Save uploaded files
        for file in files:
            file_path = paths["files"] / file.filename
            file.file.seek(0)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            uploaded_files.append({
                "id": file.filename,
                "name": file.filename,
                "size": file_path.stat().st_size,
                "type": file.content_type or "unknown",
                "uploadedAt": datetime.now().isoformat(),
                "status": "processing"
            })
        
        # DETECT CURRENCY from uploaded files
        detected_currency = detect_and_save_currency(user_id, paths["files"])
        
        # Process with REAL pipeline - NO FAKE DATA
        try:
            # Set paths for this user
            Settings.UPLOADS = paths["files"]
            Settings.FAISS_DIR = paths["faiss"]
            Settings.GRAPH_DIR = paths["graph"]
            
            # Create pipeline
            pipeline = IngestionPipeline()
            
            # Prepare file objects with path tracking
            file_objects = []
            for fp in paths["files"].glob("*"):
                if fp.is_file():
                    class FileObj:
                        def __init__(self, path):
                            self.filename = path.name
                            self._path = path  # Store full path
                            self.file = open(path, 'rb')
                    file_objects.append(FileObj(fp))
            
            # REAL INGESTION - AUTO-TRAIN after upload (fresh=False to add to existing, skip_save=True since files already saved)
            pipeline.ingest(user_id, file_objects, fresh=False, skip_save=True)
            
            # Close files
            for f in file_objects:
                try:
                    f.file.close()
                except:
                    pass
            
            # Mark completed
            for file_info in uploaded_files:
                file_info["status"] = "completed"
                file_info["trained"] = True
                file_info["currency"] = detected_currency
                
        except Exception as e:
            print(f"Processing error: {e}")
            traceback.print_exc()
            for file_info in uploaded_files:
                file_info["status"] = "failed"
                file_info["error"] = str(e)
        
        return {
            "success": True,
            "files": uploaded_files,
            "message": f"{len(uploaded_files)} file(s) processed with REAL data",
            "detectedCurrency": detected_currency
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list/{user_id}")
async def list_files(user_id: str):
    """List all uploaded files"""
    try:
        paths = get_user_paths(user_id)
        files = []
        
        if paths["files"].exists():
            for file_path in paths["files"].iterdir():
                if file_path.is_file():
                    files.append({
                        "id": file_path.name,
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                        "type": file_path.suffix[1:] if file_path.suffix else "unknown",
                        "uploadedAt": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                        "status": "completed"
                    })
        
        return {"files": files, "total": len(files)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}/{file_id}")
async def delete_file(user_id: str, file_id: str):
    """Delete a file and retrain indexes automatically with FRESH data"""
    try:
        paths = get_user_paths(user_id)
        file_path = paths["files"] / file_id
        
        print(f"🗑️ Attempting to delete: {file_path}")
        print(f"🗑️ File exists: {file_path.exists()}")
        
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
        
        # Delete the file FIRST
        file_path.unlink()
        print(f"✅ File deleted: {file_id}")
        
        # COMPLETELY clear old indexes for fresh retraining
        # Clear FAISS index and metadata completely
        if paths["faiss"].exists():
            shutil.rmtree(paths["faiss"])
        paths["faiss"].mkdir(parents=True, exist_ok=True)
        print(f"🗑️ Cleared FAISS index and metadata")
        
        # Clear Graph completely
        if paths["graph"].exists():
            shutil.rmtree(paths["graph"])
        paths["graph"].mkdir(parents=True, exist_ok=True)
        print(f"🗑️ Cleared Graph index")
        
        # Get remaining files for retraining
        remaining_files = [f for f in paths["files"].glob("*") if f.is_file()]
        print(f"📁 Remaining files for retraining: {[f.name for f in remaining_files]}")
        
        if remaining_files:
            print(f"🔄 Starting retraining with {len(remaining_files)} remaining files...")
            
            # Set paths for this user
            Settings.UPLOADS = paths["files"]
            Settings.FAISS_DIR = paths["faiss"]
            Settings.GRAPH_DIR = paths["graph"]
            
            # Create fresh pipeline
            pipeline = IngestionPipeline()
            file_objects = []
            
            # Create file objects that mimic UploadFile interface
            for fp in remaining_files:
                class FileObj:
                    def __init__(self, path):
                        self.filename = path.name
                        self._path = path
                        self.file = open(path, 'rb')
                file_objects.append(FileObj(fp))
            
            try:
                # Use fresh=True and skip_save=True for retraining
                result = pipeline.ingest(user_id, file_objects, fresh=True, skip_save=True)
                print(f"✅ Retraining complete: {result}")
            finally:
                # Always close file handles
                for f in file_objects:
                    try:
                        f.file.close()
                    except:
                        pass
                    
            # Re-detect currency after file deletion
            detected_currency = detect_and_save_currency(user_id, paths["files"])
            print(f"💰 Re-detected currency: {detected_currency}")
        else:
            print(f"📭 No remaining files - all indexes cleared")
        
        return {
            "success": True, 
            "message": f"File {file_id} deleted and AI retrained from scratch",
            "remaining_files": len(remaining_files),
            "retrained": len(remaining_files) > 0,
            "files_remaining": [f.name for f in remaining_files] if remaining_files else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}/all")
async def delete_all_files(user_id: str):
    """Delete all files and indexes"""
    try:
        paths = get_user_paths(user_id)
        
        # Delete files directory and recreate
        if paths["files"].exists():
            shutil.rmtree(paths["files"])
        paths["files"].mkdir(parents=True, exist_ok=True)
        
        # Delete FAISS directory and recreate
        if paths["faiss"].exists():
            shutil.rmtree(paths["faiss"])
        paths["faiss"].mkdir(parents=True, exist_ok=True)
        
        # Delete graph directory and recreate
        if paths["graph"].exists():
            shutil.rmtree(paths["graph"])
        paths["graph"].mkdir(parents=True, exist_ok=True)
        
        # Delete memory directory and recreate
        if paths["memory"].exists():
            shutil.rmtree(paths["memory"])
        paths["memory"].mkdir(parents=True, exist_ok=True)
        
        print(f"✅ All data deleted for user {user_id}")
        return {
            "success": True, 
            "message": f"All data deleted for user {user_id}",
            "deleted": {
                "files": True,
                "faiss": True,
                "graph": True,
                "memory": True
            }
        }
        
    except Exception as e:
        print(f"❌ Error deleting files: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to delete files: {str(e)}")

@router.post("/{user_id}/rebuild")
async def rebuild_indexes(user_id: str):
    """RETRAIN: Rebuild indexes from existing files (clears old data first) - FRESH training"""
    try:
        paths = get_user_paths(user_id)
        files = [f for f in paths["files"].glob("*") if f.is_file()]
        
        if not files:
            raise HTTPException(status_code=400, detail="No files to retrain. Upload files first.")
        
        print(f"🔄 Starting FRESH rebuild for user {user_id} with {len(files)} files")
        print(f"📁 Files to process: {[f.name for f in files]}")
        
        # COMPLETELY clear old indexes
        if paths["faiss"].exists():
            shutil.rmtree(paths["faiss"])
        paths["faiss"].mkdir(parents=True, exist_ok=True)
        print(f"🗑️ Cleared FAISS index and metadata")
        
        if paths["graph"].exists():
            shutil.rmtree(paths["graph"])
        paths["graph"].mkdir(parents=True, exist_ok=True)
        print(f"🗑️ Cleared Graph index")
        
        # Set paths
        Settings.UPLOADS = paths["files"]
        Settings.FAISS_DIR = paths["faiss"]
        Settings.GRAPH_DIR = paths["graph"]
        
        # Create fresh pipeline
        pipeline = IngestionPipeline()
        
        # Prepare file objects with proper path tracking
        file_objects = []
        for fp in files:
            class FileObj:
                def __init__(self, path):
                    self.filename = path.name
                    self._path = path  # Store full path for retraining
                    self.file = open(path, 'rb')
            file_objects.append(FileObj(fp))
        
        try:
            # Retrain from scratch with FRESH indexes
            result = pipeline.ingest(user_id, file_objects, fresh=True, skip_save=True)
            print(f"✅ Rebuild complete: {result}")
        finally:
            # Always close files
            for f in file_objects:
                try:
                    f.file.close()
                except:
                    pass
        
        # Re-detect currency after rebuild
        detected_currency = detect_and_save_currency(user_id, paths["files"])
        print(f"💰 Detected currency: {detected_currency}")
        
        return {
            "success": True,
            "message": "🔄 Successfully retrained! AI now knows ONLY your current files.",
            "files_processed": len(files),
            "files": [f.name for f in files],
            "chunks_created": result.get("chunks", 0),
            "tables_processed": result.get("tables", 0),
            "detectedCurrency": detected_currency
        }
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/currency")
async def get_currency(user_id: str):
    """Get detected currency for user's files"""
    try:
        from utils.currency import load_currency_metadata
        
        paths = get_user_paths(user_id)
        
        # Try to load stored currency
        stored = load_currency_metadata(user_id, STORAGE_BASE)
        
        if stored:
            return {
                "currency": stored,
                "source": "stored",
                "symbol": CURRENCY_CONFIG.get(stored, {}).get('symbol', '$')
            }
        
        # Detect from files
        detected = detect_and_save_currency(user_id, paths["files"])
        
        return {
            "currency": detected,
            "source": "detected",
            "symbol": CURRENCY_CONFIG.get(detected, {}).get('symbol', '$')
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/currency/{currency_code}")
async def set_currency(user_id: str, currency_code: str):
    """Manually set currency for user's data"""
    try:
        currency_code = currency_code.upper()
        
        if currency_code not in CURRENCY_CONFIG:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid currency: {currency_code}. Supported: {', '.join(CURRENCY_CONFIG.keys())}"
            )
        
        save_currency_metadata(user_id, currency_code, STORAGE_BASE)
        
        return {
            "success": True,
            "currency": currency_code,
            "symbol": CURRENCY_CONFIG[currency_code]['symbol'],
            "message": f"Currency set to {currency_code}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/currency/detect")
async def detect_currency_endpoint(user_id: str):
    """Re-detect currency from uploaded files"""
    try:
        paths = get_user_paths(user_id)
        
        if not paths["files"].exists() or not list(paths["files"].glob('*')):
            raise HTTPException(status_code=400, detail="No files uploaded. Upload files first.")
        
        detected = detect_and_save_currency(user_id, paths["files"])
        
        return {
            "success": True,
            "currency": detected,
            "symbol": CURRENCY_CONFIG.get(detected, {}).get('symbol', '$'),
            "message": f"Detected currency: {detected}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/{file_id}/download")
async def download_file(user_id: str, file_id: str):
    """Download a specific file"""
    try:
        from fastapi.responses import FileResponse
        
        paths = get_user_paths(user_id)
        file_path = paths["files"] / file_id
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(file_path),
            filename=file_id,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
