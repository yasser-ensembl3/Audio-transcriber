#!/usr/bin/env python3
"""
Process a single entry by page_id and URL.
Called by the webhook server.
"""

import sys
import os
from youtube_transcript import save_transcript as save_youtube_transcript
from article_extractor import save_article
from summarizer import summarize_file
from drive_uploader import upload_to_drive
from notion_updater import update_text_summary, update_audio_summary
from audio_generator import generate_audio_from_summary
from notion_reader import detect_type_from_url

def process_single(page_id, url):
    """Process a single URL and update Notion"""
    print(f"Processing URL: {url}")
    print(f"Page ID: {page_id}")

    content_type = detect_type_from_url(url)
    print(f"Detected type: {content_type}")

    try:
        # Step 1: Extract content
        if content_type == "Youtube video":
            filepath, title = save_youtube_transcript(url)
        elif content_type == "Article":
            filepath, title = save_article(url)
        elif content_type == "Podcast":
            print("Podcasts not supported yet")
            return False
        else:
            print(f"Unknown type: {content_type}")
            return False

        # Step 2: Summarize with Claude Code
        print("\nGenerating summary...")
        summary_path, _ = summarize_file(filepath, content_type)

        # Step 3: Generate audio
        print("\nGenerating audio...")
        audio_path = generate_audio_from_summary(summary_path)

        # Step 4: Upload to Drive (summary + audio)
        print("\nUploading to Drive...")
        file_id, drive_link = upload_to_drive(summary_path)
        audio_file_id, audio_drive_link = upload_to_drive(audio_path)

        # Step 5: Update Notion
        print("\nUpdating Notion...")
        filename = os.path.basename(summary_path)
        audio_filename = os.path.basename(audio_path)
        update_text_summary(page_id, drive_link, filename)
        update_audio_summary(page_id, audio_drive_link, audio_filename)

        print(f"\n✓ SUCCESS: {title}")
        return True

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python process_single.py <page_id> <url>")
        sys.exit(1)

    page_id = sys.argv[1]
    url = sys.argv[2]

    success = process_single(page_id, url)
    sys.exit(0 if success else 1)
