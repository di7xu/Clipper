"""PORTABLE YOUTUBE CLI INTERFACE.
Run directly from terminal inside any project:
    python youtube_automation/cli.py list
    python youtube_automation/cli.py connect --alias ch02 --name "Speed Rage" --niche "Rage"
    python youtube_automation/cli.py upload --channel channel_01 --file "clip.mp4" --title "Viral Clip"
"""
import sys
import argparse
from pathlib import Path

# Add parent directory of youtube_automation to path so it can import itself
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from youtube_automation.hub import YouTubeHub

def main():
    parser = argparse.ArgumentParser(description="Portable Multi-Channel YouTube Automation CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Command: list
    subparsers.add_parser("list", help="List all registered channels and their connection status")

    # Command: connect
    p_connect = subparsers.add_parser("connect", help="Connect/Authenticate a new YouTube Channel via OAuth")
    p_connect.add_argument("--alias", type=str, required=True, help="Short unique alias for channel (e.g. ch02, speed_rage)")
    p_connect.add_argument("--name", type=str, default=None, help="Display name for the channel")
    p_connect.add_argument("--niche", type=str, default="General", help="Niche or content category (e.g. Crashes, Rage)")
    p_connect.add_argument("--port", type=int, default=8080, help="Local OAuth listener port")

    # Command: upload
    p_upload = subparsers.add_parser("upload", help="Upload a single video/Short to a specific channel")
    p_upload.add_argument("--channel", type=str, default="channel_01", help="Channel alias to upload to")
    p_upload.add_argument("--file", type=str, required=True, help="Path to MP4 video file")
    p_upload.add_argument("--title", type=str, required=True, help="Video title")
    p_upload.add_argument("--desc", type=str, default="", help="Video description")
    p_upload.add_argument("--tags", type=str, default="Shorts,Gaming,GTA6", help="Comma-separated tags")
    p_upload.add_argument("--privacy", type=str, default="public", choices=["public", "unlisted", "private"], help="Privacy status")

    # Command: batch
    p_batch = subparsers.add_parser("batch", help="Batch upload multiple clips from a folder")
    p_batch.add_argument("--channel", type=str, required=True, help="Channel alias to upload to")
    p_batch.add_argument("--folder", type=str, required=True, help="Folder containing MP4 clips")
    p_batch.add_argument("--limit", type=int, default=5, help="Maximum number of clips to upload in this run")
    p_batch.add_argument("--privacy", type=str, default="public", choices=["public", "unlisted", "private"])

    # Command: test
    p_test = subparsers.add_parser("test", help="Test connection and token validity for a channel")
    p_test.add_argument("--channel", type=str, default="channel_01", help="Channel alias to test")

    args = parser.parse_args()
    hub = YouTubeHub()

    if args.command == "list" or args.command is None:
        channels = hub.list_channels()
        print("=" * 80)
        print("📺 REGISTERED YOUTUBE CHANNELS NETWORK")
        print("=" * 80)
        if not channels:
            print("No channels registered yet.")
            print("To connect one: python youtube_automation/cli.py connect --alias ch01")
        else:
            print(f"{'#':<3} | {'ALIAS':<16} | {'STATUS':<12} | {'NICHE':<30} | {'DISPLAY NAME'}")
            print("-" * 80)
            for idx, ch in enumerate(channels, 1):
                status_icon = "🟢" if ch["status"] == "connected" else "🔴"
                print(f"{idx:<3} | {ch['alias']:<16} | {status_icon} {ch['status']:<9} | {ch['niche']:<30} | {ch['display_name']}")
        print("=" * 80)

    elif args.command == "connect":
        hub.connect_channel(
            alias=args.alias,
            display_name=args.name,
            niche=args.niche,
            port=args.port
        )

    elif args.command == "upload":
        tags_list = [t.strip() for t in args.tags.split(",") if t.strip()]
        hub.upload_video(
            alias=args.channel,
            video_path=args.file,
            title=args.title,
            description=args.desc,
            tags=tags_list,
            privacy=args.privacy,
            is_short=True
        )

    elif args.command == "batch":
        folder = Path(args.folder)
        if not folder.exists():
            print(f"❌ Folder not found: {folder}")
            sys.exit(1)

        mp4s = sorted(list(folder.glob("*.mp4")))
        if not mp4s:
            print(f"No MP4 files found in: {folder}")
            sys.exit(0)

        limit = min(len(mp4s), args.limit)
        print(f"🚀 Batch uploading {limit} clips to Channel [{args.channel}]...")

        for idx, video_p in enumerate(mp4s[:limit], 1):
            clean_title = video_p.stem.replace("_", " ").title()
            print(f"\n[{idx}/{limit}] Uploading: {video_p.name}")
            try:
                hub.upload_video(
                    alias=args.channel,
                    video_path=str(video_p),
                    title=clean_title,
                    privacy=args.privacy,
                    is_short=True
                )
            except Exception as e:
                print(f"❌ Upload failed: {e}")
                if "quotaExceeded" in str(e):
                    print("🛑 Stopping batch run due to daily quota limit.")
                    break

    elif args.command == "test":
        print(f"🔍 Testing connection for Channel [{args.channel}]...")
        try:
            service = hub.get_service(args.channel)
            print(f"✅ Connection SUCCESSFUL! Service built and authenticated for [{args.channel}].")
        except Exception as e:
            print(f"❌ Connection FAILED: {e}")

if __name__ == "__main__":
    main()
