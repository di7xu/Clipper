"""PORTABLE YOUTUBE AUTOMATION HUB: Core Orchestrator & Auto-Discovery Engine.
Completely standalone. Automatically resolves its own folder path wherever it is copied.
Supports 1 to 10+ YouTube channels with isolated OAuth tokens and automated routing.
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from .uploader import resumable_upload

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

class YouTubeHub:
    """Portable YouTube Hub for multi-channel management and auto-uploading."""

    def __init__(self, hub_dir: Optional[str] = None):
        # Auto-discover own directory dynamically (Works in ANY project!)
        if hub_dir:
            self.root_dir = Path(hub_dir).resolve()
        else:
            self.root_dir = Path(__file__).resolve().parent

        self.client_secrets_path = self.root_dir / "client_secrets.json"
        self.registry_path = self.root_dir / "channels_registry.json"
        self.tokens_dir = self.root_dir / "tokens"
        self.tokens_dir.mkdir(parents=True, exist_ok=True)

        self.registry = self._load_registry()
        self._sync_tokens_with_registry()

    def _load_registry(self) -> Dict[str, Any]:
        """Load channels registry or create default if not present."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        default_reg = {
            "version": "1.0",
            "channels": []
        }
        self._save_registry(default_reg)
        return default_reg

    def _save_registry(self, reg_data: Optional[Dict[str, Any]] = None):
        """Save registry to disk."""
        data = reg_data or self.registry
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _sync_tokens_with_registry(self):
        """Auto-detect any token files in tokens/ folder and register them."""
        token_files = list(self.tokens_dir.glob("*.json"))
        existing_aliases = {ch.get("alias") for ch in self.registry.get("channels", [])}
        changed = False

        for tf in token_files:
            # extract alias from name e.g. ch01_default_token.json -> ch01_default
            alias = tf.stem.replace("_token", "")
            if alias not in existing_aliases:
                self.registry.setdefault("channels", []).append({
                    "alias": alias,
                    "display_name": alias.replace("_", " ").title(),
                    "niche": "General Clips",
                    "token_file": f"tokens/{tf.name}",
                    "status": "connected",
                    "daily_upload_limit": 6,
                    "daily_uploads_today": 0
                })
                changed = True

        if changed:
            self._save_registry()

    def list_channels(self) -> List[Dict[str, Any]]:
        """Return all registered channels and their connection status."""
        channels = self.registry.get("channels", [])
        result = []
        for ch in channels:
            alias = ch.get("alias", "")
            token_rel = ch.get("token_file", f"tokens/{alias}_token.json")
            token_full = self.root_dir / token_rel
            is_connected = token_full.exists() and token_full.stat().st_size > 50

            result.append({
                "alias": alias,
                "display_name": ch.get("display_name", alias),
                "niche": ch.get("niche", "General"),
                "status": "connected" if is_connected else "disconnected",
                "token_path": str(token_full).replace("\\", "/"),
                "daily_limit": ch.get("daily_upload_limit", 6)
            })
        return result

    def get_service(self, alias: str = "channel_01"):
        """Get an authenticated YouTube API service for a specific channel alias."""
        channel_info = next((ch for ch in self.registry.get("channels", []) if ch.get("alias") == alias), None)
        if not channel_info:
            # Check if token exists with this alias
            token_file = self.tokens_dir / f"{alias}_token.json"
            if not token_file.exists():
                token_file = self.tokens_dir / f"{alias}.json"
        else:
            token_file = self.root_dir / channel_info.get("token_file", f"tokens/{alias}_token.json")

        if not token_file.exists():
            raise FileNotFoundError(
                f"No token found for channel '{alias}' at {token_file}.\n"
                f"Please connect it first: python youtube_automation/cli.py connect --alias {alias}"
            )

        with open(token_file, "r", encoding="utf-8") as f:
            token_data = json.load(f)

        creds = Credentials.from_authorized_user_info(token_data)

        # Auto-refresh if expired
        if creds.expired and creds.refresh_token:
            print(f"🔄 Token for '{alias}' expired. Auto-refreshing...")
            creds.refresh(Request())
            # Save refreshed token back to disk
            with open(token_file, "w", encoding="utf-8") as f:
                f.write(creds.to_json())

        return build("youtube", "v3", credentials=creds)

    def connect_channel(self, alias: str, display_name: Optional[str] = None, niche: str = "General", port: int = 8080) -> Dict[str, Any]:
        """Launch local OAuth 2.0 flow to authenticate and connect a new channel."""
        if not self.client_secrets_path.exists():
            raise FileNotFoundError(
                f"client_secrets.json not found in {self.root_dir}!\n"
                f"Please place your Google Cloud OAuth client_secrets.json inside this folder."
            )

        token_filename = f"{alias}_token.json"
        token_path = self.tokens_dir / token_filename

        print("=" * 70)
        print(f"🔗 INITIATING GOOGLE OAUTH FOR CHANNEL: '{alias}'")
        print(f"Niche: {niche}")
        print("A browser window will open. Sign in to the specific YouTube channel account.")
        print("=" * 70)

        flow = InstalledAppFlow.from_client_secrets_file(
            str(self.client_secrets_path),
            scopes=SCOPES
        )
        creds = flow.run_local_server(
            port=port,
            prompt="consent",
            access_type="offline"
        )

        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

        print(f"✅ Token saved successfully: {token_path}")

        # Update registry
        existing = next((ch for ch in self.registry.get("channels", []) if ch.get("alias") == alias), None)
        if existing:
            existing["status"] = "connected"
            existing["display_name"] = display_name or existing.get("display_name", alias)
            existing["niche"] = niche
            existing["token_file"] = f"tokens/{token_filename}"
        else:
            self.registry.setdefault("channels", []).append({
                "alias": alias,
                "display_name": display_name or alias.replace("_", " ").title(),
                "niche": niche,
                "token_file": f"tokens/{token_filename}",
                "status": "connected",
                "daily_upload_limit": 6,
                "daily_uploads_today": 0
            })
        self._save_registry()

        return {
            "status": "connected",
            "alias": alias,
            "token_file": str(token_path).replace("\\", "/")
        }

    def upload_video(
        self,
        alias: str,
        video_path: str,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        privacy: str = "public",
        is_short: bool = True
    ) -> Dict[str, Any]:
        """Upload a video directly to a specific channel alias."""
        youtube = self.get_service(alias)
        print(f"🚀 Dispatching upload to Channel [{alias}]...")
        return resumable_upload(
            youtube=youtube,
            file_path=video_path,
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy,
            is_short=is_short
        )
