#!/usr/bin/env python3
"""Update only the profile's star counts and successful refresh date.

Uses repository metadata, never stargazer lists or user activity. All requests
must succeed before README.md is written; failures leave the last snapshot intact.
Run locally with Python 3.10+: python3 scripts/update_stars.py
GITHUB_TOKEN is optional for public repositories and supplied by Actions.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

README = Path(__file__).resolve().parents[1] / "README.md"
STARS = re.compile(
    r"(?P<start><!-- stars:(?P<repo>yuxino/[A-Za-z0-9_.-]+) -->)"
    r"[0-9][0-9,]*(?P<end><!-- /stars -->)"
)
UPDATED = re.compile(
    r"(?P<start><!-- stars-updated -->).*?(?P<end><!-- /stars-updated -->)"
)


def fetch_stars(repo: str) -> int:
    """Read the aggregate count for one explicitly listed public repository."""
    if not re.fullmatch(r"yuxino/[A-Za-z0-9_.-]+", repo):
        raise ValueError("Unexpected repository name")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "yuxino-profile-stars",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.github.com/repos/{repo}", headers=headers)
    for attempt in range(3):
        try:
            with urlopen(request, timeout=15) as response:
                data = json.load(response)
            if not isinstance(data, dict):
                raise ValueError(f"Invalid repository response: {repo}")
            count = data.get("stargazers_count")
            if (
                data.get("private") is not False
                or str(data.get("full_name", "")).lower() != repo.lower()
                or type(count) is not int
                or count < 0
            ):
                raise ValueError(f"Invalid public star count: {repo}")
            return count
        except HTTPError as error:
            if attempt == 2 or (error.code != 429 and error.code < 500):
                raise RuntimeError(f"GitHub returned HTTP {error.code} for {repo}") from error
        except (URLError, TimeoutError) as error:
            if attempt == 2:
                raise RuntimeError(f"Could not fetch {repo}") from error
        time.sleep(2 ** attempt)
    raise RuntimeError(f"Could not fetch {repo}")


def refresh(text: str, date: str) -> str:
    """Preserve descriptions, links, ordering and all other hand-written text."""
    repos = [match.group("repo") for match in STARS.finditer(text)]
    if not repos or len(repos) != len(set(repo.lower() for repo in repos)):
        raise ValueError("Missing or duplicate star markers")
    if text.count("<!-- stars:") != len(repos):
        raise ValueError("Malformed star marker")
    if len(UPDATED.findall(text)) != 1:
        raise ValueError("Expected exactly one update-date marker")
    counts = {repo: fetch_stars(repo) for repo in repos}
    updated = STARS.sub(
        lambda match: f'{match["start"]}{counts[match["repo"]]:,}{match["end"]}',
        text,
    )
    return UPDATED.sub(lambda match: f'{match["start"]}{date}{match["end"]}', updated)


def main() -> None:
    original = README.read_text(encoding="utf-8")
    updated = refresh(original, datetime.now(timezone.utc).date().isoformat())
    if updated == original:
        print("Star counts and refresh date are already current.")
        return
    temporary = README.with_suffix(".md.tmp")
    temporary.write_text(updated, encoding="utf-8")
    temporary.replace(README)
    print(f"Updated {len(STARS.findall(updated))} project counts and refresh date.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Star refresh failed; README was not changed: {error}", file=sys.stderr)
        sys.exit(1)
