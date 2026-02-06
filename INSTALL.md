# Installation Guide - Transcript Pipeline

## Prerequisites

1. **Python 3.10+**
   ```bash
   brew install python
   ```

2. **Node.js** (for Claude Code)
   ```bash
   brew install node
   ```

3. **Claude Code CLI**
   ```bash
   npm install -g @anthropic-ai/claude-code
   claude  # Run once to authenticate
   ```

## Setup

### 1. Clone the repo
```bash
git clone git@github.com:yasser-ensembl3/Audio-transcriber.git
cd Audio-transcriber
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```
# Notion Integration Token
# Get from: https://www.notion.so/my-integrations
NOTION_TOKEN=ntn_xxxxxxxxxxxxx

# Notion Database ID
# From your database URL: notion.so/DATABASE_ID?v=...
NOTION_DATABASE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Google Drive Folder ID
# From folder URL: drive.google.com/drive/folders/FOLDER_ID
GDRIVE_FOLDER_ID=xxxxxxxxxxxxxxxxxxxxxx

# Google Drive Credentials Path
GDRIVE_CREDENTIALS_PATH=credentials.json
```

### 4. Setup Google Drive OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable **Google Drive API**
4. Go to **Credentials** → Create **OAuth 2.0 Client ID**
   - Application type: **Desktop app**
5. Download the JSON file
6. Rename to `credentials.json` and place in project folder

### 5. First run (authenticate Google Drive)
```bash
source venv/bin/activate
python drive_uploader.py
```
This will open a browser for Google OAuth. Authenticate once.

### 6. Setup Notion Integration

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Create new integration
3. Copy the token to `.env`
4. Go to your Notion database → Share → Add your integration

**Required database columns:**
- `Link` (Title) - Contains the URL or title
- `Audio Link` (URL) - Alternative URL field
- `type` (Select) - "Youtube video", "Article", "Podcast"
- `Text summary` (Files) - Will be filled by pipeline
- `Audio summary` (Files) - Will be filled by pipeline

### 7. Update Claude Code path in summarizer.py

The summarizer uses the **full path** to Claude Code CLI (required for LaunchAgent to work).

Find your Claude path:
```bash
which claude
```

Then update `summarizer.py` — replace the existing path with yours:
```python
["/your/path/to/claude", "-p", prompt, "--dangerously-skip-permissions"]
```

## Running

### Start the watcher (foreground)
```bash
source venv/bin/activate
python watcher.py
```

### Start the watcher (background)
```bash
source venv/bin/activate
nohup python -u watcher.py > watcher.log 2>&1 &
```

### Check logs
```bash
tail -f watcher.log
```

### Stop the watcher
```bash
pkill -f watcher.py
```

## Auto-start on boot (macOS LaunchAgent)

The watcher can be configured to start automatically when the Mac boots and restart if it crashes.

### 1. Create the LaunchAgent

Replace `PROJECT_DIR` with your actual project path (e.g. `/Users/yourname/Audio-transcriber`):

```bash
PROJECT_DIR="/path/to/Audio-transcriber"

mkdir -p ~/Library/LaunchAgents

cat > ~/Library/LaunchAgents/com.transcript.pipeline.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.transcript.pipeline</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PROJECT_DIR}/venv/bin/python</string>
        <string>-u</string>
        <string>${PROJECT_DIR}/watcher.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${PROJECT_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${PROJECT_DIR}/watcher.log</string>
    <key>StandardErrorPath</key>
    <string>${PROJECT_DIR}/watcher.log</string>
</dict>
</plist>
EOF
```

### 2. Load (activate)
```bash
launchctl load ~/Library/LaunchAgents/com.transcript.pipeline.plist
```

### 3. Verify it's running
```bash
ps aux | grep watcher.py
tail -f /path/to/Audio-transcriber/watcher.log
```

### 4. Manage

| Action | Command |
|--------|---------|
| Stop | `launchctl unload ~/Library/LaunchAgents/com.transcript.pipeline.plist` |
| Restart | Unload then load again |
| Check logs | `tail -f /path/to/Audio-transcriber/watcher.log` |
| Check status | `ps aux \| grep watcher` |

## Troubleshooting

### "No such file or directory: 'claude'"
- The LaunchAgent does not inherit your shell PATH
- You must use the **full path** to Claude in `summarizer.py`
- Find it with `which claude` and update both occurrences in `summarizer.py`

### "Claude Code error"
- Make sure Claude Code is installed and authenticated: `claude --version`
- Run `claude` once manually to authenticate

### "Google Drive authentication required"
- Delete `token.pickle` and run `python drive_uploader.py` again

### "Notion API error"
- Check that your integration has access to the database
- Verify the database ID is correct

### "No entries found"
- Ensure the database has the correct column names
- Check that entries have URLs in `Link` or `Audio Link` fields

## Pipeline Flow

```
Notion DB (new entry detected)
    ↓
YouTube transcript / Article extraction
    ↓
Claude Code summarization
    ↓
Edge TTS audio generation (free)
    ↓
Google Drive upload (text + audio)
    ↓
Notion updated (Text summary + Audio summary)
```
