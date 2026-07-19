"""Regenerate the auto-managed OSS-contributions section in README.md.

Searches public PRs authored by USER, groups them by external repository,
and rewrites the marker-delimited block in README.md:

  <!-- OSS-CONTRIB:START --> ... <!-- OSS-CONTRIB:END -->

Each repository is rendered as a shields.io badge followed by its PRs.
The badge label includes the repo's star count ("LightGBM (⭐ 17.2k)"),
the message shows PR counts ("2 merged · 1 open"), and the color is
green once at least one PR is merged, blue while only open PRs exist.
Closed-unmerged PRs are omitted.

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
BADGE_STYLE = "for-the-badge"
# simple-icons slug per repo name; neither LightGBM nor numpyro has one yet
LOGO_OVERRIDES = {}
DEFAULT_LOGO = "github"


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


def fetch_stars(full):
    """Star count of a repository, e.g. 17234."""
    return api_get(f"/repos/{full}")["stargazers_count"]


def format_stars(count):
    """Compact star count: 987 -> '987', 17234 -> '17.2k'."""
    if count < 1000:
        return str(count)
    compact = f"{count / 1000:.1f}".rstrip("0").rstrip(".")
    return f"{compact}k"


def build_contributions():
    repos = {}
    for pr in fetch_prs():
        full = re.sub(r".*/repos/", "", pr["repository_url"])
        owner = full.split("/")[0]
        if owner.lower() == USER.lower():
            continue
        merged = pr.get("pull_request", {}).get("merged_at") is not None
        if not (merged or pr["state"] == "open"):
            continue  # closed without merge
        repos.setdefault(full, []).append(
            {
                "number": pr["number"],
                "title": pr["title"],
                "url": pr["html_url"],
                "merged": merged,
            }
        )

    blocks = []
    ranked = sorted(
        repos, key=lambda r: (-sum(p["merged"] for p in repos[r]), r)
    )
    for full in ranked:
        prs = sorted(repos[full], key=lambda p: -p["number"])
        name = full.split("/")[1]
        prs_url = f"https://github.com/{full}/pulls?q=" + urllib.parse.quote(
            f"is:pr author:{USER}"
        )
        n_merged = sum(p["merged"] for p in prs)
        n_open = len(prs) - n_merged
        counts = []
        if n_merged:
            counts.append(f"{n_merged} merged")
        if n_open:
            counts.append(f"{n_open} open")
        status = " · ".join(counts)
        color = "brightgreen" if n_merged else "blue"
        logo = LOGO_OVERRIDES.get(name, DEFAULT_LOGO)
        label = f"{name} (⭐ {format_stars(fetch_stars(full))})"
        lines = [
            f"[![{name}](https://img.shields.io/badge/"
            f"{badge_label(label)}-{badge_label(status)}-{color}"
            f"?style={BADGE_STYLE}&logo={logo}&logoColor=white)]"
            f"({prs_url})"
        ]
        for p in prs:
            suffix = "" if p["merged"] else " _(under review)_"
            lines.append(f"- [#{p['number']}]({p['url']}) — {p['title']}{suffix}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def replace_block(text, marker, content):
    start, end = f"<!-- {marker}:START -->", f"<!-- {marker}:END -->"
    pattern = re.compile(re.escape(start) + ".*?" + re.escape(end), re.DOTALL)
    return pattern.sub(f"{start}\n{content}\n{end}", text)


def main():
    contributions = build_contributions()
    with open(README, encoding="utf-8") as f:
        text = f.read()
    text = replace_block(text, "OSS-CONTRIB", contributions)
    with open(README, "w", encoding="utf-8") as f:
        f.write(text)
    print(contributions)


if __name__ == "__main__":
    main()
