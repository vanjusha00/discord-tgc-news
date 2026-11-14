
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

        if "/en/news/" not in href:
            continue

        title = " ".join(link.get_text(" ", strip=True).split())

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

def main():
    sent = load_sent()
    articles = get_articles()

    if not articles:
        print("Nessun articolo trovato.")
        return

    new_articles = [
        article for article in reversed(articles)
        if article["url"] not in sent
    ]

    # Al primo avvio registra gli articoli esistenti
    # senza pubblicare tutte le notizie arretrate.
    if not sent:
        sent.update(article["url"] for article in articles)
        save_sent(sent)
        print("Prima scansione completata.")
        return

    for article in new_articles:
        publish(article)
        sent.add(article["url"])
        print("Pubblicato:", article["title"])

    save_sent(sent)

if __name__ == "__main__":
    main()
