"""Hugging Face Hub: the public dataset listing API, no token needed."""

from __future__ import annotations

import json
import urllib.parse

NAME = "huggingface"
API = "https://huggingface.co/api/datasets"


def search(query, http, limit=20):
    url = f"{API}?{urllib.parse.urlencode({'search': query, 'limit': limit})}"
    _status, text = http("GET", url)
    hits = []
    for item in json.loads(text) or []:
        ref = item.get("id") if isinstance(item, dict) else None
        if not ref:
            continue
        license_tag = next((tag.split(":", 1)[1] for tag in item.get("tags") or []
                            if isinstance(tag, str) and tag.startswith("license:")), "")
        hits.append({"ref": ref, "title": ref.split("/")[-1], "license": license_tag,
                     "url": f"https://huggingface.co/datasets/{ref}"})
    return hits[:limit]
