"""PORTABLE YOUTUBE AUTOMATION PACKAGE.
Copy this entire `youtube_automation` folder into ANY project.
Import with:
    from youtube_automation import YouTubeHub
    hub = YouTubeHub()
"""
from .hub import YouTubeHub
from .uploader import resumable_upload

__all__ = ["YouTubeHub", "resumable_upload"]
