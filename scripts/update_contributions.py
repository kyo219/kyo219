"""Regenerate the auto-managed OSS-contribution sections of README.md.

Searches public PRs authored by USER, groups them by external repository,
and rewrites the marker-delimited blocks in README.md:

  <!-- OSS-BADGES:START --> ... <!-- OSS-BADGES:END -->
  <!-- OSS-TABLE:START -->  ... <!-- OSS-TABLE:END -->

Only the GitHub REST API and the Python standard library are used, so the
script runs as-is inside GitHub Actions with the default GITHUB_TOKEN.
"""

import json
import os
import re
import urllib.parse
import urllib.request

USER = "kyo219"
README = os.path.join(os.path.dirname(__file__), "..", "README.md")
API = "https://api.github.com"


def api_get(path, params=None):
    url = f"{API}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as res:
        return json.load(res)


def fetch_prs():
    """All public PRs authored by USER, newest first."""
    items, page = [], 1
    while True:
        data = api_get(
            "/search/issues",
            {
                "q": f"author:{USER} type:pr is:public",
                "per_page": 100,
                "page": page,
            },
        )
        items += data["items"]
        if len(items) >= data["total_count"] or not data["items"]:
            return items
        page += 1


def badge_label(text):
    """Escape a shields.io static-badge label."""
    return urllib.parse.quote(text.replace("-", "--").replace("_", "__"))


def build_sections():
    repos = {}
    for pr in fetch_prs():
        full = re.sub(r".*/repos/", "", pr["repository_url"])
        owner = full.split("/")[0]
        if owner.lower() == USER.lower():
            continue
        merged = pr.get("pull_request", {}).get("merged_at") is not None
        is_open = pr["state"] == "open"
        entry = repos.setdefault(full, {"merged": 0, "open": 0})
        entry["merged"] += merged
        entry["open"] += is_open

    # drop repos where nothing was merged and nothing is in flight
    repos = {k: v for k, v in repos.items() if v["merged"] or v["open"]}
    stars = {full: api_get(f"/repos/{full}")["stargazers_count"] for full in repos}
    ranked = sorted(repos, key=lambda r: (-stars[r], r))

    badges, rows = [], []
    for full in ranked:
        name = full.split("/")[1]
        counts = repos[full]
        prs_url = f"https://github.com/{full}/pulls?q=" + urllib.parse.quote(
            f"is:pr author:{USER}"
        )
        if counts["merged"]:
            status, color = "contributor", "brightgreen"
        else:
            status, color = "PR under review", "blue"
        badges.append(
            f"[![{name}](https://img.shields.io/badge/"
            f"{badge_label(name)}-{badge_label(status)}-{color}?logo=github)]"
            f"({prs_url})"
        )
        rows.append(
            f"| [{full}](https://github.com/{full}) | ⭐ {stars[full]:,} "
            f"| {counts['merged']} | {counts['open']} |"
        )

    table = [
        "| Repository | Stars | Merged PRs | Open PRs |",
        "| --- | --- | --- | --- |",
        *rows,
    ]
    return "\n".join(badges), "\n".join(table)


def replace_block(text, marker, content):
    start, end = f"<!-- {marker}:START -->", f"<!-- {marker}:END -->"
    pattern = re.compile(re.escape(start) + ".*?" + re.escape(end), re.DOTALL)
    return pattern.sub(f"{start}\n{content}\n{end}", text)


def main():
    badges, table = build_sections()
    with open(README, encoding="utf-8") as f:
        text = f.read()
    text = replace_block(text, "OSS-BADGES", badges)
    text = replace_block(text, "OSS-TABLE", table)
    with open(README, "w", encoding="utf-8") as f:
        f.write(text)
    print(badges, table, sep="\n\n")


if __name__ == "__main__":
    main()
