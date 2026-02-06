import os
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def update_text_summary(page_id, file_url, filename):
    """Update the 'Text summary' field in Notion with the Drive link"""
    url = f"https://api.notion.com/v1/pages/{page_id}"

    # Notion limits filename to 100 chars
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:100 - len(ext)] + ext

    # Text summary is a 'files' type field with external URL
    data = {
        "properties": {
            "Text summary": {
                "files": [
                    {
                        "name": filename,
                        "type": "external",
                        "external": {
                            "url": file_url
                        }
                    }
                ]
            }
        }
    }

    response = requests.patch(url, headers=headers, json=data)

    if response.status_code == 200:
        print(f"Notion updated: {filename}")
        return True
    else:
        print(f"Error updating Notion: {response.status_code}")
        print(response.text)
        return False

def update_audio_summary(page_id, file_url, filename):
    """Update the 'Audio summary' field in Notion with the Drive link"""
    url = f"https://api.notion.com/v1/pages/{page_id}"

    # Notion limits filename to 100 chars
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:100 - len(ext)] + ext

    # Audio summary is a 'files' type field with external URL
    data = {
        "properties": {
            "Audio summary": {
                "files": [
                    {
                        "name": filename,
                        "type": "external",
                        "external": {
                            "url": file_url
                        }
                    }
                ]
            }
        }
    }

    response = requests.patch(url, headers=headers, json=data)

    if response.status_code == 200:
        print(f"Notion audio updated: {filename}")
        return True
    else:
        print(f"Error updating Notion audio: {response.status_code}")
        print(response.text)
        return False


if __name__ == "__main__":
    # Test with a sample (won't actually run without valid page_id)
    print("Notion updater ready.")
    print("Usage: update_text_summary(page_id, file_url, filename)")
    print("Usage: update_audio_summary(page_id, file_url, filename)")
