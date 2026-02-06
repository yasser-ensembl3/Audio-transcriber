#!/usr/bin/env python3
"""
Text-to-Speech audio generation using Edge TTS (free).
"""

import asyncio
import edge_tts
import os

# Good quality English voices
VOICES = {
    "aria": "en-US-AriaNeural",      # Female, conversational
    "guy": "en-US-GuyNeural",        # Male, conversational
    "jenny": "en-US-JennyNeural",    # Female, clear
    "davis": "en-US-DavisNeural",    # Male, calm
}

# Default voice
DEFAULT_VOICE = "en-US-AriaNeural"


async def _generate_audio(text: str, output_path: str, voice: str = DEFAULT_VOICE):
    """Generate audio from text using Edge TTS"""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def generate_audio(text: str, output_path: str, voice: str = DEFAULT_VOICE) -> str:
    """
    Convert text to audio file.

    Args:
        text: The text to convert to speech
        output_path: Path for the output MP3 file
        voice: Voice ID to use (default: en-US-AriaNeural)

    Returns:
        Path to the generated audio file
    """
    asyncio.run(_generate_audio(text, output_path, voice))
    return output_path


def generate_audio_from_summary(summary_path: str, voice: str = DEFAULT_VOICE) -> str:
    """
    Generate audio from a summary markdown file.

    Args:
        summary_path: Path to the summary .md file
        voice: Voice ID to use

    Returns:
        Path to the generated audio file
    """
    # Read the summary
    with open(summary_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove markdown metadata header (everything before first ---)
    if '---' in content:
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2].strip()

    # Clean markdown for better speech
    # Remove headers markers but keep text
    lines = []
    for line in content.split('\n'):
        if line.startswith('#'):
            line = line.lstrip('#').strip()
        lines.append(line)
    content = '\n'.join(lines)

    # Generate output path
    audio_path = summary_path.replace('_summary.md', '_audio.mp3')

    print(f"Generating audio ({len(content)} chars)...")
    generate_audio(content, audio_path, voice)

    # Get file size
    size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    print(f"Audio saved: {audio_path} ({size_mb:.1f} MB)")

    return audio_path


def list_voices():
    """List available voices"""
    async def _list():
        voices = await edge_tts.list_voices()
        return [v for v in voices if v['Locale'].startswith('en-')]

    return asyncio.run(_list())


if __name__ == "__main__":
    # Test with a sample
    test_text = """
    Welcome to this audio summary. Today we'll explore the key insights
    from the content. This is a test of the Edge TTS system, which provides
    natural sounding speech synthesis completely free of charge.
    """

    output = "output/test_audio.mp3"
    print(f"Generating test audio...")
    generate_audio(test_text, output)
    print(f"Done: {output}")
