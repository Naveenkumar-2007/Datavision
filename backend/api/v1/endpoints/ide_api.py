import os
import uuid
import subprocess
import threading
import json
import zipfile
import io
import time
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Header, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Global dictionary to store running processes and their logs
# Format: { pid: { "process": subprocess.Popen, "logs": list, "status": "running"|"completed"|"error", "url": str } }
processes: Dict[str, Dict[str, Any]] = {}

class RunWorkspaceRequest(BaseModel):
    user_id: str
    files: Dict[str, str]
    command: Optional[str] = "python api_server.py"

class ChatWorkspaceRequest(BaseModel):
    user_id: str
    files: Dict[str, str]
    prompt: str
    model: str = "nvidia/nemotron-3-ultra-550b-a55b"
    chat_history: Optional[List[Dict[str, str]]] = None
    images: Optional[List[str]] = None
    mode: Optional[str] = "execute"  # 'plan' or 'execute'

def _run_process(pid: str, workspace_dir: str, command: str):
    try:
        # Run the command in the workspace directory with UTF-8 encoding forced
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        process = subprocess.Popen(
            command,
            cwd=workspace_dir,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            env=env
        )
        processes[pid]["process"] = process
        
        import re
        # Read output line by line
        if process.stdout:
            for line in process.stdout:
                if pid in processes:
                    processes[pid]["logs"].append(line)
                    # Dynamically detect when the server has started
                    if not processes[pid].get("url"):
                        match = re.search(r'http://(?:127\.0\.0\.1|localhost|0\.0\.0\.0):(\d+)', line)
                        if match:
                            port = match.group(1)
                            if "api_server.py" in command or "predict.py" in command:
                                processes[pid]["url"] = f"http://localhost:{port}/predict"
                            else:
                                processes[pid]["url"] = f"http://localhost:{port}"
        
        process.wait()
        
        if pid in processes:
            if process.returncode == 0:
                processes[pid]["status"] = "completed"
            else:
                processes[pid]["status"] = "error"
                processes[pid]["logs"].append(f"\n[Process exited with code {process.returncode}]")
                
    except Exception as e:
        if pid in processes:
            processes[pid]["status"] = "error"
            processes[pid]["logs"].append(f"\n[Execution Error]: {str(e)}")

def _run_raw_terminal(pid: str, workspace_dir: str, shell: str):
    """Runs a raw shell (cmd/powershell) and reads output byte-by-byte for interactive PTY-like behavior."""
    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PROMPT"] = "$P$G"
        
        process = subprocess.Popen(
            shell,
            cwd=workspace_dir,
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=0, # Unbuffered for instant character transmission
            env=env
        )
        processes[pid]["process"] = process
        
        if process.stdout:
            while True:
                char = process.stdout.read(1)
                if not char:
                    break
                if pid in processes:
                    # Append character to logs for client to fetch
                    processes[pid]["logs"].append(char)
                    
        process.wait()
        if pid in processes:
            processes[pid]["status"] = "completed"
            processes[pid]["logs"].append(f"\n[Terminal closed]")
            
    except Exception as e:
        if pid in processes:
            processes[pid]["status"] = "error"
            processes[pid]["logs"].append(f"\n[Terminal Error]: {str(e)}")

class TerminalSpawnRequest(BaseModel):
    user_id: str
    shell: str = "cmd.exe"

@router.post("/terminal/spawn")
async def spawn_terminal(request: TerminalSpawnRequest):
    """Spawns a persistent raw shell session."""
    try:
        pid = str(uuid.uuid4())
        workspace_dir = os.path.join(os.path.dirname(os.getcwd()), ".workspace", request.user_id)
        os.makedirs(workspace_dir, exist_ok=True)
        
        processes[pid] = {
            "process": None,
            "logs": [],
            "status": "running",
            "url": None,
            "user_id": request.user_id
        }
        
        shell_cmd = "powershell.exe" if request.shell == "powershell" else "cmd.exe"
        
        thread = threading.Thread(target=_run_raw_terminal, args=(pid, workspace_dir, shell_cmd))
        thread.daemon = True
        thread.start()
        
        return {"success": True, "pid": pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/project/{user_id}")
async def get_ide_project(
    user_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    try:
        from config.settings import Settings
        from ml.ml_code_generator import generate_code_zip
        
        base_storage = Settings.STORAGE
        actual_user_id = x_user_id if x_user_id else user_id
        
        model_path = None
        search_paths = [
            base_storage / "models" / actual_user_id / "active_model.pkl",
            base_storage / "automl" / actual_user_id / "model.pkl",
            base_storage / "users" / actual_user_id / "model.pkl",
            base_storage / "files" / actual_user_id / "model.pkl",
        ]
        
        for candidate in search_paths:
            if candidate.exists():
                model_path = candidate
                break
                
        if not model_path:
            raise HTTPException(status_code=404, detail="No trained model found. Please train a model first.")
            
        metadata = {}
        metadata_paths = [
            model_path.parent / "active_metadata.json",
            model_path.parent / "multimode_metadata.json",
            model_path.parent / "metadata.json",
            base_storage / "automl" / actual_user_id / "multimode_metadata.json",
            base_storage / "users" / actual_user_id / "multimode_metadata.json",
        ]
        for mp in metadata_paths:
            if mp.exists():
                with open(mp, 'r') as f:
                    metadata = json.load(f)
                break
                
        if not metadata:
            metadata = {"task_type": "classification", "best_mode": "traditional"}
            
        # Generate the complete ZIP project in memory
        buf = generate_code_zip(model_path, metadata)
        
        # Ensure workspace exists and is fresh
        workspace_dir = os.path.join(os.path.dirname(os.getcwd()), ".workspace", actual_user_id)
        os.makedirs(workspace_dir, exist_ok=True)
        
        # Unzip into memory dictionary and write to workspace
        files_dict = {}
        with zipfile.ZipFile(buf, 'r') as z:
            for info in z.infolist():
                if not info.is_dir():
                    # 1. Write to local workspace for local IDEs to work correctly
                    filepath = os.path.join(workspace_dir, info.filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    raw_content = z.read(info.filename)
                    with open(filepath, "wb") as f:
                        f.write(raw_content)
                        
                    # 2. Add text files to files_dict for the Web IDE UI
                    try:
                        content = raw_content.decode('utf-8')
                        files_dict[info.filename] = content
                    except UnicodeDecodeError:
                        pass # Ignore binary files for UI
                        
        return {"success": True, "files": files_dict}
    except Exception as e:
        logger.error(f"Failed to load IDE project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class TerminalInputRequest(BaseModel):
    input: str

@router.post("/terminal/input/{pid}")
async def terminal_input(pid: str, request: TerminalInputRequest):
    if pid not in processes:
        raise HTTPException(status_code=404, detail="Process not found")
        
    process = processes[pid].get("process")
    if not process or not process.stdin:
        raise HTTPException(status_code=400, detail="Process stdin not available")
        
    try:
        # xterm.js sends \r for enter
        input_str = request.input
        logger.info(f"TERMINAL INPUT: {repr(input_str)}")
        if input_str == '\r':
            input_str = '\n'  # Python's text=True handles \r\n translation on Windows
            
        process.stdin.write(input_str)
        process.stdin.flush()
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to write to terminal stdin: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class DownloadWorkspaceRequest(BaseModel):
    user_id: str
    files: Dict[str, str]

@router.post("/download")
async def download_workspace(request: DownloadWorkspaceRequest):
    try:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename, content in request.files.items():
                zf.writestr(filename, content)
                
            # Also include clean binary files (model.pkl, etc.) via code generator
            try:
                from config.settings import Settings
                from ml.ml_code_generator import generate_code_zip
                import json
                
                base_storage = Settings.STORAGE
                model_path = None
                search_paths = [
                    base_storage / "models" / request.user_id / "active_model.pkl",
                    base_storage / "automl" / request.user_id / "model.pkl",
                    base_storage / "users" / request.user_id / "model.pkl",
                    base_storage / "files" / request.user_id / "model.pkl",
                ]
                for candidate in search_paths:
                    if candidate.exists():
                        model_path = candidate
                        break
                        
                if model_path:
                    metadata = {}
                    metadata_paths = [
                        model_path.parent / "active_metadata.json",
                        model_path.parent / "multimode_metadata.json",
                        model_path.parent / "metadata.json",
                        base_storage / "automl" / request.user_id / "multimode_metadata.json",
                        base_storage / "users" / request.user_id / "multimode_metadata.json",
                    ]
                    for mp in metadata_paths:
                        if mp.exists():
                            with open(mp, 'r') as f:
                                metadata = json.load(f)
                            break
                            
                    if not metadata:
                        metadata = {"task_type": "classification", "best_mode": "traditional"}
                        
                    bin_buf = generate_code_zip(model_path, metadata)
                    with zipfile.ZipFile(bin_buf, 'r') as bz:
                        for info in bz.infolist():
                            if not info.is_dir():
                                if info.filename.endswith(".pkl") or info.filename.endswith(".png"):
                                    zf.writestr(info.filename, bz.read(info.filename))
            except Exception as e:
                logger.warning(f"Failed to append binary files to download zip: {e}")
                
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=workspace.zip"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run")
async def run_workspace(request: RunWorkspaceRequest):
    """Saves multiple files to a workspace and executes a command."""
    try:
        pid = str(uuid.uuid4())
        
        # Store outside backend folder to prevent uvicorn hot-reload loop
        workspace_dir = os.path.join(os.path.dirname(os.getcwd()), ".workspace", request.user_id)
        os.makedirs(workspace_dir, exist_ok=True)
        
        # Write all files to the workspace
        for filename, content in request.files.items():
            filepath = os.path.join(workspace_dir, filename)
            # Ensure subdirectories exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
                
        # Also attempt to extract clean binary files (model.pkl, etc.) via code generator
        try:
            from config.settings import Settings
            from ml.ml_code_generator import generate_code_zip
            import zipfile
            import io
            
            base_storage = Settings.STORAGE
            model_path = None
            search_paths = [
                base_storage / "models" / request.user_id / "active_model.pkl",
                base_storage / "automl" / request.user_id / "model.pkl",
                base_storage / "users" / request.user_id / "model.pkl",
                base_storage / "files" / request.user_id / "model.pkl",
            ]
            for candidate in search_paths:
                if candidate.exists():
                    model_path = candidate
                    break
                    
            if model_path:
                metadata = {}
                metadata_paths = [
                    model_path.parent / "active_metadata.json",
                    model_path.parent / "multimode_metadata.json",
                    model_path.parent / "metadata.json",
                    base_storage / "automl" / request.user_id / "multimode_metadata.json",
                    base_storage / "users" / request.user_id / "multimode_metadata.json",
                ]
                for mp in metadata_paths:
                    if mp.exists():
                        with open(mp, 'r') as f:
                            metadata = json.load(f)
                        break
                        
                if not metadata:
                    metadata = {"task_type": "classification", "best_mode": "traditional"}
                    
                buf = generate_code_zip(model_path, metadata)
                with zipfile.ZipFile(buf, 'r') as z:
                    for info in z.infolist():
                        if not info.is_dir():
                            if info.filename.endswith(".pkl") or info.filename.endswith(".png"):
                                content = z.read(info.filename)
                                filepath = os.path.join(workspace_dir, info.filename)
                                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                                with open(filepath, "wb") as f:
                                    f.write(content)
        except Exception as copy_err:
            logger.warning(f"Failed to copy model.pkl to workspace: {copy_err}")
                
        # Initialize process tracking
        processes[pid] = {
            "process": None,
            "logs": [f"[System] Started execution in {workspace_dir}...\n", f"[System] Command: {request.command}\n"],
            "status": "running",
            "url": None,
            "user_id": request.user_id
        }
        
        # Start execution thread
        thread = threading.Thread(target=_run_process, args=(pid, workspace_dir, request.command))
        thread.daemon = True
        thread.start()
        
        import asyncio
        # Wait a brief moment to see if URL is generated immediately
        await asyncio.sleep(0.5)
        
        return {
            "success": True, 
            "pid": pid,
            "url": None # URL will be fetched via log polling once server actually starts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workspace-path/{user_id}")
async def get_workspace_path(user_id: str):
    """Returns the absolute path to the user's workspace for deep-linking to local IDEs."""
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(os.getcwd()), ".workspace", user_id))
    os.makedirs(workspace_dir, exist_ok=True)
    # Ensure forward slashes for cross-platform deep linking
    workspace_dir = workspace_dir.replace('\\', '/')
    return {"success": True, "path": workspace_dir}

@router.post("/run-project/{user_id}")
async def run_existing_project(user_id: str):
    """Auto-detects project type in the existing workspace and runs it."""
    try:
        pid = str(uuid.uuid4())
        workspace_dir = os.path.abspath(os.path.join(os.path.dirname(os.getcwd()), ".workspace", user_id))
        
        if not os.path.exists(workspace_dir):
            raise HTTPException(status_code=404, detail="Workspace does not exist. Ask the agent to generate code first.")
            
        command = "python main.py" # Default
        
        # Auto-detect project type
        if os.path.exists(os.path.join(workspace_dir, "package.json")):
            command = "npm run dev"
            if not os.path.exists(os.path.join(workspace_dir, "node_modules")):
                command = "npm install && npm run dev"
        elif os.path.exists(os.path.join(workspace_dir, "api_server.py")):
            command = "python api_server.py"
        elif os.path.exists(os.path.join(workspace_dir, "requirements.txt")):
            command = "pip install -r requirements.txt && python main.py"
            
        processes[pid] = {
            "process": None,
            "logs": [f"[System] Starting project in {workspace_dir}...\n", f"[System] Auto-detected command: {command}\n"],
            "status": "running",
            "url": None,
            "user_id": user_id
        }
        
        thread = threading.Thread(target=_run_process, args=(pid, workspace_dir, command))
        thread.daemon = True
        thread.start()
        
        import asyncio
        await asyncio.sleep(0.5)
        
        return {"success": True, "pid": pid, "url": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{user_id}")
async def get_ide_status(user_id: str):
    active_pid = None
    for pid, p in processes.items():
        if p.get("user_id") == user_id:
            active_pid = pid
            break
            
    if not active_pid:
        return {"success": True, "active": False}
        
    return {
        "success": True,
        "active": True,
        "pid": active_pid,
        "status": processes[active_pid]["status"],
        "url": processes[active_pid]["url"]
    }

@router.get("/logs/{pid}")
async def get_logs(pid: str):
    if pid not in processes:
        raise HTTPException(status_code=404, detail="Process not found")
    return {
        "success": True, 
        "logs": "".join(processes[pid]["logs"]),
        "status": processes[pid]["status"],
        "url": processes[pid].get("url")
    }

@router.post("/stop/{pid}")
async def stop_process(pid: str):
    if pid not in processes:
        raise HTTPException(status_code=404, detail="Process not found")
        
    process_info = processes[pid]
    if process_info["status"] == "running" and process_info["process"]:
        try:
            if os.name == 'nt':
                subprocess.run(f"taskkill /F /T /PID {process_info['process'].pid}", shell=True, capture_output=True)
            else:
                process_info["process"].terminate()
            
            process_info["status"] = "completed"
            process_info["logs"].append("\n[System] Process terminated by user.")
            return {"success": True, "message": "Process stopped"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to stop process: {str(e)}")
    return {"success": True, "message": "Process already stopped"}

@router.post("/chat/stream")
async def chat_with_ide_stream(request: ChatWorkspaceRequest):
    """
    Multi-Step Autonomous Agentic AI — with Server-Sent Events (SSE) streaming!
    """
    from core.agent_engine import AgentEngine
    from core.llm import set_requested_model
    
    if request.model:
        set_requested_model(request.model)
        
    workspace_dir = os.path.join(os.path.dirname(os.getcwd()), ".workspace", request.user_id)
    os.makedirs(workspace_dir, exist_ok=True)
    
    # Write incoming files to workspace immediately so agent sees latest
    if request.files:
        for filename, content in request.files.items():
            if filename.startswith("Terminal"): continue
            filepath = os.path.join(workspace_dir, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
                
    agent = AgentEngine(workspace_dir=workspace_dir, user_id=request.user_id)
    
    return StreamingResponse(
        agent.stream_chat(
            prompt=request.prompt,
            history=request.chat_history or [],
            files=request.files,
            model=request.model or "openai/meta/llama-3.3-70b-instruct"
        ),
        media_type="text/event-stream"
    )

@router.post("/chat")
async def chat_with_ide(request: ChatWorkspaceRequest):
    """
    Multi-Step Autonomous Agentic AI — works like a professional AI coding assistant:
    Step 1: PLAN — Analyze codebase + user request → decide which files to create/modify
    Step 2: GENERATE — Write each file's COMPLETE content in a separate LLM call
    Step 3: ASSEMBLE — Return all files to the frontend
    """
    try:
        from core.llm import chat as llm_chat, set_requested_model
        
        if request.model:
            set_requested_model(request.model)
            
        # =====================================================================
        # PREPARE: Smart file context
        # =====================================================================
        prompt_lower = request.prompt.lower()
        
        allowed_extensions = ('.py', '.ts', '.tsx', '.js', '.jsx', '.html', '.css', '.md', '.json', '.txt', '.yml', '.yaml', '.toml', '.sh', '.bat')
        filtered_files = {}
        for filename, content in request.files.items():
            if not filename.endswith(allowed_extensions):
                continue
            if len(content) > 8000:
                filtered_files[filename] = content[:2000] + f"\n\n# ... [truncated, {len(content)} total bytes]"
            else:
                filtered_files[filename] = content
        
        # Build a compact file summary for the planning step
        file_summary_lines = []
        for filename, content in filtered_files.items():
            lines_count = content.count('\n') + 1
            size = len(content)
            # Show first 3 lines as preview
            preview = content.split('\n')[:3]
            preview_str = ' | '.join(line.strip()[:60] for line in preview if line.strip())
            file_summary_lines.append(f"  - {filename} ({lines_count} lines, {size} bytes): {preview_str}")
        file_summary = '\n'.join(file_summary_lines)        # =====================================================================
        # AGENTIC LOOP (PLAN -> EXECUTE -> REFLECT)
        # =====================================================================
        current_history = list(request.chat_history) if request.chat_history else []
        final_updated_files = {}
        final_explanation = ""
        auto_corrections_made = 0
        
        MAX_TURNS = 3
        for turn in range(MAX_TURNS):
            logger.info(f"🧠 IDE Agent Turn {turn + 1}/{MAX_TURNS}...")
            
            is_ui_request = any(w in prompt_lower for w in ['ui', 'design', 'frontend', 'html', 'css', 'style', 'page', 'dashboard', 'theme', 'layout', 'color', 'dark', 'redesign', 'beautiful', 'premium'])
            
            if turn == 0 and is_ui_request:
                plan = {
                    "explanation": "I'll redesign your frontend based on your request.",
                    "files_to_generate": [
                        {"filename": "templates/index.html", "action": "modify", "description": f"Complete HTML/CSS/JS single-page frontend for: {request.prompt}. Make it highly premium, modern, and dark-themed."}
                    ]
                }
            else:
                plan_prompt = f"""You are a Senior Silicon Valley AI Architect operating inside DataVision's IDE Orchestrator Hub.
DataVision is a powerful autonomous orchestration platform. You act as an autonomous agent writing code and planning architecture in the background, while the user views and edits code in their native IDEs (VS Code, Cursor, Antigravity IDE) and runs the project via the 'RUN PROJECT' button.

## Current Workspace Files:
{file_summary}

## Conversational History:
{json.dumps(current_history[-10:], indent=2) if current_history else "No previous history."}

## User Request:
{request.prompt}

## Your Task:
Analyze the request and create a comprehensive architectural plan. You are an autonomous Agent. Think end-to-end. 

Return a JSON object with:
1. "explanation" - Speak DIRECTLY to the user in a friendly, conversational tone. Acknowledge that they can click "Open in [IDE]" to see your changes and "RUN PROJECT" to test them. Do NOT talk about the user in the third person.
2. "files_to_generate" - A list of objects, each with:
   - "filename": the file path OR the command name (if running a command)
   - "action": "create", "modify", or "command"
   - "description": EXTREMELY SPECIFIC instructions on what this file should contain, or why the command is being run
   - "command": ONLY if action="command", provide the terminal command to execute (e.g., "npm install react")

IMPORTANT RULES:
- For UI redesigns, generate the necessary files. Make UIs look incredibly premium, modern, and beautiful.
- You CAN and SHOULD use action="command" to install any dependencies your plan requires.
- If the user is just saying "hi", asking a question, or chatting, set "files_to_generate" to an EMPTY LIST [].
- Only generate files if the user actually requested code changes or a new feature.

Return ONLY valid JSON, no markdown fences."""

                plan_response = llm_chat(
                    messages=plan_prompt,
                    system="You are a code architect. Return only valid JSON. No markdown. No explanation outside JSON.",
                    temperature=0.1,
                    max_tokens=2000,
                    images=request.images if turn == 0 else None
                )
                
                plan_text = plan_response.strip() if isinstance(plan_response, str) else str(plan_response)
                if "```json" in plan_text: plan_text = plan_text.split("```json")[1].split("```")[0]
                elif "```" in plan_text: plan_text = plan_text.split("```")[1].split("```")[0]
                
                s = plan_text.find('{')
                e = plan_text.rfind('}')
                if s != -1 and e != -1: plan_text = plan_text[s:e+1]
                
                try:
                    plan = json.loads(plan_text)
                except json.JSONDecodeError:
                    plan = {"explanation": "I'm here to help you code! What would you like to build?", "files_to_generate": []}
            
            files_to_gen = plan.get("files_to_generate", [])
            final_explanation = plan.get("explanation", "Changes applied successfully.")
            
            logger.info(f"📋 Plan Turn {turn + 1}: {len(files_to_gen)} files to generate: {[f['filename'] for f in files_to_gen]}")
            
            if getattr(request, "mode", "execute") == "plan":
                logger.info("🧠 Planning mode requested. Returning plan without generating files.")
                return {"success": True, "data": {"explanation": final_explanation, "updated_files": {}, "is_plan": True}}
            
            has_commands = False
            command_outputs = ""
            
            if not files_to_gen:
                break
                
            time.sleep(2.0)
            
            for i, file_spec in enumerate(files_to_gen[:8]):
                filename = file_spec.get("filename", f"file_{i}.txt")
                description = file_spec.get("description", request.prompt)
                action = file_spec.get("action", "create")
                
                if action == "command":
                    has_commands = True
                    cmd = file_spec.get("command", filename)
                    logger.info(f"⚡ Running command {cmd}...")
                    try:
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.path.join(os.path.dirname(os.getcwd()), ".workspace", request.user_id) if os.path.exists(os.path.join(os.path.dirname(os.getcwd()), ".workspace", request.user_id)) else os.getcwd())
                        output = f"$ {cmd}\n{result.stdout}\n{result.stderr}"
                        final_updated_files[f"Terminal Execution: {cmd}"] = output
                        command_outputs += f"\n{output}\n"
                    except Exception as e:
                        final_updated_files[f"Terminal Error: {cmd}"] = str(e)
                        command_outputs += f"\nError running {cmd}: {e}\n"
                    continue
                
                logger.info(f"📝 Generating {filename}...")
                existing_content = f"\n\n## EXISTING FILE CONTENT (modify this):\n```\n{filtered_files[filename]}\n```" if action == "modify" and filename in filtered_files else ""
                config_context = f"\n\n## MODEL CONFIG (use this data):\n```json\n{filtered_files['config.json'][:3000]}\n```" if "config.json" in filtered_files else ""
                api_context = ""
                if "api_server.py" in filtered_files:
                    api_lines = [line.strip() for line in filtered_files["api_server.py"].split('\n') if any(kw in line for kw in ['@app.route', 'RAW_FEATURE_INFO', 'TARGET_COLUMN', 'BEST_MODE', 'def predict', 'def health', 'def model_info'])]
                    if api_lines: api_context = f"\n\n## API ENDPOINTS (from api_server.py):\n" + '\n'.join(api_lines)

                generate_prompt = f"""Generate the COMPLETE content for the file: {filename}

## What this file should do:
{description}

## User's original request:
{request.prompt}
{existing_content}{config_context}{api_context}

## CRITICAL RULES:
1. Output ONLY the file content. No markdown fences. No explanations.
2. Write the COMPLETE file from start to finish. Every single line.
3. For HTML files: include ALL CSS in a <style> tag and ALL JS in a <script> tag.
4. Do NOT use placeholder text. Write real, working code.

Output the complete file content now:"""

                file_content = llm_chat(messages=generate_prompt, system="You are an expert full-stack developer. Output ONLY the raw file content. No markdown fences.", temperature=0.3, max_tokens=4000)
                
                if isinstance(file_content, str) and file_content.strip():
                    content = file_content.strip()
                    if content.startswith("```"):
                        first_newline = content.find('\n')
                        if first_newline != -1: content = content[first_newline+1:]
                        if content.endswith("```"): content = content[:-3].rstrip()
                            
                    if filename.endswith(".py"):
                        import traceback
                        for attempt in range(2):
                            try:
                                compile(content, filename, "exec")
                                break
                            except Exception as e:
                                error_msg = traceback.format_exc()
                                correction_response = llm_chat(messages=[{"role": "user", "content": f"Fix this syntax error in {filename}:\n{error_msg}\n\nOutput ONLY the complete raw code file."}], system="You are an expert python debugger.", temperature=0.1, max_tokens=4000)
                                if isinstance(correction_response, str) and correction_response.strip():
                                    content = correction_response.strip()
                                    if content.startswith("```"):
                                        first_newline = content.find('\n')
                                        if first_newline != -1: content = content[first_newline+1:]
                                        if content.endswith("```"): content = content[:-3]
                                    auto_corrections_made += 1
                                    
                    final_updated_files[filename] = content
                    # Immediately update filtered_files so next turn sees the change!
                    filtered_files[filename] = content
                    logger.info(f"✅ Generated {filename} ({len(content)} bytes)")
                    
                if i < len(files_to_gen) - 1:
                    time.sleep(2.0)
            
            # If there were commands run, we loop again with the outputs
            if has_commands and turn < MAX_TURNS - 1:
                current_history.append({"role": "assistant", "content": final_explanation})
                current_history.append({"role": "user", "content": f"Terminal Command Outputs:\n{command_outputs}\n\nAnalyze these outputs. If your task is complete, return empty files_to_generate. Otherwise, plan the next step."})
                logger.info(f"🔄 ReAct Loop: Found commands, triggering Turn {turn + 2}...")
                time.sleep(2.0)
            else:
                break
                
        # =====================================================================
        # STEP 3: ASSEMBLE — Return everything to frontend
        # =====================================================================
        
        updated_files = final_updated_files
        explanation = final_explanation if final_explanation else "Changes applied successfully."
        
        # Hot-reload sync: If a workspace is active for this user, write files to disk immediately
        workspace_dir = os.path.join(os.path.dirname(os.getcwd()), ".workspace", request.user_id)
        if os.path.exists(workspace_dir) and updated_files:
            try:
                for filename, content in updated_files.items():
                    # skip terminal executions
                    if filename.startswith("Terminal"):
                        continue
                    filepath = os.path.join(workspace_dir, filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                logger.info(f"🔄 Hot-reloaded {len(updated_files)} files into running workspace for {request.user_id}")
            except Exception as e:
                logger.error(f"Failed to hot-reload files: {e}")
        
        # Add summary of what was generated
        if updated_files:
            file_list = ', '.join(f"`{f}`" for f in updated_files.keys())
            explanation += f"\n\n✅ **Files generated:** {file_list}"
            if auto_corrections_made > 0:
                explanation += f"\n\n🛠️ **Self-Healing Active**: I detected and auto-corrected {auto_corrections_made} syntax errors in the background before showing you the code!"
            
            explanation += "\n\n### Code Changes\n"
            for filename, content in updated_files.items():
                ext = filename.split('.')[-1] if '.' in filename else ''
                explanation += f"\n**`{filename}`**\n```{ext}\n{content}\n```\n"
                
            explanation += f"\n\nClick **RUN** to start the server and see your changes!"
        
        logger.info(f"🎉 IDE Agent complete: {len(updated_files)} files generated")
        
        return {"success": True, "data": {
            "explanation": explanation,
            "updated_files": updated_files
        }}
            
    except Exception as e:
        logger.error(f"IDE Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# FILE CRUD ENDPOINTS — For the Explorer sidebar
# =============================================================================

class FileCreateRequest(BaseModel):
    user_id: str
    filename: str
    content: Optional[str] = ""

class FileDeleteRequest(BaseModel):
    user_id: str
    filename: str

class FileRenameRequest(BaseModel):
    user_id: str
    old_name: str
    new_name: str

@router.post("/file/create")
async def create_file(request: FileCreateRequest):
    """Create a new file in the IDE workspace."""
    return {"success": True, "filename": request.filename, "content": request.content}

@router.delete("/file/delete")
async def delete_file(request: FileDeleteRequest):
    """Delete a file from the IDE workspace."""
    return {"success": True, "filename": request.filename}

@router.put("/file/rename")
async def rename_file(request: FileRenameRequest):
    """Rename a file in the IDE workspace."""
    return {"success": True, "old_name": request.old_name, "new_name": request.new_name}

