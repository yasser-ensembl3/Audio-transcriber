import os
import yt_dlp
from faster_whisper import WhisperModel

def sanitize_filename(title):
    """Remove invalid characters from filename"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        title = title.replace(char, '')
    return title[:100].strip()

def get_podcast_info(url):
    """Get podcast title and metadata using yt-dlp"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            'title': info.get('title', 'Untitled Podcast'),
            'channel': info.get('channel', info.get('uploader', 'Unknown')),
            'duration': info.get('duration', 0),
        }

def download_audio(url, output_dir="temp"):
    """Download audio from podcast URL using yt-dlp"""
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        audio_path = os.path.join(output_dir, f"{info['id']}.mp3")
        return audio_path, info.get('title', 'Untitled')

def transcribe_audio(audio_path, model_size="base"):
    """Transcribe audio using Whisper"""
    print(f"Loading Whisper model ({model_size})...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    print("Transcribing audio (this may take a while)...")
    segments, info = model.transcribe(audio_path, beam_size=5)

    print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")

    # Combine all segments
    transcript_text = ""
    for segment in segments:
        transcript_text += segment.text + " "

    return transcript_text.strip(), info.language

def transcript_to_markdown(transcript_text, url, title):
    """Convert transcript to markdown"""
    lines = []

    lines.append(f"# {title}\n")
    lines.append(f"**Source:** {url}\n")
    lines.append("---\n")

    # Format into paragraphs (every ~5 sentences)
    sentences = transcript_text.replace('\n', ' ').split('. ')
    paragraph = []
    for i, sentence in enumerate(sentences):
        paragraph.append(sentence.strip())
        if (i + 1) % 5 == 0:
            lines.append('. '.join(paragraph) + '.\n')
            paragraph = []

    if paragraph:
        lines.append('. '.join(paragraph))

    return '\n'.join(lines)

def save_podcast_transcript(url, output_dir="output", model_size="base"):
    """Download, transcribe and save podcast as .md"""
    os.makedirs(output_dir, exist_ok=True)

    # Get podcast info
    print("Fetching podcast info...")
    podcast_info = get_podcast_info(url)
    title = podcast_info['title']
    print(f"Title: {title}")

    # Download audio
    print("Downloading audio...")
    audio_path, _ = download_audio(url)
    print(f"Audio downloaded: {audio_path}")

    # Transcribe
    transcript_text, language = transcribe_audio(audio_path, model_size)

    # Create markdown
    markdown = transcript_to_markdown(transcript_text, url, title)

    # Save
    safe_title = sanitize_filename(title)
    filename = f"{safe_title}_transcript.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown)

    # Cleanup temp audio
    if os.path.exists(audio_path):
        os.remove(audio_path)

    print(f"Transcript saved: {filepath} (language: {language})")
    return filepath, title

if __name__ == "__main__":
    # Test with a podcast
    test_url = "https://podcasts.apple.com/ca/podcast/founders/id1141877104?i=1000745366626"
    print(f"Test with: {test_url}\n")

    try:
        filepath, title = save_podcast_transcript(test_url, model_size="base")
        print(f"\nContent (first 500 chars):")
        with open(filepath, 'r') as f:
            print(f.read()[:500])
    except Exception as e:
        print(f"Error: {e}")
