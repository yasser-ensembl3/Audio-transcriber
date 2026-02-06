import os
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def detect_type_from_url(url):
    """Détecte le type de contenu à partir de l'URL"""
    url = url.lower()

    if "youtube.com" in url or "youtu.be" in url:
        return "Youtube video"
    elif "podcasts.apple.com" in url or "spotify.com/episode" in url or "podcast" in url:
        return "Podcast"
    else:
        return "Article"

def get_database_entries():
    """Récupère les entrées de la base de données Notion"""
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"

    response = requests.post(url, headers=headers)

    if response.status_code != 200:
        print(f"Erreur: {response.status_code}")
        print(response.text)
        return []

    return response.json().get("results", [])

def analyze_entries(entries):
    """Analyse les entrées et identifie celles à traiter"""
    to_process = []
    already_done = []

    for entry in entries:
        props = entry.get("properties", {})

        # Récupérer le titre (Link est le champ title)
        link_prop = props.get("Link", {})
        title_list = link_prop.get("title", [])
        name = title_list[0].get("plain_text", "Sans titre") if title_list else "Sans titre"

        # Récupérer Audio Link (peut contenir l'URL réelle)
        audio_link = props.get("Audio Link", {}).get("url", None)

        # Déterminer l'URL: si le titre est une URL, l'utiliser, sinon prendre Audio Link
        if name.startswith("http"):
            url = name
        else:
            url = audio_link

        # Récupérer le type (minuscule) ou détecter depuis l'URL
        type_prop = props.get("type", {})
        type_select = type_prop.get("select", {})
        content_type = type_select.get("name") if type_select else None

        # Si pas de type défini, détecter depuis l'URL
        if not content_type and url:
            content_type = detect_type_from_url(url)
        elif not content_type:
            content_type = "Article"

        # Vérifier Text summary (c'est un champ files, pas rich_text)
        summary_prop = props.get("Text summary", {})
        files = summary_prop.get("files", [])
        has_summary = len(files) > 0

        entry_info = {
            "id": entry.get("id"),
            "name": name,
            "url": url,
            "type": content_type,
            "has_summary": has_summary
        }

        if has_summary:
            already_done.append(entry_info)
        else:
            to_process.append(entry_info)

    return to_process, already_done

if __name__ == "__main__":
    print("Connexion à Notion...")
    entries = get_database_entries()
    print(f"Trouvé {len(entries)} entrées\n")

    to_process, already_done = analyze_entries(entries)

    print("=" * 50)
    print("À TRAITER (Text summary vide):")
    print("=" * 50)
    for item in to_process:
        print(f"  [{item['type']}] {item['name'][:50]}")
        print(f"    URL: {item['url']}")

    print(f"\nTotal à traiter: {len(to_process)}")

    print("\n" + "=" * 50)
    print("DÉJÀ TRAITÉS (Text summary rempli):")
    print("=" * 50)
    for item in already_done:
        print(f"  [{item['type']}] {item['name'][:50]}")

    print(f"\nTotal déjà traités: {len(already_done)}")
