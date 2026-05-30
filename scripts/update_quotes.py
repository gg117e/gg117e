import json
import datetime
import os
import re
import feedparser
import google.generativeai as genai

QUOTES_FILE = 'quotes.json'
README_FILE = 'README.md'
GIGAZINE_RSS_URL = "https://gigazine.net/news/rss_2.0/"
YAHOO_WORLD_NEWS_RSS_URL = "https://news.yahoo.co.jp/rss/topics/world.xml"

def load_quotes():
    with open(QUOTES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_todays_quote(quotes):
    # Use day of year to deterministically pick a quote
    # Using JST to ensure consistency with user's time
    jst = datetime.timezone(datetime.timedelta(hours=9))
    day_of_year = datetime.datetime.now(jst).timetuple().tm_yday
    # Ensure we don't go out of bounds
    index = day_of_year % len(quotes)
    return quotes[index]

def get_days_until_graduation():
    target_date = datetime.date(2028, 3, 31)
    jst = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now(jst).date()
    delta = target_date - today
    return delta.days

def generate_countdown_svg(days_left):
    """Generates SVG files for the graduation countdown (light and dark modes)."""

    # Common SVG template
    def get_svg(theme):
        if theme == 'dark':
            bg_fill = "#0d1117"
            bg_stroke = "#30363d"
            text_header = "#2f80ed"
            text_stat = "#c9d1d9"
            text_days = "#c9d1d9"
            text_desc = "#8b949e"
        else:
            bg_fill = "#fffefe"
            bg_stroke = "#e4e2e2"
            text_header = "#2f80ed"
            text_stat = "#333"
            text_days = "#333"
            text_desc = "#666"

        return f"""<svg width="495" height="195" viewBox="0 0 495 195" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style>
        .header {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: {text_header}; }}
        .stat {{ font: 600 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: {text_stat}; }}
        .days {{ font: 800 50px 'Segoe UI', Ubuntu, Sans-Serif; fill: {text_days}; }}
        .desc {{ font: 400 12px 'Segoe UI', Ubuntu, Sans-Serif; fill: {text_desc}; }}
        .bg {{ fill: {bg_fill}; stroke: {bg_stroke}; }}
    </style>
    <rect x="0.5" y="0.5" width="494" height="194" rx="4.5" class="bg" stroke-opacity="1"/>

    <text x="25" y="35" class="header">🎓 Graduation Countdown</text>

    <text x="247.5" y="100" text-anchor="middle" class="days">{days_left}</text>
    <text x="247.5" y="130" text-anchor="middle" class="stat">Days Left</text>

    <text x="25" y="170" class="desc">Until March 31, 2028</text>
</svg>
"""

    with open('graduation-light.svg', 'w', encoding='utf-8') as f:
        f.write(get_svg('light'))

    with open('graduation-dark.svg', 'w', encoding='utf-8') as f:
        f.write(get_svg('dark'))

def get_news_context():
    news_items = []

    urls = {
        "Gigazine": GIGAZINE_RSS_URL,
        "World News": YAHOO_WORLD_NEWS_RSS_URL,
        "Hatena IT": "https://b.hatena.ne.jp/hotentry/it.rss",
        "Hatena General": "https://b.hatena.ne.jp/hotentry/general.rss",
        "NHK News": "https://www.nhk.or.jp/rss/news/cat0.xml"
    }

    for source, url in urls.items():
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                entries = feed.entries[:5]
                for entry in entries:
                    title = entry.title
                    news_items.append(f"- [{source}] {title}")
        except Exception as e:
            print(f"Error fetching {source} news: {e}")

    if not news_items:
        return None

    return "\n".join(news_items)

def get_gigazine_news_formatted():
    try:
        feed = feedparser.parse(GIGAZINE_RSS_URL)
        if not feed.entries:
            return None

        entries = feed.entries[:3]
        news_items = []
        for entry in entries:
            title = entry.title
            link = entry.link
            news_items.append(f"- [{title}]({link})")

        return "\n".join(news_items)
    except Exception as e:
        print(f"Error fetching GIGAZINE news: {e}")
        return None

def generate_gemini_quote(news_context=None):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3-flash-preview')

    context_str = ""
    if news_context:
        context_str = f"以下は最近のニュース見出しです。これらを参考に現在の世界情勢を把握してください:\n{news_context}\n\n"

    prompt = (
        f"{context_str}"
        "あなたは賢者です。現在の世界の情勢（GIGAZINEや国際ニュース、技術トレンドなど）、生命の価値観、人としての生き方を深く考慮し、"
        "今を生きる私たちに向けた短く心に響く格言・アドバイスを日本語で作成してください。"
        "この処理は12時間ごとに実行されます。直近のニュースの多様なトピックからインスピレーションを得て、マンネリ化を防いでください。"
        "格言の長さは100字程度を目安にしてください。"
        "また、その英語訳も提供してください。"
        "結果は以下のキーを持つJSONオブジェクトとして出力してください: "
        "'quote' (日本語のテキスト), 'translation' (英語のテキスト), 'author' (固定値 'Gemini')。"
        "JSON以外のテキストは出力しないでください。"
    )

    response = model.generate_content(prompt)

    # Simple cleanup to handle potential markdown code blocks in response
    text = response.text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]

    return json.loads(text.strip())

def update_readme(new_quote):
    if not os.path.exists(README_FILE):
        print(f"Error: {README_FILE} not found.")
        return

    with open(README_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define markers
    daily_start = '<!-- DAILY-QUOTE-START -->'
    daily_end = '<!-- DAILY-QUOTE-END -->'
    grad_start = '<!-- GRADUATION-COUNTDOWN-START -->'
    grad_end = '<!-- GRADUATION-COUNTDOWN-END -->'
    news_start = '<!-- GIGAZINE-NEWS-START -->'
    news_end = '<!-- GIGAZINE-NEWS-END -->'

    # Regex patterns
    daily_pattern = re.compile(f'({re.escape(daily_start)})(.*?)({re.escape(daily_end)})', re.DOTALL)
    grad_pattern = re.compile(f'({re.escape(grad_start)})(.*?)({re.escape(grad_end)})', re.DOTALL)
    news_pattern = re.compile(f'({re.escape(news_start)})(.*?)({re.escape(news_end)})', re.DOTALL)

    daily_match = daily_pattern.search(content)
    grad_match = grad_pattern.search(content)
    news_match = news_pattern.search(content)

    if not daily_match:
        print("Error: Daily quote markers not found in README.md.")
        return
    # Format new daily quote
    # Using a specific delimiter structure to make parsing easier later
    new_daily_content = f"\n> {new_quote['quote']}\n>\n> {new_quote['translation']}\n>\n> — **{new_quote['author']}**\n"

    # Update Daily Section
    daily_match_new = daily_pattern.search(content)
    if daily_match_new:
        content = content.replace(daily_match_new.group(0), f"{daily_start}{new_daily_content}{daily_end}")

    # Update Graduation Countdown
    if grad_match:
        days_left = get_days_until_graduation()
        generate_countdown_svg(days_left)

        grad_content = f"""
## 🎓 Days until Graduation

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="graduation-dark.svg">
  <img alt="Graduation Countdown" src="graduation-light.svg">
</picture>
"""

        # We need to find the match again in case content changed (though unlikely to overlap with graduation section)
        # But for safety, we can just replace the original match string if it was unique, or regex search again.
        # Since graduation section is separate, searching again is safer.
        grad_match_new = grad_pattern.search(content)
        if grad_match_new:
            content = content.replace(grad_match_new.group(0), f"{grad_start}{grad_content}{grad_end}")
    else:
        print("Warning: Graduation countdown markers not found in README.md.")

    # Update GIGAZINE News
    if news_match:
        news_content = get_gigazine_news_formatted()
        if news_content:
            formatted_news = f"\n{news_content}\n"
            # Search again because content has changed
            news_match_new = news_pattern.search(content)
            if news_match_new:
                 content = content.replace(news_match_new.group(0), f"{news_start}{formatted_news}{news_end}")
            print("Updated GIGAZINE news.")
        else:
            print("No news fetched, skipping update.")
    else:
        print("Warning: GIGAZINE news markers not found in README.md.")

    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Updated daily quote to: {new_quote['quote']}")

def main():
    gemini_quote = None
    if os.environ.get("GEMINI_API_KEY"):
         try:
             news_context = get_news_context()
             gemini_quote = generate_gemini_quote(news_context)
         except Exception as e:
             print(f"Gemini generation failed: {e}")

    if gemini_quote:
        todays_quote = gemini_quote
    else:
        if not os.path.exists(QUOTES_FILE):
            print(f"{QUOTES_FILE} not found.")
            return

        try:
            quotes = load_quotes()
            todays_quote = get_todays_quote(quotes)
        except Exception as e:
            print(f"Error loading local quotes: {e}")
            return

    try:
        update_readme(todays_quote)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
