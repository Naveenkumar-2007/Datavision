import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Float, Text, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from database.db import Base

class UserProfile(Base):
    __tablename__ = 'profiles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    avatar_url = Column(String)
    company_name = Column(String)
    role = Column(String, default='user')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    files = relationship("UserFile", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("UserMemory", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")

class AdminUser(Base):
    __tablename__ = 'admin_users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), unique=True)
    admin_role = Column(String, default='moderator', nullable=False)
    permissions = Column(JSONB, default={"can_view_users": True, "can_edit_users": False, "can_delete_users": False, "can_view_analytics": True})
    granted_by = Column(UUID(as_uuid=True), ForeignKey('profiles.id'))
    granted_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String)
    mode = Column(String, default='auto')
    is_archived = Column(Boolean, default=False)
    message_count = Column(Integer, default=0)
    last_message_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserProfile", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    mode = Column(String)
    sources = Column(JSONB)
    metadata_ = Column('metadata', JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    conversation = relationship("Conversation", back_populates="messages")

class UserFile(Base):
    __tablename__ = 'user_files'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    filename = Column(String, nullable=False, index=True)
    original_filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String)
    storage_path = Column(String, nullable=False)
    bucket_name = Column(String, default='user-files')
    is_processed = Column(Boolean, default=False)
    is_indexed = Column(Boolean, default=False)
    processing_status = Column(String, default='pending')
    processing_error = Column(Text)
    metadata_ = Column('metadata', JSONB, default={})
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime)

    user = relationship("UserProfile", back_populates="files")


class UserQuery(Base):
    __tablename__ = 'user_queries'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id', ondelete='SET NULL'))
    query_text = Column(Text, nullable=False)
    query_type = Column(String)
    response_time_ms = Column(Integer)
    tokens_used = Column(Integer)
    cache_hit = Column(Boolean, default=False)
    sources_used = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class UserMemory(Base):
    __tablename__ = 'user_memory'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    memory_layer = Column(String, nullable=False, index=True)
    memory_type = Column(String, nullable=False, index=True)
    content = Column(JSONB, nullable=False)
    embedding = Column(JSONB) # Fallback if pgvector not used
    metadata_ = Column('metadata', JSONB, default={})
    confidence = Column(Float)
    expires_at = Column(DateTime, index=True)
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserProfile", back_populates="memories")

class UserPreferences(Base):
    __tablename__ = 'user_preferences'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), unique=True, nullable=False)
    theme = Column(String, default='dark')
    currency_code = Column(String, default='INR')
    currency_symbol = Column(String, default='₹')
    language = Column(String, default='en')
    notifications_enabled = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=True)
    auto_save_conversations = Column(Boolean, default=True)
    default_chat_mode = Column(String, default='auto')
    custom_settings = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserProfile", back_populates="preferences")


class NotificationSettings(Base):
    __tablename__ = 'notification_settings'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(String, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=False)
    weekly_reports = Column(Boolean, default=True)
    ai_insights = Column(Boolean, default=True)
    severity_threshold = Column(String, default='medium')
    dnd_start = Column(String)
    dnd_end = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class AIInsight(Base):
    __tablename__ = 'ai_insights'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    insight_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class AgentLog(Base):
    __tablename__ = 'agent_logs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(String, nullable=False, index=True)
    agent_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    message = Column(Text)
    executed_at = Column(DateTime, default=datetime.utcnow)

class DataConnection(Base):
    __tablename__ = 'data_connections'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    source_type = Column(String, nullable=False)  # postgres, snowflake, kafka
    host = Column(String, nullable=False)
    database_name = Column(String, nullable=False)
    target_table = Column(String, nullable=False)
    credentials = Column(Text, nullable=False)  # In production, this should be encrypted
    created_at = Column(DateTime, default=datetime.utcnow)

class Dashboard(Base):
    __tablename__ = 'dashboards'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String, nullable=False, default='Untitled Dashboard')
    layout = Column(JSONB, default=[])
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    charts = relationship("Chart", back_populates="dashboard", cascade="all, delete-orphan")

class Chart(Base):
    __tablename__ = 'charts'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id = Column(UUID(as_uuid=True), ForeignKey('dashboards.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String, nullable=False)
    chart_type = Column(String, nullable=False)
    data = Column(JSONB, nullable=False)
    config = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    dashboard = relationship("Dashboard", back_populates="charts")

class DataStory(Base):
    __tablename__ = 'data_stories'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    dataset_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class MLDeployment(Base):
    __tablename__ = 'ml_deployments'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deploy_id = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    model_name = Column(String, nullable=False)
    task_type = Column(String, nullable=False)
    version = Column(Integer)
    api_key = Column(String, nullable=False)
    status = Column(String, default='active')
    request_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_called_at = Column(DateTime)

class VisualPipeline(Base):
    __tablename__ = 'visual_pipelines'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String, nullable=False, default='Untitled Pipeline')
    description = Column(Text)
    nodes = Column(JSONB, default=[])
    edges = Column(JSONB, default=[])
    is_active = Column(Boolean, default=False)
    last_run_status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeveloperAPIKey(Base):
    __tablename__ = 'developer_api_keys'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    api_key = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, default="Default Key")
    status = Column(String, default='active')
    scopes = Column(JSONB, default=["read:data", "predict"])
    expires_at = Column(DateTime, nullable=True)
    total_calls = Column(Integer, default=0)
    data_processed_mb = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime)


class WebhookEndpoint(Base):
    __tablename__ = 'webhook_endpoints'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    url = Column(String, nullable=False)
    events = Column(JSONB, default=["autopilot.completed", "training.complete"])
    secret = Column(String, nullable=True)
    status = Column(String, default='active')
    created_at = Column(DateTime, default=datetime.utcnow)

    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")


class WebhookDelivery(Base):
    __tablename__ = 'webhook_deliveries'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    webhook_id = Column(UUID(as_uuid=True), ForeignKey('webhook_endpoints.id', ondelete='CASCADE'), nullable=False, index=True)
    event = Column(String, nullable=False)
    payload = Column(JSONB, default={})
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    success = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    webhook = relationship("WebhookEndpoint", back_populates="deliveries")


class APICallLog(Base):
    __tablename__ = 'api_call_logs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=True, index=True)
    api_key_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False, default='GET')
    status_code = Column(Integer, nullable=False)
    latency_ms = Column(Integer, nullable=False, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class ChatChannel(Base):
    __tablename__ = 'chat_channels'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChannelMessage(Base):
    __tablename__ = 'channel_messages'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel_id = Column(UUID(as_uuid=True), ForeignKey('chat_channels.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    content = Column(Text, nullable=False)
    is_ai = Column(Boolean, default=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('channel_messages.id', ondelete='CASCADE'), nullable=True, index=True)
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    parent = relationship("ChannelMessage", remote_side=[id], back_populates="replies")
    replies = relationship("ChannelMessage", back_populates="parent", cascade="all, delete-orphan")
    reactions = relationship("MessageReaction", back_populates="message", cascade="all, delete-orphan")
    user = relationship("UserProfile")

class MessageReaction(Base):
    __tablename__ = 'message_reactions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey('channel_messages.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    emoji = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    message = relationship("ChannelMessage", back_populates="reactions")
    user = relationship("UserProfile")
    
class ActivityLog(Base):
    __tablename__ = 'activity_logs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    user_name = Column(String, nullable=False)
    action = Column(String, nullable=False)
    detail = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("UserProfile")

class ScheduledReport(Base):
    __tablename__ = 'scheduled_reports'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String, nullable=False)
    report_type = Column(String, nullable=False)
    schedule_cron = Column(String, nullable=False) # e.g. "0 9 * * 1" for Monday 9am
    recipients = Column(JSONB, default=[]) # list of emails
    format = Column(String, default='pdf')
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class MLExperiment(Base):
    __tablename__ = 'ml_experiments'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String, nullable=False)
    model_type = Column(String)
    algorithm = Column(String)
    metrics = Column(JSONB, default={})
    parameters = Column(JSONB, default={})
    features = Column(JSONB, default=[])
    target_column = Column(String)
    tags = Column(JSONB, default=[])
    is_starred = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DeployedModel(Base):
    __tablename__ = 'deployed_models'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey('ml_experiments.id', ondelete='SET NULL'), nullable=True)
    name = Column(String, nullable=False)
    endpoint = Column(String)
    status = Column(String, default='active')
    traffic_split = Column(Integer, default=100) # For A/B testing
    created_at = Column(DateTime, default=datetime.utcnow)


class ReportHistory(Base):
    __tablename__ = 'report_history'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    scheduled_report_id = Column(UUID(as_uuid=True), ForeignKey('scheduled_reports.id', ondelete='SET NULL'), nullable=True)
    report_type = Column(String, nullable=False)
    title = Column(String, default='Generated Report')
    status = Column(String, default='completed')  # completed, failed, running
    sections_count = Column(Integer, default=0)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    error = Column(Text, nullable=True)


class ReportTemplate(Base):
    __tablename__ = 'report_templates'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String, nullable=False)
    report_type = Column(String, nullable=False)
    config = Column(JSONB, default={})
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ABTestConfig(Base):
    __tablename__ = 'ab_test_configs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    champion_experiment_id = Column(UUID(as_uuid=True), ForeignKey('ml_experiments.id', ondelete='SET NULL'), nullable=True)
    challenger_experiment_id = Column(UUID(as_uuid=True), ForeignKey('ml_experiments.id', ondelete='SET NULL'), nullable=True)
    champion_traffic = Column(Integer, default=80)
    challenger_traffic = Column(Integer, default=20)
    status = Column(String, default='active')  # active, completed, cancelled
    winner = Column(String, nullable=True)  # 'champion' or 'challenger'
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)


class BatchPredictionJob(Base):
    __tablename__ = 'batch_prediction_jobs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    model_name = Column(String, nullable=False)
    input_filename = Column(String, nullable=False)
    output_filename = Column(String, nullable=True)
    status = Column(String, default='running')  # running, completed, failed
    total_rows = Column(Integer, default=0)
    completed_rows = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class WorkspaceMember(Base):
    """Workspace membership - replaces Supabase workspace_members table"""
    __tablename__ = 'workspace_members'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(String, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(String, default='member')  # owner, admin, member, viewer
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserProfile")


class Notification(Base):
    """Notification history - replaces Supabase notifications_history table"""
    __tablename__ = 'notifications'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    type = Column(String, nullable=False)  # email, push, in_app
    title = Column(String, nullable=False)
    message = Column(Text, nullable=True)
    channel = Column(String, nullable=True)  # anomaly, report, system
    status = Column(String, default='sent')  # sent, failed, read
    metadata_ = Column('metadata', JSONB, default={})
    sent_at = Column(DateTime, default=datetime.utcnow)


class PushToken(Base):
    """Push notification tokens - replaces Supabase push_tokens table"""
    __tablename__ = 'push_tokens'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    token = Column(String, nullable=False)
    platform = Column(String, default='web')  # web, ios, android
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Webhook(Base):
    """Developer webhooks — persisted to PostgreSQL"""
    __tablename__ = 'webhooks'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    url = Column(String, nullable=False)
    status = Column(String, default='active')  # active / paused
    events = Column(JSONB, default=["autopilot.completed"])
    secret = Column(String, nullable=True)  # HMAC signing secret
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered_at = Column(DateTime, nullable=True)
    failure_count = Column(Integer, default=0)

# =============================================================================
# ENTERPRISE MLOPS PLATFORM
# =============================================================================

class MLRegistryModel(Base):
    __tablename__ = 'ml_registry_models'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    task_type = Column(String)  # Classification, Regression, etc.
    target_column = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    versions = relationship("MLRegistryVersion", back_populates="model", cascade="all, delete-orphan")

class MLRegistryVersion(Base):
    __tablename__ = 'ml_registry_versions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey('ml_registry_models.id', ondelete='CASCADE'), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    algorithm = Column(String)
    training_time_sec = Column(Float)
    metrics = Column(JSONB, default={})
    feature_importance = Column(JSONB, default={})
    model_size_bytes = Column(BigInteger)
    status = Column(String, default='Draft')  # Draft, Staging, Production, Archived
    created_at = Column(DateTime, default=datetime.utcnow)
    
    model = relationship("MLRegistryModel", back_populates="versions")

class MLOpsDeployment(Base):
    __tablename__ = 'mlops_deployments'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String, nullable=False)
    deployment_type = Column(String, default='Single')  # Single, A/B Testing, Canary, Shadow
    champion_version_id = Column(UUID(as_uuid=True), ForeignKey('ml_registry_versions.id', ondelete='SET NULL'), nullable=True)
    challenger_version_id = Column(UUID(as_uuid=True), ForeignKey('ml_registry_versions.id', ondelete='SET NULL'), nullable=True)
    champion_traffic = Column(Integer, default=100)
    challenger_traffic = Column(Integer, default=0)
    status = Column(String, default='Active')  # Active, Paused, Stopped
    created_at = Column(DateTime, default=datetime.utcnow)

class MLOpsExperiment(Base):
    __tablename__ = 'mlops_experiments'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deployment_id = Column(UUID(as_uuid=True), ForeignKey('mlops_deployments.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String, nullable=False)
    primary_metric = Column(String)  # Accuracy, Latency, etc.
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    winner_version_id = Column(UUID(as_uuid=True), ForeignKey('ml_registry_versions.id', ondelete='SET NULL'), nullable=True)
    status = Column(String, default='Running')  # Running, Completed, Rolled Back

class MLOpsPredictionLog(Base):
    __tablename__ = 'mlops_prediction_logs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deployment_id = Column(UUID(as_uuid=True), ForeignKey('mlops_deployments.id', ondelete='CASCADE'), nullable=False, index=True)
    version_id = Column(UUID(as_uuid=True), ForeignKey('ml_registry_versions.id', ondelete='CASCADE'), nullable=False)
    input_data = Column(JSONB, default={})
    prediction = Column(JSONB, default={})
    latency_ms = Column(Float)
    cpu_usage = Column(Float)
    memory_mb = Column(Float)
    is_shadow = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
