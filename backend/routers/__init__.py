from .proposals   import router as proposals_router
from .approvals   import router as approvals_router
from .vendors     import router as vendors_router
from .analytics   import router as analytics_router
from .auth        import router as auth_router

__all__ = [
    "proposals_router", "approvals_router",
    "vendors_router",   "analytics_router", "auth_router",
]
