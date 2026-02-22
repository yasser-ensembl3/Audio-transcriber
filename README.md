# Transcript Pipeline

Automated content processing pipeline that extracts transcripts/articles from various sources (YouTube, podcasts, web articles), generates AI summaries via Claude, converts them to audio via Edge TTS, and uploads everything to Google Drive — with Notion as the central database.

## What It Does

```
Notion Database (URL added)
    │
    ▼
Auto-detect content type (YouTube / Article / Podcast)
    │
    ├── Extract transcript or article text
    ├── Summarize with Claude Code CLI
    ├── Generate audio (Edge TTS)
    └── Upload to Google Drive
    │
    ▼
Notion updated with links to summary + audio
```

## Supported Sources

| Source | Extraction Method | Status |
|--------|-------------------|--------|
| YouTube videos | youtube-transcript-api + yt-dlp | Active |
| Web articles | Trafilatura | Active |
| Podcasts | Whisper (local transcription) | Implemented, disabled in pipeline |

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| LLM | Claude Code CLI (`claude -p`) |
| Text-to-Speech | Edge TTS (free, no API key) |
| Database | Notion API |
| File storage | Google Drive API v3 (OAuth2) |
| Web framework | Flask (webhook server) |
| Article extraction | Trafilatura |
| YouTube transcripts | youtube-transcript-api + yt-dlp |
| Podcast transcription | faster-whisper (local) |

## Architecture

```
transcript-pipeline/
├── process_all.py           # Batch processing — all pending Notion entries
├── process_single.py        # Single entry processing (webhook/manual)
├── notion_reader.py         # Notion DB queries, URL type detection
├── notion_updater.py        # Update Notion pages with results
├── youtube_transcript.py    # YouTube transcript extraction + metadata
├── article_extractor.py     # Web article extraction (Trafilatura)
├── podcast_transcript.py    # Podcast download + Whisper transcription
├── summarizer.py            # Claude Code CLI summarization with chunking
├── audio_generator.py       # Edge TTS text-to-speech (async)
├── drive_uploader.py        # Google Drive OAuth2 upload + sharing
├── watcher.py               # Polling daemon (checks Notion every 2 min)
├── webhook_server.py        # Flask webhook server (port 5050)
├── requirements.txt
├── .env.example
└── INSTALL.md
```

## How It Works

### Content Extraction

- **YouTube**: Fetches transcript via youtube-transcript-api (prefers French, then English, then any available language). Extracts title/channel/duration via yt-dlp.
- **Articles**: Downloads and extracts clean text via Trafilatura. Outputs Markdown with title, author, date, and source URL.
- **Podcasts** (disabled): Downloads audio via yt-dlp, transcribes locally with faster-whisper, auto-detects language.

### Summarization

- Uses Claude Code CLI (`claude -p`) as a subprocess — leverages existing subscription, zero API cost
- Respects 90K token limit (~360K characters) — automatically chunks oversized content
- Summary length is proportional to content:
  - YouTube/Podcast: ~25% of original (1,500–3,000 words)
  - Articles: proportional (150–1,500 words)
- Multi-chunk content is summarized per chunk then merged into a cohesive final summary

### Audio Generation

- Microsoft Edge TTS — free, no API key required
- Default voice: `en-US-AriaNeural` (female, conversational)
- Available voices: Aria, Guy, Jenny, Davis
- Strips Markdown formatting before converting to speech
- Output: MP3

### Google Drive Upload

- OAuth2 authentication with token caching (`token.pickle`)
- Uploads summary (.md) and audio (.mp3) to a configured folder
- Sets public sharing permissions automatically
- Returns shareable web links for Notion updates

### Notion Integration

**Database schema:**

| Field | Type | Purpose |
|-------|------|---------|
| Link | Title | URL or content title |
| Audio Link | URL | Alternative URL field |
| type | Select | Content type (YouTube, Podcast, Article) |
| Text summary | Files | Generated summary link |
| Audio summary | Files | Generated audio link |

The pipeline auto-detects content type from URL, processes the content, and updates the Notion page with Drive links to the generated files. It also renames the Link field to the content's actual title.

## Trigger Methods

### 1. Watcher (polling daemon)

Polls Notion every 2 minutes for new entries without summaries.

```bash
# Foreground
python watcher.py

# Background
nohup python -u watcher.py > watcher.log 2>&1 &
```

Maintains a `.processed_ids` cache to avoid reprocessing.

### 2. Webhook Server

Flask server on port 5050 for external triggers (n8n, manual API calls).

```bash
python webhook_server.py
```

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/webhook/process` | Process specific entry or all pending |
| POST | `/webhook/process-all` | Batch process all pending entries |

**Request format:**
```json
{
  "secret": "your-webhook-secret",
  "page_id": "notion-page-id",
  "url": "content-url"
}
```

### 3. Manual

```bash
# Process all pending
python process_all.py

# Process single entry
python process_single.py <page_id> <url>
```

## Setup

### Prerequisites

- Python 3.10+
- Claude Code CLI installed and authenticated
- Notion integration token
- Google Drive OAuth credentials

### Quick Start

```bash
cd transcript-pipeline
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
```

See [INSTALL.md](INSTALL.md) for detailed setup including Notion integration, Google Drive OAuth, and macOS LaunchAgent auto-start configuration.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `NOTION_TOKEN` | Notion integration token |
| `NOTION_DATABASE_ID` | Target Notion database ID |
| `GDRIVE_FOLDER_ID` | Google Drive upload folder ID |
| `GDRIVE_CREDENTIALS_PATH` | Path to Google OAuth credentials JSON |
| `WEBHOOK_SECRET` | Authentication token for webhook endpoints |

## Output Structure

```
output/
├── video_title_transcript.md    # Extracted transcript/article
├── video_title_summary.md       # AI-generated summary
└── video_title_audio.mp3        # TTS audio of summary
```
