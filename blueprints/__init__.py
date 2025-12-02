"""
Blueprints package - modular route handlers for each platform
"""
from .facebook import facebook_bp
from .twitter import twitter_bp
from .instagram import instagram_bp
from .tiktok import tiktok_bp

__all__ = ['facebook_bp', 'twitter_bp', 'instagram_bp', 'tiktok_bp']
