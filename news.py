
import os
import json
import requests
from bs4 import BeautifulSoup

NEWS_URL = "https://magic.wizards.com/en/news"
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
STATE_FILE = "sent_articles.json"

def load_sent():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            return set(json.load(file))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_sent(sent):
    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(list(sent), file, ensure_ascii=False, indent=2)

def get_articles():
    response = requests.get(
        NEWS_URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    seen = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]
        title = " ".join(link.get_text(" ", strip=True).split())

        if "/en/news/" not in href:
            continue

        if not title or len(title) < 8:
            continue

        if href.startswith("/"):
            href = "https://magic.wizards.com" + href

        if href in seen:
            continue

        seen.add(href)
        articles.append({
            "title": title,
            "url": href
        })

    return articles[:10]

def publish(article):
    payload = {
        "embeds": [{
            "title": article["title"][:256],
            "url": article["url"],
            "color": 7506394,
            "footer": {
                "text": "DailyMTG • Wizards of the Coast"
            }
        }]
    }

    response = requests.post(
        WEBHOOK_URL,
        json=payload,
        timeout=30
    )
    response.raise_for_status()
    print("PUBBLICATO:", article["title"])

def main():
    print("Avvio controllo DailyMTG...")

    sent = load_sent()
    articles = get_articles()

    print("Articoli individuati:", len(articles))
    print("Articoli già registrati:", len(sent))

    if not articles:
        print("ATTENZIONE: nessun articolo individuato.")
        return

    new_articles = [
        article for article in reversed(articles)
        if article["url"] not in sent
    ]

    print("Nuovi articoli:", len(new_articles))

    for article in new_articles:
        publish(article)
        sent.add(article["url"])

    save_sent(sent)
    print("Controllo completato.")

if __name__ == "__main__":
    main()
