import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request

USERNAME = "gg117e"
README_PATH = "README.md"
START_MARKER = "<!-- PUBLIC-REPOS-START -->"
END_MARKER = "<!-- PUBLIC-REPOS-END -->"
API_URL = f"https://api.github.com/users/{USERNAME}/repos"


def fetch_public_repositories():
    repositories = []
    page = 1

    while True:
        query = urllib.parse.urlencode(
            {
                "type": "owner",
                "sort": "updated",
                "direction": "desc",
                "per_page": 100,
                "page": page,
            }
        )
        request = urllib.request.Request(
            f"{API_URL}?{query}",
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "gg117e-readme-updater",
            },
        )

        token = os.environ.get("GITHUB_TOKEN")
        if token:
            request.add_header("Authorization", f"Bearer {token}")

        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.load(response)

        if not data:
            break

        repositories.extend(repo for repo in data if not repo.get("private"))

        if len(data) < 100:
            break
        page += 1

    return repositories


def repository_card(repository):
    name = repository["name"]
    repo_url = html.escape(repository["html_url"], quote=True)
    alt = html.escape(name, quote=True)
    card_query = urllib.parse.urlencode(
        {
            "username": USERNAME,
            "repo": name,
            "theme": "github_dark_dimmed",
            "hide_border": "true",
            "show_owner": "false",
        }
    )
    card_url = f"https://github-readme-stats.vercel.app/api/pin/?{card_query}"

    return f'  <a href="{repo_url}"><img width="420" alt="{alt}" src="{card_url}"></a>'


def render_repositories(repositories):
    if not repositories:
        return "No public repositories yet."

    cards = "\n".join(repository_card(repository) for repository in repositories)
    return f'<p align="center">\n{cards}\n</p>'


def update_readme(repository_content):
    if not os.path.exists(README_PATH):
        print(f"Error: {README_PATH} not found.")
        sys.exit(1)

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(f"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}", re.DOTALL)
    if not pattern.search(content):
        print("Repository markers not found in README.md")
        sys.exit(1)

    replacement = f"{START_MARKER}\n{repository_content}\n{END_MARKER}"
    updated_content = pattern.sub(replacement, content)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print("README.md public repository section updated successfully.")


def main():
    try:
        repositories = fetch_public_repositories()
    except Exception as e:
        print(f"Error fetching repositories: {e}")
        sys.exit(1)

    update_readme(render_repositories(repositories))


if __name__ == "__main__":
    main()
