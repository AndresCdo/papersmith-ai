"""OpenNeuro: the public GraphQL endpoint (BIDS datasets: EEG, MEG, MRI).

The query is the endpoint's ``advancedSearch`` over public datasets by
keyword (verified against the live endpoint on 2026-10-24; the older
``search(q:)`` field answers null). A schema change there surfaces as this
host's recorded failure, never as a fatal error.
"""

from __future__ import annotations

import json

NAME = "openneuro"
API = "https://openneuro.org/crn/graphql"
QUERY = """query Search($q: DatasetSearchInput!, $first: Int) {
  advancedSearch(query: $q, first: $first) {
    edges { node { id latestSnapshot { description { Name License } } } }
  }
}"""


def search(query, http, limit=20):
    body = json.dumps({"query": QUERY, "variables": {"q": {"keywords": [query], "publicOnly": True},
                                                       "first": limit}})
    _status, text = http("POST", API, body=body, headers={"Content-Type": "application/json"})
    payload = json.loads(text) or {}
    if payload.get("errors"):
        raise OSError(f"graphql: {str(payload['errors'])[:200]}")
    edges = (((payload.get("data") or {}).get("advancedSearch") or {}).get("edges")) or []
    hits = []
    for edge in edges:
        node = (edge or {}).get("node") or {}
        ref = node.get("id")
        if not ref:
            continue
        description = ((node.get("latestSnapshot") or {}).get("description")) or {}
        hits.append({"ref": ref, "title": description.get("Name") or ref,
                     "license": description.get("License") or "",
                     "url": f"https://openneuro.org/datasets/{ref}"})
    return hits[:limit]
