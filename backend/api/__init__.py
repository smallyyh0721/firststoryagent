"""
API endpoints module
"""

from .stories import router as stories_router

__all__ = ["stories_router"]