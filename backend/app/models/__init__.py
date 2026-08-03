"""
DataVision — Complete Platform Model Registry
Imports all domain models covering 100% of the platform sidebar sections.
"""

from app.models.base import Base

from app.models.user import User, UserPreferences
from app.models.auth import UserSession, RefreshToken, PasswordResetToken
from app.models.rbac import Role, Permission, RolePermission, UserRole
from app.models.data_hub import DataConnection, DataIngestionJob, LineageNode, LineageEdge
from app.models.ml import Project, Dataset, Experiment, MLModel, TrainingJob
from app.models.platform import AuditLog, APIKey, SystemSetting, FileUpload
from app.models.chat import Conversation, Message, UserMemory, AIInsight
from app.models.dashboard import Dashboard, Chart, ComputerVisionTask, Notification
from app.models.vector_rag import VectorStore, DocumentChunk, RAGQueryLog
from app.models.simulator import Simulation, SimulationVersion
from app.models.reports import Report, ScheduledReport
from app.models.collaboration import Workspace, WorkspaceMember, SharedLink
from app.models.developer import WebhookEndpoint, WebhookDelivery, APICallLog

__all__ = [
    "Base",
    # Auth & Users & RBAC
    "User",
    "UserPreferences",
    "UserSession",
    "RefreshToken",
    "PasswordResetToken",
    "Role",
    "Permission",
    "RolePermission",
    "UserRole",
    # Data Foundation (Data Hub & Data Lineage)
    "DataConnection",
    "DataIngestionJob",
    "LineageNode",
    "LineageEdge",
    # Intelligence & Analytics (Dashboards & Visuals)
    "Dashboard",
    "Chart",
    "AIInsight",
    "Notification",
    # Advanced AI Lab (AI Analyst, AutoML, CV, RAG, Simulator)
    "Conversation",
    "Message",
    "UserMemory",
    "Project",
    "Dataset",
    "Experiment",
    "MLModel",
    "TrainingJob",
    "ComputerVisionTask",
    "VectorStore",
    "DocumentChunk",
    "RAGQueryLog",
    "Simulation",
    "SimulationVersion",
    # Output & Tools (Reports, Collaborate, Developer, Settings)
    "Report",
    "ScheduledReport",
    "Workspace",
    "WorkspaceMember",
    "SharedLink",
    "WebhookEndpoint",
    "WebhookDelivery",
    "APICallLog",
    "AuditLog",
    "APIKey",
    "SystemSetting",
    "FileUpload",
]
