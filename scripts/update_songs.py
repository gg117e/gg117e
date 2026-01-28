import yt_dlp
import random
import re
import os
import sys

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PL3nJaaGwM6uqVvZVt-Lo-xBsCgXc1BbGe"
README_PATH = "README.md"
START_MARKER = "<!-- YOUTUBE-SONGS-START -->"
END_MARKER = "<!-- YOUTUBE-SONGS-END -->"

def get_playlist_items(url):
    ydl_opts = {
        'extract_flat': True,
        'dump_single_json': True,
        'quiet': True,
        'ignoreerrors': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(url, download=False)
        if 'entries' in result:
            return result['entries']
    return []

def update_readme(songs):
    if not os.path.exists(README_PATH):
        print(f"Error: {README_PATH} not found.")
        sys.exit(1)

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    parts = []
    parts.append("### 🎵 Daily Recommended Songs\n\n")
    parts.append("<table>\n")
    parts.append("  <tr>\n")

    # Thumbnails
    for song in songs:
        title = song.get('title', 'Unknown Title')
        video_id = song.get('id')
        url = song.get('url', '#')

        if not url.startswith('http') and video_id:
             url = f"https://www.youtube.com/watch?v={video_id}"

        # Try to find a thumbnail
        thumb_url = ""
        thumbnails = song.get('thumbnails', [])
        if thumbnails:
             # Prefer medium quality
             thumb_url = thumbnails[-1]['url']
        elif video_id:
             thumb_url = f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"

        # Fallback if still empty (shouldn't happen with valid ID)
        if not thumb_url:
            thumb_url = "https://via.placeholder.com/200x150?text=No+Image"

        parts.append(f"    <td align='center'>\n")
        parts.append(f"      <a href='{url}'>\n")
        parts.append(f"        <img src='{thumb_url}' width='200px' alt='{title}'>\n")
        parts.append(f"      </a>\n")
        parts.append(f"      <br />\n")
        parts.append(f"      <a href='{url}'>{title}</a>\n")
        parts.append(f"    </td>\n")

    parts.append("  </tr>\n")
    parts.append("</table>\n")
    new_content = "".join(parts)

    # Replace content between markers
    pattern = re.compile(f"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}", re.DOTALL)

    if not pattern.search(content):
        print("Markers not found in README.md")
        sys.exit(1)

    replacement = f"{START_MARKER}\n{new_content}\n{END_MARKER}"
    updated_content = pattern.sub(replacement, content)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated_content)
    print("README.md updated successfully.")

def main():
    print("Fetching playlist...")
    try:
        entries = get_playlist_items(PLAYLIST_URL)
        print(f"Found {len(entries)} songs.")
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        sys.exit(1)

    if not entries:
        print("No entries found.")
        sys.exit(1)

    valid_entries = [e for e in entries if e and e.get('title') != '[Private video]']

    if len(valid_entries) < 3:
        selected_songs = valid_entries
    else:
        selected_songs = random.sample(valid_entries, 3)

    print(f"Selected: {[s.get('title') for s in selected_songs]}")
    update_readme(selected_songs)

if __name__ == "__main__":
    main()
