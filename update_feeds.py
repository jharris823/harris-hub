"""Harris Hub public headline updater.
Free RSS feeds, automatic retries, and backup sources.
"""

import datetime
import email.utils
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

QUERIES = {
    "comics": [
        "Golden Age comic books auction Batman Wonder Woman",
        "comic book collecting vintage price guide",
    ],
    "research": [
        "global health politics health policy governance",
        "health technology assessment policy diffusion",
        "Thailand health policy universal coverage",
    ],
    "scifi": [
        "science fiction TV series premiere renewal",
        "new science fiction books post apocalyptic",
    ],
    "sports": [
        "college football SEC Big Ten AP top 25 Wisconsin LSU",
    ],
    "lastz": [
        "Last Z Survival Shooter updates redeem codes",
    ],
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (HarrisHub/2.0; RSS reader)",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

def fetch(url):
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=20) as response:
                return response.read(2_000_000)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"Attempt {attempt + 1} failed: {exc}")
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
    return None

def parse_rss(data, fallback_source):
    results = []
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        print("RSS parsing error:", exc)
        return results

    for item in root.findall("./channel/item")[:12]:
        title = html.unescape(item.findtext("title", "")).strip()
        link = item.findtext("link", "").strip()
        date = item.findtext("pubDate", "").strip()
        source = item.findtext("source", fallback_source)

        if title and link.startswith(("https://", "http://")):
            results.append({
                "title": title[:220],
                "url": link,
                "date": date[:35],
                "source": source[:80],
            })
    return results

def collect(query):
    encoded = urllib.parse.quote(query)

    sources = [
        (
            "Google News",
            "https://news.google.com/rss/search?q="
            + encoded + "&hl=en-US&gl=US&ceid=US:en",
        ),
        (
            "Bing News",
            "https://www.bing.com/news/search?q="
            + encoded + "&format=rss",
        ),
    ]

    for name, url in sources:
        print("Trying", name, "for:", query)
        data = fetch(url)

        if data:
            results = parse_rss(data, name)
            if results:
                print("Retrieved", len(results), "from", name)
                return results

        print(name, "unavailable or returned no articles")

    return []

def main():
    path = Path(__file__).parent / "data" / "feeds.json"
    previous = {}

    if path.exists():
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass

    previous_feeds = previous.get("feeds", {})
    feeds = {}
    new_count = 0

    for category, queries in QUERIES.items():
        articles = []
        seen = set()

        for query in queries:
            for article in collect(query):
                key = re.sub(
                    r"\W+", "", article["title"].lower()
                )[:100]

                if key and key not in seen:
                    articles.append(article)
                    seen.add(key)

            time.sleep(1)

        if articles:
            feeds[category] = articles[:12]
            new_count += len(feeds[category])
        else:
            feeds[category] = previous_feeds.get(category, [])[:12]
            print("Retaining previous articles for:", category)

    print("Final counts:", {k: len(v) for k, v in feeds.items()})

    if new_count == 0:
        print("WARNING: No new headlines retrieved from any source.")
        if not any(feeds.values()):
            raise RuntimeError(
                "All news sources failed and no previous headlines exist."
            )

    path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now(
        datetime.timezone.utc
    ).strftime("%Y-%m-%d %H:%M UTC")

    if new_count == 0 and previous.get("updated"):
        timestamp = previous["updated"]

    path.write_text(
        json.dumps(
            {"updated": timestamp, "feeds": feeds},
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    print("Harris Hub feed update finished.")

if __name__ == "__main__":
    main()
