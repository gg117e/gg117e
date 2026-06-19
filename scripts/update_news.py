import os
import re
import sys

import feedparser

README_PATH = "README.md"
GIGAZINE_RSS_URL = "https://gigazine.net/news/rss_2.0/"
NEWS_COUNT = 6
START_MARKER = "<!-- GIGAZINE-NEWS-START -->"
END_MARKER = "<!-- GIGAZINE-NEWS-END -->"


def get_gigazine_news():
    feed = feedparser.parse(GIGAZINE_RSS_URL)
    if not feed.entries:
        return None

    news_items = []
    for entry in feed.entries[:NEWS_COUNT]:
        news_items.append(f"- [{entry.title}]({entry.link})")

    return "\n".join(news_items)


def update_readme(news_content):
    if not os.path.exists(README_PATH):
        print(f"Error: {README_PATH} not found.")
        sys.exit(1)

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(f"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}", re.DOTALL)
    if not pattern.search(content):
        print("Markers not found in README.md")
        sys.exit(1)

    replacement = f"{START_MARKER}\n{news_content}\n{END_MARKER}"
    updated_content = pattern.sub(replacement, content)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print("README.md news section updated successfully.")


def main():
    try:
        news_content = get_gigazine_news()
    except Exception as e:
        print(f"Error fetching news: {e}")
        sys.exit(1)

    if not news_content:
        print("No news fetched.")
        sys.exit(1)

    update_readme(news_content)


if __name__ == "__main__":
    main()
