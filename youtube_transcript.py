import re
import os
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

def get_video_info(video_url):
    """Get video title and metadata using yt-dlp"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return {
            'title': info.get('title', 'Untitled'),
            'channel': info.get('channel', info.get('uploader', 'Unknown')),
            'duration': info.get('duration', 0),
        }

def sanitize_filename(title):
    """Remove invalid characters from filename"""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        title = title.replace(char, '')
    # Limit length and strip
    return title[:100].strip()

def extract_video_id(url):
    """Extrait l'ID de la vidéo depuis une URL YouTube"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_transcript(video_url, languages=['fr', 'en']):
    """Récupère le transcript d'une vidéo YouTube"""
    video_id = extract_video_id(video_url)
    if not video_id:
        raise ValueError(f"Impossible d'extraire l'ID de la vidéo: {video_url}")

    try:
        api = YouTubeTranscriptApi()

        # Essayer de récupérer directement avec les langues préférées
        try:
            transcript = api.fetch(video_id, languages=languages)
            return transcript.snippets, transcript.language_code
        except:
            pass

        # Sinon, lister et prendre le premier disponible
        transcript_list = api.list(video_id)
        for transcript in transcript_list:
            data = transcript.fetch()
            return data.snippets, data.language_code

        raise Exception("Aucun transcript disponible")

    except Exception as e:
        raise Exception(f"Erreur lors de la récupération du transcript: {e}")

def transcript_to_markdown(transcript_data, video_url, title=None):
    """Convertit le transcript en markdown"""
    lines = []

    if title:
        lines.append(f"# {title}\n")
    else:
        lines.append(f"# Transcript\n")

    lines.append(f"**Source:** {video_url}\n")
    lines.append("---\n")

    # Combiner le texte du transcript
    full_text = ""
    for entry in transcript_data:
        text = entry.text.strip() if entry.text else ''
        if text:
            full_text += text + " "

    # Formater en paragraphes (environ toutes les 5 phrases)
    sentences = full_text.replace('\n', ' ').split('. ')
    paragraph = []
    for i, sentence in enumerate(sentences):
        paragraph.append(sentence.strip())
        if (i + 1) % 5 == 0:
            lines.append('. '.join(paragraph) + '.\n')
            paragraph = []

    if paragraph:
        lines.append('. '.join(paragraph))

    return '\n'.join(lines)

def save_transcript(video_url, output_dir="output"):
    """Get and save transcript as .md with video title"""
    os.makedirs(output_dir, exist_ok=True)

    # Get video info (title, channel, etc.)
    print("Fetching video info...")
    video_info = get_video_info(video_url)
    title = video_info['title']
    print(f"Title: {title}")

    transcript_data, lang = get_transcript(video_url)
    markdown = transcript_to_markdown(transcript_data, video_url, title)

    # Filename based on video title
    safe_title = sanitize_filename(title)
    filename = f"{safe_title}_transcript.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"Transcript saved: {filepath} (language: {lang})")
    return filepath, title

if __name__ == "__main__":
    # Test with a video
    test_url = "https://youtube.com/watch?v=aVHMqoGtqKM"
    print(f"Test with: {test_url}\n")

    try:
        filepath, title = save_transcript(test_url)
        print(f"\nContent (first 500 chars):")
        with open(filepath, 'r') as f:
            print(f.read()[:500])
    except Exception as e:
        print(f"Error: {e}")
