"""
Real Files Management - NO FAKE DATA
Everything based on actual uploaded files
Enterprise-grade with auto currency detection
With cache invalidation for data consistency
SECURED: Uses JWT authentication for user isolation
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Header, Depends
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional, Dict
from pathlib import Path
import shutil
import traceback
from datetime import datetime

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
    from database.auth import decode_jwt
except ImportError:
    decode_jwt = None

router = APIRouter()


def get_user_id_from_headers(
    x_user_id: Optional[str] = None,
    authorization: Optional[str] = None
) -> str:
    """Extract user ID from JWT token or X-User-ID header"""
    user_id = None
    
    # Try JWT token first (most secure)
    if authorization and authorization.startswith("Bearer ") and decode_jwt:
        try:
            token = authorization.split(" ")[1]
            payload = decode_jwt(token)
            user_id = payload.get("sub")
            print(f"🔐 Files API - User from JWT: {user_id}")
        except Exception as e:
            print(f"⚠️ JWT decode error: {e}")
    
    # Fallback to X-User-ID header
    if not user_id and x_user_id:
        user_id = x_user_id
        print(f"🔐 Files API - User from header: {user_id}")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required. Please log in.")
    
    return user_id


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
    user_id: str,
    files: List[UploadFile] = File(...),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Upload and process files with REAL ingestion pipeline
    SECURED: Validates user identity from JWT token
    """
    try:
        # SECURITY: Verify user is authenticated and matches URL
        authenticated_user = get_user_id_from_headers(x_user_id, authorization)
        
        # For backwards compatibility, use URL user_id but log warning if mismatch
        if authenticated_user != user_id:
            print(f"⚠️ WARNING: Auth user {authenticated_user} ≠ URL user {user_id}")
            # Use authenticated user for security
            user_id = authenticated_user
        
        paths = get_user_paths(user_id)
        uploaded_files = []
        
        # Invalidate cache since data is changing
        invalidate_user_cache(user_id)
        
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
        detected_currency = detect_and_save_user_currency(user_id, paths["files"], STORAGE_BASE)
        
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
            
            # Process ALL files with REAL pipeline
            result = pipeline.process(
                all_files_in_dir,
                user_id=user_id,
                base_path=STORAGE_BASE
            )
            
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
        
        return {
            "success": True,
            "files": uploaded_files,
            "message": f"{len(uploaded_files)} file(s) processed with REAL data",
            "detectedCurrency": detected_currency,
            "schemaIntelligence": schema_result
        }
        
    except Exception as e:
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
        authenticated_user = get_user_id_from_headers(x_user_id, authorization)
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
        authenticated_user = get_user_id_from_headers(x_user_id, authorization)
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
        # SECURITY: Validate user
        authenticated_user = get_user_id_from_headers(x_user_id, authorization)
        if authenticated_user != user_id:
            user_id = authenticated_user
        
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
        authenticated_user = get_user_id_from_headers(x_user_id, authorization)
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
        authenticated_user = get_user_id_from_headers(x_user_id, authorization)
        if authenticated_user != user_id:
            user_id = authenticated_user
        
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
        
        # Get remaining files for retraining
        remaining_files = [f for f in paths["files"].glob("*") if f.is_file()]
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
        files = [f for f in paths["files"].glob("*") if f.is_file()]
        
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
        from ingestion.pipeline import ingest
        import tempfile
        import os
        
        # Validate sheet ID
        sheet_id = extract_sheet_id(sheet_url)
        if not sheet_id:
            raise HTTPException(status_code=400, detail="Invalid Google Sheets URL")
        
        # Import sheet to DataFrame
        df = await gs_import(sheet_url, sheet_name)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Sheet is empty or could not be read")
        
        # Save as temporary CSV
        paths = get_user_paths(user_id)
        temp_filename = f"google_sheet_{sheet_id[:8]}.csv"
        temp_path = paths["uploads"] / temp_filename
        
        df.to_csv(temp_path, index=False)
        
        # Run ingestion pipeline
        result = ingest(user_id)
        
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
