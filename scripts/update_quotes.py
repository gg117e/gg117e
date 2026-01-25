import json
import datetime
import os
import re

QUOTES_FILE = 'quotes.json'
README_FILE = 'README.md'

def load_quotes():
    with open(QUOTES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_todays_quote(quotes):
    # Use day of year to deterministically pick a quote
    # Using UTC to ensure consistency across environments
    day_of_year = datetime.datetime.now(datetime.timezone.utc).timetuple().tm_yday
    # Ensure we don't go out of bounds
    index = day_of_year % len(quotes)
    return quotes[index]

def get_days_until_graduation():
    target_date = datetime.date(2028, 3, 31)
    today = datetime.datetime.now(datetime.timezone.utc).date()
    delta = target_date - today
    return delta.days

def update_readme(new_quote):
    if not os.path.exists(README_FILE):
        print(f"Error: {README_FILE} not found.")
        return

    with open(README_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define markers
    daily_start = '<!-- DAILY-QUOTE-START -->'
    daily_end = '<!-- DAILY-QUOTE-END -->'
    log_start = '<!-- QUOTE-LOG-START -->'
    log_end = '<!-- QUOTE-LOG-END -->'
    grad_start = '<!-- GRADUATION-COUNTDOWN-START -->'
    grad_end = '<!-- GRADUATION-COUNTDOWN-END -->'

    # Regex patterns
    daily_pattern = re.compile(f'({re.escape(daily_start)})(.*?)({re.escape(daily_end)})', re.DOTALL)
    log_pattern = re.compile(f'({re.escape(log_start)})(.*?)({re.escape(log_end)})', re.DOTALL)
    grad_pattern = re.compile(f'({re.escape(grad_start)})(.*?)({re.escape(grad_end)})', re.DOTALL)

    daily_match = daily_pattern.search(content)
    log_match = log_pattern.search(content)
    grad_match = grad_pattern.search(content)

    if not daily_match:
        print("Error: Daily quote markers not found in README.md.")
        return
    if not log_match:
        print("Error: Quote log markers not found in README.md.")
        return

    current_daily_content = daily_match.group(2)

    # Format new daily quote
    # Using a specific delimiter structure to make parsing easier later
    new_daily_content = f"\n> {new_quote['quote']}\n>\n> {new_quote['translation']}\n>\n> — **{new_quote['author']}**\n"

    updated_log_content = log_match.group(2)

    # Logic: If current content exists AND it's not the same as the new one, add to log.
    if current_daily_content and current_daily_content.strip() and current_daily_content.strip() != new_daily_content.strip():
        # Try to parse the previous quote
        try:
            # Expected format:
            # > Quote...
            # >
            # > Translation...
            # >
            # > — **Author**

            # Split by the empty quote lines used as spacers
            parts = current_daily_content.strip().split('\n>\n> ')

            if len(parts) == 3:
                # Part 1: Quote (remove leading '> ')
                quote_part = parts[0].replace('>', '', 1).strip()
                # Part 2: Translation
                trans_part = parts[1].strip()
                # Part 3: Author (remove '— **' and '**')
                author_part = parts[2].strip()
                if author_part.startswith('— '):
                    author_part = author_part[2:]
                author_part = author_part.replace('**', '')

                log_entry = f"- \"{quote_part}\" ({trans_part}) - **{author_part}**"

                # Avoid duplicates in log
                if log_entry not in updated_log_content:
                    if not updated_log_content.strip():
                        updated_log_content = f"\n{log_entry}\n"
                    else:
                        updated_log_content = updated_log_content.rstrip() + f"\n{log_entry}\n"
            else:
                print("Warning: Could not parse previous quote format. Skipping log update for it.")
        except Exception as e:
            print(f"Warning: Error parsing previous quote: {e}")

    # Update Log Section First (replace content between markers)
    # We reconstruct the file content to handle replacements safely

    # Update the content variable with the new log
    # We need to find the match again or use the indices from the previous match?
    # String replacement is safe if markers are unique.
    content = content.replace(log_match.group(0), f"{log_start}{updated_log_content}{log_end}")

    # Update Daily Section
    # Note: Regex match object is based on original string.
    # Since we modified 'content', the daily_match indices are no longer valid if the log appeared BEFORE the daily section
    # and the length changed.
    # However, usually Daily is top, Log is bottom.
    # But to be safe, let's re-run the search or use replace on the string key.

    # Simple string replace of the *entire* old block with new block
    # This works regardless of position as long as the old block text is unique enough or we use the markers.

    # Using markers + old content to replace might be risky if we just modified it?
    # No, we modified 'content' variable.
    # We just replaced the LOG block. The DAILY block is untouched in 'content'.
    # We can search for the DAILY block again in the *new* content variable.

    daily_match_new = daily_pattern.search(content)
    if daily_match_new:
        content = content.replace(daily_match_new.group(0), f"{daily_start}{new_daily_content}{daily_end}")

    # Update Graduation Countdown
    if grad_match:
        days_left = get_days_until_graduation()
        grad_content = f"\n## 🎓 Days until Graduation\n\n**{days_left}** days left until March 31, 2028!\n"
        # We need to find the match again in case content changed (though unlikely to overlap with graduation section)
        # But for safety, we can just replace the original match string if it was unique, or regex search again.
        # Since graduation section is separate, searching again is safer.
        grad_match_new = grad_pattern.search(content)
        if grad_match_new:
            content = content.replace(grad_match_new.group(0), f"{grad_start}{grad_content}{grad_end}")
    else:
        print("Warning: Graduation countdown markers not found in README.md.")

    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Updated daily quote to: {new_quote['quote']}")

def main():
    if not os.path.exists(QUOTES_FILE):
        print(f"{QUOTES_FILE} not found.")
        return

    try:
        quotes = load_quotes()
        todays_quote = get_todays_quote(quotes)
        update_readme(todays_quote)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
