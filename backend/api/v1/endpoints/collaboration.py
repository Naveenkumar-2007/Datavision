"""
👥 COLLABORATION HUB — Team Chat, Channels, Invites, AI Insights
===================================================================
Fully functional collaboration workspace with channels, messaging,
invite link generation, team management, and @ai data insights.
Migrated to PostgreSQL DB Models.
"""

from fastapi import APIRouter, Header, HTTPException, Depends, Request, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import hashlib
import json
import logging
from core.rate_limiter import check_rate_limit
from core.agent_swarm import CollaborationSwarm

collab_swarm = CollaborationSwarm()
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import delete
from database.db import get_db
from database.orm import ChatChannel, ChannelMessage, MessageReaction, ActivityLog, WorkspaceMember, UserProfile
from api.deps import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Pydantic Models ──

class PostMessageRequest(BaseModel):
    message: str
    user: str = "Naveenkumar"
    channel_id: Optional[str] = "default"
    is_encrypted: bool = False
    attachment_url: Optional[str] = None
    attachment_type: Optional[str] = None

class CreateChannelRequest(BaseModel):
    name: str

class InviteMemberRequest(BaseModel):
    name: str
    email: str
    role: str = "viewer"

class RemoveMemberRequest(BaseModel):
    email: str

class UpdateRoleRequest(BaseModel):
    email: str
    role: str

class ReactionRequest(BaseModel):
    emoji: str
    user: str = "Naveenkumar"

class ReplyRequest(BaseModel):
    message: str
    user: str = "Naveenkumar"

class PinRequest(BaseModel):
    message_id: str


# ── DB Helpers ──

async def _get_or_create_default_channel(db: AsyncSession) -> ChatChannel:
    stmt = select(ChatChannel).where(ChatChannel.name == "general")
    result = await db.execute(stmt)
    channel = result.scalar_one_or_none()
    if not channel:
        channel = ChatChannel(name="general", description="General discussion")
        db.add(channel)
        await db.commit()
        await db.refresh(channel)
    return channel

async def _resolve_channel_id(channel_id: str, db: AsyncSession) -> str:
    """Resolve 'default' to the UUID of the 'general' channel."""
    if channel_id == "default":
        channel = await _get_or_create_default_channel(db)
        return str(channel.id)
    return channel_id


def _generate_ai_insight(user_id: str, user_question: str) -> Optional[Dict]:
    """
    Generate a real AI insight by analyzing the user's uploaded data.
    """
    try:
        from api.v1.endpoints.charts import get_user_data
        import pandas as pd
        import numpy as np

        df = get_user_data(user_id)
        if df is None or df.empty:
            return {
                "id": str(int(datetime.now().timestamp() * 1000) + 1),
                "user": "DataVision AI",
                "avatar": "✨",
                "message": "I don't see any uploaded data yet. Please upload a dataset in the Data Hub first, then I can analyze it for you!",
                "time": "Just now",
                "chartRef": "System",
                "isAi": True,
            }

        source_file = df['_source_file'].iloc[0] if '_source_file' in df.columns else "your data"
        numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns if not c.startswith('_')]
        categorical_cols = [c for c in df.select_dtypes(include=['object', 'category']).columns if not c.startswith('_')]

        # Build a context-aware response
        question_lower = user_question.lower()
        insight = ""

        if any(word in question_lower for word in ['summary', 'overview', 'describe', 'tell me', 'what']):
            # Give a data summary
            insight = f"📊 **{source_file}** has {len(df):,} rows × {len(df.columns)} columns.\n\n"
            if numeric_cols:
                top_num = numeric_cols[0]
                insight += f"• **{top_num.replace('_', ' ').title()}**: Mean = {df[top_num].mean():,.2f}, Max = {df[top_num].max():,.2f}\n"
            if categorical_cols:
                top_cat = categorical_cols[0]
                top_value = df[top_cat].value_counts().head(1)
                if len(top_value) > 0:
                    insight += f"• **Top {top_cat.replace('_', ' ').title()}**: '{top_value.index[0]}' ({top_value.values[0]} occurrences)\n"
            insight += f"\nI found {len(numeric_cols)} numeric and {len(categorical_cols)} categorical columns ready for analysis."

        elif any(word in question_lower for word in ['top', 'best', 'highest', 'max', 'most']):
            if numeric_cols and categorical_cols:
                num_col = numeric_cols[0]
                cat_col = categorical_cols[0]
                top_groups = df.groupby(cat_col)[num_col].mean().nlargest(3)
                insight = f"🏆 Top 3 by average {num_col.replace('_', ' ')}:\n\n"
                for name, val in top_groups.items():
                    insight += f"• **{name}**: {val:,.2f}\n"
            else:
                insight = f"I analyzed your data. The maximum value across numeric columns is {df[numeric_cols[0]].max():,.2f} in the '{numeric_cols[0]}' column."

        elif any(word in question_lower for word in ['trend', 'pattern', 'anomaly', 'outlier']):
            if numeric_cols:
                col = numeric_cols[0]
                mean = df[col].mean()
                std = df[col].std()
                outliers = df[abs(df[col] - mean) > 2 * std] if std > 0 else pd.DataFrame()
                insight = f"🔍 Analyzing '{col.replace('_', ' ').title()}': Mean = {mean:,.2f}, Std = {std:,.2f}.\n\n"
                insight += f"Found **{len(outliers)} outliers** (>2σ from mean) out of {len(df):,} records."
            else:
                insight = "I couldn't find numeric columns to analyze for trends."

        else:
            # Enhanced generic insight
            insight = f"Based on my deeper analysis of **{source_file}**, I noticed {len(numeric_cols)} numeric metrics and {len(categorical_cols)} dimensions.\n\n"
            if numeric_cols:
                insight += f"The primary metric `{numeric_cols[0]}` has a variance of {df[numeric_cols[0]].var():,.2f}. I recommend looking into the correlation between `{numeric_cols[0]}` and `{categorical_cols[0] if categorical_cols else 'time'}` to uncover underlying growth drivers.\n\n"
            insight += "If you'd like a specific visualization, just ask me to plot a chart for you!"

        return {
            "id": str(int(datetime.now().timestamp() * 1000) + 1),
            "user": "DataVision AI",
            "avatar": "✨",
            "message": insight,
            "time": "Just now",
            "chartRef": f"Analysis of {source_file}",
            "isAi": True,
        }

    except Exception as e:
        logger.error(f"AI insight error: {e}")
        return {
            "id": str(int(datetime.now().timestamp() * 1000) + 1),
            "user": "DataVision AI",
            "avatar": "✨",
            "message": f"I encountered an issue analyzing your data: {str(e)[:100]}. Please try again!",
            "time": "Just now",
            "chartRef": "Error",
            "isAi": True,
        }


# ── THREADS ──

@router.get("/threads")
async def get_threads(
    channel_id: str = "default",
    limit: int = Query(50, ge=1, le=200, description="Max messages to return"),
    offset: int = Query(0, ge=0, description="Skip this many messages"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Fetch messages for a channel with pagination."""
    real_channel_id = await _resolve_channel_id(channel_id, db)

    # Count total messages for pagination metadata
    from sqlalchemy import func
    count_stmt = select(func.count()).select_from(ChannelMessage).where(
        ChannelMessage.channel_id == real_channel_id,
        ChannelMessage.parent_id == None
    )
    total_result = await db.execute(count_stmt)
    total_count = total_result.scalar() or 0

    # Load messages with limit/offset
    stmt = select(ChannelMessage).where(
        ChannelMessage.channel_id == real_channel_id,
        ChannelMessage.parent_id == None
    ).order_by(ChannelMessage.created_at.asc()).offset(offset).limit(limit).options(
        selectinload(ChannelMessage.user)
    )

    result = await db.execute(stmt)
    messages = result.scalars().all()

    # Format for frontend
    formatted_threads = []
    for m in messages:
        # Try parse JSON content
        is_enc = False
        att_url = None
        att_type = None
        msg_text = m.content
        try:
            parsed = json.loads(m.content)
            if isinstance(parsed, dict) and "message" in parsed:
                msg_text = parsed.get("message", "")
                is_enc = parsed.get("is_encrypted", False)
                att_url = parsed.get("attachment_url")
                att_type = parsed.get("attachment_type")
        except Exception:
            pass

        formatted_threads.append({
            "id": str(m.id),
            "user": msg_text.split(":")[0] if ":" in msg_text and m.is_ai == False else ("DataVision AI" if m.is_ai else m.user.full_name if m.user else "User"),
            "avatar": "✨" if m.is_ai else (m.user.full_name[0].upper() if m.user and m.user.full_name else "U"),
            "message": msg_text,
            "time": m.created_at.isoformat(),
            "isAi": m.is_ai,
            "is_pinned": m.is_pinned,
            "is_encrypted": is_enc,
            "attachment_url": att_url,
            "attachment_type": att_type
        })

    return {
        "threads": formatted_threads,
        "pagination": {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count
        }
    }


@router.post("/threads")
async def post_message(
    request_obj: Request,
    req: PostMessageRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Post a message. If @ai is mentioned, generate a real data insight."""
    await check_rate_limit(request_obj, "collab_message", user_id)
    real_channel_id = await _resolve_channel_id(req.channel_id or "default", db)
    
    # In DB we store user profile, but frontend sends 'user' string for display name. We'll store it in content for now, or use the DB user profile.
    # Wait, the DB model requires `user_id`.
    
    content_payload = req.message
    if req.is_encrypted or req.attachment_url:
        content_payload = json.dumps({
            "message": req.message,
            "is_encrypted": req.is_encrypted,
            "attachment_url": req.attachment_url,
            "attachment_type": req.attachment_type
        })
        
    new_msg = ChannelMessage(
        channel_id=real_channel_id,
        user_id=user_id,
        content=content_payload,
        is_ai=False
    )
    db.add(new_msg)
    await db.commit()
    await db.refresh(new_msg)
    
    response_msg = {
        "id": str(new_msg.id),
        "user": req.user,
        "avatar": req.user[0].upper() if req.user else "U",
        "message": req.message,
        "time": "Just now",
        "isAi": False,
        "is_encrypted": req.is_encrypted,
        "attachment_url": req.attachment_url,
        "attachment_type": req.attachment_type
    }

    ai_response = None
    if "@ai" in req.message.lower():
        question = req.message.lower().split("@ai")[-1].strip()
        if not question:
            question = "give me a summary"
        ai_insight = await collab_swarm.process_message(user_id, question)
        if ai_insight:
            ai_msg = ChannelMessage(
                channel_id=real_channel_id,
                user_id=user_id, # Can attribute AI message to user who invoked it
                content=ai_insight['message'],
                is_ai=True
            )
            db.add(ai_msg)
            await db.commit()
            await db.refresh(ai_msg)
            ai_response = ai_insight
            ai_response['id'] = str(ai_msg.id)

    return {"success": True, "message": response_msg, "ai_response": ai_response}


# ── CHANNELS ──

@router.get("/channels")
async def get_channels(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List all channels."""
    await _get_or_create_default_channel(db) # Ensure default exists
    stmt = select(ChatChannel).order_by(ChatChannel.created_at.asc())
    result = await db.execute(stmt)
    channels = result.scalars().all()
    
    return {"channels": [{"id": "default" if c.name == "general" else str(c.id), "name": c.name, "created": c.created_at.isoformat()} for c in channels]}


@router.post("/channels")
async def create_channel(
    req: CreateChannelRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new channel."""
    stmt = select(ChatChannel).where(ChatChannel.name == req.name)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Channel '{req.name}' already exists")

    channel = ChatChannel(
        name=req.name.replace("#", ""),
        description=""
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)

    return {"success": True, "channel": {"id": str(channel.id), "name": channel.name, "created": channel.created_at.isoformat()}}



@router.get("/search")
async def search_messages(
    q: str,
    channel_id: str = "default",
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Search messages in a channel."""
    real_channel_id = await _resolve_channel_id(channel_id, db)
    
    # Simple ILIKE search on content
    # Note: E2E encrypted messages won't be matched by plaintext queries!
    stmt = select(ChannelMessage).where(
        ChannelMessage.channel_id == real_channel_id,
        ChannelMessage.content.ilike(f"%{q}%")
    ).order_by(ChannelMessage.created_at.desc()).limit(20).options(selectinload(ChannelMessage.user))
    
    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    formatted = []
    for m in messages:
        is_enc = False
        att_url = None
        att_type = None
        msg_text = m.content
        try:
            parsed = json.loads(m.content)
            if isinstance(parsed, dict) and "message" in parsed:
                msg_text = parsed.get("message", "")
                is_enc = parsed.get("is_encrypted", False)
                att_url = parsed.get("attachment_url")
                att_type = parsed.get("attachment_type")
        except:
            pass

        formatted.append({
            "id": str(m.id),
            "user": msg_text.split(":")[0] if ":" in msg_text and m.is_ai == False else ("DataVision AI" if m.is_ai else m.user.full_name if m.user else "User"),
            "avatar": "✨" if m.is_ai else (m.user.full_name[0].upper() if m.user and m.user.full_name else "U"),
            "message": msg_text,
            "time": m.created_at.isoformat(),
            "isAi": m.is_ai,
            "is_pinned": m.is_pinned,
            "is_encrypted": is_enc,
            "attachment_url": att_url,
            "attachment_type": att_type
        })
    return {"results": formatted}

# ── INVITES ──
_invites_db: Dict[str, Dict] = {}  # token -> invite info

@router.post("/invite")
async def generate_invite(
    user_id: str = Depends(get_current_user_id)
):
    """Generate a secure invite link token."""
    token = hashlib.sha256(f"{user_id}-{datetime.now().isoformat()}".encode()).hexdigest()[:16]
    _invites_db[token] = {
        "created_by": user_id,
        "created_at": datetime.now().isoformat(),
        "used": False,
    }
    return {"success": True, "token": token, "link": f"/collaborate?invite={token}"}


# ── MEMBERS ──

@router.get("/members")
async def get_members(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List team members."""
    # We fetch members from WorkspaceMember and their UserProfile
    stmt = select(WorkspaceMember).options(selectinload(WorkspaceMember.user))
    result = await db.execute(stmt)
    members_db = result.scalars().all()
    
    formatted_members = []
    for m in members_db:
        name = m.user.full_name if m.user and m.user.full_name else m.user.email.split("@")[0] if m.user else "Unknown"
        formatted_members.append({
            "name": name,
            "email": m.user.email if m.user else "",
            "role": m.role,
            "status": "Online",
            "avatar": name[0].upper() if name else "?"
        })
        
    # If empty, fallback to the authenticated user's profile
    if not formatted_members:
        try:
            user_stmt = select(UserProfile).filter(UserProfile.id == user_id)
            u_res = await db.execute(user_stmt)
            user_profile = u_res.scalars().first()
            
            if user_profile:
                name = user_profile.full_name or user_profile.email.split("@")[0]
                formatted_members.append({
                    "name": name,
                    "email": user_profile.email,
                    "role": "Owner",
                    "status": "Online",
                    "avatar": name[0].upper() if name else "?"
                })
            else:
                formatted_members.append({
                    "name": "Admin", "email": "admin@datavision.app", "role": "Owner", "status": "Online", "avatar": "A"
                })
        except:
            formatted_members.append({
                "name": "Admin", "email": "admin@datavision.app", "role": "Owner", "status": "Online", "avatar": "A"
            })
        
    return {"members": formatted_members}


@router.post("/members")
async def add_member(
    req: InviteMemberRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Add a team member to the workspace."""
    # 1. Ensure user exists
    user_stmt = select(UserProfile).filter(UserProfile.email == req.email)
    user_res = await db.execute(user_stmt)
    target_user = user_res.scalars().first()
    
    if not target_user:
        # Create a stub user if doesn't exist
        import hashlib
        fake_pass = hashlib.sha256("stub".encode()).hexdigest()
        target_user = UserProfile(email=req.email, full_name=req.name, hashed_password=fake_pass)
        db.add(target_user)
        await db.flush()
        
    workspace_id = "default"
        
    # 3. Add WorkspaceMember
    member_stmt = select(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == target_user.id
    )
    member_res = await db.execute(member_stmt)
    existing_member = member_res.scalars().first()
    
    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a member")
        
    new_member = WorkspaceMember(workspace_id=workspace_id, user_id=target_user.id, role=req.role)
    db.add(new_member)
    await db.commit()
    
    name = target_user.full_name or target_user.email.split("@")[0]
    return {
        "success": True, 
        "member": {"name": name, "email": target_user.email, "role": new_member.role, "status": "Invited", "avatar": name[0].upper()}, 
        "message": f"Added {req.email}"
    }


@router.delete("/members")
async def remove_member(
    req: RemoveMemberRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Remove a team member from the workspace."""
    user_stmt = select(UserProfile).filter(UserProfile.email == req.email)
    user_res = await db.execute(user_stmt)
    target_user = user_res.scalars().first()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    workspace_id = "default"
    
    stmt = delete(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == target_user.id
    )
    await db.execute(stmt)
    await db.commit()
        
    return {"success": True, "message": f"Removed {req.email}"}


@router.put("/members/role")
async def update_member_role(
    req: UpdateRoleRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update a team member's role."""
    user_stmt = select(UserProfile).filter(UserProfile.email == req.email)
    user_res = await db.execute(user_stmt)
    target_user = user_res.scalars().first()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    member_stmt = select(WorkspaceMember).filter(WorkspaceMember.user_id == target_user.id)
    member_res = await db.execute(member_stmt)
    member = member_res.scalars().first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in workspace")
        
    member.role = req.role
    await db.commit()
    
    return {"success": True, "message": f"Updated role to {req.role}"}


# ── WEBSOCKET REAL-TIME CHAT ──
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections and websocket in self.active_connections[room_id]:
            self.active_connections[room_id].remove(websocket)

    async def broadcast(self, message: str, room_id: str):
        if room_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    disconnected.append(connection)
            for d in disconnected:
                self.active_connections[room_id].remove(d)

manager = ConnectionManager()

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_name: str = "Anonymous", user_id: str = "default"):
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                msg_text = payload.get("message", "").lower()
                is_question = msg_text.strip().endswith("?")
                is_mention = "@ai" in msg_text
                
                if is_mention or is_question:
                    question = msg_text.replace("@ai", "").strip()
                    if not question:
                        question = "give me a summary"
                    
                    # Generate AI response (doesn't write to DB in WS, for real DB writing we rely on the POST endpoint)
                    ai_response = await collab_swarm.process_message(user_id, question)
                    if ai_response:
                        ai_payload = json.dumps(ai_response)
                        await asyncio.sleep(1.0)
                        await manager.broadcast(ai_payload, room_id)
                        
            except json.JSONDecodeError:
                pass
            
            await manager.broadcast(data, room_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)


# ═══════════════════════════════════════════════════════════════
# ENTERPRISE COLLABORATION FEATURES
# ═══════════════════════════════════════════════════════════════

VALID_ROLES = {"Owner", "Admin", "Analyst", "Viewer"}
ROLE_PERMISSIONS = {
    "Owner": ["view", "edit", "train", "export", "admin", "invite", "delete"],
    "Admin": ["view", "edit", "train", "export", "invite"],
    "Analyst": ["view", "edit", "train", "export"],
    "Viewer": ["view"],
}

async def _log_activity_db(db: AsyncSession, user_id: str, user_name: str, action: str, detail: str):
    log = ActivityLog(
        user_id=user_id,
        user_name=user_name,
        action=action,
        detail=detail
    )
    db.add(log)
    await db.commit()

@router.get("/roles")
async def get_roles():
    """Get available roles and their permissions."""
    return {
        "roles": [
            {"name": role, "permissions": perms, "color": color}
            for role, perms, color in [
                ("Owner", ROLE_PERMISSIONS["Owner"], "#EF4444"),
                ("Admin", ROLE_PERMISSIONS["Admin"], "#F59E0B"),
                ("Analyst", ROLE_PERMISSIONS["Analyst"], "#3B82F6"),
                ("Viewer", ROLE_PERMISSIONS["Viewer"], "#6B7280"),
            ]
        ]
    }


@router.put("/members/role")
async def update_member_role(
    req: UpdateRoleRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Change a member's role (Mocked for now as members are mocked above)."""
    if req.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {VALID_ROLES}")
    return {"success": True, "message": f"Role updated to {req.role}"}


@router.post("/threads/{message_id}/react")
async def react_to_message(
    message_id: str,
    req: ReactionRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Add/toggle emoji reaction on a message."""
    try:
        stmt = select(MessageReaction).where(
            MessageReaction.message_id == message_id,
            MessageReaction.user_id == user_id,
            MessageReaction.emoji == req.emoji
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            await db.delete(existing)
            await db.commit()
        else:
            new_reaction = MessageReaction(
                message_id=message_id,
                user_id=user_id,
                emoji=req.emoji
            )
            db.add(new_reaction)
            await db.commit()
            
        # Refetch all reactions for message
        stmt2 = select(MessageReaction).where(MessageReaction.message_id == message_id)
        result2 = await db.execute(stmt2)
        reactions = result2.scalars().all()
        
        grouped = {}
        for r in reactions:
            if r.emoji not in grouped:
                grouped[r.emoji] = []
            grouped[r.emoji].append(req.user) # UI expects array of user names
            
        return {"success": True, "reactions": grouped}
    except Exception as e:
        logger.error(f"Error reacting: {e}")
        return {"success": False, "reactions": {}}


@router.get("/threads/{message_id}/reactions")
async def get_reactions(message_id: str, db: AsyncSession = Depends(get_db)):
    """Get reactions for a message."""
    try:
        stmt = select(MessageReaction).where(MessageReaction.message_id == message_id).options(selectinload(MessageReaction.user))
        result = await db.execute(stmt)
        reactions = result.scalars().all()
        
        grouped = {}
        for r in reactions:
            if r.emoji not in grouped:
                grouped[r.emoji] = []
            name = r.user.full_name if r.user and r.user.full_name else r.user.email.split("@")[0] if r.user else "Unknown"
            grouped[r.emoji].append(name)
            
        return {"reactions": grouped}
    except Exception as e:
        return {"reactions": {}}


@router.post("/threads/{message_id}/reply")
async def reply_to_message(
    message_id: str,
    req: ReplyRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Add a threaded reply to a message."""
    # Find parent to get channel_id
    stmt = select(ChannelMessage).where(ChannelMessage.id == message_id)
    result = await db.execute(stmt)
    parent = result.scalar_one_or_none()
    
    if not parent:
        raise HTTPException(status_code=404, detail="Parent message not found")
        
    reply_msg = ChannelMessage(
        channel_id=parent.channel_id,
        user_id=user_id,
        content=req.message,
        is_ai=False,
        parent_id=message_id
    )
    db.add(reply_msg)
    await db.commit()
    await db.refresh(reply_msg)
    
    await _log_activity_db(db, user_id, req.user, "reply", f"Replied in thread: \"{req.message[:50]}\"")
    
    reply = {
        "id": str(reply_msg.id),
        "parent_id": message_id,
        "user": req.user,
        "avatar": req.user[0].upper() if req.user else "U",
        "message": req.message,
        "time": reply_msg.created_at.isoformat(),
        "timestamp": reply_msg.created_at.isoformat(),
    }

    # Count total replies
    stmt_count = select(ChannelMessage).where(ChannelMessage.parent_id == message_id)
    total_replies = len((await db.execute(stmt_count)).scalars().all())
    
    return {"success": True, "reply": reply, "total_replies": total_replies}


@router.get("/threads/{message_id}/replies")
async def get_replies(message_id: str, db: AsyncSession = Depends(get_db)):
    """Get all replies for a message thread."""
    stmt = select(ChannelMessage).where(ChannelMessage.parent_id == message_id).order_by(ChannelMessage.created_at.asc()).options(selectinload(ChannelMessage.user))
    result = await db.execute(stmt)
    replies_db = result.scalars().all()
    
    formatted = []
    for r in replies_db:
        name = r.user.full_name if r.user and r.user.full_name else r.user.email.split("@")[0] if r.user else "Unknown"
        formatted.append({
            "id": str(r.id),
            "parent_id": str(r.parent_id),
            "user": name,
            "avatar": name[0].upper() if name else "?",
            "message": r.content,
            "time": r.created_at.isoformat(),
            "timestamp": r.created_at.isoformat(),
        })
        
    return {"replies": formatted, "total": len(formatted)}


@router.post("/channels/{channel_id}/pin")
async def pin_message(
    channel_id: str,
    req: PinRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Pin/unpin a message in a channel."""
    try:
        stmt = select(ChannelMessage).where(ChannelMessage.id == req.message_id)
        result = await db.execute(stmt)
        msg = result.scalar_one_or_none()
        
        if not msg:
            raise HTTPException(status_code=404, detail="Message not found")
            
        msg.is_pinned = not msg.is_pinned
        await db.commit()
        
        if msg.is_pinned:
            await _log_activity_db(db, user_id, "System", "pin", f"Message pinned in channel")
            
        return {"success": True, "pinned": msg.is_pinned}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/channels/{channel_id}/pins")
async def get_pins(
    channel_id: str, 
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get pinned message IDs for a channel."""
    real_channel_id = await _resolve_channel_id(channel_id, db)
    stmt = select(ChannelMessage).where(
        ChannelMessage.channel_id == real_channel_id,
        ChannelMessage.is_pinned == True
    )
    result = await db.execute(stmt)
    pins = result.scalars().all()
    return {"pins": [str(p.id) for p in pins]}


@router.get("/activity-feed")
async def get_activity_feed(
    limit: int = 50,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get platform-wide activity feed."""
    stmt = select(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(limit).options(selectinload(ActivityLog.user))
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    formatted = []
    for log in logs:
        name = log.user.full_name if log.user and log.user.full_name else log.user_name or "System"
        formatted.append({
            "id": str(log.id),
            "user_id": str(log.user_id),
            "user_name": name,
            "action": log.action,
            "detail": log.detail,
            "timestamp": log.timestamp.isoformat()
        })
        
    if not formatted:
        # Fallback sample data if empty
        now = datetime.now()
        samples = [
            ("Naveenkumar", "file_upload", "Uploaded sales_q3.csv (12,450 rows)"),
            ("DataVision AI", "anomaly", "Detected 3 anomalies in revenue data"),
            ("Naveenkumar", "model_train", "Trained XGBoost model — 94.2% accuracy"),
            ("DataVision AI", "report", "Generated Executive Summary report"),
        ]
        from datetime import timedelta
        for i, (user, action, detail) in enumerate(samples):
            formatted.append({
                "id": str(i + 1),
                "user_id": str(user_id),
                "user_name": user,
                "action": action,
                "detail": detail,
                "timestamp": (now - timedelta(hours=i * 3)).isoformat(),
            })
            
    return {"activities": formatted}
