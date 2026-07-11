from .chat import router as chat_router
from .files import router as files_router
from .analytics import router as analytics_router
from .reports import router as reports_router
from .email_prefs import router as email_prefs_router
from .dashboard_api import router as dashboard_router
from .brain import router as brain_router
from .datavision_api import router as datavision_router
from .automl_api import router as automl_router
from .data_health_api import router as data_health_router
from .explainability_api import router as explainability_router
from .playground_api import router as playground_router
from .deploy import router as deploy_router

# Export all routers
__all__ = [
    "chat_router",
    "files_router",
    "analytics_router",
    "reports_router",
    "email_prefs_router",
    "dashboard_router",
    "brain_router",
    "datavision_router",
    "automl_router",
    "data_health_router",
    "explainability_router",
    "playground_router",
    "deploy_router"
]