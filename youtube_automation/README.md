# 📺 Portable Multi-Channel YouTube Automation Hub

> [!IMPORTANT]
> **100% Standalone & Portable:**  
> Is poore `youtube_automation` folder ko aap kisi bhi project me direct copy-paste kar sakte hain. Kisi bhi project me paste karne par ye khud hi apne credentials, client secrets, aur connected channels ko auto-detect kar lega!

---

## 📂 Folder Structure

```
youtube_automation/
├── __init__.py               # Python module exports (YouTubeHub, resumable_upload)
├── hub.py                    # Auto-discovery orchestrator & multi-channel manager
├── uploader.py               # Resumable chunked video/Shorts uploader (with auto-retry)
├── cli.py                    # Standalone Command-Line Tool
├── client_secrets.json       # Google Cloud OAuth 2.0 Credentials
├── channels_registry.json    # Connected channels database (aliases, niches, stats)
├── README.md                 # This guide
└── tokens/                   # Permanent OAuth token storage for each channel
    ├── channel_01_token.json # Channel 1 (Authenticated)
    ├── channel_02_token.json # Channel 2
    └── ...
```

---

## 🚀 Dusre Project me Kaise Use Karein (Portable Setup)

### Tarika 1: Python Code me Use Karna (Sirf 2 Lines!)
Kisi bhi project ke Python code me:
```python
from youtube_automation import YouTubeHub

# Auto-detects all channels & credentials automatically
hub = YouTubeHub()

# 1. Sabhi channels list karein
channels = hub.list_channels()
print(channels)

# 2. Kisi bhi channel par video/short upload karein
hub.upload_video(
    alias="channel_01",              # Channel alias (channel_01, channel_02, etc.)
    video_path="path/to/clip.mp4",   # Video path
    title="Epic GTA 6 Crash #Shorts",
    description="Crazy moment in Vice City! #GTA6 #Shorts",
    tags=["GTA6", "Shorts", "Gaming"],
    privacy="public",                # "public", "unlisted", ya "private"
    is_short=True
)
```

---

### Tarika 2: Terminal / Command Line se Use Karna

Aap kisi bhi project ke terminal se direct commands chala sakte hain:

#### 1. Sabhi Connected Channels Dekhein:
```bash
python youtube_automation/cli.py list
```

#### 2. Naya Channel Connect Karein (e.g. Channel 2 se 10):
```bash
python youtube_automation/cli.py connect --alias channel_02 --name "Speed Rage Moments" --niche "Rage & Barking"
```
*(Browser khulega, apna 2nd YouTube account select karke allow karein — token automatically `tokens/channel_02_token.json` me save ho jayega).*

#### 3. Single Video / Short Upload Karein:
```bash
python youtube_automation/cli.py upload --channel channel_01 --file "my_clip.mp4" --title "Speed First Drive in GTA 6" --privacy public
```

#### 4. Poore Folder ke Clips Batch Upload Karein:
```bash
python youtube_automation/cli.py batch --channel channel_01 --folder "output_clips/IShowSpeed_GTA6/Phase_01" --limit 3 --privacy public
```

#### 5. Channel Connection Test Karein:
```bash
python youtube_automation/cli.py test --channel channel_01
```

---

## ⚡ 10 Channels Network Setup Strategy

| Channel Alias | Channel Niche | Target Audience | Recommended Schedule |
| :---: | :--- | :--- | :---: |
| **`channel_01`** | *Crazy Crashes & High Speed Chases* | Car / Racing / Action | 1:00 PM & 6:00 PM |
| **`channel_02`** | *Unhinged Rage, Barking & Screaming* | Comedy / Meme / Reaction | 2:00 PM & 7:00 PM |
| **`channel_03`** | *Vice City Beach & NPC Trolling* | Open World / Funny / NPCs | 3:00 PM & 8:00 PM |
| **`channel_04`** | *5-Star Police Shootouts & Escapes* | Hardcore Police Chases / Action | 4:00 PM & 9:00 PM |
| **`channel_05`** | *Mindblown Reactions & Physics Glitches*| Glitches / Bugs / Secrets | 5:00 PM & 10:00 PM |
| **`channel_06`** | *Vice City Stunts & Air Flips* | Ramp Jumps / Parachute / Jet Ski | 12:00 PM & 6:30 PM |
| **`channel_07`** | *Speed Spanish & Voice Cracks* | Short Meme Moments | 1:30 PM & 7:30 PM |
| **`channel_08`** | *GTA 6 Graphics & Secret Spots* | Easter Eggs / Graphics Comparisons | 2:30 PM & 8:30 PM |
| **`channel_09`** | *Best Combat & Melee Brawls* | Knockouts / Street Brawls | 3:30 PM & 9:30 PM |
| **`channel_10`** | *Daily Vice City Shorts Compilation* | Top Viral Highlights | 5:30 PM & 10:30 PM |

---

## 🛡️ Quota & Safety Rules
1. **Daily Upload Quota:** Ek Google Cloud Project me daily ~6 uploads free hote hain. Agar 10 channels par roz 2-3 clips upload karni hon to 2-3 Google Cloud Projects bana kar unke `client_secrets.json` use kar sakte hain.
2. **Auto Token Refresh:** Har token me refresh token shamil hai, isliye expiry par script khud Google se naya token le leti hai (zero human intervention).
