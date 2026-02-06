#!/usr/bin/env python3
"""
Watcher that polls Notion and processes new entries automatically.
No need for n8n or ngrok - runs locally.
"""

import time
import os
from datetime import datetime
from notion_reader import get_database_entries, analyze_entries
from process_all import process_entry

# Check every 2 minutes (adjust as needed)
POLL_INTERVAL = 120

# Track processed entries to avoid duplicates
processed_ids = set()

def load_processed_ids():
    """Load previously processed IDs from file"""
    cache_file = os.path.join(os.path.dirname(__file__), ".processed_ids")
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_processed_id(page_id):
    """Save processed ID to file"""
    cache_file = os.path.join(os.path.dirname(__file__), ".processed_ids")
    with open(cache_file, "a") as f:
        f.write(f"{page_id}\n")

def check_and_process():
    """Check for new entries and process them"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking Notion...")

    try:
        entries = get_database_entries()
        to_process, _ = analyze_entries(entries)

        # Filter out podcasts and already processed
        new_entries = [
            e for e in to_process
            if e['type'] != "Podcast" and e['id'] not in processed_ids
        ]

        if not new_entries:
            print("  No new entries to process")
            return

        print(f"  Found {len(new_entries)} new entry(ies)")

        for entry in new_entries:
            print(f"\n  → Processing: {entry['name'][:50]}...")
            success = process_entry(entry)

            if success:
                processed_ids.add(entry['id'])
                save_processed_id(entry['id'])
                print(f"  ✓ Done: {entry['name'][:50]}")
            else:
                print(f"  ✗ Failed: {entry['name'][:50]}")

    except Exception as e:
        print(f"  Error: {e}")

def main():
    global processed_ids

    print("=" * 50)
    print("Transcript Pipeline Watcher")
    print(f"Polling every {POLL_INTERVAL} seconds")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    # Load previously processed IDs
    processed_ids = load_processed_ids()
    print(f"Loaded {len(processed_ids)} previously processed entries")

    # Initial check
    check_and_process()

    # Polling loop
    while True:
        time.sleep(POLL_INTERVAL)
        check_and_process()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStopped.")
