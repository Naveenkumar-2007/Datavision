"""
Real Files Management - NO FAKE DATA
Everything based on actual uploaded files
Enterprise-grade with auto currency detection
With cache invalidation for data consistency
SECURED: Uses JWT authentication for user isolation
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Header, Depends, Request
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional, Dict
from pathlib import Path
import shutil
import traceback
from datetime import datetime
import re
import os

from ingestion.pipeline import IngestionPipeline
from config.settings import Settings
from utils.paths import get_user_paths, STORAGE_BASE
from utils.currency import (
    detect_and_save_user_currency,
    save_currency_metadata,
    load_currency_metadata,
    CURRENCY_CONFIG
)

# Import auth helper for JWT decode
try:
    from database.auth import decode_jwt, get_user_id_from_headers
except ImportError:
    decode_jwt = None
    def get_user_id_from_headers(*args, **kwargs): return None  # Return None to preserve URL user_id

router = APIRouter()

# ============================================
# SECURITY: File Upload Validation
# ============================================
# Allowed file extensions (whitelist approach)
ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.json', '.pdf', '.docx', '.doc', '.txt', '.png', '.jpg', '.jpeg'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB max
MAX_FILENAME_LENGTH = 255

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.
    - Remove path separators
    - Remove null bytes
    - Limit length
    - Only allow safe characters
    """
    if not filename:
        raise HTTPException(status_code=400, detail="Filename cannot be empty")
    
    # Remove path separators and parent directory references
    filename = os.path.basename(filename)
    filename = filename.replace('..', '')
    filename = filename.replace('\x00', '')  # Remove null bytes
    
    # Remove any remaining path separators
    filename = re.sub(r'[/\\]', '', filename)
    
    # Limit filename length
    if len(filename) > MAX_FILENAME_LENGTH:
        name, ext = os.path.splitext(filename)
        filename = name[:MAX_FILENAME_LENGTH - len(ext)] + ext
    
    # Ensure filename is not empty after sanitization
    if not filename or filename in ('.', '..'):
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    return filename

def validate_file(file: UploadFile) -> None:
    """Validate uploaded file for security"""
    # Sanitize and validate filename
    sanitized_name = sanitize_filename(file.filename)
    
    # Check file extension (whitelist)
    ext = os.path.splitext(sanitized_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type '{ext}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Update filename with sanitized version
    file.filename = sanitized_name

def validate_user_id(user_id: str) -> str:
    """Validate user_id to prevent path traversal"""
    if not user_id or not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    if '..' in user_id or '/' in user_id or '\\' in user_id:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    return user_id

# ============================================
# UPLOAD CANCELLATION STATE MANAGEMENT
# ============================================
# In-memory store to track cancellation requests per user
# This allows the cancel button to actually stop ongoing processing
_upload_cancellation_flags: Dict[str, bool] = {}

def request_cancellation(user_id: str) -> None:
    """Set cancellation flag for a user's upload"""
    _upload_cancellation_flags[user_id] = True
    print(f"🛑 Cancellation requested for user: {user_id}")

def clear_cancellation(user_id: str) -> None:
    """Clear cancellation flag after upload completes or is cancelled"""
    _upload_cancellation_flags.pop(user_id, None)

def is_upload_cancelled(user_id: str) -> bool:
    """Check if user has requested upload cancellation"""
    return _upload_cancellation_flags.get(user_id, False)

# Cancel upload endpoint - Frontend calls this when user clicks Cancel
@router.post("/cancel-upload/{user_id}")
async def cancel_upload(user_id: str):
    """Cancel an ongoing upload for a user"""
    request_cancellation(user_id)
    return {"success": True, "message": "Cancellation requested"}

def invalidate_user_cache(user_id: str):
    """Invalidate query cache when data changes"""
    try:
        from core.cache import get_cache
        cache = get_cache()
        cache.invalidate(user_id=user_id)
        print(f"🗑️ Query cache invalidated for user: {user_id}")
    except Exception as e:
        print(f"⚠️ Cache invalidation error: {e}")


@router.post("/upload/{user_id}")
async def upload_files(
    request: Request,  # Moved to first position for proper FastAPI injection
    user_id: str,
    files: List[UploadFile] = File(...),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Upload and process files with REAL ingestion pipeline
    SECURED: Validates user identity from JWT token
    CANCELLABLE: Stops processing if client disconnects or cancel is requested
    """
    # SECURITY: Validate user_id to prevent path traversal
    user_id = validate_user_id(user_id)
    
    # Get the actual user_id first for cancellation checks
    authenticated_user = await get_user_id_from_headers(x_user_id, authorization)
    actual_user_id = authenticated_user if authenticated_user else user_id
    
    # SECURITY: Validate authenticated user_id as well
    if actual_user_id:
        actual_user_id = validate_user_id(actual_user_id)
    
    # Clear any previous cancellation flag at the start
    clear_cancellation(actual_user_id)
    
    # Helper to check if client cancelled (checks BOTH disconnection AND explicit cancel flag)
    async def is_cancelled() -> bool:
        # Check explicit cancellation flag first (set by cancel-upload endpoint)
        if is_upload_cancelled(actual_user_id):
            return True
        # Also check if HTTP connection was closed
        try:
            return await request.is_disconnected()
        except:
            return False
    
    # Helper to clean up files on cancellation
    def cleanup_uploaded_files(file_list: list, paths_obj):
        for file_info in file_list:
            try:
                file_path = paths_obj["files"] / file_info["name"]
                if file_path.exists():
                    file_path.unlink()
                    print(f"🗑️ Cleaned up cancelled file: {file_info['name']}")
            except Exception as e:
                print(f"⚠️ Cleanup error: {e}")
    
    try:
        # For backwards compatibility, use URL user_id but log warning if mismatch
        if authenticated_user != user_id:
            print(f"⚠️ WARNING: Auth user {authenticated_user} ≠ URL user {user_id}")
            # Use authenticated user for security
            user_id = authenticated_user
        
        paths = get_user_paths(user_id)
        uploaded_files = []
        
        # Invalidate cache since data is changing
        invalidate_user_cache(user_id)
        
        # Check for cancellation before file save
        if await is_cancelled():
            print("🛑 Upload cancelled by client before file save")
            clear_cancellation(user_id)
            return {"success": False, "cancelled": True, "message": "Upload cancelled by user"}
        
        # Save uploaded files
        for file in files:
            # SECURITY: Validate each uploaded file
            validate_file(file)
            
            # Check cancellation for each file
            if await is_cancelled():
                print(f"🛑 Upload cancelled by client during file save ({file.filename})")
                cleanup_uploaded_files(uploaded_files, paths)
                clear_cancellation(user_id)
                return {"success": False, "cancelled": True, "message": "Upload cancelled by user"}
            
            # 🔍 Deduplication / Schema Conflict Logic
            import pandas as pd
            
            # Check if there are existing files
            existing_csvs = list(paths["files"].glob("*.csv"))
            existing_csvs = [f for f in existing_csvs if not f.name.startswith("cleaned_") and not f.name.startswith("LIVE_")]
            
            if len(existing_csvs) > 0 and file.filename.endswith(".csv"):
                try:
                    # Read header of the incoming file without saving it yet
                    file.file.seek(0)
                    new_df = pd.read_csv(file.file, nrows=0)
                    new_cols = set(new_df.columns)
                    
                    # Read header of the first existing file
                    existing_df = pd.read_csv(existing_csvs[0], nrows=0)
                    existing_cols = set(existing_df.columns)
                    
                    if new_cols != existing_cols:
                        # Schemas don't match! This is a different dataset.
                        raise HTTPException(
                            status_code=409, 
                            detail="⚠️ Different dataset detected! Please delete your previous data files first to avoid AI context conflicts."
                        )
                    else:
                        print(f"✅ Schema matched existing data. Allowing upload of {file.filename}.")
                except HTTPException:
                    raise
                except Exception as e:
                    print(f"⚠️ Could not verify schema: {e}")
                    
            file.file.seek(0)
            
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
        detected_currency = detect_and_save_user_currency(user_id, paths["files"], STORAGE_BASE)
        
        # Check for cancellation before pipeline processing
        if await is_cancelled():
            print("🛑 Upload cancelled by client before pipeline processing")
            cleanup_uploaded_files(uploaded_files, paths)
            clear_cancellation(user_id)
            return {"success": False, "cancelled": True, "message": "Upload cancelled by user"}
        
        # Process with REAL pipeline - NO FAKE DATA
        try:
            # Set paths for this user
            Settings.UPLOADS = paths["files"]
            Settings.FAISS_DIR = paths["faiss"]
            Settings.GRAPH_DIR = paths["graph"]
            
            # Create pipeline
            pipeline = IngestionPipeline()
            
            # IMPORTANT: Process ALL files in the user's directory, not just newly uploaded ones
            # This ensures a complete, unified dataset when adding new files
            all_files_in_dir = []
            for f in paths["files"].iterdir():
                if f.is_file():
                    all_files_in_dir.append({
                        "id": f.name,
                        "name": f.name,
                        "size": f.stat().st_size,
                        "type": f.suffix[1:] if f.suffix else "unknown",
                    })
            
            print(f"📁 Reprocessing ALL {len(all_files_in_dir)} files after new upload")
            
            # Check for cancellation before heavy processing
            if await is_cancelled():
                print("🛑 Upload cancelled by client before pipeline.process()")
                cleanup_uploaded_files(uploaded_files, paths)
                clear_cancellation(user_id)
                return {"success": False, "cancelled": True, "message": "Upload cancelled by user"}
            
            # Process ALL files with REAL pipeline
            result = pipeline.process(
                all_files_in_dir,
                user_id=user_id,
                base_path=STORAGE_BASE
            )
            
            # Check for cancellation AFTER heavy processing - user may have cancelled during pipeline
            if await is_cancelled():
                print("🛑 Upload cancelled by client AFTER pipeline.process() - cleaning up")
                cleanup_uploaded_files(uploaded_files, paths)
                clear_cancellation(user_id)
                return {"success": False, "cancelled": True, "message": "Upload cancelled by user"}
            
            # Map pipeline results back to file info
            for file_info in uploaded_files:
                file_info["status"] = "completed"
                file_info["trained"] = True
                file_info["currency"] = detected_currency
                
        except Exception as e:
            print(f"Processing error: {e}")
            import traceback as tb
            tb.print_exc()
            for file_info in uploaded_files:
                file_info["status"] = "failed"
                file_info["error"] = str(e)
        
        # Check for cancellation before schema analysis
        if await is_cancelled():
            print("🛑 Upload cancelled by client before schema analysis")
            return {"success": True, "files": uploaded_files, "message": "Partial upload - cancelled before schema analysis", "cancelled": True}
        
        # ============================================
        # 🧠 AI SCHEMA INTELLIGENCE - Auto-analyze upload
        # ============================================
        print("=" * 60)
        print("🧠 STARTING AI SCHEMA INTELLIGENCE ANALYSIS...")
        print("=" * 60)
        schema_result = None
        try:
            print("📦 Importing schema_intelligence module...")
            from core.schema_intelligence import UniversalSchemaAnalyzer, SchemaStorage
            print("✅ Import successful!")
            
            # Read the first uploaded CSV/Excel for schema analysis
            print(f"📁 Looking for files in: {paths['files']}")
            print(f"📁 Files uploaded: {[f.filename for f in files]}")
            
            for file in files:
                # Check cancellation for each file schema analysis
                if await is_cancelled():
                    print("🛑 Upload cancelled by client during schema analysis")
                    break
                
                file_path = paths["files"] / file.filename
                print(f"🔍 Checking file: {file_path}")
                print(f"🔍 File suffix: {file_path.suffix.lower()}")
                print(f"🔍 File exists: {file_path.exists()}")
                
                if file_path.suffix.lower() in ['.csv', '.xlsx', '.xls']:
                    import pandas as pd
                    print(f"📊 Reading file: {file_path}")
                    
                    if file_path.suffix.lower() == '.csv':
                        df = pd.read_csv(file_path)
                    else:
                        df = pd.read_excel(file_path)
                    
                    print(f"📊 DataFrame loaded: {len(df)} rows, {len(df.columns)} columns")
                    print(f"📊 Columns: {list(df.columns)}")
                    
                    print(f"🧠 AI Schema Analysis starting for: {file.filename}")
                    analyzer = UniversalSchemaAnalyzer()
                    schema = analyzer.analyze_dataframe(df, file.filename)
                    
                    # Store schema in user's base directory
                    schema_dir = paths["base"] / "schemas"
                    schema_dir.mkdir(parents=True, exist_ok=True)
                    print(f"💾 Saving schema to: {schema_dir}")
                    storage = SchemaStorage(schema_dir)
                    storage.save_schema(file_path.stem, schema)
                    
                    schema_result = {
                        "domain": schema.domain,
                        "domain_confidence": schema.domain_confidence,
                        "key_metrics": schema.key_metrics,
                        "dimensions": schema.dimensions,
                        "suggested_analyses": len(schema.suggested_analyses)
                    }
                    print(f"✅ Schema detected: {schema.domain} (confidence: {schema.domain_confidence:.0%})")
                    print(f"📊 Key metrics: {schema.key_metrics}")
                    print(f"📁 Dimensions: {schema.dimensions}")
                    print("=" * 60)
                    break
                else:
                    print(f"⏭️ Skipping non-data file: {file.filename}")
        except Exception as e:
            print(f"❌ Schema analysis ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        # Clear cancellation flag on successful completion
        clear_cancellation(user_id)
        
        return {
            "success": True,
            "files": uploaded_files,
            "message": f"{len(uploaded_files)} file(s) processed with REAL data",
            "detectedCurrency": detected_currency,
            "schemaIntelligence": schema_result
        }
        
    except Exception as e:
        # Clear cancellation flag on error too
        clear_cancellation(user_id)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/{user_id}")
async def get_schema_intelligence(
    user_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    🧠 AI Schema Intelligence Endpoint
    Returns the AI-detected schema for user's uploaded data.
    Includes domain detection, key metrics, dimensions, and suggested analyses.
    """
    try:
        # SECURITY: Validate user
        authenticated_user = await get_user_id_from_headers(x_user_id, authorization)
        if authenticated_user != user_id:
            user_id = authenticated_user
        
        paths = get_user_paths(user_id)
        
        # Try to load stored schema
        from core.schema_intelligence import SchemaStorage, SchemaIntelligence
        
        schema_dir = paths["base"] / "schemas"
        if not schema_dir.exists():
            return {
                "hasSchema": False,
                "message": "No schema found. Upload data files first."
            }
        
        # Get latest schema file
        schema_files = list(schema_dir.glob("*_schema.json"))
        if not schema_files:
            return {
                "hasSchema": False,
                "message": "No schema found. Upload data files first."
            }
        
        # Load latest schema
        latest_file = max(schema_files, key=lambda x: x.stat().st_mtime)
        storage = SchemaStorage(schema_dir)
        file_id = latest_file.stem.replace("_schema", "")
        schema = storage.load_schema(file_id)
        
        if schema:
            return {
                "hasSchema": True,
                "schema": schema.to_dict(),
                "summary": {
                    "domain": schema.domain,
                    "domainConfidence": f"{schema.domain_confidence:.0%}",
                    "keyMetrics": schema.key_metrics,
                    "dimensions": schema.dimensions,
                    "timeColumn": schema.time_column,
                    "suggestedAnalysesCount": len(schema.suggested_analyses),
                    "dataQuality": {
                        "completeness": f"{schema.data_quality.completeness:.0%}",
                        "rows": schema.data_quality.row_count,
                        "columns": schema.data_quality.column_count
                    }
                }
            }
        else:
            return {
                "hasSchema": False,
                "message": "Schema file exists but could not be loaded."
            }
            
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schema/{user_id}/refresh")
async def refresh_schema_intelligence(
    user_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Re-analyze uploaded files and refresh schema intelligence.
    Use this when data files change.
    """
    try:
        # SECURITY: Validate user
        authenticated_user = await get_user_id_from_headers(x_user_id, authorization)
        if authenticated_user != user_id:
            user_id = authenticated_user
        
        paths = get_user_paths(user_id)
        
        # Find CSV/Excel files
        data_files = []
        if paths["files"].exists():
            for f in paths["files"].iterdir():
                if f.suffix.lower() in ['.csv', '.xlsx', '.xls']:
                    data_files.append(f)
        
        if not data_files:
            raise HTTPException(status_code=400, detail="No CSV/Excel files found. Upload data first.")
        
        # Analyze the first/latest file
        import pandas as pd
        from core.schema_intelligence import UniversalSchemaAnalyzer, SchemaStorage
        
        file_path = max(data_files, key=lambda x: x.stat().st_mtime)
        
        if file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        print(f"🧠 Refreshing schema analysis for: {file_path.name}")
        analyzer = UniversalSchemaAnalyzer()
        schema = analyzer.analyze_dataframe(df, file_path.name)
        
        # Store schema
        schema_dir = paths["base"] / "schemas"
        schema_dir.mkdir(parents=True, exist_ok=True)
        storage = SchemaStorage(schema_dir)
        storage.save_schema(file_path.stem, schema)
        
        return {
            "success": True,
            "message": f"Schema refreshed for {file_path.name}",
            "schema": {
                "domain": schema.domain,
                "domainConfidence": f"{schema.domain_confidence:.0%}",
                "keyMetrics": schema.key_metrics,
                "dimensions": schema.dimensions,
                "suggestedAnalyses": len(schema.suggested_analyses)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list/{user_id}")
async def list_files(
    user_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """List all uploaded files - SECURED"""
    try:
        # SECURITY: Validate user (only override if auth returns valid user)
        authenticated_user = await get_user_id_from_headers(x_user_id, authorization)
        if authenticated_user and authenticated_user != user_id:
            user_id = authenticated_user
        
        paths = get_user_paths(user_id)
        files = []
        
        # DEBUG: Print path resolution
        print(f"📂 [FILE LIST] user_id={user_id}")
        print(f"📂 [FILE LIST] files_path={paths['files']}")
        print(f"📂 [FILE LIST] exists={paths['files'].exists()}")
        
        if paths["files"].exists():
            for file_path in paths["files"].iterdir():
                print(f"📄 [FILE LIST] Found: {file_path}")
                # HIDE Generated Cleaned files from the main list (User Request)
                if file_path.name.startswith("cleaned_"):
                    continue
                    
                if file_path.is_file():
                    files.append({
                        "id": file_path.name,
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                        "type": file_path.suffix[1:] if file_path.suffix else "unknown",
                        "uploadedAt": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                        "status": "completed"
                    })
                    
        # ✨ MAGIC: Append Live Connections as virtual files so ML/Reports can use them natively!
        try:
            from database.db import AsyncSessionLocal
            from database.orm import DataConnection
            from sqlalchemy import select
            import asyncio
            
            async def get_live_connections():
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(DataConnection).where(DataConnection.user_id == user_id))
                    return result.scalars().all()
                    
            connections = await get_live_connections()
                
            for conn in connections:
                source_label = conn.source_type.upper()
                table_name = conn.target_table or conn.database_name or "live_data"
                files.append({
                    "id": f"live_stream_{str(conn.id)[:12]}.csv",
                    "name": f"📡 {table_name} ({source_label} Live)",
                    "size": 0,
                    "type": "csv",
                    "uploadedAt": conn.created_at.isoformat(),
                    "status": "streaming",
                    "is_live": True
                })
        except Exception as live_e:
            print(f"⚠️ Could not list live connections: {live_e}")
        
        return {"files": files, "total": len(files)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# IMPORTANT: This route MUST come before /{user_id}/{file_id} to properly match /all
@router.delete("/{user_id}/all")
async def delete_all_files(
    user_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Delete all files and indexes - SECURED"""
    try:
        # SECURITY: Validate user
        authenticated_user = await get_user_id_from_headers(x_user_id, authorization)
        if authenticated_user != user_id:
            user_id = authenticated_user
        
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
        
        # Clear metadata
        metadata_path = STORAGE_BASE / user_id / "metadata.json"
        if metadata_path.exists():
            metadata_path.unlink()
        
        # Invalidate cache
        invalidate_user_cache(user_id)
        
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

@router.delete("/{user_id}/{file_id}")
async def delete_file(
    user_id: str,
    file_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Delete a file and retrain indexes - SECURED"""
    try:
        # SECURITY: Validate user
        authenticated_user = await get_user_id_from_headers(x_user_id, authorization)
        if authenticated_user != user_id:
            user_id = authenticated_user
            
        # ✨ MAGIC: Intercept Live Connection Deletions
        if file_id.startswith("LIVE_") and file_id.endswith(".csv"):
            conn_id = file_id.replace("LIVE_", "").replace(".csv", "")
            
            from database.db import AsyncSessionLocal
            from database.orm import DataConnection
            from sqlalchemy import select
            
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(DataConnection).where(DataConnection.id == conn_id))
                conn = result.scalar_one_or_none()
                if conn:
                    await db.delete(conn)
                    await db.commit()
            
            invalidate_user_cache(user_id)
            return {"success": True, "message": "Live connection deleted"}
        
        paths = get_user_paths(user_id)
        file_path = paths["files"] / file_id
        
        # Invalidate cache since data is changing
        invalidate_user_cache(user_id)
        
        print(f"🗑️ Attempting to delete: {file_path}")
        print(f"🗑️ File exists: {file_path.exists()}")
        
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
        
        # Delete the file FIRST
        file_path.unlink()
        print(f"✅ File deleted: {file_id}")
        
        # ALSO DELETE ALL cleaned_*.csv files (AutoML generated files)
        # These are temporary files from ML training and should be cleared on delete
        cleaned_files = list(paths["files"].glob("cleaned_*.csv"))
        for cf in cleaned_files:
            try:
                cf.unlink()
                print(f"🗑️ Deleted AutoML cleaned file: {cf.name}")
            except Exception as e:
                print(f"⚠️ Could not delete {cf.name}: {e}")
        
        # COMPLETELY clear old indexes for fresh retraining
        # Clear FAISS index and metadata completely
        if paths["faiss"].exists():
            shutil.rmtree(paths["faiss"])
        paths["faiss"].mkdir(parents=True, exist_ok=True)
        print(f"🗑️ Cleared FAISS index and metadata")
        
        # Clear Graph completely (user-specific)
        if paths["graph"].exists():
            shutil.rmtree(paths["graph"])
        paths["graph"].mkdir(parents=True, exist_ok=True)
        print(f"🗑️ Cleared User Graph index")
        
        # Also clear global graph locations
        global_graph_path = Settings.STORAGE / "graph" / f"{user_id}.gpickle"
        if global_graph_path.exists():
            global_graph_path.unlink()
            print(f"🗑️ Cleared global graph file")
        
        alt_graph_path = Settings.GRAPH_DIR / f"{user_id}.gpickle"
        if alt_graph_path.exists():
            alt_graph_path.unlink()
            print(f"🗑️ Cleared alt graph file")
        
        # Get remaining files for retraining (EXCLUDING cleaned_ files)
        remaining_files = [
            f for f in paths["files"].glob("*") 
            if f.is_file() and not f.name.startswith("cleaned_")
        ]
        print(f"📁 Remaining files for retraining: {[f.name for f in remaining_files]}")
        
        if remaining_files:
            print(f"🔄 Starting retraining with {len(remaining_files)} remaining files...")
            
            # Set paths for this user
            Settings.UPLOADS = paths["files"]
            Settings.FAISS_DIR = paths["faiss"]
            Settings.GRAPH_DIR = paths["graph"]
            
            # Create file info for pipeline
            file_infos = []
            for f in remaining_files:
                file_infos.append({
                    "id": f.name,
                    "name": f.name,
                    "size": f.stat().st_size,
                    "type": f.suffix[1:] if f.suffix else "unknown",
                })
            
            # FRESH process remaining files with IngestionPipeline
            try:
                pipeline = IngestionPipeline()
                result = pipeline.process(
                    file_infos,
                    user_id=user_id,
                    base_path=STORAGE_BASE
                )
                print(f"✅ Retraining complete: {result}")
            except Exception as e:
                print(f"⚠️ Retraining error: {e}")
                traceback.print_exc()
                    
            # Re-detect currency after file deletion
            detected_currency = detect_and_save_user_currency(user_id, paths["files"], STORAGE_BASE)
            print(f"💰 Re-detected currency: {detected_currency}")
        else:
            print(f"📭 No remaining files - all indexes cleared")
            # Clear metadata when no files remain
            metadata_path = STORAGE_BASE / user_id / "metadata.json"
            if metadata_path.exists():
                metadata_path.unlink()
                print(f"🗑️ Cleared user metadata (no files remaining)")
        
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

@router.post("/{user_id}/rebuild")
async def rebuild_indexes(user_id: str):
    """RETRAIN: Rebuild indexes from existing files (clears old data first) - FRESH training"""
    try:
        paths = get_user_paths(user_id)
        
        # First, delete all cleaned_*.csv files (AutoML generated)
        cleaned_files = list(paths["files"].glob("cleaned_*.csv"))
        for cf in cleaned_files:
            try:
                cf.unlink()
                print(f"🗑️ Deleted AutoML cleaned file: {cf.name}")
            except Exception as e:
                print(f"⚠️ Could not delete {cf.name}: {e}")
        
        # Get only original files (not cleaned_ files)
        files = [
            f for f in paths["files"].glob("*") 
            if f.is_file() and not f.name.startswith("cleaned_")
        ]
        
        if not files:
            raise HTTPException(status_code=400, detail="No files to retrain. Upload files first.")
        
        print(f"🔄 Starting FRESH rebuild for user {user_id} with {len(files)} files")
        print(f"📁 Files to process: {[f.name for f in files]}")
        
        # INVALIDATE CACHE - Clear all cached responses for this user
        invalidate_user_cache(user_id)
        
        # COMPLETELY clear old indexes
        if paths["faiss"].exists():
            shutil.rmtree(paths["faiss"])
        paths["faiss"].mkdir(parents=True, exist_ok=True)
        print(f"🗑️ Cleared FAISS index and metadata")
        
        if paths["graph"].exists():
            shutil.rmtree(paths["graph"])
        paths["graph"].mkdir(parents=True, exist_ok=True)
        print(f"🗑️ Cleared User Graph index")
        
        # Also clear the global graph directory for this user
        global_graph_path = Settings.STORAGE / "graph" / f"{user_id}.gpickle"
        if global_graph_path.exists():
            global_graph_path.unlink()
            print(f"🗑️ Cleared global graph file: {global_graph_path}")
        
        # Clear any other graph file locations
        alt_graph_path = Settings.GRAPH_DIR / f"{user_id}.gpickle"
        if alt_graph_path.exists():
            alt_graph_path.unlink()
            print(f"🗑️ Cleared alt graph file: {alt_graph_path}")
        
        # Clear old metadata to force fresh currency detection
        metadata_path = STORAGE_BASE / user_id / "metadata.json"
        if metadata_path.exists():
            metadata_path.unlink()
            print(f"🗑️ Cleared old metadata for fresh currency detection")
        
        # Set paths
        Settings.UPLOADS = paths["files"]
        Settings.FAISS_DIR = paths["faiss"]
        Settings.GRAPH_DIR = paths["graph"]
        
        # Create file info for pipeline
        file_infos = []
        for f in files:
            file_infos.append({
                "id": f.name,
                "name": f.name,
                "size": f.stat().st_size,
                "type": f.suffix[1:] if f.suffix else "unknown",
            })
        
        # FRESH process ALL files with IngestionPipeline
        print(f"🔄 Processing {len(file_infos)} files with IngestionPipeline...")
        try:
            pipeline = IngestionPipeline()
            result = pipeline.process(
                file_infos,
                user_id=user_id,
                base_path=STORAGE_BASE
            )
            print(f"✅ Pipeline processing complete: {result}")
        except Exception as e:
            print(f"⚠️ Pipeline error: {e}")
            traceback.print_exc()
            result = {"chunks": 0, "tables": 0}
        
        # Re-detect currency after rebuild
        detected_currency = detect_and_save_user_currency(user_id, paths["files"], STORAGE_BASE)
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
        detected = detect_and_save_user_currency(user_id, paths["files"], STORAGE_BASE)
        
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
        
        detected = detect_and_save_user_currency(user_id, paths["files"], STORAGE_BASE)

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

@router.get("/{user_id}/{file_id}/columns")
async def get_file_columns(
    user_id: str, 
    file_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Get columns of a file (handles CSV and Excel safely)"""
    try:
        authenticated_user = await get_user_id_from_headers(x_user_id, authorization)
        if authenticated_user and authenticated_user != user_id:
            user_id = authenticated_user
            
        paths = get_user_paths(user_id)
        file_path = paths["files"] / file_id
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
            
        import pandas as pd
        if file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path, nrows=0)
        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path, nrows=0)
        else:
            return {"success": False, "error": "Unsupported file format for column extraction"}
            
        return {"success": True, "columns": list(df.columns)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/{user_id}/{file_id}/download")
async def download_file(user_id: str, file_id: str):
    """Download a specific file, intercepting Live Connections to return real-time CSV"""
    try:
        from fastapi.responses import FileResponse, StreamingResponse
        
        # ✨ MAGIC: Intercept Live Connections
        if file_id.startswith("LIVE_") and file_id.endswith(".csv"):
            conn_id = file_id.replace("LIVE_", "").replace(".csv", "")
            
            from database.db import AsyncSessionLocal
            from database.orm import DataConnection
            from sqlalchemy import select
            import pandas as pd
            import psycopg2
            import io
            
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(DataConnection).where(DataConnection.id == conn_id))
                conn = result.scalar_one_or_none()
                
                if not conn:
                    raise HTTPException(status_code=404, detail="Live Connection not found")
                
                try:
                    import urllib.parse
                    safe_creds = urllib.parse.quote_plus(conn.credentials)
                    conn_str = f"postgresql://postgres:{safe_creds}@{conn.host}/{conn.database_name}"
                    
                    # Offload the blocking DB read and CSV generation to a background thread
                    import asyncio
                    loop = asyncio.get_running_loop()
                    
                    def fetch_to_csv():
                        with psycopg2.connect(conn_str) as pg_conn:
                            df = pd.read_sql(f"SELECT * FROM {conn.target_table}", pg_conn)
                            csv_data = df.to_csv(index=False)
                            return csv_data
                            
                    csv_string = await loop.run_in_executor(None, fetch_to_csv)
                    
                    return StreamingResponse(
                        io.StringIO(csv_string),
                        media_type="text/csv",
                        headers={"Content-Disposition": f"attachment; filename={file_id}"}
                    )
                except Exception as db_e:
                    print(f"⚠️ Live download failed: {db_e}")
                    raise HTTPException(status_code=500, detail=f"Failed to fetch live data: {db_e}")

        # Normal file download
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


# ============================================================================
# GOOGLE SHEETS IMPORT ENDPOINT
# ============================================================================

@router.post("/{user_id}/import-google-sheet")
async def import_google_sheet(
    user_id: str,
    sheet_url: str = Query(..., description="Google Sheets URL or ID"),
    sheet_name: Optional[str] = Query(None, description="Optional sheet/tab name")
):
    """
    Import data from a public Google Sheet
    The sheet must be accessible via link (Anyone with the link can view)
    """
    try:
        from integrations.google_sheets import import_google_sheet as gs_import, extract_sheet_id
        from ingestion.pipeline import IngestionPipeline
        
        # Validate sheet ID
        sheet_id = extract_sheet_id(sheet_url)
        if not sheet_id:
            raise HTTPException(status_code=400, detail="Invalid Google Sheets URL")
        
        # Import sheet to DataFrame
        print(f"📊 Importing Google Sheet: {sheet_id}")
        df = await gs_import(sheet_url, sheet_name)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Sheet is empty or could not be read")
        
        print(f"📊 Sheet loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # Save as CSV to user's files directory
        paths = get_user_paths(user_id)
        temp_filename = f"google_sheet_{sheet_id[:8]}.csv"
        temp_path = paths["files"] / temp_filename
        
        df.to_csv(temp_path, index=False)
        print(f"📊 Saved to: {temp_path}")
        
        # Run ingestion pipeline using process method (for files already on disk)
        pipeline = IngestionPipeline()
        file_info = [{
            "id": f"gs_{sheet_id[:8]}",
            "name": temp_filename,
            "size": temp_path.stat().st_size if temp_path.exists() else 0,
            "type": "text/csv"
        }]
        pipeline.process(file_info, user_id, paths["files"].parent)
        
        # Invalidate cache
        invalidate_user_cache(user_id)
        
        return {
            "success": True,
            "message": "Google Sheet imported successfully",
            "filename": temp_filename,
            "rows": len(df),
            "columns": list(df.columns),
            "sampleData": df.head(3).to_dict(orient='records')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to import: {str(e)}")


@router.get("/{user_id}/preview-google-sheet")
async def preview_google_sheet(
    user_id: str,
    sheet_url: str = Query(..., description="Google Sheets URL or ID")
):
    """
    Preview a Google Sheet before importing
    Returns column names, row count, and sample data
    """
    try:
        from integrations.google_sheets import get_sheet_info
        
        info = await get_sheet_info(sheet_url)
        
        if not info.get("success"):
            raise HTTPException(
                status_code=400, 
                detail=info.get("error", "Failed to read sheet")
            )
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/join-suggestions")
async def get_join_suggestions(
    user_id: str,
    file1: str = Query(..., description="First filename"),
    file2: str = Query(..., description="Second filename")
):
    """
    Suggests possible join keys between two files.
    """
    try:
        paths = get_user_paths(user_id)
        file1_path = paths["files"] / sanitize_filename(file1)
        file2_path = paths["files"] / sanitize_filename(file2)
        
        if not file1_path.exists() or not file2_path.exists():
            raise HTTPException(status_code=404, detail="One or both files not found")
            
        import pandas as pd
        df1 = pd.read_csv(file1_path, nrows=1000)
        df2 = pd.read_csv(file2_path, nrows=1000)
        
        from core.multi_dataset_engine import MultiDatasetEngine
        suggestions = MultiDatasetEngine.infer_joins(df1, df2, file1, file2)
        
        return {"suggestions": suggestions}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel
class JoinRequest(BaseModel):
    file1: str
    file2: str
    left_on: str
    right_on: str
    how: str = "left"
    output_filename: str = "joined_dataset.csv"

@router.post("/{user_id}/join")
async def join_datasets(
    user_id: str,
    req: JoinRequest
):
    """
    Joins two datasets and saves the result as a new file.
    """
    try:
        paths = get_user_paths(user_id)
        file1_path = paths["files"] / sanitize_filename(req.file1)
        file2_path = paths["files"] / sanitize_filename(req.file2)
        
        if not file1_path.exists() or not file2_path.exists():
            raise HTTPException(status_code=404, detail="One or both files not found")
            
        import pandas as pd
        df1 = pd.read_csv(file1_path)
        df2 = pd.read_csv(file2_path)
        
        from core.multi_dataset_engine import MultiDatasetEngine
        merged_df = MultiDatasetEngine.join_datasets(
            df1, df2, req.left_on, req.right_on, req.how
        )
        
        # Save output
        output_name = sanitize_filename(req.output_filename)
        if not output_name.endswith('.csv'):
            output_name += '.csv'
            
        output_path = paths["files"] / output_name
        merged_df.to_csv(output_path, index=False)
        
        # Invalidate cache
        invalidate_user_cache(user_id)
        
        # Register in metadata
        pipeline = IngestionPipeline()
        file_info = [{
            "filename": output_name,
            "original_name": output_name,
            "path": str(output_path),
            "size": output_path.stat().st_size,
            "type": "text/csv"
        }]
        pipeline.process(file_info, user_id, paths["files"].parent)
        
        return {
            "success": True,
            "message": "Datasets joined successfully",
            "filename": output_name,
            "rows": len(merged_df),
            "columns": list(merged_df.columns)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
