import json
import logging
import os
import re
from typing import Dict, Any, List, AsyncGenerator
from core.llm import chat

logger = logging.getLogger(__name__)

class AgentEngine:
    """
    An XML-based ReAct agent engine that streams Server-Sent Events (SSE) to the frontend.
    Supports tools: read_file, write_file, run_command, ask_user.
    """
    def __init__(self, workspace_dir: str, user_id: str):
        self.workspace_dir = workspace_dir
        self.user_id = user_id
        
    async def stream_chat(self, prompt: str, history: List[Dict[str, str]], files: Dict[str, str], model: str) -> AsyncGenerator[str, None]:
        # Pre-process file summary
        file_summary = ""
        for name, content in files.items():
            file_summary += f"- {name} ({len(content)} bytes)\n"
            
        system_prompt = f"""You are DataVision Agent, a highly capable Silicon Valley AI Architect.
You operate in a continuous Loop: THOUGHT -> ACTION -> OBSERVATION.
CRITICAL RULE: You are fully capable of writing files and executing commands on the user's local system using the tools below. NEVER say you cannot write files or ask the user to implement things manually. You MUST use your tools to complete the user's task yourself!
CRITICAL RULE 2: If a file or project does not exist, DO NOT complain to the user! You must CREATE the files yourself using `write_file` or initialize the project yourself using `run_command` (e.g. `npm init`, `npx create-vite`, etc.). Be proactive!

Available Tools:
1. `read_file`: Read the contents of a file. Args: {{"path": "string", "offset": "optional line start (int)", "limit": "optional max lines (int)"}}
2. `write_file`: Write or overwrite a file.
3. `run_command`: Run a terminal command.
4. `ask_user`: Ask the user a clarifying question or request permission to proceed.
5. `mcp_call`: Call a Model Context Protocol (MCP) server tool. Args: {{"server": "name", "tool": "tool_name", "args": {{}}}}

To use a tool, you MUST use XML tags exactly like this:
<thought>
I need to check the package.json to see if react is installed.
</thought>
<tool name="read_file">
{{"path": "package.json"}}
</tool>

When you are finished and want to respond to the user, use:
<thought>
I have completed the task.
</thought>
<response>
Your task is complete! Here is what I did...
</response>

Workspace Context:
{file_summary}
"""
        
        # We will loop up to 10 times autonomously
        MAX_TURNS = 10
        current_messages = list(history) if history else []
        current_messages.append({"role": "user", "content": prompt})
        
        for turn in range(MAX_TURNS):
            yield f"data: {json.dumps({'type': 'status', 'content': f'Turn {turn+1}/{MAX_TURNS}: Thinking...'})}\n\n"
            
            try:
                # Call LLM
                response_text = chat(
                    messages=current_messages,
                    system=system_prompt,
                    model=model,
                    temperature=0.2
                )
                
                # We append assistant's raw output to history
                current_messages.append({"role": "assistant", "content": response_text})
                
                # Parse the response for thoughts, tools, and final response
                thought_match = re.search(r'<thought>(.*?)</thought>', response_text, re.DOTALL)
                if thought_match:
                    thought = thought_match.group(1).strip()
                    yield f"data: {json.dumps({'type': 'thought', 'content': thought})}\n\n"
                
                tool_match = re.search(r'<tool name="(.*?)">(.*?)</tool>', response_text, re.DOTALL)
                response_match = re.search(r'<response>(.*?)</response>', response_text, re.DOTALL)
                
                if response_match:
                    # The agent is done
                    final_text = response_match.group(1).strip()
                    yield f"data: {json.dumps({'type': 'message', 'content': final_text})}\n\n"
                    break
                    
                elif tool_match:
                    tool_name = tool_match.group(1).strip()
                    try:
                        tool_args = json.loads(tool_match.group(2).strip())
                        if not isinstance(tool_args, dict):
                            tool_args = {"raw": str(tool_args)}
                    except:
                        tool_args = {"raw": tool_match.group(2).strip()}
                        
                    if tool_name == "ask_user":
                        # Stream the question to the user and stop the loop
                        question = tool_args.get("question", tool_args.get("raw", "I need your input."))
                        yield f"data: {json.dumps({'type': 'message', 'content': question})}\n\n"
                        break
                        
                    yield f"data: {json.dumps({'type': 'tool_call', 'tool': tool_name, 'args': tool_args})}\n\n"
                    
                    # Execute Tool
                    observation = self._execute_tool(tool_name, tool_args)
                    
                    yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool_name, 'result': observation})}\n\n"
                    
                    # Append observation and loop again
                    current_messages.append({"role": "user", "content": f"<observation>\n{observation}\n</observation>"})
                    
                else:
                    # Neither a tool nor a response was found. Assume they just responded directly.
                    yield f"data: {json.dumps({'type': 'message', 'content': response_text})}\n\n"
                    break
                    
            except Exception as e:
                logger.error(f"Agent Loop Error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
                break
                
        # Sync files back to frontend
        updated_files = {}
        for root, _, files_in_dir in os.walk(self.workspace_dir):
            for file in files_in_dir:
                if file.endswith(('.py', '.ts', '.tsx', '.js', '.jsx', '.html', '.css', '.md', '.json', '.txt', '.yml', '.yaml', '.toml', '.sh', '.bat')):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.workspace_dir)
                    rel_path = rel_path.replace("\\", "/") # Normalize for web
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            updated_files[rel_path] = f.read()
                    except:
                        pass
                        
        yield f"data: {json.dumps({'type': 'sync_files', 'files': updated_files})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    def _execute_tool(self, name: str, args: dict) -> str:
        try:
            if name == "read_file":
                path = os.path.join(self.workspace_dir, args.get("path", ""))
                offset = args.get("offset")
                limit = args.get("limit")
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                if offset is not None:
                    lines = lines[int(offset):]
                if limit is not None:
                    lines = lines[:int(limit)]
                return "".join(lines)
            elif name == "write_file":
                path = os.path.join(self.workspace_dir, args.get("path", ""))
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(args.get("content", ""))
                return "File written successfully."
            elif name == "run_command":
                import subprocess
                cmd = args.get("command", "")
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                result = subprocess.run(
                    cmd, shell=True, cwd=self.workspace_dir, 
                    capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=30
                )
                output = result.stdout + result.stderr
                return output if output else "Command executed silently with code 0."
            elif name == "mcp_call":
                # Stub for MCP client.
                # In a full implementation, this would connect to the MCP server and call the tool.
                server = args.get("server")
                tool = args.get("tool")
                return f"MCP Error: Server '{server}' is not configured. Please configure MCP servers in settings."
            else:
                return f"Unknown tool: {name}"
        except Exception as e:
            return f"Error executing tool: {e}"
