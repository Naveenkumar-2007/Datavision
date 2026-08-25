"""
Legacy ORM Compatibility Layer — Maps legacy database.orm imports to app.models.

This ensures 100% backward compatibility for v1 legacy endpoints while maintaining
a single unified 43-table production PostgreSQL schema.
"""

from app.models.base import Base
from app.models.user import User as UserProfile, UserPreferences
from app.models.auth import UserSession, RefreshToken, PasswordResetToken
from app.models.rbac import Role, Permission, RolePermission, UserRole
from app.models.data_hub import DataConnection, DataIngestionJob, LineageNode, LineageEdge
from app.models.ml import Project, Dataset, Experiment, Experiment as MLExperiment, MLModel as DeployedModel, TrainingJob
from app.models.platform import AuditLog, AuditLog as ActivityLog, APIKey as DeveloperAPIKey, SystemSetting, FileUpload as UserFile
from app.models.chat import Conversation, Message, UserMemory, AIInsight
from app.models.dashboard import Dashboard, Chart, ComputerVisionTask, Notification as NotificationSettings
from app.models.vector_rag import VectorStore, DocumentChunk, RAGQueryLog
from app.models.simulator import Simulation, SimulationVersion
from app.models.reports import Report, ScheduledReport
from app.models.collaboration import Workspace, WorkspaceMember, SharedLink, ChatChannel, ChannelMessage, MessageReaction
from app.models.developer import WebhookEndpoint, WebhookDelivery, APICallLog

# Legacy Aliases
User = UserProfile
AdminUser = UserRole
UserQuery = Message
SavedScenario = Simulation
DataStory = Report
VisualPipeline = LineageNode
AgentLog = AuditLog
PushToken = NotificationSettings
Notification = NotificationSettings
MLDeployment = DeployedModel
MLOpsDeployment = DeployedModel
MLOpsExperiment = MLExperiment
MLOpsPredictionLog = APICallLog
Webhook = WebhookEndpoint
BatchPredictionJob = TrainingJob
ABTestConfig = Experiment
MLRegistryModel = DeployedModel
MLRegistryVersion = TrainingJob
ReportHistory = Report
ReportTemplate = Report

__all__ = [
    "Base",
    "UserProfile",
    "User",
    "AdminUser",
    "UserPreferences",
    "Conversation",
    "Message",
    "UserFile",
    "UserQuery",
    "UserMemory",
    "NotificationSettings",
    "Notification",
    "PushToken",
    "AIInsight",
    "AgentLog",
    "DataConnection",
    "Dashboard",
    "Chart",
    "DataStory",
    "MLDeployment",
    "MLOpsDeployment",
    "MLOpsExperiment",
    "MLOpsPredictionLog",
    "Webhook",
    "VisualPipeline",
    "Simulation",
    "SavedScenario",
    "Report",
    "ScheduledReport",
    "ReportHistory",
    "ReportTemplate",
    "Workspace",
    "WorkspaceMember",
    "SharedLink",
    "ChatChannel",
    "ChannelMessage",
    "MessageReaction",
    "ActivityLog",
    "DeveloperAPIKey",
    "WebhookEndpoint",
    "WebhookDelivery",
    "APICallLog",
    "MLExperiment",
    "DeployedModel",
    "BatchPredictionJob",
    "ABTestConfig",
    "MLRegistryModel",
    "MLRegistryVersion",
]

