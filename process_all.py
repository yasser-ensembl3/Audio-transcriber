import os
from notion_reader import get_database_entries, analyze_entries
from youtube_transcript import save_transcript as save_youtube_transcript
from article_extractor import save_article
from summarizer import summarize_file
from audio_generator import generate_audio_from_summary
from drive_uploader import upload_to_drive
from notion_updater import update_text_summary, update_audio_summary, update_page_title

def process_entry(entry):
    """Process a single entry: extract content, summarize, upload, update Notion"""
    content_type = entry['type']
    url = entry['url']
    page_id = entry['id']
    name = entry['name']

    print(f"\n{'='*60}")
    print(f"Processing: {name[:50]}...")
    print(f"Type: {content_type}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    if not url:
        print("  SKIP: No URL found")
        return False

    try:
        # Step 1: Extract content
        if content_type == "Youtube video":
            filepath, title = save_youtube_transcript(url)
        elif content_type == "Article":
            filepath, title = save_article(url)
        elif content_type == "Podcast":
            print("  SKIP: Podcasts not supported yet")
            return False
        else:
            print(f"  SKIP: Unknown type {content_type}")
            return False

        # Step 2: Summarize
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

        # Step 6: Rename the Link column to the content title
        update_page_title(page_id, title)

        print(f"\n✓ SUCCESS: {title}")
        return True

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False

def main():
    print("Fetching entries from Notion...")
    entries = get_database_entries()
    to_process, _ = analyze_entries(entries)

    # Filter out podcasts
    to_process = [e for e in to_process if e['type'] != "Podcast"]

    print(f"\nFound {len(to_process)} entries to process (excluding podcasts)\n")

    success = 0
    failed = 0

    for entry in to_process:
        if process_entry(entry):
            success += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"DONE: {success} success, {failed} failed")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
