# Installation Guide - Transcript Pipeline

## Prerequisites

1. **Python 3.10+**
   ```bash
   brew install python
   ```

2. **Claude Code CLI**
   ```bash
   npm install -g @anthropic-ai/claude-code
   claude  # Run once to authenticate
   ```

## Setup

### 1. Clone/Copy the project
```bash
cp -r transcript-pipeline /path/to/destination
cd /path/to/destination/transcript-pipeline
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

# Webhook Secret (optional, for n8n integration)
WEBHOOK_SECRET=your-secret-here
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

## Auto-start on boot (macOS)

Create a LaunchAgent:

```bash
mkdir -p ~/Library/LaunchAgents
cat > ~/Library/LaunchAgents/com.transcript.pipeline.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.transcript.pipeline</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/transcript-pipeline/venv/bin/python</string>
        <string>-u</string>
        <string>/path/to/transcript-pipeline/watcher.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/transcript-pipeline</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/path/to/transcript-pipeline/watcher.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/transcript-pipeline/watcher.log</string>
</dict>
</plist>
EOF
```

**Important:** Replace `/path/to/transcript-pipeline` with the actual path.

Load the agent:
```bash
launchctl load ~/Library/LaunchAgents/com.transcript.pipeline.plist
```

Unload:
```bash
launchctl unload ~/Library/LaunchAgents/com.transcript.pipeline.plist
```

## Troubleshooting

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
