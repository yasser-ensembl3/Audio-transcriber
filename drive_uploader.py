import os
import pickle
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/drive.file']
GDRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID")
GDRIVE_CREDENTIALS_PATH = os.getenv("GDRIVE_CREDENTIALS_PATH", "credentials.json")

def get_drive_service():
    """Authenticate and return Google Drive service"""
    creds = None

    # Token from previous auth
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If no valid creds, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(GDRIVE_CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"{GDRIVE_CREDENTIALS_PATH} not found. Download it from Google Cloud Console:\n"
                    "1. Go to https://console.cloud.google.com/apis/credentials\n"
                    "2. Create OAuth 2.0 Client ID (Desktop app)\n"
                    "3. Download and save as credentials.json (or set GDRIVE_CREDENTIALS_PATH in .env)"
                )
            flow = InstalledAppFlow.from_client_secrets_file(GDRIVE_CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=8080)

        # Save token for next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def get_mimetype(filepath):
    """Detect MIME type based on file extension"""
    ext = os.path.splitext(filepath)[1].lower()
    mimetypes = {
        '.md': 'text/markdown',
        '.txt': 'text/plain',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.m4a': 'audio/mp4',
        '.pdf': 'application/pdf',
    }
    return mimetypes.get(ext, 'application/octet-stream')


def upload_to_drive(filepath, folder_id=None):
    """Upload a file to Google Drive and return the shareable link"""
    if folder_id is None:
        folder_id = GDRIVE_FOLDER_ID

    service = get_drive_service()

    filename = os.path.basename(filepath)
    mimetype = get_mimetype(filepath)

    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }

    media = MediaFileUpload(filepath, mimetype=mimetype, resumable=True)

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()

    file_id = file.get('id')
    web_link = file.get('webViewLink')

    # Make file accessible via link
    service.permissions().create(
        fileId=file_id,
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()

    print(f"Uploaded: {filename}")
    print(f"Link: {web_link}")

    return file_id, web_link

if __name__ == "__main__":
    # Test upload
    test_file = "output/aVHMqoGtqKM_transcript_summary.md"

    if os.path.exists(test_file):
        print(f"Uploading: {test_file}\n")
        try:
            file_id, link = upload_to_drive(test_file)
            print(f"\nSuccess! File ID: {file_id}")
        except FileNotFoundError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"File not found: {test_file}")
