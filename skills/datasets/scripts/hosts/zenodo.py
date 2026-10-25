"""Zenodo: the public records API, restricted to the dataset resource type."""

from __future__ import annotations

import json
import urllib.parse

NAME = "zenodo"
API = "https://zenodo.org/api/records"


def search(query, http, limit=20):
    url = f"{API}?{urllib.parse.urlencode({'q': query, 'type': 'dataset', 'size': limit})}"
    _status, text = http("GET", url)
    hits = []
    for record in ((json.loads(text) or {}).get("hits") or {}).get("hits") or []:
        if not isinstance(record, dict) or record.get("id") is None:
            continue
        meta = record.get("metadata") or {}
        license_info = meta.get("license") or {}
        ref = str(record["id"])
        hits.append({"ref": ref, "title": meta.get("title") or ref,
                     "license": license_info.get("id", "") if isinstance(license_info, dict) else "",
                     "url": (record.get("links") or {}).get("self_html") or f"https://zenodo.org/records/{ref}"})
    return hits[:limit]
