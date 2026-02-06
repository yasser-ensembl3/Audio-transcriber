import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

# ~4 chars per token, limit at 90K tokens = 360K chars
MAX_CHARS_PER_CHUNK = 360000

def count_words(text):
    """Count words in text"""
    return len(text.split())

def estimate_audio_minutes(word_count):
    """Estimate audio duration: ~150 words per minute spoken"""
    return word_count / 150

def get_summary_length(content_type, word_count):
    """Determine summary length based on type and content length"""
    if content_type in ["Youtube video", "Podcast"]:
        # Target: 20-30% of original duration
        # ~150 words/min spoken, so for 10-15 min summary we need 1500-2250 words
        original_minutes = estimate_audio_minutes(word_count)
        target_minutes = original_minutes * 0.25  # 25% of original
        target_words = int(target_minutes * 150)
        # Minimum 1500 words, maximum 3000 words
        target_words = max(1500, min(3000, target_words))
        return f"approximately {target_words} words (targeting {int(target_minutes)} minutes of audio)"
    elif content_type == "Article":
        # Proportional to article length
        if word_count < 500:
            return "approximately 150-250 words"
        elif word_count < 1500:
            return "approximately 400-600 words"
        elif word_count < 3000:
            return "approximately 600-1000 words"
        else:
            return "approximately 1000-1500 words"
    else:
        return "approximately 500-1000 words"

def chunk_content(content, max_chars=MAX_CHARS_PER_CHUNK):
    """Split content into chunks of max_chars"""
    if len(content) <= max_chars:
        return [content]

    chunks = []
    current_chunk = ""
    paragraphs = content.split('\n\n')

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_chars:
            current_chunk += para + '\n\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + '\n\n'

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def summarize_chunk(content, content_type, title, chunk_num, total_chunks, word_count, summary_length):
    """Summarize a single chunk of content using Claude Code CLI"""
    title_context = f"Title: {title}\n\n" if title else ""
    chunk_context = f"(Part {chunk_num}/{total_chunks})\n\n" if total_chunks > 1 else ""

    prompt = f"""You are an expert content summarizer. Create a clear and structured summary of the following content.

Content type: {content_type}
Original length: {word_count} words
Expected summary length: {summary_length}
{chunk_context}
{title_context}Content to summarize:
---
{content}
---

Instructions:
- Write in English
- Structure the summary with clear sections (use ## headings)
- Highlight key points and important insights
- Keep an informative and accessible tone
- Include notable quotes or examples if relevant
- This summary will be converted to audio, so make it flow naturally when read aloud
- End with main conclusions or takeaways

Summary:"""

    result = subprocess.run(
        ["/Users/mac/.local/bin/claude", "-p", prompt, "--dangerously-skip-permissions"],
        capture_output=True,
        text=True,
        timeout=300
    )

    if result.returncode != 0:
        raise Exception(f"Claude Code error: {result.stderr}")

    return result.stdout.strip()

def merge_summaries(summaries, title, content_type, target_length):
    """Merge multiple chunk summaries into one cohesive summary using Claude Code CLI"""
    combined = "\n\n---\n\n".join(summaries)

    prompt = f"""You have multiple partial summaries of the same content. Merge them into one cohesive, well-structured summary.

Title: {title}
Content type: {content_type}
Target length: {target_length}

Partial summaries to merge:
---
{combined}
---

Instructions:
- Create ONE unified summary, not a list of separate summaries
- Remove redundancy and repetition
- Maintain a logical flow and structure with ## headings
- Keep the most important insights from each part
- This will be converted to audio, so ensure it flows naturally
- Target the specified length

Merged Summary:"""

    result = subprocess.run(
        ["/Users/mac/.local/bin/claude", "-p", prompt, "--dangerously-skip-permissions"],
        capture_output=True,
        text=True,
        timeout=300
    )

    if result.returncode != 0:
        raise Exception(f"Claude Code error: {result.stderr}")

    return result.stdout.strip()

def summarize(content, content_type="Article", title=None):
    """Generate a summary of the content with Claude, handling chunking for long content"""
    word_count = count_words(content)
    summary_length = get_summary_length(content_type, word_count)

    chunks = chunk_content(content)
    print(f"Content split into {len(chunks)} chunk(s)")

    if len(chunks) == 1:
        return summarize_chunk(content, content_type, title, 1, 1, word_count, summary_length)

    # Summarize each chunk
    summaries = []
    for i, chunk in enumerate(chunks, 1):
        print(f"  Summarizing chunk {i}/{len(chunks)}...")
        chunk_summary = summarize_chunk(chunk, content_type, title, i, len(chunks), word_count, summary_length)
        summaries.append(chunk_summary)

    # Merge all summaries
    print("  Merging summaries...")
    return merge_summaries(summaries, title, content_type, summary_length)

def summarize_file(filepath, content_type="Article"):
    """Read a .md file and generate its summary"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract title from file (first # line)
    lines = content.split('\n')
    title = None
    for line in lines:
        if line.startswith('# '):
            title = line[2:].strip()
            break

    word_count = count_words(content)
    estimated_minutes = estimate_audio_minutes(word_count)
    print(f"Original content: {word_count} words (~{estimated_minutes:.1f} min audio)")

    summary = summarize(content, content_type, title)

    summary_words = count_words(summary)
    summary_minutes = estimate_audio_minutes(summary_words)

    # Save summary
    output_path = filepath.replace('.md', '_summary.md')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Summary: {title or 'Untitled'}\n\n")
        f.write(f"**Type:** {content_type}\n")
        f.write(f"**Original:** {word_count} words (~{estimated_minutes:.1f} min)\n")
        f.write(f"**Summary:** {summary_words} words (~{summary_minutes:.1f} min audio)\n")
        f.write(f"**Source:** {filepath}\n\n")
        f.write("---\n\n")
        f.write(summary)

    print(f"Summary saved: {output_path}")
    print(f"Summary length: {summary_words} words (~{summary_minutes:.1f} min audio)")
    return output_path, summary

if __name__ == "__main__":
    # Test avec le transcript YouTube généré
    test_file = "output/aVHMqoGtqKM_transcript.md"

    if os.path.exists(test_file):
        print(f"Test avec: {test_file}\n")
        output_path, summary = summarize_file(test_file, "Youtube video")
        print(f"\nRésumé ({count_words(summary)} mots):\n")
        print(summary[:1000] + "..." if len(summary) > 1000 else summary)
    else:
        print(f"Fichier non trouvé: {test_file}")
