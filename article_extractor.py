import os
import trafilatura
from urllib.parse import urlparse

def sanitize_filename(title):
    """Remove invalid characters from filename"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        title = title.replace(char, '')
    return title[:100].strip()

def extract_article(url):
    """Extrait le contenu textuel d'un article web"""
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise Exception(f"Impossible de télécharger: {url}")

    # Extraire le texte avec métadonnées
    result = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=True,
        output_format='txt'
    )

    # Récupérer les métadonnées séparément
    metadata = trafilatura.extract_metadata(downloaded)

    return result, metadata

def article_to_markdown(content, url, metadata=None):
    """Convertit l'article en markdown"""
    lines = []

    # Titre
    title = metadata.title if metadata and metadata.title else "Article"
    lines.append(f"# {title}\n")

    # Métadonnées
    if metadata:
        if metadata.author:
            lines.append(f"**Auteur:** {metadata.author}")
        if metadata.date:
            lines.append(f"**Date:** {metadata.date}")

    lines.append(f"**Source:** {url}\n")
    lines.append("---\n")

    # Contenu
    if content:
        lines.append(content)
    else:
        lines.append("*Contenu non disponible*")

    return '\n'.join(lines)

def save_article(url, output_dir="output"):
    """Extract and save article as .md with article title"""
    os.makedirs(output_dir, exist_ok=True)

    print("Fetching article...")
    content, metadata = extract_article(url)

    # Get title from metadata
    title = metadata.title if metadata and metadata.title else "Untitled Article"
    print(f"Title: {title}")

    markdown = article_to_markdown(content, url, metadata)

    # Filename based on article title
    safe_title = sanitize_filename(title)
    filename = f"{safe_title}_article.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"Article saved: {filepath}")
    return filepath, title

if __name__ == "__main__":
    # Test with an article from Notion DB
    test_url = "https://sharptext.net/2025/the-definitive-ranking-of-tech-company-takeability/"
    print(f"Test with: {test_url}\n")

    try:
        filepath, title = save_article(test_url)
        print(f"\nContent (first 500 chars):")
        with open(filepath, 'r') as f:
            print(f.read()[:500])
    except Exception as e:
        print(f"Error: {e}")
