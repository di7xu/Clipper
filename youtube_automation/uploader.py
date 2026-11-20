"""PORTABLE YOUTUBE AUTOMATION MODULE: Video & Shorts Uploader
Robust, chunked resumable video uploader with exponential backoff,
automatic Shorts tags injection, and YouTube Data API quota protection.
"""
import os
import time
import http.client
import httplib2
from pathlib import Path
from typing import Dict, List, Optional, Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

RETRIABLE_EXCEPTIONS = (
    httplib2.HttpLib2Error,
    IOError,
    http.client.NotConnected,
    http.client.IncompleteRead,
    http.client.ImproperConnectionState,
    http.client.CannotSendRequest,
    http.client.CannotSendHeader,
    http.client.ResponseNotReady,
    http.client.BadStatusLine,
)

RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

def resumable_upload(
    youtube,
    file_path: str,
    title: str,
    description: str = "",
    tags: Optional[List[str]] = None,
    category_id: str = "20",  # 20 = Gaming, 24 = Entertainment
    privacy_status: str = "public",
    is_short: bool = True,
    chunk_size: int = 1024 * 1024 * 8,  # 8MB chunks
    max_retries: int = 10
) -> Dict[str, Any]:
    """Execute a reliable resumable upload with chunk progress and retry logic."""
    video_p = Path(file_path)
    if not video_p.exists():
        raise FileNotFoundError(f"Video file not found: {file_path}")

    # Build viral title & tags for Shorts
    final_title = title
    if is_short and "#Shorts" not in final_title and "#shorts" not in final_title:
        if len(final_title) <= 90:
            final_title = f"{final_title} #Shorts"

    final_tags = tags or ["Shorts", "GTA6", "Gaming"]
    if is_short and "Shorts" not in final_tags:
        final_tags.append("Shorts")

    final_description = description.strip()
    if is_short and "#Shorts" not in final_description:
        final_description += "\n\n#Shorts #GTA6 #Gaming #Viral"

    body = {
        "snippet": {
            "title": final_title,
            "description": final_description,
            "tags": final_tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        }
    }

    media = MediaFileUpload(
        str(video_p),
        mimetype="video/mp4",
        chunksize=chunk_size,
        resumable=True
    )

    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    retry = 0
    file_size = video_p.stat().st_size

    print(f"   📤 Uploading: {video_p.name} ({file_size / (1024*1024):.1f} MB)")
    print(f"      Title: '{final_title}' | Privacy: {privacy_status}")

    while response is None:
        try:
            status, response = insert_request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"      ⏳ Progress: {pct}%")
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error_msg = f"A retriable HTTP error {e.resp.status} occurred:\n{e.content}"
            else:
                if "quotaExceeded" in str(e):
                    print("   ❌ YouTube API Error: Daily Upload Quota Exceeded (10,000 units limit).")
                raise e
        except RETRIABLE_EXCEPTIONS as e:
            error_msg = f"A retriable network error occurred: {e}"

        if response is None and retry < max_retries:
            retry += 1
            wait_sec = 2 ** retry
            print(f"      ⚠️ Network hiccup. Retrying in {wait_sec}s (Attempt {retry}/{max_retries})...")
            time.sleep(wait_sec)
        elif response is None and retry >= max_retries:
            raise RuntimeError(f"Max retries exceeded for {file_path}")

    video_id = response.get("id")
    video_url = f"https://youtu.be/{video_id}"
    print(f"   🎉 SUCCESS! Video Live at: {video_url}")
    return {
        "status": "success",
        "video_id": video_id,
        "video_url": video_url,
        "title": final_title,
        "privacy": privacy_status
    }
