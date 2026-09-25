#!/usr/bin/env python3
"""Fetch aggregate stars, sort descending, and render the bilingual profile.

Only explicitly curated public repositories are queried, never stargazer lists.
All API reads and rendering must succeed before any generated file is changed.
Uses Python 3.10+ and its standard library only.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
import time
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from render_profile import build_outputs, validate_projects

ROOT = Path(__file__).resolve().parents[1]
PROFILE_TIMEZONE = ZoneInfo("Asia/Shanghai")


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


def main() -> None:
    projects = json.loads((ROOT / "profile/projects.json").read_text(encoding="utf-8"))
    validate_projects(projects)
    intro = (ROOT / "profile/intro.md").read_text(encoding="utf-8")
    footer = (ROOT / "profile/footer.md").read_text(encoding="utf-8")
    counts = {project["repo"]: fetch_stars(project["repo"]) for project in projects}
    # Use the same timezone as the schedule, including the date after midnight.
    date = datetime.now(PROFILE_TIMEZONE).date().isoformat()
    outputs = build_outputs(intro, projects, counts, date, footer)
    outputs["profile/stars.json"] = json.dumps(
        {"date": date, "timezone": PROFILE_TIMEZONE.key, "counts": counts},
        ensure_ascii=False, indent=2
    ) + "\n"
    changed = 0
    for relative, content in outputs.items():
        path = ROOT / relative
        if path.exists() and path.read_text(encoding="utf-8") == content:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(path)
        changed += 1
    print(f"Refreshed {len(projects)} projects, sorted by stars; {changed} files changed.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Profile refresh failed: {error}", file=sys.stderr)
        sys.exit(1)
