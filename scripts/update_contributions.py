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
# Hand-written per-PR copy keyed by "owner/repo#number". The block is
# regenerated from GitHub PR titles, so richer copy must live here to
# survive. Fields (all optional):
#   title   — replaces the fetched PR title, rendered in bold
#   summary — sub-bullet describing what the change does
#   why     — sub-bullet rendered as "**Why it matters:** ..."
OVERRIDES = {
    "lightgbm-org/LightGBM#7247": {
        "title": "Added LightGBM-MoE to the official external repositories list",
        "summary": (
            "Documented a C++-native Mixture-of-Experts extension that "
            "combines specialized GBDTs through a learned gating function."
        ),
        "why": (
            "It makes regime-aware gradient boosting easier to discover for "
            "problems where one global model struggles with heterogeneous "
            "data, such as changing market conditions or distinct user "
            "segments."
        ),
    },
    "lightgbm-org/LightGBM#7246": {
        "title": "Added native `int8` input support for pre-discretized features",
        "summary": (
            "Eliminates the intermediate `float32` copy at the Python–C++ "
            "boundary, reducing feature-matrix memory usage by up to 75% "
            "while preserving identical predictions."
        ),
        "why": (
            "Large, low-cardinality datasets can be passed to LightGBM "
            "without temporarily quadrupling their memory footprint, making "
            "training and inference more practical in memory-constrained "
            "environments."
        ),
    },
    "pyro-ppl/numpyro#2222": {
        "title": (
            "Removed unnecessary deep copies in module sampling and "
            "batch-shape promotion"
        ),
        "summary": (
            "Replaced full parameter and distribution copies with "
            "structure-only or shallow copies, substantially lowering peak "
            "memory usage and making eager batch-shape promotion about 3× "
            "faster on large arrays."
        ),
        "why": (
            "Bayesian inference with large neural networks and distributions "
            "can avoid duplicating gigabytes of unchanged parameters, "
            "reducing out-of-memory failures and improving eager-execution "
            "performance without changing model behavior."
        ),
    },
}


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
        entries = []
        for p in prs:
            o = OVERRIDES.get(f"{full}#{p['number']}", {})
            title = f"**{o['title']}**" if "title" in o else p["title"]
            entry = [f"- [#{p['number']}]({p['url']}) — {title}"]
            if not p["merged"]:
                entry[0] += " _(under review)_"
            if o.get("summary"):
                entry.append(f"  - {o['summary']}")
            if o.get("why"):
                entry.append(f"  - **Why it matters:** {o['why']}")
            entries.append("\n".join(entry))
        # blank line between multi-line entries so sub-bullets read cleanly
        sep = "\n\n" if any("\n" in e for e in entries) else "\n"
        lines.append(sep.join(entries))
        blocks.append("\n\n".join(lines) if sep == "\n\n" else "\n".join(lines))
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
