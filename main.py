from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import json
import time
import feedparser
import os

app = Flask(__name__)

# Path where JSON file will be saved
GRANTS_FILE = "/opt/render/project/src/grants.json"

# RSS Feeds for grant monitoring (Google Alerts)
RSS_FEEDS = [
    "https://www.google.com/alerts/feeds/15471598175210223981/1249085420698810313",
    "https://www.google.com/alerts/feeds/15471598175210223981/1413775523916636761",
    "https://www.google.com/alerts/feeds/15471598175210223981/13238716951020665409"
]

# URLs for Funds for NGOs categories
FUNDS_FOR_NGOS_CATEGORIES = [
    "https://www2.fundsforngos.org/category/civil-society/",
    "https://www2.fundsforngos.org/category/education/",
    "https://www2.fundsforngos.org/category/human-rights/",
    "https://www2.fundsforngos.org/category/information-technology/",
    "https://www2.fundsforngos.org/category/science-and-technology/",
    "https://www2.fundsforngos.org/category/peace-and-conflict-resolution/"
]

# Reddit search URLs for grants
REDDIT_GRANTS_URLS = [
    "https://www.reddit.com/r/grants/search.json?q=grant+opportunities&sort=new&restrict_sr=on",
    "https://www.reddit.com/r/nonprofit/search.json?q=grants&sort=new&restrict_sr=on"
]

HEADERS = {"User-Agent": "Mozilla/5.0"}

def scrape_fundsforngos(url):
    """Scrapes grant listings from Funds for NGOs pages."""
    print(f"Scraping: {url}")
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to fetch {url}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    grants = []

    for article in soup.find_all("article"):
        title_tag = article.find("h2", class_="entry-title")
        link_tag = title_tag.find("a") if title_tag else None
        excerpt_tag = article.find("div", class_="entry-summary")

        if title_tag and link_tag:
            grants.append({
                "title": title_tag.text.strip(),
                "link": link_tag["href"],
                "description": excerpt_tag.text.strip() if excerpt_tag else "No description",
                "source": "Funds for NGOs"
            })

    return grants

def scrape_reddit():
    """Scrapes latest grant-related posts from Reddit."""
    print("Scraping Reddit for grants...")
    grants = []

    for url in REDDIT_GRANTS_URLS:
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Failed to fetch {url}")
            continue

        data = response.json()
        for post in data["data"]["children"]:
            post_data = post["data"]
            grants.append({
                "title": post_data["title"],
                "link": f"https://www.reddit.com{post_data['permalink']}",
                "description": post_data.get("selftext", "No description"),
                "source": "Reddit"
            })

        time.sleep(2)  # Prevents hitting Reddit's rate limit

    return grants

def fetch_rss_feeds():
    """Fetches grant opportunities from Google Alerts RSS feeds."""
    print("Fetching RSS feeds...")
    grants = []

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            grants.append({
                "title": entry.title,
                "link": entry.link,
                "description": entry.summary if hasattr(entry, 'summary') else "No description",
                "source": "Google Alerts RSS"
            })

    return grants

@app.route("/run", methods=["GET"])
def run_scraper():
    """Runs the full scraping process and saves grants to a JSON file."""
    all_grants = []

    # Scrape Funds for NGOs
    for category_url in FUNDS_FOR_NGOS_CATEGORIES:
        all_grants.extend(scrape_fundsforngos(category_url))
        time.sleep(2)  # Prevents rate-limiting

    # Scrape Reddit
    all_grants.extend(scrape_reddit())

    # Fetch RSS feeds
    all_grants.extend(fetch_rss_feeds())

    # Save grants to a JSON file
    with open(GRANTS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_grants, f, indent=4)

    return jsonify({"message": "✅ Grants scraped and saved successfully", "file": GRANTS_FILE})

@app.route("/grants", methods=["GET"])
def get_grants():
    """Returns the saved grants JSON file."""
    if not os.path.exists(GRANTS_FILE):
        return jsonify({"error": "No grants data found. Run /run first."}), 500

    with open(GRANTS_FILE, "r", encoding="utf-8") as f:
        grants = json.load(f)

    return jsonify(grants)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)  # Runs Flask server on Render
