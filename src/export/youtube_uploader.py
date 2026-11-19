"""YouTube Shorts & Video Automated Uploader using YouTube Data API v3.

Provides official, secure, OAuth 2.0 authorized video publishing to YouTube:
- Automatic token caching (youtube_token.json)
- Automatic resumable chunked upload
- Reads companion .meta.json for titles, descriptions, and hashtags
- Direct Shorts compatibility (9:16 vertical + #Shorts tag)
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
except ImportError:
    raise ImportError("Google API libraries not found. Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")

# OAuth 2.0 Scope for uploading YouTube videos
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
DEFAULT_CLIENT_SECRETS = Path("client_secrets.json")
DEFAULT_TOKEN_FILE = Path("youtube_token.json")


def get_authenticated_service(
    client_secrets_path: Path = DEFAULT_CLIENT_SECRETS,
    token_path: Path = DEFAULT_TOKEN_FILE
):
    """Authenticate via OAuth 2.0 and return YouTube Data API client."""
    creds = None

    # Load cached token if available
    if token_path.is_file():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except Exception:
            creds = None

    # If no valid credentials, perform login or refresh
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[YouTube Auth] Refreshing expired credentials...", flush=True)
            creds.refresh(Request())
        else:
            if not client_secrets_path.is_file():
                raise FileNotFoundError(
                    f"OAuth client secrets file not found at: {client_secrets_path.resolve()}\n"
                    "Please download client_secrets.json from Google Cloud Console and place it in the project root."
                )

            print("[YouTube Auth] Opening browser for one-time YouTube account authorization...", flush=True)
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets_path), SCOPES)
            creds = flow.run_local_server(port=0, prompt="consent")

        # Save credentials for subsequent runs
        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        print(f"[YouTube Auth] Authorization successful! Token saved to: {token_path}", flush=True)

    return build("youtube", "v3", credentials=creds)


def upload_video(
    youtube,
    file_path: str,
    title: str,
    description: str,
    tags: Optional[List[str]] = None,
    category_id: str = "24",  # 24 = Entertainment, 22 = People & Blogs
    privacy_status: str = "unlisted"
) -> Dict[str, Any]:
    """Upload video to YouTube with resumable chunked upload."""
    video_file = Path(file_path).resolve()
    if not video_file.is_file():
        raise FileNotFoundError(f"Video file does not exist: {video_file}")

    # Ensure title is within 100 characters limit
    clean_title = title[:100]

    # Ensure #Shorts is present in title or description for vertical videos
    if "#Shorts" not in clean_title and "#Shorts" not in description:
        description = f"{description}\n\n#Shorts"

    body = {
        "snippet": {
            "title": clean_title,
            "description": description,
            "tags": tags or ["Shorts", "Viral"],
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    # Resumable media file upload
    media = MediaFileUpload(
        str(video_file),
        chunksize=1024 * 1024 * 2,  # 2MB chunks
        resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    print(f"\n[YouTube Uploader] Uploading: {video_file.name}", flush=True)
    print(f"  Title: {clean_title}", flush=True)
    print(f"  Privacy: {privacy_status}", flush=True)

    response = None
    last_pct = -10
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            if pct >= last_pct + 15:
                last_pct = pct
                print(f"  [Upload Progress] {pct}% uploaded...", flush=True)

    video_id = response.get("id")
    shorts_url = f"https://www.youtube.com/shorts/{video_id}"
    watch_url = f"https://youtu.be/{video_id}"

    print(f"  [Upload Complete] Video ID: {video_id}", flush=True)
    print(f"  [Link] {shorts_url}", flush=True)

    return {
        "videoId": video_id,
        "watchUrl": watch_url,
        "shortsUrl": shorts_url,
        "privacyStatus": privacy_status,
        "title": clean_title
    }


def upload_folder(
    folder_path: str,
    privacy_status: str = "unlisted",
    interval_seconds: int = 5
) -> List[Dict[str, Any]]:
    """Upload all MP4 clips in a folder, parsing companion .meta.json files."""
    folder = Path(folder_path).resolve()
    if not folder.is_dir():
        raise NotADirectoryError(f"Directory not found: {folder}")

    mp4_files = sorted(folder.glob("*.mp4"))
    if not mp4_files:
        print(f"[YouTube Uploader] No MP4 files found in {folder}")
        return []

    print(f"[YouTube Uploader] Found {len(mp4_files)} clips in {folder.name} to upload.")
    youtube = get_authenticated_service()

    results = []
    for idx, mp4 in enumerate(mp4_files, 1):
        print(f"\n[{idx}/{len(mp4_files)}] Preparing {mp4.name}...")
        meta_file = mp4.with_suffix(".meta.json")

        title = mp4.stem
        desc = f"{title}\n\nProduced with AI Video Clipper\n#Shorts #Viral"
        tags = ["Shorts", "Viral"]

        if meta_file.is_file():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    title = meta.get("title", title)
                    desc = meta.get("description", desc)
                    tags = meta.get("hashtags", tags)
            except Exception as e:
                print(f"  Warning: Failed to parse metadata file {meta_file.name}: {e}")

        try:
            res = upload_video(
                youtube=youtube,
                file_path=str(mp4),
                title=title,
                description=desc,
                tags=tags,
                privacy_status=privacy_status
            )
            results.append(res)
        except Exception as e:
            print(f"  Upload error for {mp4.name}: {e}", file=sys.stderr)

        if idx < len(mp4_files) and interval_seconds > 0:
            time.sleep(interval_seconds)

    print(f"\n[YouTube Uploader] Finished! Successfully uploaded {len(results)}/{len(mp4_files)} clips.")
    return results


def main():
    parser = argparse.ArgumentParser(description="Automated YouTube Video/Shorts Uploader")
    parser.add_argument("--auth", action="store_true", help="Perform one-time OAuth authentication and save token")
    parser.add_argument("-f", "--file", help="Path to single MP4 file to upload")
    parser.add_argument("-d", "--folder", help="Path to directory of MP4 clips to upload in batch")
    parser.add_argument("-p", "--privacy", choices=["public", "unlisted", "private"], default="unlisted", help="Upload privacy status (default: unlisted)")
    parser.add_argument("-t", "--title", help="Custom video title")
    parser.add_argument("--desc", help="Custom video description")

    args = parser.parse_args()

    if args.auth:
        print("[YouTube Auth] Starting authorization flow...")
        service = get_authenticated_service()
        print("[YouTube Auth] Ready! Your YouTube account is now connected and authorized.")
        return

    if args.folder:
        upload_folder(args.folder, privacy_status=args.privacy)
    elif args.file:
        youtube = get_authenticated_service()
        title = args.title or Path(args.file).stem
        desc = args.desc or f"{title}\n\n#Shorts #Viral"
        upload_video(youtube, args.file, title, desc, privacy_status=args.privacy)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
